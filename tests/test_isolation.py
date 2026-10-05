"""Synthetic AJ16 acceptance cases; no real coordinates or data."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest

from dispatcher.git_ledger import GitLedger, digest
from dispatcher.git_transport import MemoryGitTransport
from dispatcher.model import AgentJob, Status, ProtocolError
from dispatcher.isolation import (bootstrap, cell, string_row, validate_cell, verify_manifest,
    import_snapshot, LocalAuthorityProvider, IsolationCoordinator, ROUTES)


def fixture_manifest():
    rows = {f'AJ-{8000+i}': [cell('string', v) for v in AgentJob(
        f'AJ-{8000+i}', job_deliverable='Invented task '+str(i), status=s).to_cells()]
        for i, s in enumerate(Status)}
    return bootstrap(rows, provisional_ids=['AJ-8001'],
        privacy_policy='synthetic-only; no bodies, secrets or personal data; no normalization',
        provenance='synthetic://accepted-snapshot/fixture-v1')


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.m = fixture_manifest(); self.d = digest(self.m)
        self.t = MemoryGitTransport(); self.l = GitLedger(Path(self.temp.name)/'ledger', self.t)
        self.token = self.l.acquire('synthetic-writer')
        self.p = LocalAuthorityProvider(Path(self.temp.name)/'authority')
        self.c = IsolationCoordinator(self.p, self.l, self.m, self.d)

    def prepare(self):
        self.c.initialize(); self.c.transition('LEGACY', 'HELD'); self.c.transition('HELD', 'PREPARING')
        return import_snapshot(self.l, self.token, self.m, self.d)

    def active(self):
        h = self.prepare(); self.c.activate(h); return h

    def test_exact_bootstrap_all17_all7_one_event_per_commit(self):
        h = self.prepare(); state = self.l._remote()[2]
        self.assertEqual(state['rows'], {j:string_row(c) for j,c in self.m['rows'].items()})
        self.assertEqual({v[4] for v in state['rows'].values()}, {s.value for s in Status})
        self.assertEqual((self.t.commits, self.t.calls), (7,7))
        self.assertEqual(h, import_snapshot(self.l,self.token,self.m,self.d))
        self.assertEqual((self.t.commits, self.t.calls), (7,7))
        for cells in self.m['rows'].values(): self.assertEqual(len(cells),17)

    def test_deterministic_manifest_reconciliation_provisional_unknown(self):
        self.assertEqual(self.m, fixture_manifest()); verify_manifest(self.m,self.d)
        self.assertEqual(self.m['audit_exception']['legacy_unconditional_write'],'UNKNOWN')
        self.assertEqual(self.m['provisional_ids'],['AJ-8001'])
        for j,cells in self.m['rows'].items(): self.assertEqual(self.m['reconciliation'][j],[digest(c) for c in cells])

    def test_wrong_repo_ref_source_columns_provenance_digest_rejected(self):
        for key in ('repo','ref','source','columns','source_digest','operations','reconciliation','identity','audit_exception'):
            bad = deepcopy(self.m); bad[key] = 'invented-wrong'
            with self.subTest(key=key), self.assertRaises((ProtocolError, TypeError)):
                verify_manifest(bad,digest(bad))
        with self.assertRaises(ProtocolError): verify_manifest(self.m,'wrong')

    def test_delayed_old_write_during_bootstrap_and_after_activation(self):
        old = deepcopy(self.m['rows']); h = self.prepare()
        old['AJ-8001'][4] = cell('string','Cancelled')
        self.c.activate(h)
        old['AJ-8001'][4] = cell('string','Done')
        self.assertEqual(self.c.dispatch('AJ-8001',surface='new',epoch=1,head=h)['epoch'],1)
        self.assertEqual(self.l._remote()[2]['rows']['AJ-8001'][4],'Ready')
        self.assertEqual(self.p.read()['exception']['legacy_unconditional_write'],'UNKNOWN')

    def test_all_legacy_routes_and_uninventoried_routes_denied(self):
        h = self.active()
        for r in ROUTES:
            with self.subTest(route=r), self.assertRaises(ProtocolError): self.c.gate(r,'legacy',0,h)
            self.c.gate(r,'new',1,h)
        with self.assertRaises(ProtocolError): self.c.gate('new-hidden-route','new',1,h)

    def test_stale_ready_cached_queued_retired_epoch(self):
        h = self.active()
        for surface,epoch,head in [('legacy',0,h),('new',0,h),('new',2,h),('new',1,'stale')]:
            with self.subTest(surface=surface,epoch=epoch,head=head), self.assertRaises(ProtocolError):
                self.c.dispatch('AJ-8001',surface=surface,epoch=epoch,head=head)
        with self.assertRaises(ProtocolError): self.c.dispatch('AJ-8000',surface='new',epoch=1,head=h)

    def test_missing_and_contradictory_epoch_holds(self):
        with self.assertRaises(ProtocolError): self.c.gate('reader','new',1,'none')
        h = self.active(); s = self.p.read(); bad=deepcopy(s); bad['selected']='legacy'; self.p.cas(s,bad)
        with self.assertRaises(ProtocolError): self.c.gate('reader','new',1,h)

    def test_crash_before_after_switch_one_selected_authority(self):
        h = self.prepare(); restarted = IsolationCoordinator(self.p,self.l,self.m,self.d)
        with self.assertRaises(ProtocolError): restarted.gate('reader','new',1,h)
        restarted.activate(h)
        restarted = IsolationCoordinator(LocalAuthorityProvider(self.p.path),self.l,self.m,self.d)
        restarted.gate('reader','new',1,h)
        with self.assertRaises(ProtocolError): restarted.activate(h)
        self.assertEqual(self.p.read()['selected'],'new')

    def test_independent_coordinators_shared_provider_only_one_wins(self):
        h = self.prepare(); barrier=threading.Barrier(2); results=[]
        def run():
            c = IsolationCoordinator(LocalAuthorityProvider(self.p.path), self.l, self.m, self.d)
            barrier.wait()
            try: c.activate(h); results.append('won')
            except ProtocolError: results.append('held')
        threads=[threading.Thread(target=run) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(sorted(results),['held','won'])

    def test_lost_response_same_identity_no_replay(self):
        self.t.mode='lost'; h=self.prepare()
        self.assertEqual(self.t.calls,7)
        restarted = GitLedger(self.l.path,self.t)
        self.assertEqual(import_snapshot(restarted,self.token,self.m,self.d),h)
        self.assertEqual((self.t.calls,self.t.commits),(7,7))

    def test_unknown_without_landing_holds_never_noop(self):
        self.t.mode='unknown'
        with self.assertRaises(ProtocolError):self.prepare()
        self.assertEqual(self.p.read()['phase'],'PREPARING')
        self.assertEqual(self.t.calls,1)
        with self.assertRaises(ProtocolError):import_snapshot(self.l,self.token,self.m,self.d)
        self.assertEqual(self.t.calls,1)

    def test_corruption_fork_stale_heads_holds(self):
        h=self.active()
        self.t.remote='invented-missing-object'
        with self.assertRaises((ProtocolError,KeyError)):self.c.gate('reader','new',1,h)
        self.t.remote=h; self.t.objects[h][1]['snapshot.json']=b'{}'
        with self.assertRaises(ProtocolError):self.c.gate('reader','new',1,h)

    def test_projection_never_promotes_authority(self):
        h=self.prepare(); self.l.projection({})
        self.assertEqual(self.p.read()['phase'],'PREPARING')
        with self.assertRaises(ProtocolError):self.c.gate('reader','new',1,h)

    def test_rollback_holds_no_old_reactivation(self):
        h=self.active(); self.c.rollback_hold()
        for surface in ('legacy','new'):
            with self.assertRaises(ProtocolError):self.c.gate('reader',surface,1,h)
        with self.assertRaises(ProtocolError):self.c.transition('HELD','PREPARING')
        with self.assertRaises(ProtocolError):self.c.activate(h)
        self.assertEqual(self.p.read()['epoch'],1)

    def test_native_typed_cells_preserve_and_reject_lossy_string_export(self):
        cases=[cell('date_serial',46200.125,format='yyyy-mm-dd hh:mm',timezone='Africa/Lagos'),
               cell('datetime','2026-10-05T13:00:00+01:00',timezone='Africa/Lagos'),
               cell('blank'),cell('absent'),cell('formula','=A1+1',format='0.00'),cell('number',123)]
        for c in cases:
            self.assertEqual(validate_cell(json.loads(json.dumps(c))),c)
            cells=deepcopy(self.m['rows']['AJ-8000']); cells[6]=c
            with self.assertRaises(ProtocolError):string_row(cells)
        self.assertNotEqual(cases[2],cases[3])
        self.assertEqual(cell('string','  Exact\nText  ')['value'],'  Exact\nText  ')
        with self.assertRaises(ProtocolError): cell('number',True)
        with self.assertRaises(ValueError): cell('number',float('nan'))
        with self.assertRaises(ProtocolError): cell('datetime','2026-10-05',timezone='UTC')

    def test_privacy_minimization_explicit_not_normalization(self):
        with self.assertRaises(ProtocolError):bootstrap(self.m['rows'],provisional_ids=[],privacy_policy='',provenance=self.m['provenance'])
        bad=deepcopy(self.m['rows']);bad['AJ-8000'][2]=cell('string','  invented exact  ')
        m=bootstrap(bad,provisional_ids=[],privacy_policy=self.m['privacy_policy'],provenance=self.m['provenance'])
        self.assertEqual(string_row(m['rows']['AJ-8000'])[2],'  invented exact  ')

    def test_process_death_before_and_after_atomic_switch(self):
        h = self.prepare()
        before = os.fork()
        if before == 0:
            os._exit(0)  # PREPARING already durable; no switch decision
        self.assertEqual(os.waitpid(before, 0)[1], 0)
        with self.assertRaises(ProtocolError): self.c.gate('reader','new',1,h)
        after = os.fork()
        if after == 0:
            try:
                self.c.activate(h)
                os._exit(0)  # die without returning switch result to parent
            except BaseException:
                os._exit(1)
        self.assertEqual(os.waitpid(after, 0)[1], 0)
        restarted = IsolationCoordinator(LocalAuthorityProvider(self.p.path),self.l,self.m,self.d)
        restarted.gate('reader','new',1,h)
        with self.assertRaises(ProtocolError): restarted.activate(h)

    def test_two_process_coordinators_shared_provider_only_one_wins(self):
        h = self.prepare(); readfd,writefd = os.pipe(); children=[]
        for _ in range(2):
            pid=os.fork()
            if pid==0:
                os.close(writefd); os.read(readfd,1); os.close(readfd)
                try:
                    IsolationCoordinator(LocalAuthorityProvider(self.p.path),self.l,self.m,self.d).activate(h)
                    os._exit(0)
                except ProtocolError:
                    os._exit(2)
                except BaseException:
                    os._exit(3)
            children.append(pid)
        os.close(readfd); os.write(writefd,b'xx'); os.close(writefd)
        statuses=sorted(os.waitpid(pid,0)[1] for pid in children)
        self.assertEqual(statuses,[0,2 << 8])
        self.assertEqual(self.p.read()['selected'],'new')
