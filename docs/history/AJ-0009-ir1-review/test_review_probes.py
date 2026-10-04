"""Review-only regression and process tests. Expected safety failures are evidence."""
import sys
sys.path.insert(0, '/workspace/Command-Center-Gravity')
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
from dataclasses import replace
from pathlib import Path
import multiprocessing
import tempfile
import unittest
from dispatcher.mock_sheets import MockAuthority, MockSheets
from dispatcher.sheets_writer import SheetsWriter, RecoveryChange, Outcome
from dispatcher.writer_journal import WriterJournal
from dispatcher.model import ProtocolError, Conflict
from tests.test_sheets_writer import request, SCOPE, AUTH, NOW, RepositoryIntegrationTests


def claim_racer(journal_path, provider_path, actor, ready, start, queue):
    writer=SheetsWriter(WriterJournal(journal_path,SCOPE),MockSheets(provider_path,SCOPE),MockAuthority(),clock=lambda:NOW)
    ready.set()
    if not start.wait(5):
        raise AssertionError('race gate timed out')
    try:
        token=writer.claim(actor,AUTH)
        result=writer.write(request(),token)
        queue.put(('claimed',actor,str(result.outcome)))
    except ProtocolError:
        queue.put(('blocked',actor))

class ReviewChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        self.journal=WriterJournal(str(self.path/'journal.db'),SCOPE)
        self.mock=MockSheets(str(self.path/'provider.db'),SCOPE)
        self.authority=MockAuthority()
        self.writer=SheetsWriter(self.journal,self.mock,self.authority,clock=lambda:NOW)
        self.token=self.writer.claim('Dẹkun',AUTH)
    def change(self,r):
        return RecoveryChange('review://change',r.condition,'verified-fixed','mock-fallback','LOCAL changed-condition evidence',True,AUTH,NOW,SCOPE,r.operation_id,r.digest)
    def test_authenticated_revocation_during_final_recovery_preflight_survives_restart(self):
        r=request();self.mock.plan('tool-noop');self.writer.write(r,self.token)
        inspect=self.authority.inspect;seen=[]
        def flipping(reference,scope,actor):
            grant=replace(inspect(reference,scope,actor),state='revoked' if len(seen)==2 else 'valid')
            seen.append(grant.state)
            return grant
        self.authority.inspect=flipping
        with self.assertRaises(ProtocolError):self.writer.recover(r.operation_id,self.change(r),self.token)
        self.assertEqual(seen,['valid','valid','revoked'])
        self.authority.inspect=inspect
        replacement=SheetsWriter(WriterJournal(str(self.path/'journal.db'),SCOPE),MockSheets(str(self.path/'provider.db'),SCOPE),self.authority,clock=lambda:NOW)
        replacement.retire(self.token,AUTH,'root explicitly retires old writer; no renewed mutation authority')
        token=replacement.claim('replacement',AUTH)
        try:
            replacement.recover(r.operation_id,self.change(r),token)
        except ProtocolError:
            pass
        self.assertEqual(len(self.mock.calls),1,'Genuine revocation was forgotten: replacement submitted a recovery without renewed authority')
    def test_authenticated_initial_denial_cannot_be_erased_by_fresh_operation_context(self):
        r=request();self.authority.states[AUTH]='denied'
        self.assertEqual(self.writer.write(r,self.token).outcome,Outcome.FAILED)
        self.authority.states[AUTH]='valid' # same old grant reference; no explicit reviewed renewal
        try:self.writer.write(replace(r,operation_id='new-id',context_ref='review://new-context'),self.token)
        except ProtocolError:pass
        self.assertEqual(len(self.mock.calls),0,'Authenticated denial was forgotten across a fresh operation context')
    def test_two_processes_race_to_claim_single_shared_journal(self):
        self.writer.retire(self.token,AUTH,'retire before independent race')
        ctx=multiprocessing.get_context('fork');start=ctx.Event();queue=ctx.Queue()
        ready=[ctx.Event(),ctx.Event()]
        children=[ctx.Process(target=claim_racer,args=(str(self.path/'journal.db'),str(self.path/'provider.db'),f'racer-{i}',ready[i],start,queue)) for i in range(2)]
        for child in children:child.start()
        try:
            for event in ready:self.assertTrue(event.wait(5))
            start.set()
            for child in children:
                child.join(5);self.assertFalse(child.is_alive());self.assertEqual(child.exitcode,0)
            outcomes=[queue.get(timeout=2),queue.get(timeout=2)]
            self.assertEqual(sorted(r[0] for r in outcomes),['blocked','claimed'])
            self.assertEqual(len(self.mock.calls),1)
        finally:
            for child in children:
                if child.is_alive():child.terminate();child.join()
            queue.close()

class BridgeChecks(RepositoryIntegrationTests):
    # This suite explicitly loads only the added method, avoiding inherited reruns.
    def test_expected_spec_epoch_attempt_are_compared_at_current_record_revision(self):
        h=self.harness();record=h.record;calls=len(self.mock.calls)
        for field in ('spec_revision','run_epoch','attempt'):
            with self.subTest(field=field),self.assertRaises(Conflict):
                h.repo.commit(record,record.version,replace(record.lineage,**{field:2}),'Dẹkun')
        self.assertEqual(len(self.mock.calls),calls)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReviewChecks)
    suite.addTest(BridgeChecks('test_expected_spec_epoch_attempt_are_compared_at_current_record_revision'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
