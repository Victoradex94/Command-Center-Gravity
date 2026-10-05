"""AJ-0016 opt-in OFFLINE isolation capsule; never imported by the live engine.

Separate v1 control contract, not an extension of AJ15's closed Git file schema.
Only cooperating processes sharing this POSIX provider have atomic decisions.
"""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path

from .git_ledger import canonical, digest, Operation
from .model import AGENT_JOB_COLUMNS, AgentJob, Status, Lineage, ProtocolError, require

REPO = 'Victoradex94/Command-Center-Gravity'
REF = 'refs/heads/aj-0016-isolation-prototype-v1'
BASE = 'ce956abbe6b8217c1101edea1cbed6f8c9addeb3'
SOURCE = 'synthetic://invented-sheet/agent-jobs/A1:Q8'
LINEAGE = 'AJ-0016/s1/r1/a1/VA-ISOLATION-0016-01'
ROUTES = ('reader', 'allocator', 'dispatcher', 'writer', 'cache', 'reverse_sync')
PROVISIONAL = 'PENDING_CANONICAL_RECONCILIATION'


def cell(kind, value=None, *, format='', timezone=''):
    """No normalization: explicit blank/absent, native serials and formula semantics."""
    result = {'kind': kind, 'value': value, 'format': format, 'timezone': timezone}
    validate_cell(result)
    return result


def validate_cell(c):
    require(type(c) is dict and set(c) == {'kind', 'value', 'format', 'timezone'}, 'closed typed cell required')
    k, v = c['kind'], c['value']
    require(type(c['format']) is str and type(c['timezone']) is str, 'exact metadata required')
    require(k in ('string', 'number', 'date_serial', 'datetime', 'blank', 'absent', 'formula'), 'unsupported cell')
    if k in ('blank', 'absent'):
        require(v is None, 'blank/absent has no value')
    elif k in ('number', 'date_serial'):
        require(type(v) in (int, float), 'native number required')
        canonical(v)  # rejects NaN/infinity; no float/date coercion
        if k == 'date_serial':
            require(bool(c['timezone']) and bool(c['format']), 'date serial semantics missing')
    elif k == 'datetime':
        require(type(v) is str and bool(c['timezone']), 'datetime semantics missing')
        try:
            require(datetime.fromisoformat(v).tzinfo is not None, 'timezone-aware native datetime required')
        except ValueError as exc:
            raise ProtocolError('invalid native datetime') from exc
    else:
        require(type(v) is str, 'exact string required')
        if k == 'formula':
            require(v.startswith('='), 'formula expression required')
    return deepcopy(c)


def string_row(cells):
    """AJ15 export is exact only for literal strings without extra semantics."""
    require(type(cells) is list and len(cells) == 17, 'exact 17 cells required')
    for c in cells:
        validate_cell(c)
        require(c['kind'] == 'string' and not c['format'] and not c['timezone'],
                'unsupported/lossy AJ15 string conversion; retain typed capsule')
    values = [c['value'] for c in cells]
    AgentJob.from_cells(values)
    return values


def bootstrap(rows, *, provisional_ids, privacy_policy, provenance):
    """Build synthetic accepted-candidate manifest, never manufacture past events."""
    require(privacy_policy == 'synthetic-only; no bodies, secrets or personal data; no normalization', 'explicit privacy policy required')
    require(type(provenance) is str and provenance.startswith('synthetic://'), 'synthetic provenance required')
    require(type(rows) is dict and bool(rows), 'nonempty synthetic snapshot required')
    require(type(provisional_ids) is list and len(set(provisional_ids)) == len(provisional_ids)
            and set(provisional_ids) <= set(rows), 'explicit provisional inclusion required')
    for job, cells in rows.items():
        values = string_row(cells)
        Lineage(job, 1, 1, 1)
        require(values[0] == job, 'source identity mismatch')
    source_digest = digest(rows)
    manifest = {'version': 1, 'repo': REPO, 'ref': REF, 'base': BASE, 'source': SOURCE,
                'lineage': LINEAGE, 'identity': PROVISIONAL, 'columns': list(AGENT_JOB_COLUMNS),
                'statuses': [s.value for s in Status], 'source_digest': source_digest,
                'rows': deepcopy(rows), 'provisional_ids': sorted(provisional_ids),
                'privacy_policy': privacy_policy, 'provenance': provenance,
                'reconciliation': {j: [digest(c) for c in cells] for j, cells in sorted(rows.items())},
                'operations': {j: 'import:' + digest([SOURCE, source_digest, j, cells]) for j, cells in sorted(rows.items())},
                'history': 'snapshot import only; prior history unknown',
                'audit_exception': {'legacy_unconditional_write': 'UNKNOWN', 'cancel_finality': 'UNKNOWN'},
                'routes': {r: 'deny-legacy' for r in ROUTES}}
    return manifest


def verify_manifest(m, accepted_digest):
    require(type(m) is dict and digest(m) == accepted_digest, 'exact accepted manifest required')
    rebuilt = bootstrap(m['rows'], provisional_ids=m['provisional_ids'],
                        privacy_policy=m['privacy_policy'], provenance=m['provenance'])
    require(m == rebuilt, 'wrong repo/ref/source or corrupt manifest')
    return m


def import_operation(m, accepted_digest, job, head, event_hash):
    return Operation(job, 1, m['operations'][job], 0, head, event_hash,
                     string_row(m['rows'][job]), 'offline-manifest:' + accepted_digest,
                     m['provenance'], '2026-10-05T00:00:00+00:00', 'synthetic-importer', 'offline',
                     1, 1, 1, 'VA-ISOLATION-0016-01', outcome='SNAPSHOT_IMPORT_NO_PRIOR_HISTORY')


def verify_import_payload(payload, m, accepted_digest, job):
    expected = import_operation(m, accepted_digest, job, payload['expected_head'],
                                payload['expected_event_hash']).payload()
    require(payload == expected, 'wrong bootstrap operation identity/provenance')


def import_snapshot(ledger, token, manifest, accepted_digest):
    """AJ15 remains unchanged: exactly one snapshot-import event per commit.

Restart walks the exact existing prefix; lost responses reconcile, never replay.
No history inferred from status and no projection input accepted.
"""
    m = verify_manifest(manifest, accepted_digest)
    jobs = sorted(m['rows'])
    head, _, state = ledger._remote()
    imported = list(state['operations'])
    require(imported == [m['operations'][j] for j in jobs[:len(imported)]] and len(imported) <= len(jobs), 'fork/non-bootstrap ledger')
    for j in jobs[:len(imported)]:
        require(state['rows'][j] == string_row(m['rows'][j]), 'bootstrap cells differ')
        # Verify exact original payload, not only an operation ID and snapshot.
        event = json.loads(ledger.transport.read(head)[state['events'][jobs.index(j)]])['payload']
        verify_import_payload(event, m, accepted_digest, j)
    # Clears an exact already-imported pending response without republishing.
    with ledger.locked() as control:
        pending = deepcopy(control['pending'])
    if pending and pending['payload']['operation_id'] in imported:
        require(pending['payload']['operation_id'] in m['operations'].values(), 'foreign pending operation')
        require(ledger.reconcile(token)['outcome'] == 'RECONCILED', 'pending bootstrap held')
    for j in jobs[len(imported):]:
        op = import_operation(m, accepted_digest, j, head, state['last_event_hash'])
        # Pending attempt may have been accepted with a lost process response.
        with ledger.locked() as control:
            pending = deepcopy(control['pending'])
        if pending:
            require(pending['payload'] == op.payload(), 'pending bootstrap identity differs')
            result = ledger.reconcile(token) if pending['attempted'] else ledger.resume(token)
        else:
            result = ledger.append(token, op)
        require(result['outcome'] == 'RECONCILED', 'bootstrap held for uncertain publication')
        head, _, state = ledger._remote()
    require(state['rows'] == {j: string_row(c) for j, c in m['rows'].items()}, 'per-cell bootstrap mismatch')
    return head


class LocalAuthorityProvider:
    """Durable local atomic CAS; no hosted/distributed or malicious-code guarantee."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with open(str(self.path) + '.lock', 'a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def read(self):
        require(self.path.exists(), 'missing authority: HOLD')
        try:
            envelope = json.loads(self.path.read_bytes())
            require(set(envelope) == {'state', 'digest'} and digest(envelope['state']) == envelope['digest'], 'corrupt authority: HOLD')
            return envelope['state']
        except (ValueError, KeyError, TypeError) as exc:
            raise ProtocolError('invalid authority: HOLD') from exc

    def cas(self, expected, state):
        with self.locked():
            current = self.read() if self.path.exists() else None
            require(current == expected, 'authority CAS conflict: HOLD')
            temp = self.path.with_suffix('.tmp')
            with open(temp, 'wb') as f:
                f.write(canonical({'state': state, 'digest': digest(state)})); f.flush(); os.fsync(f.fileno())
            os.replace(temp, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)


class IsolationCoordinator:
    def __init__(self, provider, ledger, manifest, accepted_digest):
        self.provider, self.ledger = provider, ledger
        self.manifest = deepcopy(verify_manifest(manifest, accepted_digest))
        self.accepted_digest = accepted_digest

    def _state(self):
        s = self.provider.read()
        require(set(s) == {'version', 'phase', 'epoch', 'selected', 'manifest', 'head', 'routes', 'exception'}, 'contradictory authority: HOLD')
        require(s['version'] == 1 and type(s['epoch']) is int and s['epoch'] in (0, 1)
                and s['manifest'] == self.accepted_digest and s['routes'] == self.manifest['routes']
                and s['exception'] == self.manifest['audit_exception'], 'authority identity conflict: HOLD')
        require(s['phase'] in ('LEGACY', 'HELD', 'PREPARING', 'NEW_ACTIVE'), 'unknown authority phase: HOLD')
        require((s['phase'] == 'NEW_ACTIVE' and s['epoch'] == 1 and s['selected'] == 'new' and type(s['head']) is str)
                or (s['phase'] != 'NEW_ACTIVE' and s['selected'] is None
                    and s['epoch'] in (0, 1) and (s['phase'] == 'HELD' or s['epoch'] == 0)), 'contradictory epoch: HOLD')
        return s

    def initialize(self):
        s = {'version': 1, 'phase': 'LEGACY', 'epoch': 0, 'selected': None,
             'manifest': self.accepted_digest, 'head': None, 'routes': self.manifest['routes'],
             'exception': self.manifest['audit_exception']}
        self.provider.cas(None, s)

    def transition(self, expected_phase, next_phase):
        require((expected_phase, next_phase) in (('LEGACY', 'HELD'), ('HELD', 'PREPARING')), 'invalid transition')
        s = self._state()
        require(s['phase'] == expected_phase and s['epoch'] == 0, 'stale/retired transition')
        new = deepcopy(s); new['phase'] = next_phase
        self.provider.cas(s, new)

    def activate(self, expected_head):
        s = self._state()
        require(s['phase'] == 'PREPARING' and s['epoch'] == 0, 'activation already decided/held')
        head, _, reduced = self.ledger._remote()
        require(head == expected_head and head is not None, 'stale authority head')
        require(reduced['rows'] == {j: string_row(c) for j, c in self.manifest['rows'].items()}
                and set(reduced['operations']) == set(self.manifest['operations'].values()), 'unreconciled bootstrap')
        # Read-only exact prefix/provenance validation; activation never imports.
        jobs = sorted(self.manifest['rows'])
        require(len(reduced['events']) == len(jobs), 'unexpected bootstrap history')
        for i, j in enumerate(jobs):
            payload = json.loads(self.ledger.transport.read(head)[reduced['events'][i]])['payload']
            verify_import_payload(payload, self.manifest, self.accepted_digest, j)
        new = deepcopy(s); new.update(phase='NEW_ACTIVE', epoch=1, selected='new', head=head)
        self.provider.cas(s, new)  # sole durable switch linearization point
        return 1

    def gate(self, route, surface, epoch, head):
        require(route in ROUTES, 'uninventoried route: HOLD')
        s = self._state()
        require(s['phase'] == 'NEW_ACTIVE' and surface == 'new' and epoch == s['epoch']
                and head == s['head'], 'stale/legacy route: HOLD')
        actual, _, _ = self.ledger._remote()
        require(actual == head, 'stale/forked authority head: HOLD')
        return deepcopy(s)

    def dispatch(self, job, *, surface, epoch, head):
        # Local synthetic selection only, no external side effect or worker launch.
        selected = self.gate('dispatcher', surface, epoch, head)
        actual, _, reduced = self.ledger._remote()
        require(actual == head, 'authority changed during selection: HOLD')
        require(job in reduced['rows'] and reduced['rows'][job][4] == 'Ready', 'authoritative Ready required')
        require(self._state() == selected and self.ledger.transport.head() == head,
                'authority changed during selection: HOLD')
        return {'synthetic': True, 'job': job, 'epoch': epoch, 'head': head}

    def rollback_hold(self):
        s = self._state(); new = deepcopy(s)
        new.update(phase='HELD', selected=None)
        self.provider.cas(s, new)  # consumed epoch remains retired; never old fallback
