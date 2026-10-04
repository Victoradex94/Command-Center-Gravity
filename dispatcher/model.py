"""Exact ledger schema and typed protocol values. Unknown evidence never passes."""

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta
from enum import StrEnum
import hashlib
import json
import re


class ProtocolError(ValueError):
    pass


class Conflict(ProtocolError):
    pass


class ReconciliationRequired(ProtocolError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def present(*values: str) -> bool:
    return all(isinstance(v, str) and bool(v.strip()) for v in values)


def timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ProtocolError("ISO timestamp required") from exc
    require(parsed.tzinfo is not None, "timestamp must include timezone")
    return parsed


def packed(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Status(StrEnum):
    INTAKE = "Intake"
    READY = "Ready"
    WORKING = "Working"
    REVIEW = "Review"
    BLOCKED = "Blocked"
    DONE = "Done"
    CANCELLED = "Cancelled"


class ReturnClass(StrEnum):
    FULL = "Full"
    PARTIAL = "Partial"
    BLOCKED = "Blocked"


class DeliveryState(StrEnum):
    PENDING = "Pending"
    SENT = "Sent"
    VERIFIED = "Verified"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class EventKind(StrEnum):
    ACKNOWLEDGEMENT = "acknowledgement"
    ADMISSION = "admission"
    START = "substantive_start"
    RETURN = "return"
    REVIEW = "review"
    COMPLETION = "completion"
    ESCALATION = "escalation"
    DELIVERY = "delivery"
    TRANSITION = "transition"
    RECONCILIATION = "reconciliation"
    REJECTION = "rejected_return"
    DISPATCH = "dispatch"
    REVISION = "revision"


AGENT_JOB_COLUMNS = (
    "Job ID", "Parent Workplan ID", "Job / Deliverable", "Assigned Worker",
    "Status", "Priority", "Assigned At", "Control Date", "Dependency",
    "Source / Brief", "Output", "Verification", "Return Summary", "Needs Victor",
    "Victor Decision", "Last Update", "Run / Revision ID",
)


@dataclass
class AgentJob:
    job_id: str
    parent_workplan_id: str = ""
    job_deliverable: str = ""
    assigned_worker: str = ""
    status: Status = Status.INTAKE
    priority: str = ""
    assigned_at: str = ""
    control_date: str = ""
    dependency: str = ""
    source_brief: str = ""
    output: str = ""
    verification: str = ""
    return_summary: str = ""
    needs_victor: str = "No"
    victor_decision: str = "Not required"
    last_update: str = ""
    run_revision_id: str = ""

    def to_cells(self) -> list[str]:
        require(isinstance(self.status, Status), "invalid status")
        require(self.needs_victor in ("Yes", "No"), "invalid Needs Victor")
        return [str(getattr(self, f.name)) for f in fields(self)]

    @classmethod
    def from_cells(cls, cells: list[str]) -> "AgentJob":
        require(len(cells) == 17 and all(isinstance(x, str) for x in cells),
                "Agent Jobs requires exactly 17 string cells")
        try:
            row = cls(*cells)
            row.status = Status(cells[4])
            row.to_cells()
            return row
        except ValueError as exc:
            raise ProtocolError("invalid Agent Jobs row") from exc


@dataclass(frozen=True)
class Lineage:
    job_id: str
    spec_revision: int
    run_epoch: int
    attempt: int

    def __post_init__(self) -> None:
        require(bool(re.fullmatch(r"AJ-\d{4,}", self.job_id)), "invalid Job ID")
        require(all(type(n) is int and n > 0 for n in
                    (self.spec_revision, self.run_epoch, self.attempt)), "invalid lineage")

    @property
    def key(self) -> str:
        return f"{self.job_id}/s{self.spec_revision}/r{self.run_epoch}/a{self.attempt}"

    def ledger_text(self, worker_run: str = "") -> str:
        return (f"SpecRevision={self.spec_revision}; RunEpoch={self.run_epoch}; "
                f"Attempt={self.attempt}; WorkerRun={worker_run}; ProtocolVersion=v1.0")


def validate_nonce(nonce: str) -> None:
    require(bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}", nonce)),
            "nonce must be 8–128 safe characters")


@dataclass(frozen=True)
class SourceCommand:
    workspace: str
    author: str
    channel: str
    message_ts: str
    thread: str
    version: str
    permalink: str
    authenticated: bool

    @property
    def key(self) -> str:
        return f"{self.workspace}/{self.channel}/{self.message_ts}"

    def validate(self) -> None:
        require(self.authenticated and self.workspace == "T0C63317YDV"
                and self.author == "U0C6LCCH9QR", "authenticated Victor source required")
        require(present(self.channel, self.message_ts, self.thread, self.version,
                        self.permalink), "source metadata missing")


@dataclass(frozen=True)
class Brief:
    outcome: str
    target: str
    scope: str
    criteria: tuple[str, ...]
    exclusions: str
    authority: str
    inputs: str
    destination: str
    control_point: str
    recovery: str
    verification_method: str
    return_route: str
    parent_id: str = ""
    parent_evidence_or_reason: str = ""
    explicit_worker: str = ""

    def validate(self) -> None:
        require(present(self.outcome, self.target, self.scope, self.exclusions,
                        self.authority, self.inputs, self.destination, self.control_point,
                        self.recovery, self.verification_method, self.return_route,
                        self.parent_evidence_or_reason), "incomplete dispatch brief")
        require(bool(self.criteria) and present(*self.criteria)
                and len(set(self.criteria)) == len(self.criteria), "criteria required and unique")

    @property
    def identity(self) -> str:
        # Deterministic exact semantic tuple; never claim natural-language equivalence.
        parts = (self.outcome, self.target, self.scope, self.parent_id)
        normalized = [" ".join(p.casefold().split()) for p in parts]
        return hashlib.sha256(packed(normalized).encode()).hexdigest()


@dataclass(frozen=True)
class Gate:
    passed: bool | None
    evidence: str


@dataclass(frozen=True)
class Gates:
    authority: Gate
    identity: Gate
    capability: Gate
    access: Gate
    dependencies: Gate
    readiness: Gate
    return_contract: Gate
    checked_at: str

    def validate(self, now: str) -> None:
        age = timestamp(now) - timestamp(self.checked_at)
        require(timedelta(0) <= age <= timedelta(seconds=60), "gates stale or future")
        for name in ("authority", "identity", "capability", "access", "dependencies",
                     "readiness", "return_contract"):
            gate = getattr(self, name)
            require(gate.passed is True and present(gate.evidence), f"failed/unknown gate: {name}")
        require(self.dependencies.evidence.strip().casefold() not in {status.value.casefold() for status in Status},
                "dependency status label is not usable evidence")


@dataclass(frozen=True)
class RouteCandidate:
    worker: str
    route: str
    capabilities: frozenset[str]
    authorized: bool
    route_verified: bool
    environment_verified: bool
    result_retrieval_verified: bool
    access: Gate
    readiness: Gate
    checked_at: str
    evidence: str
    preference: int = 0

    def eligible(self, required: frozenset[str], now: str) -> bool:
        age = timestamp(now) - timestamp(self.checked_at)
        return (required <= self.capabilities and self.authorized and self.route_verified
                and self.environment_verified and self.result_retrieval_verified
                and self.access.passed is True and self.readiness.passed is True
                and present(self.worker, self.route, self.evidence, self.access.evidence,
                            self.readiness.evidence)
                and timedelta(0) <= age <= timedelta(seconds=60))


@dataclass(frozen=True)
class RouteDecision:
    worker: str
    route: str
    eligible: bool
    reason: str


def choose_route(candidates: tuple[RouteCandidate, ...], required: frozenset[str],
                 explicit_worker: str, now: str) -> RouteDecision:
    eligible = [r for r in candidates if r.eligible(required, now)
                and (not explicit_worker or r.worker == explicit_worker)]
    if not eligible:
        return RouteDecision(explicit_worker, "", False,
                             "explicit assignment unavailable" if explicit_worker else "no eligible route")
    best = sorted(eligible, key=lambda r: (-r.preference, r.worker, r.route))[0]
    return RouteDecision(best.worker, best.route, True,
                         "Victor override preserved" if explicit_worker else "eligible task fit and preference")


@dataclass(frozen=True)
class ReturnEnvelope:
    lineage: Lineage
    nonce: str
    worker: str
    worker_run: str
    return_id: str
    observed_at: str
    attempted: str
    output: str
    evidence: str
    remaining: str
    blockers: str
    side_effects: str
    recommendation: str
    claimed_class: ReturnClass
    authenticated: bool
    criteria_met: tuple[str, ...]
    criteria_unmet: tuple[str, ...]
    next_owner: str
    failed_gate: str
    execution_state: str
    control_point: str

    def validate(self) -> None:
        validate_nonce(self.nonce)
        timestamp(self.observed_at)
        require(self.authenticated and isinstance(self.claimed_class, ReturnClass),
                "authenticated attributed return required")
        require(present(self.worker, self.worker_run, self.return_id, self.attempted,
                        self.output, self.evidence, self.remaining, self.blockers,
                        self.side_effects, self.recommendation, self.next_owner,
                        self.failed_gate, self.execution_state, self.control_point),
                "return fields must be explicit; use Not applicable or explain unknowns")
        require(self.execution_state in ("Completed", "Running", "Stopped", "Failed", "Unknown"),
                "explicit last-confirmed execution state required")
        require(not set(self.criteria_met) & set(self.criteria_unmet), "contradictory criterion report")
        if self.claimed_class == ReturnClass.BLOCKED:
            require(self.failed_gate != "Not applicable" and self.blockers != "Not applicable",
                    "Blocked return needs exact failed gate and blocker")

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(packed(asdict(self)).encode()).hexdigest()


@dataclass(frozen=True)
class Check:
    passed: bool | None
    method: str
    evidence: str

    def validate(self) -> None:
        require(self.passed is True and present(self.method, self.evidence),
                "verification check must explicitly pass with method and evidence")
        require(not self.evidence.strip().casefold().startswith(
            ("unknown", "not tested", "unverified", "no output yet", "not applicable")),
            "unknown acceptance evidence cannot pass")


def classify_return(envelope: ReturnEnvelope) -> ReturnClass:
    """Downgrade contradictory Full claims; classification never establishes acceptance."""
    if envelope.claimed_class == ReturnClass.BLOCKED:
        return ReturnClass.BLOCKED
    if (envelope.claimed_class == ReturnClass.PARTIAL or envelope.criteria_unmet
            or envelope.execution_state != "Completed" or envelope.remaining != "Not applicable"
            or envelope.blockers != "Not applicable"):
        return ReturnClass.PARTIAL
    return ReturnClass.FULL


@dataclass(frozen=True)
class Verification:
    lineage: Lineage
    checker: str
    checked_at: str
    criteria_evidence: dict[str, Check]
    artifact_evidence: Check
    destination_evidence: Check
    tests_or_readbacks: Check
    scope_and_permissions_evidence: Check
    dependencies_evidence: Check
    side_effects_evidence: Check
    parent_reconciliation: Check
    provenance_evidence: Check
    limitations: str
    synthetic: bool

    def validate(self, brief: Brief, lineage: Lineage, worker: str, now: str) -> None:
        require(self.lineage == lineage, "stale verification")
        require(self.checker != worker, "worker self-rating is not coordinator verification")
        require(timestamp(self.checked_at) <= timestamp(now), "future verification")
        require(set(self.criteria_evidence) == set(brief.criteria), "missing acceptance evidence")
        checks = [*self.criteria_evidence.values(), self.artifact_evidence, self.destination_evidence,
                  self.tests_or_readbacks, self.scope_and_permissions_evidence, self.dependencies_evidence,
                  self.side_effects_evidence, self.parent_reconciliation, self.provenance_evidence]
        for check in checks:
            require(isinstance(check, Check), "typed verification check required")
            check.validate()
        require(present(self.checker, self.limitations), "incomplete independent verification")
