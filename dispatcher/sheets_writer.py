"""Exclusive coordinator writer, exact readback, and Protocol v1.1 recovery.

No connector or credentials. Adapter evidence and authority are trusted inputs,
validated for binding/freshness here; they must be authenticated at a live edge.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import os
import re
from typing import Callable, Protocol

from .engine import ALLOWED_TRANSITIONS
from .model import (AGENT_JOB_COLUMNS, AgentJob, Conflict, Lineage, ProtocolError,
                    ReconciliationRequired, packed, present, require, timestamp)
from .writer_journal import WriterJournal


FAILURE_CLASSES = frozenset({"state-ledger", "execution-context", "transport-routing",
                             "capability-access", "verification-evidence", "persistence-artifact",
                             "permissions", "transient-availability"})
FAILURE_SIGNALS = frozenset({"provider-unknown", "provider-rejection", "cancelled-call", "timeout",
                            "rate-limit", "unavailable", "readback-mismatch", "conflict", "access-denied"})


class Outcome(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"


class Effect(StrEnum):
    APPLIED = "applied"
    NOOP = "no-op"
    PARTIAL = "partial"
    ACTIVE = "active"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Authority:
    reference: str
    scope: str
    actor: str
    state: str  # valid / human-cancelled / denied / revoked / unknown
    authenticated: bool
    evidence: str
    kind: str = "ordinary"  # trusted adapter classification: ordinary / renewal


@dataclass(frozen=True)
class AuthorityRenewal:
    reference: str
    scope: str
    actor: str
    job_id: str
    source_keys: tuple[str, ...]
    stop_ids: tuple[str, ...]
    authenticated: bool
    evidence: str
    original_authority_ref: str = ""
    intent_digest: str = ""  # exact semantic mutation, excluding occurrence/route/authority labels


@dataclass(frozen=True)
class LineageChange:
    reference: str
    scope: str
    actor: str
    before: Lineage
    after: Lineage
    action: str  # existing engine actions: clarify / revise / reopen / retry
    authenticated: bool
    evidence: str


class AuthorityReader(Protocol):
    def inspect(self, reference: str, scope: str, actor: str) -> Authority: ...
    def inspect_renewal(self, reference: str, scope: str, actor: str) -> AuthorityRenewal: ...
    def inspect_lineage_change(self, reference: str, scope: str, actor: str) -> LineageChange: ...


@dataclass(frozen=True)
class WriterToken:
    actor: str
    epoch: int


@dataclass(frozen=True)
class WriteRequest:
    operation_id: str
    job_id: str
    expected_revision: int | None  # None=create; otherwise update
    cells: tuple[str, ...]
    source_keys: tuple[str, ...]
    authority_ref: str
    context_ref: str
    condition: str  # stable verified safety context, not a writer/session name
    route: str
    aggregate: str = ""  # optional local dispatcher snapshot, never an 18th cell
    expected_lineage: Lineage | None = None
    intended_lineage: Lineage | None = None
    lineage_change_ref: str = ""
    original_authority_ref: str = ""  # required when an initial request uses a reviewed renewal

    @property
    def digest(self) -> str:
        return hashlib.sha256(packed(asdict(self)).encode()).hexdigest()

    @property
    def intent_digest(self) -> str:
        fields = asdict(self)
        return hashlib.sha256(packed({key: fields[key] for key in (
            "job_id", "expected_revision", "cells", "source_keys", "aggregate",
            "expected_lineage", "intended_lineage", "lineage_change_ref")}).encode()).hexdigest()


@dataclass(frozen=True)
class CurrentRow:
    position: int
    cells: tuple[str, ...]
    source_keys: tuple[str, ...]

    def _counter(self, name: str) -> int:
        labels = [s.strip() for s in self.cells[16].split(";") if s.strip().startswith(name)]
        require(len(labels) == 1 and re.fullmatch(name + r"=[1-9][0-9]{0,17}", labels[0]) is not None,
                f"exactly one positive {name} required")
        return int(labels[0].split("=")[1])

    @property
    def revision(self) -> int:
        return self._counter("RecordRevision")

    @property
    def lineage(self) -> Lineage:
        return Lineage(self.cells[0], self._counter("SpecRevision"), self._counter("RunEpoch"),
                       self._counter("Attempt"))


@dataclass(frozen=True)
class Snapshot:
    scope: str
    columns: tuple[str, ...]
    rows: tuple[CurrentRow, ...]
    authoritative: bool
    complete: bool
    evidence: str


@dataclass(frozen=True)
class Submission:
    operation_id: str  # stable incident identity across routes/restarts
    attempt_id: str  # deterministic /0 or /1, journaled before submit
    digest: str
    scope: str
    position: int  # exact single A:Q row, resolved from current logical ID
    before: CurrentRow | None
    cells: tuple[str, ...]
    source_keys: tuple[str, ...]
    route: str
    authority_ref: str  # effective instruction for this submission, including reviewed renewal


@dataclass(frozen=True)
class Observation:
    attempt_id: str
    digest: str
    scope: str
    effect: Effect
    settled: bool
    effects_resolved: bool
    authoritative: bool
    evidence: str
    signal: str = "provider-unknown"  # normalized adapter code, never raw request text
    failure_class: str = "state-ledger"
    cancellation: str = "none"  # none / tool / human / denied / unknown
    cancellation_authenticated: bool = False


@dataclass(frozen=True)
class RecoveryChange:
    reference: str
    from_condition: str
    to_condition: str
    route: str
    evidence: str
    verified: bool
    authority_ref: str
    checked_at: str
    scope: str
    operation_id: str
    digest: str


class SheetsAdapter(Protocol):
    """All methods must address the configured scope; submit changes values only.

    inspect must settle the EXACT attempt (including possible late effects).
    Snapshot alone is insufficient to establish no-op. A future provider without
    such evidence must return UNKNOWN indefinitely, not invent a safe retry.
    """
    def snapshot(self, scope: str) -> Snapshot: ...
    def submit(self, submission: Submission) -> None: ...
    def inspect(self, submission: Submission) -> Observation: ...


@dataclass(frozen=True)
class WriteResult:
    operation_id: str
    outcome: Outcome
    reason: str
    cells: tuple[str, ...] | None
    recovery_used: int
    circuit_open: bool
    fingerprint: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def failure_fingerprint(scope: str, condition: str, failure_class: str,
                        signal: str, uncertainty: str) -> str:
    """Occurrence IDs, actor names and timestamps intentionally are not inputs."""
    return hashlib.sha256(packed(["ledger/write-row", scope, failure_class,
                                signal, condition, uncertainty]).encode()).hexdigest()


class SheetsWriter:
    def __init__(self, journal: WriterJournal, adapter: SheetsAdapter,
                 authority: AuthorityReader, *, clock: Callable[[], str] = utc_now):
        self.journal, self.adapter, self.authority, self.clock = journal, adapter, authority, clock
        self._claimed_token: WriterToken | None = None
        self._claim_pid: int | None = None

    def _audit(self, state: dict, kind: str, **data) -> None:
        state["audit"].append({"sequence": len(state["audit"]) + 1, "at": self.clock(),
                               "kind": kind, **data})

    @staticmethod
    def _matching_stops(state: dict, reference: str, request: WriteRequest) -> set[str]:
        original = request.original_authority_ref or getattr(request, "authority_ref", reference)
        return {key for key, stop in state["permission_stops"].items()
                if stop["authority_ref"] in (reference, original) or stop["job_id"] == request.job_id
                or set(stop["source_keys"]) & set(request.source_keys)}

    def _stop(self, state: dict, reference: str, evidence: dict, op: dict | None = None) -> None:
        request = op["request"] if op is not None else {}
        stop = {"authority_ref": reference, "job_id": request.get("job_id", ""),
                "source_keys": request.get("source_keys", []), "evidence": evidence}
        key = hashlib.sha256(packed(stop).encode()).hexdigest()
        if key not in state["permission_stops"]:
            state["permission_stops"][key] = stop
            self._audit(state, "permission_stop", stop_id=key, stop=stop,
                        operation=request.get("operation_id", "administrative-authority"))
        if op is not None:
            op["permission_stop"] = True  # historical; only explicit renewal may cover it
            if not op["submissions"]:
                op["outcome"], op["reason"] = Outcome.FAILED, "permission denied before provider submission"
        self.journal.save(state)  # persist even if a later guard/read/exception aborts preflight

    @staticmethod
    def _renewal_scope(state: dict, reference: str, request: WriteRequest) -> dict:
        """A renewal is never a general grant, even if no local stop matches."""
        renewal = state["renewals"].get(reference)
        require(renewal is not None and renewal.get("reference") == reference
                and renewal.get("scope") == state["scope"] and renewal.get("actor") == state["coordinator"]
                and renewal.get("authenticated") is True and present(renewal.get("evidence", ""))
                and renewal["job_id"] == request.job_id
                and set(renewal["source_keys"]) == set(request.source_keys)
                and renewal.get("intent_digest") == request.intent_digest
                and renewal.get("original_authority_ref") == (request.original_authority_ref or request.authority_ref),
                "reviewed renewal must match exact job/source/intent and original authority")
        return renewal

    def _permission_gate(self, state: dict, reference: str, request: WriteRequest,
                         kind: str) -> None:
        renewal = None
        if kind == "renewal" or reference in state["renewals"]:
            require(kind == "renewal", "authority classification changed for reviewed renewal")
            renewal = self._renewal_scope(state, reference, request)
        elif reference == request.authority_ref:
            require(not request.original_authority_ref, "ordinary grant cannot attest a renewal relationship")
        stops = self._matching_stops(state, reference, request)
        require(not stops or (renewal is not None and stops <= set(renewal["stop_ids"])),
                "persistent permission stop requires explicit reviewed renewal for this exact target")

    def _authority(self, state: dict, reference: str, op: dict | None = None,
                   *, renewal_review: bool = False) -> Authority:
        grant = self.authority.inspect(reference, state["scope"], state["coordinator"])
        if (isinstance(grant, Authority) and grant.reference == reference
                and grant.scope == state["scope"] and grant.actor == state["coordinator"]
                and grant.authenticated is True and grant.state in ("human-cancelled", "denied", "revoked")):
            self._stop(state, reference, {"grant": asdict(grant)}, op)
        require(isinstance(grant, Authority) and grant.reference == reference
                and grant.scope == state["scope"] and grant.actor == state["coordinator"]
                and grant.authenticated is True and present(grant.evidence)
                and grant.state == "valid" and grant.kind in ("ordinary", "renewal"),
                "current authenticated coordinator authority required")
        if op is not None:
            self._permission_gate(state, reference, self._request(op), grant.kind)
        elif renewal_review:
            require(grant.kind == "renewal", "authority adapter must identify the explicit renewal")
        else:
            require(grant.kind == "ordinary" and reference not in state["renewals"],
                    "targeted renewal cannot authorize administrative ownership changes")
        return grant

    def review_renewal(self, reference: str, token: WriterToken) -> None:
        """Record an authenticated, explicit root renewal; never reset effects/budget.

        Old stops/references remain retained. Only the distinct new reference is
        usable for its exact target and enumerated historical stops.
        """
        with self.journal.locked():
            state = self.journal.load()
            self._mutator(state, token)
            renewal = self.authority.inspect_renewal(reference, state["scope"], state["coordinator"])
            require(isinstance(renewal, AuthorityRenewal) and renewal.reference == reference
                    and renewal.scope == state["scope"] and renewal.actor == state["coordinator"]
                    and renewal.authenticated is True and present(renewal.evidence, renewal.job_id)
                    and present(renewal.original_authority_ref)
                    and isinstance(renewal.intent_digest, str)
                    and re.fullmatch(r"[0-9a-f]{64}", renewal.intent_digest) is not None
                    and isinstance(renewal.source_keys, tuple) and bool(renewal.source_keys)
                    and present(*renewal.source_keys) and len(set(renewal.source_keys)) == len(renewal.source_keys)
                    and isinstance(renewal.stop_ids, tuple) and bool(renewal.stop_ids)
                    and len(set(renewal.stop_ids)) == len(renewal.stop_ids), "explicit authenticated renewal required")
            Lineage(renewal.job_id, 1, 1, 1)
            require(all(key in state["permission_stops"] for key in renewal.stop_ids), "unknown renewal stop")
            stops = [state["permission_stops"][key] for key in renewal.stop_ids]
            require(all(reference != stop["authority_ref"] for stop in stops), "renewal must use a new authority reference")
            require(reference != renewal.original_authority_ref
                    and any(stop["authority_ref"] == renewal.original_authority_ref for stop in stops),
                    "renewal must explicitly identify a stopped original authority")
            require(all(not stop["job_id"] or (stop["job_id"] == renewal.job_id
                        and set(stop["source_keys"]) == set(renewal.source_keys)) for stop in stops),
                    "renewal stops do not match target")
            require(self._matching_stops(state, reference, renewal) <= set(renewal.stop_ids),
                    "renewal must explicitly cover every matching permission stop")
            self._authority(state, reference, renewal_review=True)
            value = asdict(renewal)
            if reference in state["renewals"]:
                require(packed(state["renewals"][reference]) == packed(value), "renewal reference is immutable")
                return
            state["renewals"][reference] = value
            self._audit(state, "authority_renewed", renewal=value)
            self.journal.save(state)

    def claim(self, actor: str, authority_ref: str) -> WriterToken:
        with self.journal.locked():
            state = self.journal.load()
            self._authority(state, authority_ref)
            require(present(actor) and state["owner"] is None, "retire old writer before replacement")
            require(not self._unsettled(state), "reconcile outstanding writes before handoff")
            state["epoch"] += 1
            token = WriterToken(actor, state["epoch"])
            state["owner"] = asdict(token)
            self._audit(state, "writer_claimed", token=asdict(token), authority=authority_ref)
            self.journal.save(state)
            self._claimed_token = token
            self._claim_pid = os.getpid()
            return token

    @staticmethod
    def _owner(state: dict, token: WriterToken) -> None:
        require(isinstance(token, WriterToken) and state["owner"] == asdict(token),
                "retired/stale/nonexclusive writer")

    def _mutator(self, state: dict, token: WriterToken) -> None:
        self._owner(state, token)
        require(token == self._claimed_token and self._claim_pid == os.getpid(),
                "replacement instance must reconcile, retire prior writer, and claim a fresh epoch")

    @staticmethod
    def _unsettled(state: dict) -> bool:
        return any(op["outcome"] == Outcome.UNCERTAIN for op in state["operations"].values())

    def assert_owner(self, token: WriterToken) -> None:
        with self.journal.locked():
            self._mutator(self.journal.load(), token)

    def retire(self, token: WriterToken, authority_ref: str, evidence: str) -> None:
        with self.journal.locked():
            state = self.journal.load()
            self._authority(state, authority_ref)
            self._owner(state, token)
            require(present(evidence) and not self._unsettled(state),
                    "settle every outstanding write before explicit retirement")
            state["owner"] = None
            self._audit(state, "writer_retired", token=asdict(token), evidence=evidence,
                        authority=authority_ref)
            self.journal.save(state)
            if token == self._claimed_token:
                self._claimed_token = None

    @staticmethod
    def _request(op: dict) -> WriteRequest:
        fields = dict(op["request"])
        fields["cells"], fields["source_keys"] = tuple(fields["cells"]), tuple(fields["source_keys"])
        for name in ("expected_lineage", "intended_lineage"):
            if fields[name] is not None:
                fields[name] = Lineage(**fields[name])
        return WriteRequest(**fields)

    @staticmethod
    def _submission(data: dict) -> Submission:
        fields = dict(data)
        fields["cells"], fields["source_keys"] = tuple(fields["cells"]), tuple(fields["source_keys"])
        if fields["before"] is not None:
            row = fields["before"]
            fields["before"] = CurrentRow(row["position"], tuple(row["cells"]), tuple(row["source_keys"]))
        return Submission(**fields)

    @staticmethod
    def _result(op: dict) -> WriteResult:
        return WriteResult(op["request"]["operation_id"], Outcome(op["outcome"]), op["reason"],
                           tuple(op["request"]["cells"]) if op["outcome"] == Outcome.SUCCESS else None,
                           op["recovery_used"], op["circuit_open"], op["fingerprint"])

    def state(self) -> dict:
        with self.journal.locked():
            return self.journal.load()

    def _snapshot(self, state: dict) -> Snapshot:
        snap = self.adapter.snapshot(state["scope"])
        require(isinstance(snap, Snapshot) and snap.scope == state["scope"]
                and snap.columns == AGENT_JOB_COLUMNS and snap.authoritative is True
                and snap.complete is True and present(snap.evidence), "incomplete/untrusted/schema-mismatched read")
        positions = set()
        for row in snap.rows:
            require(type(row.position) is int and row.position >= 2 and row.position not in positions,
                    "invalid/duplicate row position")
            positions.add(row.position)
            AgentJob.from_cells(list(row.cells))
            require(isinstance(row.source_keys, tuple) and bool(row.source_keys) and present(*row.source_keys)
                    and len(set(row.source_keys)) == len(row.source_keys), "invalid source index")
            row.revision
            row.lineage
        return snap

    def read(self, job_id: str) -> CurrentRow | None:
        with self.journal.locked():
            snap = self._snapshot(self.journal.load())
            rows = [row for row in snap.rows if row.cells[0] == job_id]
            require(len(rows) <= 1, "duplicate logical Job ID")
            return rows[0] if rows else None

    def snapshot(self) -> Snapshot:
        with self.journal.locked():
            return self._snapshot(self.journal.load())

    @staticmethod
    def _validate(request: WriteRequest) -> None:
        require(isinstance(request, WriteRequest), "typed request required")
        require(present(request.operation_id, request.authority_ref, request.context_ref,
                        request.condition, request.route), "operation, authority and context required")
        require(isinstance(request.original_authority_ref, str), "typed original authority required")
        require(bool(re.fullmatch(r"[A-Za-z0-9_.:/-]{1,200}", request.operation_id)), "invalid operation ID")
        require(present(request.job_id) and isinstance(request.aggregate, str), "typed Job ID and aggregate required")
        Lineage(request.job_id, 1, 1, 1)
        require(request.expected_revision is None or
                (type(request.expected_revision) is int and request.expected_revision > 0), "invalid expected revision")
        require(isinstance(request.cells, tuple) and len(request.cells) == 17
                and all(isinstance(c, str) and len(c) <= 50000 for c in request.cells), "17 bounded string cells required")
        AgentJob.from_cells(list(request.cells))
        require(request.cells[0] == request.job_id, "narrow target Job ID mismatch")
        require(isinstance(request.source_keys, tuple) and bool(request.source_keys)
                and present(*request.source_keys) and len(set(request.source_keys)) == len(request.source_keys),
                "nonempty unique canonical source keys required")
        row = CurrentRow(2, request.cells, request.source_keys)
        require(row.revision == (request.expected_revision or 0) + 1, "intended revision must advance exactly once")
        require(isinstance(request.intended_lineage, Lineage) and row.lineage == request.intended_lineage,
                "intended lineage must exactly match Q and logical Job ID")
        require((request.expected_revision is None and request.expected_lineage is None)
                or (request.expected_revision is not None and isinstance(request.expected_lineage, Lineage)
                    and request.expected_lineage.job_id == request.job_id), "explicit expected lineage required for update")

    @staticmethod
    def _target(snap: Snapshot, request: WriteRequest) -> CurrentRow | None:
        matches = [r for r in snap.rows if r.cells[0] == request.job_id]
        require(len(matches) <= 1, "duplicate logical Job ID")
        for row in snap.rows:
            require(row.cells[0] == request.job_id or not set(row.source_keys) & set(request.source_keys),
                    "duplicate source on another logical Job ID")
        return matches[0] if matches else None

    def _preflight(self, state: dict, request: WriteRequest, op: dict,
                   authority_ref: str | None = None) -> tuple[CurrentRow | None, int]:
        self._validate(request)
        self._authority(state, authority_ref or request.authority_ref, op)
        snap = self._snapshot(state)
        current = self._target(snap, request)
        if request.expected_revision is None:
            require(current is None, "Job ID already exists; create cannot recycle it")
        else:
            require(current is not None and current.revision == request.expected_revision, "stale RecordRevision/conflict")
            require(current.lineage == request.expected_lineage, "stale SpecRevision/RunEpoch/Attempt")
            if request.intended_lineage != current.lineage:
                self._lineage_change(state, request, op)
            require(set(current.source_keys) <= set(request.source_keys), "source history cannot be removed")
            old, new = AgentJob.from_cells(list(current.cells)), AgentJob.from_cells(list(request.cells))
            require(old.status == new.status or new.status in ALLOWED_TRANSITIONS[old.status], "forbidden status transition")
        reserved = {s["position"] for op in state["operations"].values()
                    if op["outcome"] == Outcome.UNCERTAIN for s in op["submissions"]}
        require(current is None or current.position not in reserved, "physical target has an outstanding write")
        position = current.position if current else max({1, *reserved, *(r.position for r in snap.rows)}) + 1
        return current, position

    def _lineage_change(self, state: dict, request: WriteRequest, op: dict) -> None:
        require(present(request.lineage_change_ref), "explicit lineage-change authority required")
        change = self.authority.inspect_lineage_change(request.lineage_change_ref, state["scope"], state["coordinator"])
        before, after = request.expected_lineage, request.intended_lineage
        require(isinstance(change, LineageChange) and change.reference == request.lineage_change_ref
                and change.scope == state["scope"] and change.actor == state["coordinator"]
                and change.before == before and change.after == after and change.authenticated is True
                and present(change.evidence), "bound authenticated lineage-change decision required")
        # These are exactly the existing Dispatcher lifecycle counter changes.
        allowed = {"clarify": Lineage(before.job_id, before.spec_revision + 1, before.run_epoch, before.attempt),
                   "revise": Lineage(before.job_id, before.spec_revision + 1, before.run_epoch + 1, 1),
                   "reopen": Lineage(before.job_id, before.spec_revision, before.run_epoch + 1, 1),
                   "retry": Lineage(before.job_id, before.spec_revision, before.run_epoch, before.attempt + 1)}
        require(allowed.get(change.action) == after, "lineage change is not an existing coordinator lifecycle transition")
        self._authority(state, change.reference, op)
        self._audit(state, "lineage_change_verified", operation=request.operation_id, change=asdict(change))

    def write(self, request: WriteRequest, token: WriterToken) -> WriteResult:
        # Invalid call types are programmer errors. Domain rejections are explicit FAILED.
        require(isinstance(request, WriteRequest), "typed request required")
        require(isinstance(request.operation_id, str), "addressable string operation identity required")
        with self.journal.locked():
            state = self.journal.load()
            self._mutator(state, token)
            old = state["operations"].get(request.operation_id)
            if old:
                if old["digest"] != request.digest:
                    raise Conflict("operation identity reused for different intent")
                return self._result(old)  # observation only; never an implicit retry
            for op in state["operations"].values():
                if not op["submissions"] or op["outcome"] == Outcome.SUCCESS:
                    continue
                sources = request.source_keys if isinstance(request.source_keys, tuple) and present(*request.source_keys) else ()
                same_target = (op["request"]["job_id"] == request.job_id or
                               bool(set(op["request"]["source_keys"]) & set(sources)))
                if same_target:
                    raise ReconciliationRequired("existing incident freezes this logical ID/source across routes")
            op = {"request": asdict(request), "digest": request.digest, "outcome": Outcome.UNCERTAIN,
                  "reason": "prepared; not proof of submission or no-op", "submissions": [],
                  "recovery_used": 0, "circuit_open": False, "fingerprint": "",
                  "fingerprint_components": {},
                  "failure_occurrences": [], "recurrence_count": 0, "permission_stop": False}
            state["operations"][request.operation_id] = op
            try:
                current, position = self._preflight(state, request, op)
            except Exception as exc:
                reason = str(exc) if isinstance(exc, ProtocolError) else "preflight unavailable: " + type(exc).__name__
                op["outcome"], op["reason"] = Outcome.FAILED, reason
                self._audit(state, "local_rejection", operation=request.operation_id, reason=reason,
                            submitted=False, authority=request.authority_ref)
                self.journal.save(state)
                return self._result(op)
            # Local rejection above is authoritative: submit has never been invoked.
            self._submit(state, op, token, current, position, request.route)
            return self._result(op)

    def _submit(self, state: dict, op: dict, token: WriterToken,
                current: CurrentRow | None, position: int, route: str,
                authority_ref: str | None = None) -> None:
        request = self._request(op)
        sub = Submission(request.operation_id, f"{request.operation_id}/{len(op['submissions'])}",
                         op["digest"], state["scope"], position, current, request.cells,
                         request.source_keys, route, authority_ref or request.authority_ref)
        op["submissions"].append(asdict(sub))
        op["outcome"], op["reason"] = Outcome.UNCERTAIN, "intent durable; effects require reconciliation"
        self._audit(state, "write_attempted", operation=request.operation_id, submission=asdict(sub),
                    authority=sub.authority_ref, original_authority=request.authority_ref,
                    context=request.context_ref, token=asdict(token))
        self.journal.save(state)  # crash after this point freezes even if submit never occurred
        try:
            self.adapter.submit(sub)
        except Exception as exc:
            # Raw tool labels/exceptions establish neither human revocation nor no-op.
            self._audit(state, "transport_signal", operation=request.operation_id,
                        exception_type=type(exc).__name__)
            self.journal.save(state)
        # BaseException deliberately escapes: models abrupt death with intent intact.
        self._reconcile(state, op)

    def reconcile(self, operation_id: str) -> WriteResult:
        """Read-only provider inspection; permitted even while authority is revoked.

        Local evidence/markers may be repaired. No claim, submit, retry or handoff.
        """
        with self.journal.locked():
            state = self.journal.load()
            op = state["operations"][operation_id]
            if op["outcome"] != Outcome.SUCCESS and op["submissions"]:
                self._reconcile(state, op)
            return self._result(op)

    def _reconcile(self, state: dict, op: dict) -> None:
        request = self._request(op)
        sub = self._submission(op["submissions"][-1])
        outcome, reason, observation = Outcome.UNCERTAIN, "unresolved provider effects", None
        try:
            observation = self.adapter.inspect(sub)
            require(isinstance(observation, Observation) and observation.attempt_id == sub.attempt_id
                    and observation.digest == sub.digest and observation.scope == state["scope"]
                    and observation.authoritative is True and present(observation.evidence)
                    and isinstance(observation.effect, Effect)
                    and observation.cancellation in ("none", "tool", "human", "denied", "unknown")
                    and observation.failure_class in FAILURE_CLASSES and observation.signal in FAILURE_SIGNALS,
                    "unbound/non-authoritative/malformed operation evidence")
            self._audit(state, "operation_observed", operation=request.operation_id, observation=asdict(observation))
            if observation.cancellation in ("human", "denied"):
                require(observation.cancellation_authenticated is True,
                        "purported human denial has unresolved provenance")
                self._stop(state, sub.authority_ref, {"observation": asdict(observation)}, op)
            snap = self._snapshot(state)
            current = self._target(snap, request)
            settled = observation.settled is True and observation.effects_resolved is True
            if settled and observation.effect == Effect.APPLIED and current is not None:
                if current.cells == request.cells and current.source_keys == request.source_keys:
                    outcome, reason = Outcome.SUCCESS, "settled application and exact 17-cell/source readback verified"
            elif settled and observation.effect == Effect.NOOP and current == sub.before:
                outcome, reason = Outcome.FAILED, "authoritative settled no-op and unchanged target verified"
            self._audit(state, "authoritative_reconciliation", operation=request.operation_id,
                        observation=asdict(observation), snapshot=asdict(snap), outcome=outcome)
        except Exception as exc:
            reason = "reconciliation unavailable or inconsistent: " + type(exc).__name__
            self._audit(state, "reconciliation_gap", operation=request.operation_id, reason=reason)
        op["outcome"], op["reason"] = outcome, reason
        if outcome != Outcome.SUCCESS:
            self._failure(state, op, sub, observation)
        self._audit(state, "verified_outcome" if outcome != Outcome.UNCERTAIN else "mutation_frozen",
                    operation=request.operation_id, outcome=outcome, reason=reason)
        self.journal.save(state)

    def _failure(self, state: dict, op: dict, sub: Submission, obs: Observation | None) -> None:
        request = self._request(op)
        # Retain the first semantic family through later resolution; never rewrite
        # history or derive a fresh family from retry route/actor/nonce.
        valid = (isinstance(obs, Observation) and obs.authoritative is True and obs.attempt_id == sub.attempt_id
                 and obs.digest == sub.digest and obs.scope == sub.scope)
        signal = obs.signal if valid and obs.signal in FAILURE_SIGNALS else "provider-unknown"
        primary = obs.failure_class if valid and obs.failure_class in FAILURE_CLASSES else "state-ledger"
        uncertainty = "confirmed-no-op" if op["outcome"] == Outcome.FAILED else "write-effects-unresolved"
        fingerprint = failure_fingerprint(state["scope"], request.condition, primary, signal,
                                          uncertainty)
        if not op["fingerprint"]:
            op["fingerprint"] = fingerprint
            op["fingerprint_components"] = {"action": "ledger/write-row", "scope": state["scope"],
                                             "condition": request.condition, "failure_class": primary,
                                             "signal": signal, "uncertainty": uncertainty}
        occurrence = sub.attempt_id
        if not any(e["attempt"] == occurrence for e in op["failure_occurrences"]):
            op["failure_occurrences"].append({"attempt": occurrence, "fingerprint": fingerprint})
            op["recurrence_count"] = sum(e["fingerprint"] == op["fingerprint"]
                                         for e in op["failure_occurrences"]) - 1
        if op["recovery_used"]:
            was_open = op["circuit_open"]
            op["circuit_open"] = True
            state["circuits"][op["fingerprint"]] = request.operation_id
            if not was_open:
                self._audit(state, "circuit_open", operation=request.operation_id,
                            fingerprint=op["fingerprint"], recurrence_count=op["recurrence_count"])

    def recover(self, operation_id: str, change: RecoveryChange, token: WriterToken) -> WriteResult:
        """One changed-condition submission; retry and fallback use this same entry."""
        with self.journal.locked():
            state = self.journal.load()
            self._mutator(state, token)
            op = state["operations"][operation_id]
            request = self._request(op)
            if op["outcome"] == Outcome.SUCCESS:
                return self._result(op)
            require(bool(op["submissions"]), "local rejection requires a corrected request, not provider recovery")
            self._reconcile(state, op)  # fresh exact observation, including late success
            if op["outcome"] == Outcome.SUCCESS:
                return self._result(op)
            require(op["outcome"] == Outcome.FAILED,
                    "effects or cancellation provenance unresolved; mutation frozen")
            require(not op["circuit_open"] and op["recovery_used"] == 0
                    and op["fingerprint"] not in state["circuits"], "shared recovery budget/circuit blocks mutation")
            require(isinstance(change, RecoveryChange), "typed change evidence required")
            active_ref = request.authority_ref
            if change.authority_ref in state["renewals"]:
                self._renewal_scope(state, change.authority_ref, request)
                active_ref = change.authority_ref
            self._authority(state, active_ref, op)
            self._authority(state, change.authority_ref, op)
            age = (timestamp(self.clock()) - timestamp(change.checked_at)).total_seconds()
            require(change.verified is True and 0 <= age <= 60
                    and change.scope == state["scope"] and change.operation_id == operation_id
                    and change.digest == op["digest"] and change.from_condition == request.condition
                    and change.to_condition != change.from_condition
                    and present(change.reference, change.to_condition, change.route, change.evidence),
                    "fresh, bound, verified condition/capability/route change required")
            current, position = self._preflight(state, request, op, active_ref)
            op["recovery_used"] = 1  # durable with submission, before external effect
            self._audit(state, "recovery_authorized", operation=operation_id, change=asdict(change),
                        shared_budget_used=1)
            self._submit(state, op, token, current, position, change.route, active_ref)
            return self._result(op)
