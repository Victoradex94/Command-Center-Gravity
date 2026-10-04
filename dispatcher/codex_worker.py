"""Synthetic-only durable worker boundary; never imports a live provider or ledger writer."""
from dataclasses import asdict, dataclass
import hashlib
from typing import Callable, Protocol

from .adapters import Admission, DispatchRequest, ReservationObservation, RunObservation
from .model import (Gates, Lineage, ProtocolError, ReturnClass, ReturnEnvelope, RouteCandidate,
                    packed, present, require, timestamp, validate_nonce)
from .writer_journal import WriterJournal


def digest(value):
    return hashlib.sha256(packed(value).encode()).hexdigest()


@dataclass(frozen=True)
class Authority:
    """Trusted coordinator snapshot, obtained afresh, never inferred from provider output."""
    request_digest: str
    lineage: Lineage
    nonce: str
    active: bool
    reference: str
    gates: Gates
    route: RouteCandidate
    required: frozenset[str]

    def validate(self, request, now):
        require(self.active and self.request_digest == digest(asdict(request))
                and self.lineage == request.lineage and self.nonce == request.nonce
                and present(self.reference), "current exact authority required")
        request.brief.validate()
        validate_nonce(request.nonce)
        require(request.worker == "Codex" and request.brief.explicit_worker == request.worker,
                "explicit Codex assignment required")
        self.gates.validate(now)
        require(self.route.worker == request.worker and self.route.route == request.route
                and self.route.eligible(self.required, now), "exact eligible route required")


class MockTransport(Protocol):
    synthetic_only: bool
    def submit(self, request: dict) -> dict: ...
    def reservation(self, request: dict) -> dict | None: ...
    def inspect(self, task: str, turn: str) -> dict | None: ...
    def stop(self, task: str, turn: str, reason: str) -> str: ...


class CodexWorkerAdapter:
    """All instances/wrappers MUST share a dedicated local journal path and scope.

    Injection is for trusted offline fixtures only, not a Python security sandbox.
    Ambiguous submission is permanently frozen; even positive absence cannot retry it.
    """
    def __init__(self, journal: WriterJournal, transport: MockTransport,
                 authority: Callable[[DispatchRequest], Authority], clock: Callable[[], str],
                 checkpoint: Callable[[str], None] = lambda _: None):
        require(getattr(transport, "synthetic_only", False) is True,
                "only synthetic transport permitted")
        self.journal, self.transport, self.authority = journal, transport, authority
        self.clock, self.checkpoint = clock, checkpoint

    def _authority(self, request):
        grant = self.authority(request)
        grant.validate(request, self.clock())
        data = asdict(grant) | {"required": sorted(grant.required)}
        data["route"]["capabilities"] = sorted(grant.route.capabilities)
        return data

    @staticmethod
    def _operation(state, request):
        op = state["operations"].get(request.idempotency_key)
        if op:
            require(op["request"] == asdict_json(request), "changed payload under bound identity")
        return op

    def _failure(self, state, op, category):
        # Job scope deliberately excludes route, wrapper, attempt and volatile exception text.
        group = op["request"]["lineage"]["job_id"]
        incident = state["circuits"].setdefault(group, {
            "fingerprint": digest([group, "worker-execution-boundary"]),
            "failures": 0, "recovery_used": False, "circuit": False,
            "permission_stop": False, "history": []})
        incident["failures"] += 1
        incident["circuit"] |= incident["failures"] > 1 or incident["recovery_used"]
        incident["permission_stop"] |= category == "permission"
        incident["history"].append({"category": category, "at": self.clock(), "synthetic": True})
        op["uncertainty"] = category
        self.journal.save(state)

    def authorize_recovery(self, request, changed_condition):
        """One shared budget; authorizes a future distinct identity, never resubmission.

        Trusted coordinator must supply usable changed-condition evidence AND fresh exact
        authority. Existing unresolved reservations for this job still prohibit submission.
        Permission stops have no automatic renewal path.
        """
        with self.journal.locked():
            state = self.journal.load()
            grant = self._authority(request)
            incident = state["circuits"][request.lineage.job_id]
            require(present(changed_condition) and changed_condition.strip().casefold()
                    not in {"unknown", "ready", "done", "not applicable"}, "changed condition required")
            require(not incident["permission_stop"] and not incident["circuit"]
                    and not incident["recovery_used"], "recovery budget/circuit/permission stop")
            incident.update(recovery_used=True, recovery_identity=request.idempotency_key,
                            changed_condition=changed_condition, authority=grant)
            self.journal.save(state)

    def dispatch(self, request: DispatchRequest) -> Admission:
        with self.journal.locked():
            state = self.journal.load()
            op = self._operation(state, request)
            grant = self._authority(request)
            if op:
                require(not state["circuits"].get(request.lineage.job_id, {}).get("permission_stop"),
                        "durable permission stop")
                require(not op["fenced"], "reservation fenced")
                if op.get("admission"):
                    return Admission(**op["admission"])
                raise ProtocolError("synthetic unresolved intent; inspect original reservation, never resubmit")
            group = request.lineage.job_id
            incident = state["circuits"].get(group)
            if incident:
                require(not incident["permission_stop"] and not incident["circuit"]
                        and incident.get("recovery_identity") == request.idempotency_key,
                        "shared recovery budget/circuit/permission stop")
            for previous in state["operations"].values():
                if previous["request"]["lineage"]["job_id"] == group:
                    require(previous.get("terminal") is True and previous["fenced"]
                            and not previous.get("execution_conflict"),
                            "prior execution unresolved or unfenced; replacement prohibited")
            op = dict(request=asdict_json(request), authority=grant, intent_at=self.clock(),
                      synthetic=True, admission=None, task="", turn="", observations=[],
                      returns={}, rejected_returns=[], fenced=False, stop="none", terminal=False,
                      uncertainty="submission intent; outcome unknown")
            state["operations"][request.idempotency_key] = op
            self.journal.save(state)  # FULL commit BEFORE even entering submit
            self.checkpoint("before_submit")
            receipt = None
            try:
                receipt = self.transport.submit(op["request"])
                self.checkpoint("after_acceptance")
                observation = self._validate_receipt(op, receipt)
                self._bind(state, op, receipt, observation)
            except Exception as exc:
                op["observations"].append({"observed_at": self.clock(), "synthetic": True,
                                           "rejected_receipt": receipt, "error": str(exc)})
                self._failure(state, op, "permission" if isinstance(exc, PermissionError) else "admission_unknown")
                raise ProtocolError("synthetic admission uncertain; inspect original reservation") from exc
            self.journal.save(state)
            self.checkpoint("after_receipt")
            return Admission(**op["admission"])

    def _validate_receipt(self, op, receipt):
        request = op["request"]
        require(isinstance(receipt, dict), "missing/inconclusive synthetic lookup")
        require(receipt.get("synthetic") is True and receipt.get("authenticated") is True,
                "synthetic attributable receipt required")
        require(receipt.get("request_digest") == digest(request), "receipt payload mismatch")
        for field in ("lineage", "nonce", "worker", "route"):
            require(receipt.get(field) == request[field], "receipt attribution mismatch: " + field)
        require(present(receipt.get("task"), receipt.get("turn"), receipt.get("evidence")),
                "exact task+turn and evidence required")
        if op["task"]:
            require((receipt["task"], receipt["turn"]) == (op["task"], op["turn"]), "handle conflict")
        state = receipt.get("state")
        require(state in {"admitted", "running", "completed", "failed", "stopped", "unknown"}, "invalid state")
        require(timestamp(op["intent_at"]) <= timestamp(receipt["observed_at"]) <= timestamp(self.clock()),
                "stale/future observation")
        if op["observations"]:
            require(timestamp(receipt["observed_at"]) >= timestamp(op["observations"][-1]["observed_at"]),
                    "observation regressed")
        terminal_state = op.get("terminal_state")
        if terminal_state and state != terminal_state:
            op.update(execution_conflict=True, terminal=False,
                      uncertainty="conflicting evidence after terminal observation")
            raise ProtocolError("terminal execution evidence conflict; root reconciliation required")
        require(not op.get("execution_conflict"), "unresolved terminal execution conflict")
        handle = packed([receipt["task"], receipt["turn"]])
        substantive = (state == "running" and receipt.get("substantive") is True
                       and present(receipt.get("start_evidence")))
        return RunObservation(handle, "running" if state == "admitted" else state,
                              receipt["observed_at"], "synthetic: " + receipt["evidence"]
                              + ("; substantive: " + receipt["start_evidence"] if substantive else ""),
                              True, substantive)

    def _bind(self, state, op, receipt, observation):
        op.update(task=receipt["task"], turn=receipt["turn"], uncertainty="",
                  admission=asdict(Admission(observation.worker_run, "synthetic exact provider admission")))
        op["observations"].append(receipt)
        op["terminal"] |= receipt["state"] in {"completed", "failed", "stopped"}
        if op["terminal"]:
            op["terminal_state"] = receipt["state"]
        if receipt["state"] == "failed" and not op.get("execution_failure_recorded"):
            op["execution_failure_recorded"] = True
            self._failure(state, op, "execution_failed")
        if receipt["state"] == "stopped" and op["stop"] != "none":
            op["stop"] = "confirmed_stopped"

    def _lookup(self, state, op):
        receipt = None
        try:
            receipt = (self.transport.inspect(op["task"], op["turn"]) if op["task"]
                       else self.transport.reservation(op["request"]))
            observation = self._validate_receipt(op, receipt)
            self._bind(state, op, receipt, observation)
            self.journal.save(state)
            return observation
        except Exception as exc:
            if isinstance(exc, PermissionError):
                group = op["request"]["lineage"]["job_id"]
                if not state["circuits"].get(group, {}).get("permission_stop"):
                    self._failure(state, op, "permission")
            op["observations"].append({"observed_at": self.clock(), "synthetic": True,
                                       "lookup_error": str(exc), "rejected_receipt": receipt})
            self.journal.save(state)
            return RunObservation(packed([op["task"], op["turn"]]) if op["task"] else "",
                                  "unknown", self.clock(), "synthetic lookup inconclusive: " + str(exc), False)

    def inspect_reservation(self, request: DispatchRequest) -> ReservationObservation:
        with self.journal.locked():
            state = self.journal.load()
            op = self._operation(state, request)
            require(op is not None, "no durable original reservation")
            run = self._lookup(state, op)
            return ReservationObservation(request.lineage, request.nonce, request.worker, request.route, run)

    @staticmethod
    def _by_handle(state, worker_run):
        matches = [op for op in state["operations"].values() if op["admission"]
                   and op["admission"]["worker_run"] == worker_run]
        require(len(matches) == 1, "unknown/ambiguous exact handle")
        return matches[0]

    def inspect(self, worker_run: str) -> RunObservation:
        with self.journal.locked():
            state = self.journal.load()
            return self._lookup(state, self._by_handle(state, worker_run))

    def fence(self, request, reason):
        """Trusted root cancellation/reassignment/supersession; output isolation only."""
        with self.journal.locked():
            state = self.journal.load()
            op = self._operation(state, request)
            require(op is not None and present(reason), "bound reservation and reason required")
            op.update(fenced=True, fence_reason=reason)
            self.journal.save(state)

    def request_stop(self, worker_run: str, reason: str) -> str:
        with self.journal.locked():
            state = self.journal.load()
            op = self._by_handle(state, worker_run)
            require(present(reason), "stop reason required")
            if op["stop"] != "none":
                return "synthetic stop " + op["stop"] + "; inspect exact handle for termination"
            op.update(fenced=True, stop="requested", stop_reason=reason)
            self.journal.save(state)
            self.checkpoint("before_stop")
            try:
                result = self.transport.stop(op["task"], op["turn"], reason)
                self.checkpoint("after_stop")
                require(result in {"acknowledged", "unsupported", "unknown"}, "invalid stop receipt")
                op["stop"] = result
            except Exception as exc:
                self._failure(state, op, "permission" if isinstance(exc, PermissionError) else "stop_unknown")
            self.journal.save(state)
            return "synthetic stop " + op["stop"] + "; physical termination unconfirmed"

    def normalize_return(self, request, receipt: dict) -> ReturnEnvelope | None:
        """Persist complete raw evidence; invalid/incomplete/conflicting returns stay explicit.

        Returning an envelope is NOT acceptance, completion, or permission to write a ledger.
        Root must independently validate with Dispatcher.receive/complete and report delivery.
        """
        with self.journal.locked():
            state = self.journal.load()
            op = self._operation(state, request)
            require(op is not None, "no original reservation")
            raw = asdict_json(receipt)
            try:
                self._authority(request)
                require(not state["circuits"].get(request.lineage.job_id, {}).get("permission_stop"),
                        "durable permission stop fences acceptance")
                require(not op["fenced"], "cancelled/reassigned/superseded/stopped return fenced")
                require(op["admission"] is not None, "return cannot bind admission")
                observation = self._validate_receipt(op, raw)
                require(raw.get("truncated") is False and raw.get("complete") is True,
                        "missing completeness or truncated evidence")
                data = dict(raw["return"])
                data["lineage"] = Lineage(**data["lineage"])
                data["claimed_class"] = ReturnClass(data["claimed_class"])
                for field in ("criteria_met", "criteria_unmet"):
                    require(isinstance(data[field], list) and all(isinstance(x, str) for x in data[field]),
                            "criterion list required")
                    data[field] = tuple(data[field])
                envelope = ReturnEnvelope(**data)
                require(envelope.authenticated is True, "strict boolean return authentication required")
                envelope.validate()
                require(envelope.lineage == request.lineage and envelope.nonce == request.nonce
                        and envelope.worker == request.worker
                        and envelope.worker_run == op["admission"]["worker_run"], "return attribution conflict")
                require(timestamp(op["intent_at"]) <= timestamp(envelope.observed_at) <= timestamp(self.clock()),
                        "return timestamp invalid")
                require(set(envelope.criteria_met) | set(envelope.criteria_unmet) == set(request.brief.criteria),
                        "missing/unknown criteria evidence")
                expected = {"completed": "Completed", "running": "Running", "admitted": "Unknown",
                            "stopped": "Stopped", "failed": "Failed", "unknown": "Unknown"}[raw["state"]]
                require(envelope.execution_state == expected, "conflicting execution evidence")
                old = op["returns"].get(envelope.return_id)
                require(old is None or old["fingerprint"] == envelope.fingerprint, "conflicting duplicate return")
                require(not op["returns"] or old is not None, "outcome already recorded; root review required")
                self._bind(state, op, raw, observation)
                op["returns"][envelope.return_id] = dict(fingerprint=envelope.fingerprint, raw=raw,
                                                         synthetic=True, independently_accepted=False)
                self.journal.save(state)
                return envelope
            except (ProtocolError, KeyError, TypeError, ValueError) as exc:
                op["rejected_returns"].append(dict(raw=raw, reason=str(exc), synthetic=True))
                self.journal.save(state)
                return None


def asdict_json(value):
    import json
    return json.loads(packed(asdict(value) if hasattr(value, "__dataclass_fields__") else value))


class DeterministicMockProvider:
    """Durable synthetic provider in a SEPARATE fixture journal; no network or child tasks."""
    synthetic_only = True

    def __init__(self, journal: WriterJournal, clock: Callable[[], str]):
        self.journal, self.clock = journal, clock
        self.mode = "accepted"
        self.stop_mode = "acknowledged"

    def submit(self, request):
        with self.journal.locked():
            state = self.journal.load()
            key = Lineage(**request["lineage"]).key
            state["audit"].append({"synthetic": True, "submit": key})
            if self.mode == "permission":
                self.journal.save(state)
                raise PermissionError("synthetic denied")
            if self.mode == "timeout_before":
                self.journal.save(state)
                raise TimeoutError("synthetic pre-acceptance timeout")
            previous = state["operations"].get(key)
            if previous:
                require(previous["request_digest"] == digest(request), "mock changed identity")
                receipt = previous
            else:
                receipt = {k: request[k] for k in ("lineage", "nonce", "worker", "route")}
                receipt.update(synthetic=True, authenticated=True, request_digest=digest(request),
                               task="synthetic-task-" + digest(request)[:24], turn="synthetic-turn-1",
                               state="admitted", substantive=False, evidence="synthetic queue receipt",
                               observed_at=self.clock())
                state["operations"][key] = receipt
            self.journal.save(state)
            if self.mode == "timeout_after":
                raise TimeoutError("synthetic receipt lost after acceptance")
            return asdict_json(receipt)

    def reservation(self, request):
        with self.journal.locked():
            return self.journal.load()["operations"].get(Lineage(**request["lineage"]).key)

    def inspect(self, task, turn):
        with self.journal.locked():
            return next((v for v in self.journal.load()["operations"].values()
                         if (v["task"], v["turn"]) == (task, turn)), None)

    def stop(self, task, turn, reason):
        return self.stop_mode

    def observe(self, request, **changes):
        """Test fixture control: synthetic activity or adversarial receipt injection."""
        with self.journal.locked():
            state = self.journal.load()
            receipt = state["operations"][request.idempotency_key]
            receipt.update(changes)
            self.journal.save(state)
            return asdict_json(receipt)
