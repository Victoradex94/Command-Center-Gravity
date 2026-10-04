"""Exact future ports and fake implementations. This module imports no network SDK."""

from dataclasses import dataclass
from typing import Protocol

from .model import Brief, Lineage


@dataclass(frozen=True)
class DispatchRequest:
    lineage: Lineage
    nonce: str
    worker: str
    route: str
    brief: Brief
    limits: str = "No ledger writes, new jobs, live integrations, secrets, or unapproved actions"

    @property
    def idempotency_key(self) -> str:
        return self.lineage.key


@dataclass(frozen=True)
class Admission:
    worker_run: str
    evidence: str


@dataclass(frozen=True)
class RunObservation:
    worker_run: str
    state: str  # running, completed, stopped, failed, unknown
    observed_at: str
    evidence: str
    authenticated: bool
    substantive: bool = False


@dataclass(frozen=True)
class ReservationObservation:
    lineage: Lineage
    nonce: str
    worker: str
    route: str
    run: RunObservation


@dataclass(frozen=True)
class MessageObservation:
    state: str  # found, absent, unknown; absent must be positively established
    reference: str = ""


class ExecutorAdapter(Protocol):
    """Codex Cloud, Gemini, Antigravity: implement separately after route verification."""
    def dispatch(self, request: DispatchRequest) -> Admission: ...
    def inspect(self, worker_run: str) -> RunObservation: ...
    def inspect_reservation(self, request: DispatchRequest) -> ReservationObservation: ...
    def request_stop(self, worker_run: str, reason: str) -> str: ...


class MessageAdapter(Protocol):
    """Slack: authenticate inbound commands outside this port; never trust display names."""
    def inspect(self, event_key: str, destination: str, thread: str) -> MessageObservation: ...
    def send(self, event_key: str, destination: str, thread: str, text: str) -> str: ...


class UncertainDelivery(RuntimeError):
    pass


class RejectedDelivery(RuntimeError):
    """Provider definitively rejected without acceptance."""


class FakeExecutor:
    def __init__(self) -> None:
        self.requests: dict[str, DispatchRequest] = {}
        self.calls = 0
        self.mode = "accepted"
        self.observations: dict[str, RunObservation] = {}
        self.reservations: dict[str, ReservationObservation] = {}

    def dispatch(self, request: DispatchRequest) -> Admission:
        self.calls += 1
        self.requests.setdefault(request.idempotency_key, request)
        if self.mode == "unknown":
            raise TimeoutError("synthetic admission timeout; effects unknown")
        return Admission(f"fake:{request.idempotency_key}", "synthetic queue admission only")

    def inspect(self, worker_run: str) -> RunObservation:
        return self.observations[worker_run]

    def inspect_reservation(self, request: DispatchRequest) -> ReservationObservation:
        return self.reservations[request.idempotency_key]

    def request_stop(self, worker_run: str, reason: str) -> str:
        return f"synthetic stop requested for {worker_run}: {reason}; termination unconfirmed"


class FakeMessenger:
    def __init__(self) -> None:
        self.messages: dict[tuple[str, str, str], tuple[str, str]] = {}
        self.calls = 0
        self.mode = "ok"
        self.lookup_unknown = False

    def inspect(self, event_key: str, destination: str, thread: str) -> MessageObservation:
        if self.lookup_unknown:
            return MessageObservation("unknown")
        found = self.messages.get((event_key, destination, thread))
        return MessageObservation("found", found[0]) if found else MessageObservation("absent")

    def send(self, event_key: str, destination: str, thread: str, text: str) -> str:
        self.calls += 1
        if self.mode == "failed":
            raise RejectedDelivery("synthetic definitive rejection")
        reference = f"fake-message:{self.calls}"
        if self.mode != "unknown_absent":
            self.messages[(event_key, destination, thread)] = (reference, text)
        if self.mode.startswith("unknown"):
            raise UncertainDelivery("synthetic send timeout")
        return reference
