"""Opt-in append-only Git journal. Agent Jobs remains current authority.

Trusted local coordinator API; not an authentication boundary. Durable control
state is a recovery/lease journal, never a second operational database.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path

from .model import AgentJob, Lineage, ProtocolError, require, timestamp, validate_nonce


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class Operation:
    job_id: str
    record_revision: int
    operation_id: str
    expected_revision: int
    expected_head: str | None
    expected_event_hash: str | None
    intended_cells: list[str]
    authority_ref: str
    context_ref: str
    timestamp: str
    worker: str
    route: str
    spec_revision: int
    run_epoch: int
    attempt: int
    nonce: str
    evidence_refs: tuple[str, ...] = ()
    outcome: str = 'INTENDED'
    task_ref: str = ''
    turn_ref: str = ''

    def payload(self):
        value = asdict(self)
        Lineage(self.job_id, self.spec_revision, self.run_epoch, self.attempt)
        validate_nonce(self.nonce)
        timestamp(self.timestamp)
        require(type(self.record_revision) is int and type(self.expected_revision) is int
                and self.expected_revision >= 0 and self.record_revision == self.expected_revision + 1,
                'invalid revision')
        require(all(isinstance(x, str) and x.strip() for x in
                    (self.operation_id, self.authority_ref, self.context_ref, self.worker, self.route, self.outcome)),
                'missing operation context')
        require(AgentJob.from_cells(self.intended_cells).job_id == self.job_id, 'wrong row identity')
        require(all(isinstance(x, str) for x in self.evidence_refs), 'invalid evidence references')
        # JSON roundtrip normalizes tuple/list representation across restarts.
        return json.loads(canonical(value))


def reduce_files(files):
    """Verify complete manifest, chain, indexes and exact deterministic snapshot."""
    if not files:
        return {'events': [], 'rows': {}, 'revisions': {}, 'last_event_hash': None, 'operations': {}}
    try:
        manifest = json.loads(files['manifest.json'])
        require(set(files) == set(manifest['files']) | {'manifest.json'}, 'missing/extra ledger blob')
        require(all(hashlib.sha256(files[p]).hexdigest() == h for p, h in manifest['files'].items()), 'blob hash mismatch')
        state = reduce_files({})
        for sequence, path in enumerate(manifest['events'], 1):
            event = json.loads(files[path])
            payload = event['payload']
            op = Operation(**payload)
            require(op.payload() == payload, 'noncanonical event payload')
            require(event['hash'] == digest(payload), 'event hash mismatch')
            require(payload['expected_event_hash'] == state['last_event_hash'], 'broken event chain')
            job = payload['job_id']
            require(payload['expected_revision'] == state['revisions'].get(job, 0), 'revision chain mismatch')
            require(payload['operation_id'] not in state['operations'], 'duplicate operation in journal')
            require(path == f"events/{job}/{sequence:08d}-{event['hash']}.json", 'event path mismatch')
            state['events'].append(path)
            state['operations'][payload['operation_id']] = event['hash']
            state['rows'][job] = payload['intended_cells']
            state['revisions'][job] = payload['record_revision']
            state['last_event_hash'] = event['hash']
        require(len(set(manifest['events'])) == len(manifest['events']), 'duplicate event path')
        require(set(manifest['files']) == set(state['events']) | {'snapshot.json', 'index.json'}, 'unindexed events')
        require(files['snapshot.json'] == canonical(state['rows']), 'snapshot differs from reducer')
        require(files['index.json'] == canonical({k: state[k] for k in ('revisions', 'operations', 'last_event_hash')}), 'index differs from reducer')
        require(manifest['version'] == 1, 'unsupported manifest')
        return state
    except (KeyError, TypeError, ValueError) as exc:
        raise ProtocolError('invalid ledger: ' + str(exc)) from exc


class GitLedger:
    def __init__(self, control_path, transport):
        self.path = Path(control_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.transport = transport

    @contextmanager
    def locked(self):
        with open(str(self.path) + '.lock', 'a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.path.read_bytes()) if self.path.exists() else {
                'owner': None, 'generation': 0, 'retired': [], 'pending': None,
                'fingerprints': {}, 'circuit': None, 'permission_cancelled': False}
            try:
                yield state
            finally:
                # Persist even after ambiguous transport exceptions or failed validation.
                temp = self.path.with_suffix(self.path.suffix + '.tmp')
                with open(temp, 'wb') as out:
                    out.write(canonical(state)); out.flush(); os.fsync(out.fileno())
                os.replace(temp, self.path)
                fd = os.open(self.path.parent, os.O_RDONLY)
                try: os.fsync(fd)
                finally: os.close(fd)

    def acquire(self, writer):
        require(isinstance(writer, str) and bool(writer.strip()), 'writer identity required')
        with self.locked() as s:
            require(s['owner'] is None and writer not in s['retired'], 'writer already active/retired')
            s['generation'] += 1
            s['owner'] = writer
            return (writer, s['generation'])

    def _fence(self, s, token):
        require(tuple(token) == (s['owner'], s['generation']) and s['owner'] is not None, 'stale writer fenced')

    def retire(self, token):
        with self.locked() as s:
            self._fence(s, token)
            require(s['circuit'] != 'IN_FLIGHT', 'in-flight writer must reconcile before retirement')
            s['retired'].append(s['owner']); s['owner'] = None

    def _remote(self):
        head = self.transport.head()
        files = self.transport.read(head) if head else {}
        reduced = reduce_files(files)
        current = head
        current_files, current_state = files, reduced
        visited = set()
        while current:
            require(current not in visited, 'cyclic commit ancestry')
            visited.add(current)
            parent = self.transport.parent(current)
            previous_files = self.transport.read(parent) if parent else {}
            previous_state = reduce_files(previous_files)
            require(len(current_state['events']) == len(previous_state['events']) + 1,
                    'commit must append exactly one event; no fork/merge')
            require(current_state['events'][:-1] == previous_state['events'], 'forked event history')
            require(all(current_files[p] == previous_files[p] for p in previous_state['events']), 'rewritten prior event')
            event = json.loads(current_files[current_state['events'][-1]])
            require(event['payload']['expected_head'] == parent, 'event expected head differs from Git parent')
            current, current_files, current_state = parent, previous_files, previous_state
        return head, files, reduced

    def append(self, token, operation, prepare_only=False):
        payload = operation.payload()
        fingerprint = digest(payload)
        with self.locked() as s:
            self._fence(s, token)
            require(not s['permission_cancelled'], 'human permission cancellation blocks writer')
            head, files, reduced = self._remote()
            existing = reduced['operations'].get(operation.operation_id)
            if existing:
                require(existing == fingerprint, 'operation id changed payload')
                pending = s['pending']
                if pending and pending['payload']['operation_id'] == operation.operation_id:
                    require(head == pending['intended_sha'] and files == {
                        k: v.encode() for k, v in pending['files'].items()}, 'pending exact commit differs')
                    s['pending'] = None; s['circuit'] = None
                return {'outcome': 'RECONCILED', 'sha': head}
            require(not s['circuit'], 'circuit frozen: reconcile pending operation')
            require(s['pending'] is None, 'pending operation must reconcile first')
            prior = s['fingerprints'].get(operation.operation_id)
            require(prior is None or prior == fingerprint, 'operation id changed payload')
            require(head == operation.expected_head and reduced['last_event_hash'] == operation.expected_event_hash,
                    'stale head/event or fork')
            require(reduced['revisions'].get(operation.job_id, 0) == operation.expected_revision, 'stale revision')
            event_path = f"events/{operation.job_id}/{len(reduced['events']) + 1:08d}-{fingerprint}.json"
            files[event_path] = canonical({'payload': payload, 'hash': fingerprint})
            reduced['events'].append(event_path)
            reduced['rows'][operation.job_id] = payload['intended_cells']
            reduced['revisions'][operation.job_id] = operation.record_revision
            reduced['operations'][operation.operation_id] = fingerprint
            reduced['last_event_hash'] = fingerprint
            files['snapshot.json'] = canonical(reduced['rows'])
            files['index.json'] = canonical({k: reduced[k] for k in ('revisions', 'operations', 'last_event_hash')})
            files['manifest.json'] = canonical({'version': 1, 'events': reduced['events'], 'files': {
                p: hashlib.sha256(b).hexdigest() for p, b in files.items() if p != 'manifest.json'}})
            reduce_files(files)
            s['fingerprints'][operation.operation_id] = fingerprint
            s['pending'] = {'payload': payload, 'files': {p: b.decode() for p, b in files.items()},
                            'intended_sha': None, 'local_head': head, 'remote_head': head,
                            'attempted': False, 'receipt': None, 'budget_used': False, 'condition': None}
        # A restart can resume or abandon this durable precommit intent.
        if prepare_only:
            return {'outcome': 'PREPARED', 'sha': None}
        return self.resume(token)

    def resume(self, token, publish=True):
        with self.locked() as s:
            self._fence(s, token)
            require(not s['permission_cancelled'], 'human permission cancellation blocks writer')
            p = s['pending']; require(p is not None, 'no pending operation')
            require(not p['attempted'] and not s['circuit'], 'uncertain attempt requires reconciliation')
            head, _, _ = self._remote()
            require(head == p['remote_head'], 'remote advanced: conflict/fork')
            files = {k: v.encode() for k, v in p['files'].items()}
            if p['intended_sha'] is None:
                p['intended_sha'] = self.transport.construct(p['local_head'], files)
        # Persist SHA before any update, then persist attempted BEFORE invoking transport.
        if not publish:
            return {'outcome': 'LOCAL_COMMIT', 'sha': p['intended_sha']}
        with self.locked() as s:
            self._fence(s, token)
            require(not s['permission_cancelled'] and not s['circuit'], 'writer frozen')
            p = s['pending']; require(p is not None and not p['attempted'], 'pending attempt changed')
            p['attempted'] = True; s['circuit'] = 'IN_FLIGHT'
        try:
            receipt = self.transport.publish(p['remote_head'], p['intended_sha'])
        except Exception:
            receipt = 'UNKNOWN'
        with self.locked() as s:
            self._fence(s, token)
            s['pending']['receipt'] = receipt
            if receipt == 'HUMAN_PERMISSION_CANCELLED':
                s['permission_cancelled'] = True
            s['circuit'] = receipt
        return self.reconcile(token)

    def reconcile(self, token):
        with self.locked() as s:
            self._fence(s, token)
            p = s['pending']; require(p is not None, 'no pending operation')
            head, files, _ = self._remote()
            if p['intended_sha'] is not None and head == p['intended_sha']:
                require(files == {k: v.encode() for k, v in p['files'].items()}, 'exact SHA blobs mismatch')
                s['pending'] = None; s['circuit'] = None
                return {'outcome': 'RECONCILED', 'sha': head}
            if head != p['remote_head']:
                s['circuit'] = 'CONFLICT'
                return {'outcome': 'CONFLICT', 'sha': head}
            return {'outcome': 'FINAL_NOOP' if p['receipt'] == 'FINAL_NOOP' else
                    'LOCAL_COMMIT' if not p['attempted'] and p['intended_sha'] else 'UNCERTAIN',
                    'sha': head}

    def recover(self, token, changed_condition, verified=False):
        """Trusted caller attests a new evidence reference; one shared budget."""
        with self.locked() as s:
            self._fence(s, token)
            p = s['pending']; require(p is not None, 'no pending operation')
            require(not s['permission_cancelled'], 'human permission cancellation blocks recovery')
            require(p['receipt'] == 'FINAL_NOOP', 'prior attempt lacks authoritative final/noop receipt')
            require(verified is True and isinstance(changed_condition, str) and changed_condition.strip()
                    and changed_condition != p['condition'], 'verified changed condition required')
            require(not p['budget_used'], 'shared recovery budget exhausted')
            require(self.transport.head() == p['remote_head'], 'remote advanced')
            p['budget_used'] = True; p['condition'] = changed_condition
            p['attempted'] = False; p['receipt'] = None; s['circuit'] = None
        return self.resume(token)

    def abandon(self, token):
        with self.locked() as s:
            self._fence(s, token)
            p = s['pending']; require(p is not None, 'no pending operation')
            require(not p['attempted'] and self.transport.head() == p['remote_head'], 'cannot abandon uncertain attempt')
            s['pending'] = None; s['circuit'] = None

    def projection(self, canonical_rows):
        """Read-only intended Sheets snapshot/diff; metadata is not a job status."""
        head, _, reduced = self._remote()
        for job, cells in canonical_rows.items():
            require(AgentJob.from_cells(cells).job_id == job, 'projection identity mismatch')
        rows = deepcopy(reduced['rows'])
        diff = {j: {'before': canonical_rows.get(j), 'after': rows.get(j)}
                for j in sorted(set(rows) | set(canonical_rows)) if canonical_rows.get(j) != rows.get(j)}
        return {'head': head, 'snapshot': rows, 'diff': diff,
                'projection_state': 'SYNC_PENDING' if rows != canonical_rows else 'VERIFIED'}
