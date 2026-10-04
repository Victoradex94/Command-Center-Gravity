"""Independent acknowledgement review: simulated transport only."""
import sys
sys.path.insert(0, "/workspace/Command-Center-Gravity")
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
import json
import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from tests.test_google_sheets import AdapterTests, FakeConnector
from dispatcher.google_sheets import GoogleSheetsAdapter, ReceiptJournal
from dispatcher.model import ProtocolError, ReconciliationRequired
from dispatcher.sheets_writer import Effect, Outcome, SheetsWriter
from dispatcher.writer_journal import WriterJournal
from dispatcher.mock_sheets import MockAuthority
from dispatcher.sheets_sandbox import SOURCE, CREATE_ID, UPDATE_ID, plan, execute_once, reconcile_existing

class AckProbes(unittest.TestCase):
    setUp = AdapterTests.setUp
    writer = AdapterTests.writer

    def alter_receipt(self, change):
        body = self.adapter.receipts.get(self.sub)
        change(body)
        with self.adapter.receipts.connect() as db:
            db.execute("UPDATE receipts SET body=? WHERE attempt=?", (json.dumps(body), self.sub.attempt_id))

    def test_applied_crash_before_response_retention_never_settles_or_replays(self):
        original=self.fake.__call__
        class Death(BaseException): pass
        def call(name, args):
            result=original(name,args)
            if name.endswith("batch_update_spreadsheet"): raise Death()
            return result
        self.adapter.call=call
        with self.assertRaises(Death): self.adapter.submit(self.sub)
        restarted=GoogleSheetsAdapter(self.target,self.fake,ReceiptJournal(self.path,self.target))
        for _ in range(2):
            obs=restarted.inspect(self.sub)
            self.assertEqual(obs.effect,Effect.UNKNOWN)
            self.assertFalse(obs.settled)
        with self.assertRaises(ProtocolError): restarted.submit(self.sub)
        self.assertEqual(len(self.fake.writes),1)

    def test_retained_ack_crash_before_marker_adopts_using_fresh_objects(self):
        writer=self.writer()
        token=writer.claim("Dẹkun",self.req.authority_ref)
        class Death(BaseException): pass
        def inspect(sub): raise Death()
        self.adapter.inspect=inspect
        with self.assertRaises(Death): writer.write(self.req,token)
        self.adapter=GoogleSheetsAdapter(self.target,self.fake,ReceiptJournal(self.path,self.target))
        restarted=self.writer()
        self.assertEqual(restarted.reconcile(CREATE_ID).outcome,Outcome.SUCCESS)
        self.assertEqual(restarted.read(self.req.job_id).cells,self.req.cells)
        self.assertEqual(restarted.reconcile(CREATE_ID).outcome,Outcome.SUCCESS)
        self.assertEqual(len(self.fake.writes),1)

    def test_success_payload_cannot_overrule_recorded_exception(self):
        self.adapter.submit(self.sub)
        self.alter_receipt(lambda body: body.update(exception_type="TimeoutError"))
        obs=self.adapter.inspect(self.sub)
        self.assertEqual(obs.effect,Effect.UNKNOWN)
        self.assertFalse(obs.settled)
        self.assertEqual(obs.signal,"timeout")
        self.assertEqual(len(self.fake.writes),1)

    def test_success_payload_cannot_settle_different_stored_request(self):
        self.adapter.submit(self.sub)
        def change(body):
            body["request"]["requests"][0]["updateCells"]["range"]["startColumnIndex"]=1
        self.alter_receipt(change)
        self.assertFalse(self.adapter.inspect(self.sub).settled)
        self.assertEqual(len(self.fake.writes),1)

    def test_applied_timeout_stays_fenced_after_route_returns_to_normal(self):
        self.fake.mode="apply-timeout"
        writer=self.writer();token=writer.claim("Dẹkun",self.req.authority_ref)
        first=writer.write(self.req,token)
        self.assertEqual(first.outcome,Outcome.UNCERTAIN)
        self.fake.mode="apply"
        self.adapter=GoogleSheetsAdapter(self.target,self.fake,ReceiptJournal(self.path,self.target))
        restart=self.writer()
        for _ in range(3):
            result=restart.reconcile(CREATE_ID)
            self.assertEqual(result.outcome,Outcome.UNCERTAIN)
            self.assertEqual(result.fingerprint,first.fingerprint)
            self.assertEqual(result.recovery_used,0)
        with self.assertRaises(ReconciliationRequired):
            writer.write(replace(self.req,operation_id="replacement-label"),token)
        self.assertEqual(len(self.fake.writes),1)

    def test_pending_retry_metadata_blocks_positive_native_shaped_payload(self):
        self.adapter.submit(self.sub)
        def change(body): body["response"]["_meta"]={"pendingRetry": True}
        self.alter_receipt(change)
        obs=self.adapter.inspect(self.sub)
        self.assertFalse(obs.settled)
        self.assertEqual(obs.effect,Effect.UNKNOWN)
        self.assertEqual(len(self.fake.writes),1)

    def test_permissions_drift_after_ack_does_not_settle(self):
        self.adapter.submit(self.sub)
        self.fake.file["shared"]=True
        self.assertFalse(self.adapter.inspect(self.sub).settled)
        self.assertEqual(len(self.fake.writes),1)

    def test_exact_saved_fixture_two_writes_restart_zero_replay(self):
        stored=json.loads(Path("docs/AJ-0010-fixture-plan.json").read_text())
        fixture=plan(stored["planned_at"])
        for key,request in (("create",fixture.create),("update",fixture.update)):
            self.assertEqual(json.loads(json.dumps(asdict(request))),stored[key])
        target=replace(self.target,source_keys=(SOURCE,))
        fake=FakeConnector(target)
        receipt_path=str(Path(self.temp.name)/"fixture-receipts.sqlite")
        writer_path=str(Path(self.temp.name)/"fixture-writer.sqlite")
        adapter=GoogleSheetsAdapter(target,fake,ReceiptJournal(receipt_path,target))
        before=adapter.capture()
        writer=SheetsWriter(WriterJournal(writer_path,target.scope),adapter,MockAuthority())
        token=writer.claim("Dẹkun",fixture.create.authority_ref)
        result=execute_once(writer,token,fixture)
        self.assertEqual(result["create"].outcome,Outcome.SUCCESS)
        self.assertEqual(result["update"].outcome,Outcome.SUCCESS)
        self.assertEqual(len(fake.writes),2)
        restarted_adapter=GoogleSheetsAdapter(target,fake,ReceiptJournal(receipt_path,target))
        restarted=SheetsWriter(WriterJournal(writer_path,target.scope),restarted_adapter,MockAuthority())
        outcomes=reconcile_existing(restarted)
        self.assertEqual(set(outcomes),{CREATE_ID,UPDATE_ID})
        self.assertTrue(all(o.outcome==Outcome.SUCCESS for o in outcomes.values()))
        current=restarted.read("AJ-0010")
        self.assertEqual(current.cells,fixture.update.cells)
        self.assertEqual(current.revision,2)
        self.assertEqual(current.lineage,fixture.update.intended_lineage)
        self.assertEqual(len(fake.writes),2)
        self.assertTrue(adapter.unchanged_structure(before,restarted_adapter.capture(),2))

if __name__ == "__main__": unittest.main(defaultTest="AckProbes", verbosity=2)
