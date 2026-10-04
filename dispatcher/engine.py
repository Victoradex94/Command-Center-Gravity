"""Coordinator-owned protocol state machine with reserved-before-send dispatch."""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Callable

from .adapters import (DispatchRequest, ExecutorAdapter, MessageAdapter, RejectedDelivery,
                       ReservationObservation, RunObservation, UncertainDelivery)
from .model import (AgentJob, Brief, DeliveryState, EventKind, Gates, Lineage,
                    ProtocolError, ReturnClass, ReturnEnvelope, RouteCandidate,
                    SourceCommand, Status, Verification, choose_route, classify_return, packed,
                    present, require, timestamp, validate_nonce)
from .store import Attempt, Delivery, Event, JobRepository, Record


ALLOWED_TRANSITIONS = {
    Status.INTAKE: frozenset({Status.READY, Status.BLOCKED, Status.CANCELLED}),
    Status.READY: frozenset({Status.WORKING, Status.INTAKE, Status.BLOCKED, Status.CANCELLED}),
    Status.WORKING: frozenset({Status.REVIEW, Status.BLOCKED, Status.CANCELLED}),
    Status.REVIEW: frozenset({Status.DONE, Status.READY, Status.INTAKE, Status.BLOCKED, Status.CANCELLED}),
    Status.BLOCKED: frozenset({Status.READY, Status.INTAKE, Status.REVIEW, Status.WORKING, Status.CANCELLED}),
    Status.DONE: frozenset({Status.REVIEW, Status.INTAKE}),
    Status.CANCELLED: frozenset({Status.INTAKE}),
}


@dataclass(frozen=True)
class Authorization:
    action: str
    job_id: str
    source: SourceCommand
    evidence: str

    def validate(self, action: str, job_id: str) -> None:
        self.source.validate()
        require(self.action == action and self.job_id == job_id and present(self.evidence),
                "explicit, scoped authorization required")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Dispatcher:
    def __init__(self, repository: JobRepository, *, writer: str = "Dẹkun",
                 clock: Callable[[], str] = utc_now) -> None:
        self.repository = repository
        self.writer = writer
        self.clock = clock
        # Reference outbox for commands received before a tracked job exists.
        self.acknowledgements: dict[str, Delivery] = {}
        self.command_events: list[Event] = []

    def _read(self, lineage: Lineage) -> Record:
        self.repository.assert_writer(self.writer)
        record = self.repository.read(lineage.job_id)
        require(record.lineage == lineage, "stale caller lineage; reread before mutation")
        return record

    def _event(self, record: Record, kind: EventKind, evidence: str, **data: object) -> str:
        require(present(evidence), "event evidence required")
        key = f"{record.lineage.key}/{kind}/{len(record.events) + 1}"
        record.events.append(Event(key, kind, self.clock(), self.writer,
                                   record.lineage, evidence, data))
        return key

    def _marker(self, record: Record, key: str, text: str) -> None:
        record.deliveries[key] = Delivery(key, record.brief.destination, record.row.job_id,
                                          self.clock(), text)

    def _move(self, record: Record, target: Status, reason: str, evidence: str) -> None:
        require(target in ALLOWED_TRANSITIONS[record.row.status],
                f"forbidden transition: {record.row.status} -> {target}")
        require(present(reason, evidence), "transition reason and evidence required")
        previous = record.row.status
        record.row.status = target
        key = self._event(record, EventKind.TRANSITION, evidence,
                          previous=previous, status=target, reason=reason)
        self._marker(record, key, f"{record.lineage.key} {target}: {reason}")

    def _save(self, record: Record, *, old_lineage: Lineage | None = None,
              new: bool = False) -> Record:
        record.row.last_update = self.clock()
        attempt = record.current_attempt
        record.row.run_revision_id = record.lineage.ledger_text(attempt.worker_run if attempt else "")
        record.row.source_brief = packed({"brief": asdict(record.brief), "sources": record.sources,
                                          "ProtocolVersion": "v1.0"})
        record.row.return_summary = packed({
            "ReturnClass": record.return_class, "Nonce": record.nonce,
            "StartedAt": attempt.started_at if attempt else "",
            "StartEvidence": attempt.start_evidence if attempt else "",
            "LastSignalAt": record.last_signal_at, "NextCheck": record.next_check,
            "ActivityRequiredAfter": record.activity_required_after,
            "HoldReason": record.hold_reason, "blocker": record.blocker,
            "attempts": [asdict(a) for a in record.attempts],
            "events": [asdict(e) for e in record.events],
            "deliveries": {k: asdict(d) for k, d in record.deliveries.items()},
        })
        record.row.to_cells()
        return self.repository.commit(record, None if new else record.version,
                                      old_lineage or record.lineage, self.writer)

    def acknowledge(self, source: SourceCommand) -> Delivery:
        self.repository.assert_writer(self.writer)
        source.validate()
        key = f"command/{source.key}/ack"
        if key not in self.acknowledgements:
            self.acknowledgements[key] = Delivery(
                key, source.channel, source.thread, self.clock(),
                "Received; next step is authority, identity and dispatch-gate checks.")
            self.command_events.append(Event(key, EventKind.ACKNOWLEDGEMENT, self.clock(),
                                              self.writer, None, source.permalink,
                                              {"SourceEventKey": source.key, "state": "Pending"}))
        return replace(self.acknowledgements[key])

    @staticmethod
    def _deliver(delivery: Delivery, messenger: MessageAdapter) -> None:
        observed = messenger.inspect(delivery.event_key, delivery.destination, delivery.thread)
        if observed.state == "found":
            require(present(observed.reference), "observed delivery requires message reference")
            delivery.state, delivery.reference = DeliveryState.VERIFIED, observed.reference
            return
        if observed.state != "absent":
            delivery.state = DeliveryState.UNKNOWN
            return
        delivery.attempts += 1
        try:
            delivery.reference = messenger.send(delivery.event_key, delivery.destination,
                                                 delivery.thread, delivery.text)
            delivery.state = DeliveryState.SENT
        except RejectedDelivery:
            delivery.state = DeliveryState.FAILED
            return
        except (UncertainDelivery, TimeoutError):
            delivery.state = DeliveryState.UNKNOWN
            return
        observed = messenger.inspect(delivery.event_key, delivery.destination, delivery.thread)
        if observed.state == "found" and present(observed.reference):
            delivery.state, delivery.reference = DeliveryState.VERIFIED, observed.reference
        else:
            delivery.state = DeliveryState.UNKNOWN

    def deliver_acknowledgement(self, source: SourceCommand, messenger: MessageAdapter) -> Delivery:
        delivery = self.acknowledge(source)
        self._deliver(delivery, messenger)
        self.acknowledgements[delivery.event_key] = delivery
        self.command_events.append(Event(delivery.event_key + f"/{len(self.command_events)}",
                                          EventKind.DELIVERY, self.clock(), self.writer, None,
                                          "command acknowledgement delivery inspection", asdict(delivery)))
        # Repair a linked job's acknowledgement evidence without changing execution.
        for record in self.repository.all():
            if delivery.event_key in record.deliveries:
                record.deliveries[delivery.event_key] = replace(delivery)
                self._save(record)
        return replace(delivery)

    def intake(self, job_id: str, nonce: str, source: SourceCommand, brief: Brief,
               *, actionable: bool = True, priority: str = "Normal") -> Record | None:
        ack = self.acknowledge(source)  # immediate receipt record; send via explicit adapter call
        if not actionable:
            return None
        validate_nonce(nonce)
        for existing in self.repository.all():
            same_source = any(s["key"] == source.key for s in existing.sources)
            if same_source or brief.identity in existing.identities:
                reference = {"key": source.key, "version": source.version, "url": source.permalink}
                if reference not in existing.sources:
                    existing.sources.append(reference)
                    existing.deliveries[ack.event_key] = ack
                    self._event(existing, EventKind.ACKNOWLEDGEMENT, source.permalink,
                                duplicate=True, source=source.key)
                    return self._save(existing)
                return existing
        lineage = Lineage(job_id, 1, 1, 1)
        row = AgentJob(job_id, brief.parent_id, brief.outcome, brief.explicit_worker,
                       priority=priority, control_date=brief.control_point)
        record = Record(row, brief, lineage, nonce,
                        sources=[{"key": source.key, "version": source.version, "url": source.permalink}],
                        identities={brief.identity}, deliveries={ack.event_key: ack},
                        next_check=brief.control_point)
        self._event(record, EventKind.ACKNOWLEDGEMENT, source.permalink,
                    source=source.key, delivery=ack.state)
        return self._save(record, new=True)

    def _gates(self, record: Record, gates: Gates, candidates: tuple[RouteCandidate, ...],
               required: frozenset[str]) -> str:
        record.brief.validate()
        gates.validate(self.clock())
        selected = choose_route(candidates, required,
                                record.brief.explicit_worker or record.row.assigned_worker, self.clock())
        require(selected.eligible, selected.reason)
        if record.row.assigned_worker != selected.worker:
            record.row.assigned_worker = selected.worker
            record.row.assigned_at = self.clock()
        elif not record.row.assigned_at:
            record.row.assigned_at = self.clock()
        record.row.dependency = packed(asdict(gates.dependencies))
        self._event(record, EventKind.RECONCILIATION, "dispatch gates checked",
                    gates=asdict(gates), route=asdict(selected))
        return selected.route

    def ready(self, lineage: Lineage, gates: Gates, candidates: tuple[RouteCandidate, ...],
              required: frozenset[str]) -> Record:
        record = self._read(lineage)
        require(record.row.status in (Status.INTAKE, Status.BLOCKED), "readiness requires Intake/Blocked")
        require(not record.hold_reason, "hold must be explicitly resolved")
        require(record.current_attempt is None, "existing attempt must be reconciled, not relaunched")
        require(all(a.fenced and a.execution_state in ("Completed", "Stopped", "Failed", "Isolated")
                    for a in record.attempts), "older execution effects unresolved")
        self._gates(record, gates, candidates, required)
        record.blocker = {}
        self._move(record, Status.READY, "all start gates pass", "current checks recorded")
        return self._save(record)

    def dispatch(self, lineage: Lineage, gates: Gates, candidates: tuple[RouteCandidate, ...],
                 required: frozenset[str], executor: ExecutorAdapter) -> Record:
        record = self._read(lineage)
        require(record.row.status == Status.READY and not record.hold_reason, "dispatch requires Ready")
        if record.current_attempt is not None:
            return record  # reserved/accepted identity is never sent twice, even without a run ID
        require(all(a.fenced and a.execution_state in ("Completed", "Stopped", "Failed", "Isolated")
                    for a in record.attempts), "older execution effects unresolved")
        route = self._gates(record, gates, candidates, required)
        record.attempts.append(Attempt(lineage, record.nonce, record.row.assigned_worker, route,
                                       reserved_at=self.clock()))
        self._event(record, EventKind.DISPATCH, "identity reserved before adapter invocation")
        record = self._save(record)  # uncertain reservation blocks adapter invocation
        request = DispatchRequest(lineage, record.nonce, record.row.assigned_worker, route, record.brief)
        try:
            admission = executor.dispatch(request)
            require(present(admission.worker_run, admission.evidence), "admission evidence missing")
        except (TimeoutError, ProtocolError) as exc:
            record.current_attempt.execution_state = "Unknown"
            record.activity_required_after = self.clock()
            record.blocker = {"gate": "execution", "reason": str(exc), "owner": self.writer,
                              "may_still_run": True, "next": "inspect original reserved identity"}
            self._move(record, Status.BLOCKED, "launch outcome unknown", str(exc))
            return self._save(record)
        record.current_attempt.worker_run = admission.worker_run
        record.current_attempt.execution_state = "Admitted"
        key = self._event(record, EventKind.ADMISSION, admission.evidence, worker_run=admission.worker_run)
        self._marker(record, key, f"{lineage.key} Ready; admitted, substantive start unconfirmed")
        return self._save(record)

    def start(self, lineage: Lineage, observation: RunObservation, *, reconciliation: str = "") -> Record:
        record = self._read(lineage)
        attempt = record.current_attempt
        require(attempt is not None and not attempt.fenced, "no current authorized attempt")
        require(attempt.return_envelope is None, "returned work requires review, not another start")
        require(record.row.status in (Status.READY, Status.BLOCKED), "start requires Ready or reconciled Blocked")
        require(not record.hold_reason, "held execution cannot resume")
        require(observation.authenticated and observation.substantive and observation.state == "running"
                and observation.worker_run == attempt.worker_run
                and present(observation.evidence, observation.worker_run),
                "actual current-run substantive work required; admission is insufficient")
        require(timestamp(observation.observed_at) <= timestamp(self.clock()), "future start evidence")
        self._fresh_activity(record, observation.observed_at)
        if record.row.status == Status.BLOCKED:
            require(present(reconciliation), "Blocked -> Working requires recorded reconciliation")
        attempt.execution_state = "Running"
        attempt.started_at = attempt.started_at or observation.observed_at
        attempt.start_evidence = observation.evidence
        record.last_signal_at = observation.observed_at
        record.activity_required_after = ""
        record.blocker = {}
        self._event(record, EventKind.START, observation.evidence, observation=asdict(observation),
                    reconciliation=reconciliation)
        self._move(record, Status.WORKING, "substantive execution observed", observation.evidence)
        return self._save(record)

    @staticmethod
    def _fresh_activity(record: Record, observed_at: str) -> None:
        lower_bounds = [record.last_signal_at, record.activity_required_after]
        if record.current_attempt:
            lower_bounds.append(record.current_attempt.reserved_at)
        require(all(timestamp(observed_at) >= timestamp(bound) for bound in lower_bounds if bound),
                "renewed current-run activity required; stale observation cannot resolve uncertainty")

    def recover_admission(self, lineage: Lineage, observation: ReservationObservation) -> Record:
        """Bind a run found by the exact reserved identity; never invoke dispatch again."""
        record = self._read(lineage)
        attempt = record.current_attempt
        require(record.row.status in (Status.READY, Status.BLOCKED) and attempt is not None
                and not attempt.fenced and not attempt.worker_run, "unbound current reservation required")
        require(observation.lineage == lineage and observation.nonce == record.nonce
                and observation.worker == attempt.worker and observation.route == attempt.route,
                "reservation identity mismatch")
        run = observation.run
        require(run.authenticated and present(run.worker_run, run.evidence)
                and run.state in ("running", "completed", "failed", "stopped")
                and timestamp(run.observed_at) <= timestamp(self.clock()), "authenticated original run required")
        require(timestamp(run.observed_at) >= timestamp(attempt.reserved_at), "reservation observation predates dispatch")
        attempt.worker_run = run.worker_run
        attempt.execution_state = {"running": "Admitted", "completed": "Completed",
                                   "failed": "Failed", "stopped": "Stopped"}[run.state]
        key = self._event(record, EventKind.ADMISSION, run.evidence,
                          recovery=asdict(observation), start="requires separate substantive observation")
        self._marker(record, key, f"{lineage.key} original admission recovered; status {record.row.status}")
        return self._save(record)

    def reconcile_prior_attempt(self, lineage: Lineage, prior: Lineage,
                                observation: ReservationObservation, effects_evidence: str) -> Record:
        """Resolve fenced execution after cancellation/reopening without adopting its output."""
        record = self._read(lineage)
        attempt = next((a for a in record.attempts if a.lineage == prior), None)
        require(attempt is not None and attempt.fenced, "fenced historical attempt required")
        require(observation.lineage == prior and observation.nonce == attempt.nonce
                and observation.worker == attempt.worker and observation.route == attempt.route,
                "historical reservation identity mismatch")
        run = observation.run
        require(run.authenticated and run.state in ("stopped", "failed", "completed")
                and present(run.worker_run, run.evidence, effects_evidence)
                and (not attempt.worker_run or run.worker_run == attempt.worker_run)
                and timestamp(run.observed_at) <= timestamp(self.clock()),
                "confirmed historical terminal state and effects evidence required")
        attempt.worker_run = run.worker_run
        attempt.execution_state = {"stopped": "Stopped", "failed": "Failed", "completed": "Completed"}[run.state]
        self._event(record, EventKind.RECONCILIATION, effects_evidence,
                    historical=asdict(observation), output_adopted=False)
        return self._save(record)

    def block(self, lineage: Lineage, *, gate: str, reason: str, evidence: str,
              owner: str, next_action: str, execution_state: str = "Unknown") -> Record:
        record = self._read(lineage)
        require(present(gate, reason, evidence, owner, next_action), "exact blocker and recovery required")
        require(execution_state in ("Unknown", "Running", "Stopped", "Failed", "Completed"),
                "invalid execution state")
        attempt = record.current_attempt
        if attempt:
            attempt.execution_state = execution_state
        record.activity_required_after = self.clock()
        record.blocker = {"gate": gate, "reason": reason, "evidence": evidence, "owner": owner,
                          "next": next_action, "control_point": record.next_check,
                          "execution_state": execution_state,
                          "may_still_run": execution_state in ("Unknown", "Running")}
        if record.row.status != Status.BLOCKED:
            self._move(record, Status.BLOCKED, reason, evidence)
        else:
            self._event(record, EventKind.RECONCILIATION, evidence, blocker=record.blocker)
        return self._save(record)

    def observe_run(self, lineage: Lineage, observation: RunObservation, next_check: str) -> Record:
        record = self._read(lineage)
        attempt = record.current_attempt
        require(attempt is not None and not attempt.fenced and record.row.status in
                (Status.READY, Status.WORKING, Status.BLOCKED), "no live current run to observe")
        require(observation.authenticated and present(observation.evidence, next_check, observation.worker_run)
                and observation.worker_run == attempt.worker_run, "current run observation required")
        require(timestamp(observation.observed_at) <= timestamp(self.clock()), "future observation")
        self._fresh_activity(record, observation.observed_at)
        states = {"running": "Running", "completed": "Completed", "stopped": "Stopped",
                  "failed": "Failed", "unknown": "Unknown"}
        require(observation.state in states, "unknown observation state")
        attempt.execution_state = states[observation.state]
        record.last_signal_at, record.next_check = observation.observed_at, next_check
        self._event(record, EventKind.RECONCILIATION, observation.evidence, observation=asdict(observation))
        if observation.state == "unknown" and record.row.status != Status.BLOCKED:
            record.activity_required_after = observation.observed_at
            record.blocker = {"execution_state": "Unknown", "may_still_run": True,
                              "next": "inspect original run; never automatically redispatch"}
            self._move(record, Status.BLOCKED, "execution state unresolved", observation.evidence)
        return self._save(record)

    def receive(self, envelope: ReturnEnvelope) -> Record:
        self.repository.assert_writer(self.writer)
        record = self.repository.read(envelope.lineage.job_id)
        attempt = record.current_attempt
        rejection = ""
        try:
            envelope.validate()
            require(timestamp(envelope.observed_at) <= timestamp(self.clock()), "future return")
            require(record.row.status != Status.CANCELLED, "cancelled run is fenced")
            require(envelope.lineage == record.lineage and envelope.nonce == record.nonce,
                    "stale lineage or nonce mismatch")
            require(attempt is not None and not attempt.fenced
                    and envelope.worker == attempt.worker and envelope.worker_run == attempt.worker_run,
                    "worker/run attribution mismatch")
            require(timestamp(envelope.observed_at) >= timestamp(attempt.reserved_at)
                    and (not attempt.started_at or timestamp(envelope.observed_at) >= timestamp(attempt.started_at)),
                    "return observation predates current execution")
            require(set(envelope.criteria_met) | set(envelope.criteria_unmet) == set(record.brief.criteria),
                    "return must account for all current criteria")
        except ProtocolError as exc:
            rejection = str(exc)
        if rejection:
            self._event(record, EventKind.REJECTION, rejection, envelope=asdict(envelope))
            return self._save(record)
        if attempt.return_envelope:
            if attempt.return_envelope.fingerprint == envelope.fingerprint:
                return record
            self._event(record, EventKind.REJECTION, "conflicting duplicate; retain original output",
                        envelope=asdict(envelope))
            if record.row.status == Status.DONE:
                self._move(record, Status.REVIEW, "completion challenged by conflicting evidence",
                           "conflicting return retained; coordinator correction report")
                record.verification = None
                record.row.verification = ""
            return self._save(record)
        # A result can establish review from Blocked; Ready needs separate substantive evidence.
        require(record.row.status in (Status.WORKING, Status.BLOCKED),
                "return cannot bypass actual start or terminal review rules")
        attempt.return_envelope = envelope
        attempt.execution_state = envelope.execution_state
        record.row.output = envelope.output
        record.return_class = classify_return(envelope)
        record.last_signal_at = max(filter(None, (record.last_signal_at, envelope.observed_at)), key=timestamp)
        self._event(record, EventKind.RETURN, envelope.evidence, envelope=asdict(envelope),
                    classification="worker claim; coordinator verification pending")
        if record.return_class == ReturnClass.BLOCKED:
            record.blocker = {"reason": envelope.blockers, "remaining": envelope.remaining,
                              "gate": envelope.failed_gate, "owner": envelope.next_owner,
                              "next": envelope.recommendation, "execution_state": envelope.execution_state,
                              "may_still_run": envelope.execution_state in ("Unknown", "Running"),
                              "control_point": envelope.control_point}
            if record.row.status != Status.BLOCKED:
                self._move(record, Status.BLOCKED, envelope.blockers, envelope.evidence)
        elif record.hold_reason:
            key = self._event(record, EventKind.REVIEW, "return retained while pause remains active",
                              next="explicit resume, then review current return")
            self._marker(record, key, f"{record.lineage.key} Blocked: paused; current return retained")
        else:
            record.blocker = {}
            self._move(record, Status.REVIEW, f"{record.return_class} return for assessment", envelope.evidence)
            self._event(record, EventKind.REVIEW, "current return retained for coordinator assessment")
        return self._save(record)

    def review_blocked(self, lineage: Lineage, evidence: str) -> Record:
        record = self._read(lineage)
        require(record.row.status == Status.BLOCKED and record.current_attempt is not None
                and record.current_attempt.return_envelope is not None and not record.hold_reason,
                "unheld current return required")
        self._move(record, Status.REVIEW, "evidence now permits assessment", evidence)
        return self._save(record)

    def complete(self, lineage: Lineage, verification: Verification) -> Record:
        record = self._read(lineage)
        require(record.row.status == Status.REVIEW, "must pass through Review before Done")
        attempt = record.current_attempt
        require(attempt is not None and attempt.return_envelope is not None and not attempt.fenced,
                "current return missing")
        result = attempt.return_envelope
        require(record.return_class == ReturnClass.FULL and result.remaining == "Not applicable"
                and result.blockers == "Not applicable" and not record.hold_reason,
                "partial/blocked/held work cannot be Done")
        require(not result.output.strip().casefold().startswith(("unknown", "no output yet", "not applicable")),
                "actual deliverable required")
        require(record.row.needs_victor == "No" and not record.escalations, "unresolved Victor decision")
        verification.validate(record.brief, lineage, attempt.worker, self.clock())
        require(timestamp(verification.checked_at) >= timestamp(result.observed_at),
                "verification must inspect the returned result")
        record.verification = verification
        record.row.verification = packed(asdict(verification))
        self._move(record, Status.DONE, "all acceptance criteria independently verified",
                   verification.artifact_evidence.evidence)
        self._event(record, EventKind.COMPLETION, verification.artifact_evidence.evidence,
                    synthetic=verification.synthetic, delivery="tracked separately")
        return self._save(record)

    def correct_completion(self, lineage: Lineage, evidence: str, correction_report: str) -> Record:
        record = self._read(lineage)
        require(record.row.status == Status.DONE and present(correction_report), "completion correction report required")
        self._move(record, Status.REVIEW, correction_report, evidence)
        record.verification = None
        record.row.verification = ""
        return self._save(record)

    def cancel(self, lineage: Lineage, authorization: Authorization, stop_evidence: str) -> Record:
        record = self._read(lineage)
        authorization.validate("cancel", lineage.job_id)
        require(present(stop_evidence), "record stop requested/confirmed/unsupported and residual effects")
        if record.current_attempt:
            record.current_attempt.fenced = True
        self._move(record, Status.CANCELLED, authorization.evidence, stop_evidence)
        self._event(record, EventKind.RECONCILIATION, authorization.source.permalink,
                    stop=stop_evidence, physical_termination="not implied", side_effects="preserved")
        return self._save(record)

    def pause(self, lineage: Lineage, authorization: Authorization, evidence: str) -> Record:
        record = self._read(lineage)
        authorization.validate("pause", lineage.job_id)
        require(record.row.status in (Status.READY, Status.WORKING, Status.BLOCKED, Status.REVIEW),
                "only active work can be paused")
        record.hold_reason = "Paused"
        record.activity_required_after = self.clock()
        record.blocker = {"gate": "hold", "reason": "Paused", "evidence": evidence, "owner": "Victor",
                          "next": "explicit resume and original-run reconciliation",
                          "may_still_run": True, "execution_state": "Unknown"}
        if record.current_attempt:
            record.current_attempt.execution_state = "Unknown"
        if record.row.status != Status.BLOCKED:
            self._move(record, Status.BLOCKED, authorization.evidence, evidence)
        else:
            self._event(record, EventKind.RECONCILIATION, evidence, hold="Paused")
        return self._save(record)

    def resume(self, lineage: Lineage, authorization: Authorization, evidence: str) -> Record:
        record = self._read(lineage)
        authorization.validate("resume", lineage.job_id)
        require(record.row.status == Status.BLOCKED and record.hold_reason == "Paused", "no paused hold")
        record.hold_reason = ""
        record.activity_required_after = self.clock()
        self._event(record, EventKind.RECONCILIATION, evidence, authority=authorization.evidence,
                    next="reconcile original run before Working; no replacement dispatch")
        return self._save(record)

    def _safe_previous(self, record: Record, authorization: Authorization, evidence: str,
                       isolation: bool = False) -> None:
        require(present(evidence), "previous-run state and side effects evidence required")
        if record.current_attempt:
            attempt = record.current_attempt
            if isolation:
                authorization.validate("isolated_retry", record.row.job_id)
                attempt.execution_state = "Isolated"
            require(attempt.execution_state in ("Completed", "Stopped", "Failed", "Isolated"),
                    "old attempt may still execute; no duplicate launch")
            attempt.fenced = True
        self._event(record, EventKind.RECONCILIATION, evidence, isolation=isolation)

    def retry(self, lineage: Lineage, authorization: Authorization, nonce: str,
              evidence: str, gates: Gates, candidates: tuple[RouteCandidate, ...],
              required: frozenset[str], *, isolation: bool = False) -> Record:
        record = self._read(lineage)
        authorization.validate("isolated_retry" if isolation else "retry", lineage.job_id)
        require(record.row.status in (Status.REVIEW, Status.BLOCKED) and not record.hold_reason,
                "corrective attempt requires reviewed/blocked unheld work")
        self._safe_previous(record, authorization, evidence, isolation)
        validate_nonce(nonce)
        require(nonce != record.nonce and all(nonce != a.nonce for a in record.attempts), "nonce reuse")
        record.lineage = replace(lineage, attempt=lineage.attempt + 1)
        record.nonce = nonce
        record.last_signal_at, record.activity_required_after = "", self.clock()
        record.return_class = ""
        record.verification = None
        record.row.verification = ""
        record.blocker = {}
        self._gates(record, gates, candidates, required)
        self._move(record, Status.READY, "explicitly authorized bounded corrective attempt", authorization.evidence)
        return self._save(record, old_lineage=lineage)

    def reopen(self, lineage: Lineage, authorization: Authorization, nonce: str,
               prior_effects_evidence: str) -> Record:
        record = self._read(lineage)
        authorization.validate("reopen", lineage.job_id)
        require(record.row.status in (Status.DONE, Status.CANCELLED), "reopening requires terminal run")
        validate_nonce(nonce)
        require(nonce != record.nonce and all(nonce != a.nonce for a in record.attempts), "nonce reuse")
        require(present(prior_effects_evidence), "preserve prior outcome and residual effects")
        if record.current_attempt:
            record.current_attempt.fenced = True
        record.lineage = replace(lineage, run_epoch=lineage.run_epoch + 1, attempt=1)
        record.nonce = nonce
        record.last_signal_at, record.activity_required_after = "", ""
        record.hold_reason = ""
        record.return_class = ""
        record.verification = None
        record.row.verification = ""
        self._move(record, Status.INTAKE, authorization.evidence, prior_effects_evidence)
        return self._save(record, old_lineage=lineage)

    def revise(self, lineage: Lineage, authorization: Authorization, brief: Brief,
               nonce: str, previous_run_evidence: str) -> Record:
        record = self._read(lineage)
        authorization.validate("revise", lineage.job_id)
        require(record.row.status in (Status.READY, Status.REVIEW, Status.BLOCKED, Status.INTAKE),
                "hold executing work before material revision/reassignment")
        require(not record.hold_reason, "resolve hold before revision")
        self._safe_previous(record, authorization, previous_run_evidence)
        validate_nonce(nonce)
        require(nonce != record.nonce and all(nonce != a.nonce for a in record.attempts), "nonce reuse")
        previous_brief = asdict(record.brief)
        previous_worker = record.row.assigned_worker
        record.lineage = replace(lineage, spec_revision=lineage.spec_revision + 1,
                                 run_epoch=lineage.run_epoch + 1, attempt=1)
        record.nonce, record.brief = nonce, brief
        record.last_signal_at, record.activity_required_after = "", ""
        record.identities.add(brief.identity)
        record.row.assigned_worker = brief.explicit_worker
        record.row.assigned_at = self.clock() if brief.explicit_worker else ""
        record.row.job_deliverable, record.row.parent_workplan_id = brief.outcome, brief.parent_id
        record.row.control_date, record.next_check = brief.control_point, brief.control_point
        record.sources.append({"key": authorization.source.key, "version": authorization.source.version,
                               "url": authorization.source.permalink})
        record.return_class, record.row.verification, record.verification = "", "", None
        if record.row.status != Status.INTAKE:
            self._move(record, Status.INTAKE, "material revision or authorized reassignment", previous_run_evidence)
        self._event(record, EventKind.REVISION, authorization.evidence, previous=asdict(lineage),
                    previous_brief=previous_brief, previous_worker=previous_worker,
                    authority=asdict(authorization))
        return self._save(record, old_lineage=lineage)

    def clarify(self, lineage: Lineage, authorization: Authorization, brief: Brief,
                worker_acknowledgement: str) -> Record:
        record = self._read(lineage)
        authorization.validate("clarify", lineage.job_id)
        require(record.row.status in (Status.INTAKE, Status.READY, Status.WORKING, Status.BLOCKED),
                "clarification requires active scope")
        require(brief.identity == record.brief.identity and brief.explicit_worker == record.brief.explicit_worker,
                "material scope/assignment change requires revise")
        previous_brief = asdict(record.brief)
        if record.current_attempt:
            require(record.current_attempt.return_envelope is None and present(worker_acknowledgement),
                    "executing revision requires safe incorporation and worker acknowledgement evidence")
            record.current_attempt.lineage = replace(lineage, spec_revision=lineage.spec_revision + 1)
        record.lineage = replace(lineage, spec_revision=lineage.spec_revision + 1)
        record.brief = brief
        record.verification, record.row.verification = None, ""
        record.sources.append({"key": authorization.source.key, "version": authorization.source.version,
                               "url": authorization.source.permalink})
        self._event(record, EventKind.REVISION, authorization.evidence,
                    acknowledgement=worker_acknowledgement, previous=asdict(lineage),
                    previous_brief=previous_brief, authority=asdict(authorization))
        return self._save(record, old_lineage=lineage)

    def escalate(self, lineage: Lineage, issue: str, *, facts: str, decision: str,
                 recommendation: str, consequence: str, deadline: str,
                 material_risk: bool = False, action_required: bool = True) -> Record:
        record = self._read(lineage)
        require(action_required or material_risk, "routine mechanics are not an attention escalation")
        require(present(issue, facts, decision, recommendation, consequence, deadline), "specific escalation required")
        signature = packed([facts, decision, recommendation, consequence, deadline])
        if record.escalations.get(issue) == signature:
            return record
        record.escalations[issue] = signature
        record.row.needs_victor = "Yes"
        record.row.victor_decision = signature
        key = self._event(record, EventKind.ESCALATION, facts, issue=issue,
                          action_required=action_required, material_risk=material_risk)
        record.deliveries[key] = Delivery(key, "attention", record.row.job_id,
                                          self.clock(), signature)
        return self._save(record)

    def resolve_escalation(self, lineage: Lineage, issue: str, authorization: Authorization) -> Record:
        record = self._read(lineage)
        authorization.validate("resolve", lineage.job_id)
        require(issue in record.escalations, "unknown escalation")
        del record.escalations[issue]
        record.row.needs_victor = "Yes" if record.escalations else "No"
        record.row.victor_decision = packed({"response": authorization.evidence,
                                           "source": authorization.source.permalink,
                                           "remaining": record.escalations})
        self._event(record, EventKind.RECONCILIATION, authorization.evidence, issue=issue)
        return self._save(record)

    def deliver(self, lineage: Lineage, event_key: str, messenger: MessageAdapter) -> Record:
        record = self._read(lineage)
        require(event_key in record.deliveries, "required return marker missing; reconcile first")
        delivery = record.deliveries[event_key]
        event = next((e for e in record.events if e.key == event_key), None)
        # A delayed progress report must not claim an obsolete status. Exact destination
        # lookup still runs first inside _deliver, so existing sends are never replaced.
        if event and event.kind in (EventKind.TRANSITION, EventKind.ADMISSION):
            historical_status = event.data.get("status")
            if historical_status not in (Status.DONE, Status.CANCELLED):
                delivery.text = (f"{lineage.key} current status {record.row.status}; "
                                 f"delayed report for {event.lineage.key} at {event.at}. "
                                 f"Historical event: {event.evidence}")
        # Marker was committed and read back before a caller can reach this method.
        self._deliver(delivery, messenger)
        self._event(record, EventKind.DELIVERY, "destination inspected using event identity",
                    delivery=asdict(delivery))
        return self._save(record)

    def reconcile_delivery_markers(self, lineage: Lineage) -> Record:
        record = self._read(lineage)
        missing = [e for e in record.events if e.kind in
                   (EventKind.TRANSITION, EventKind.ADMISSION) and e.key not in record.deliveries]
        for event in missing:
            self._marker(record, event.key,
                         f"{lineage.key} current status {record.row.status}; recovered report for {event.at}")
        if missing:
            self._event(record, EventKind.RECONCILIATION, "missing notification markers recovered",
                        events=[e.key for e in missing])
            return self._save(record)
        return record
