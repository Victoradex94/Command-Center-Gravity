"""Bounded AJ-0012 transport preparation; callbacks are trusted coordinator ports.

No credentials, Slack HTTP client, tool caller, or unattended service. A future
agent-mediated executor must independently verify its sending route before wiring
these ports. Tool availability and historical bot messages are not identity proof.
"""
from dataclasses import dataclass
from .model import require
from .slack import Readback, SlackBoundary, digest


LINEAGE = "AJ-0012/1/1/1/VA-LIVE-SLACK-0012-01"
EVENT = LINEAGE + "/synthetic-transport"
ROUTE = "mcp__codex_apps__slack_slack_send_message"
WORKSPACE = "T0C63317YDV"
SENDER = "U0C6C7V10P5"
DESTINATIONS = (("activity", "C0C7CRRJDLY"),
                ("attention", "C0C6N5H1QCU"), ("owner", "D0C6J9ZKF4J"))


def bind_synthetic(journal):
    """Atomically bind exactly three immutable intents, without creating a job."""
    keys = []
    with journal.transaction() as state:
        for label, destination in DESTINATIONS:
            key = EVENT + "/" + label
            text = "Synthetic test — no action required. " + key
            SlackBoundary._message(state, key, destination, "", text, "AJ-0012")
            keys.append(key)
        binding = {key: {field: state["messages"][key][field]
                         for field in ("key", "destination", "thread", "text", "group")}
                   for key in keys}
        proposed = dict(binding=binding, fingerprint=digest(binding), operations={})
        old = state.setdefault("controlled_slack", proposed)
        require(old["binding"] == binding and old["fingerprint"] == digest(binding),
                "controlled binding collision")
    return tuple(keys)


@dataclass(frozen=True)
class RouteIdentity:
    workspace: str
    sender: str
    route: str
    evidence: str


@dataclass(frozen=True)
class Observation:
    """Normalized from an original destination read by a trusted executor.

    `complete_absence` requires authoritative coverage, never a search miss or a
    partial page. Original tool response is retained separately from normalization.
    """
    readback: Readback
    workspace: str
    sender: str
    raw: object
    complete_absence: bool = False


@dataclass(frozen=True)
class Acceptance:
    reference: str
    raw: object


class ControlledTransport:
    """Single-use send port; preserves the accepted boundary's uncertainty freezes.

    verify_identity and allowed are trusted, fresh checks, not Slack payload fields.
    No automatic retry even after a positive absence or root recovery: this bounded
    job authorises at most one provider invocation for each of its three operations.
    """
    def __init__(self, journal, identity, verify_identity, allowed, read, send):
        self.journal, self.identity = journal, identity
        self.verify_identity, self.allowed = verify_identity, allowed
        self.read, self.dispatch = read, send

    def _gate(self):
        i = self.identity
        require((i.workspace, i.sender, i.route) == (WORKSPACE, SENDER, ROUTE)
                and bool(i.evidence) and self.verify_identity(i) is True,
                "independently verified workspace/dot-bot sending route required")
        require(self.allowed() is True, "controlled send permission withdrawn or cancelled")

    def _bound(self, key, destination, thread, text=None):
        control = self.journal.snapshot()["controlled_slack"]
        require(control["fingerprint"] == digest(control["binding"]), "binding corrupt")
        require(key in control["binding"], "operation outside controlled scope")
        item = control["binding"][key]
        require((destination, thread) == (item["destination"], item["thread"]),
                "destination/thread mismatch")
        require(text is None or text == item["text"], "content mismatch")
        return item

    def inspect(self, key, destination, thread):
        self._gate()
        item = self._bound(key, destination, thread)
        observation = self.read(key, destination, thread)
        require(isinstance(observation, Observation), "normalized destination evidence required")
        r = observation.readback
        with self.journal.transaction() as state:
            control = state["controlled_slack"]
            control.setdefault("reads", []).append(dict(key=key, raw=observation.raw,
                normalized=vars(r), workspace=observation.workspace,
                sender=observation.sender, complete_absence=observation.complete_absence))
            attempted = key in control["operations"]
        exact = (observation.workspace == WORKSPACE and observation.sender == SENDER
                 and r.state == "found" and bool(r.reference)
                 and all(getattr(r, field) == item[field]
                         for field in ("key", "destination", "thread", "text")))
        if exact:
            return r
        if (r.state == "absent" and observation.complete_absence is True
                and observation.workspace == WORKSPACE and not attempted):
            return Readback("absent")
        return Readback("unknown")

    def send(self, key, destination, thread, text):
        self._gate()
        self._bound(key, destination, thread, text)
        with self.journal.transaction() as state:
            control = state["controlled_slack"]
            require(key not in control["operations"], "reserved operation cannot be replayed")
            control["operations"][key] = dict(state="reserved", calls=1,
                identity=vars(self.identity), destination=destination, thread=thread, text=text)
        # Persist reservation before external effect. Exceptions/process death leave
        # it permanently reserved. A callback must invoke the provider at most once.
        result = self.dispatch(key, destination, thread, text)
        require(isinstance(result, Acceptance), "original acceptance response required")
        with self.journal.transaction() as state:
            state["controlled_slack"]["operations"][key].update(
                state="accepted" if result.reference else "unknown",
                reference=result.reference, raw=result.raw)
        return result.reference
