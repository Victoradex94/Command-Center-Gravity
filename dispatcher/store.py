"""One-writer, copy-on-read reference store; never a claim about Sheets atomicity."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Protocol

from .model import (AgentJob, Brief, Conflict, DeliveryState, EventKind, Lineage,
                    ReconciliationRequired, ReturnEnvelope, Verification, require)


@dataclass(frozen=True)
class Event:
    key: str
    kind: EventKind
    at: str
    actor: str
    lineage: Lineage | None
    evidence: str
    data: dict = field(default_factory=dict)


@dataclass
class Delivery:
    event_key: str
    destination: str
    thread: str
    required_at: str
    text: str
    state: DeliveryState = DeliveryState.PENDING
    reference: str = ""
    attempts: int = 0


@dataclass
class Attempt:
    lineage: Lineage
    nonce: str
    worker: str
    route: str
    reserved_at: str = ""
    worker_run: str = ""
    execution_state: str = "Reserved"
    started_at: str = ""
    start_evidence: str = ""
    fenced: bool = False
    return_envelope: ReturnEnvelope | None = None


@dataclass
class Record:
    row: AgentJob
    brief: Brief
    lineage: Lineage
    nonce: str
    version: int = 0
    attempts: list[Attempt] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    identities: set[str] = field(default_factory=set)
    events: list[Event] = field(default_factory=list)
    deliveries: dict[str, Delivery] = field(default_factory=dict)
    verification: Verification | None = None
    return_class: str = ""
    hold_reason: str = ""
    last_signal_at: str = ""
    activity_required_after: str = ""
    next_check: str = ""
    blocker: dict = field(default_factory=dict)
    escalations: dict[str, str] = field(default_factory=dict)

    @property
    def current_attempt(self) -> Attempt | None:
        return next((a for a in reversed(self.attempts) if a.lineage == self.lineage), None)


class JobRepository(Protocol):
    def read(self, job_id: str) -> Record: ...
    def all(self) -> tuple[Record, ...]: ...
    def commit(self, record: Record, expected_version: int | None,
               expected_lineage: Lineage, writer: str) -> Record: ...
    def assert_writer(self, writer: str) -> None: ...
    def reconcile(self, job_id: str, writer: str) -> Record: ...


class InMemoryRepository:
    def __init__(self, coordinator: str = "Dẹkun") -> None:
        self.coordinator = coordinator
        self.writer = coordinator
        self._records: dict[str, Record] = {}
        self.uncertain_job: str | None = None
        self.fail_after_write = False

    def assert_writer(self, writer: str) -> None:
        require(writer == self.writer, "only the active exclusive coordinator writer may mutate")
        if self.uncertain_job:
            raise ReconciliationRequired(f"reconcile uncertain write: {self.uncertain_job}")

    def delegate(self, caller: str, proxy: str, exact_instructions: str) -> None:
        require(caller == self.coordinator and bool(proxy) and bool(exact_instructions),
                "root must explicitly delegate exclusive recording instructions")
        require(not self.uncertain_job, "reconcile before writer handoff")
        self.writer = proxy

    def read(self, job_id: str) -> Record:
        return deepcopy(self._records[job_id])

    def all(self) -> tuple[Record, ...]:
        return tuple(deepcopy(r) for r in self._records.values())

    def commit(self, record: Record, expected_version: int | None,
               expected_lineage: Lineage, writer: str) -> Record:
        self.assert_writer(writer)
        current = self._records.get(record.row.job_id)
        if expected_version is None:
            if current is not None:
                raise Conflict("Job ID is never recycled")
        elif (current is None or current.version != expected_version
              or current.lineage != expected_lineage):
            raise Conflict("reread required: version/lineage changed")
        record.version = 1 if current is None else current.version + 1
        self._records[record.row.job_id] = deepcopy(record)
        if self.fail_after_write:
            self.fail_after_write = False
            self.uncertain_job = record.row.job_id
            raise ReconciliationRequired("write outcome unknown; inspect existing Job ID before retry")
        observed = self.read(record.row.job_id)
        if observed != record:
            self.uncertain_job = record.row.job_id
            raise ReconciliationRequired("readback mismatch")
        return observed

    def reconcile(self, job_id: str, writer: str) -> Record:
        require(writer == self.writer and self.uncertain_job == job_id,
                "only current writer can reconcile the uncertain job")
        observed = self.read(job_id)
        self.uncertain_job = None
        return observed
