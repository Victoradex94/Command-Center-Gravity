"""Offline Slack boundary. Trusted coordinator supplies grants; payloads grant nothing.

No SDK, credentials, scheduler or network implementation is provided. SQLite
serializes local intents; the coordinator remains the sole JobRepository writer.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from typing import Callable

from .adapters import RejectedDelivery
from .engine import Authorization, Dispatcher
from .model import Brief, EventKind, Lineage, SourceCommand, Status, packed, require


def digest(value):
    return hashlib.sha256(packed(value).encode()).hexdigest()


@dataclass(frozen=True)
class SlackConfig:
    workspace: str = "T0C63317YDV"
    owner: str = "U0C6LCCH9QR"
    command: str = "C0C6331GE0P"
    activity: str = "C0C7CRRJDLY"
    attention: str = "C0C6N5H1QCU"
    owner_dm: str = "D0C6J9ZKF4J"


@dataclass(frozen=True)
class Command:
    source: SourceCommand
    action: str
    job_id: str
    nonce: str
    brief: Brief | None = None
    lineage: Lineage | None = None
    evidence: str = ""

    @property
    def key(self):
        return f"{self.source.key}/{self.source.version}"

    @property
    def fingerprint(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class Grant:
    """Construct ONLY in trusted owner-authentication/coordinator code, never parsing Slack."""
    fingerprint: str
    authority_reference: str


@dataclass(frozen=True)
class Readback:
    state: str  # found, absent, unknown; absent means complete authoritative negative
    key: str = ""
    destination: str = ""
    thread: str = ""
    text: str = ""
    reference: str = ""


class SlackJournal:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
        self.db.execute("INSERT OR IGNORE INTO state VALUES (1, ?)",
                        (packed(dict(commands={}, messages={}, incidents={})),))

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            state = json.loads(self.db.execute("SELECT body FROM state WHERE id=1").fetchone()[0])
            yield state
            self.db.execute("UPDATE state SET body=? WHERE id=1", (packed(state),))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def snapshot(self):
        return json.loads(self.db.execute("SELECT body FROM state WHERE id=1").fetchone()[0])

    def close(self):
        self.db.close()


class SlackBoundary:
    def __init__(self, dispatcher: Dispatcher, journal: SlackJournal,
                 verify_grant: Callable[[Grant, Command], bool], config=SlackConfig()):
        self.core, self.journal, self.verify_grant, self.config = dispatcher, journal, verify_grant, config

    @staticmethod
    def _message(state, key, destination, thread, text, group):
        value = dict(key=key, destination=destination, thread=thread, text=text, group=group,
                     state="pending", attempts=0, reference="", human_read="unknown")
        old = state["messages"].get(key)
        if old:
            require(all(old[k] == value[k] for k in ("destination", "thread", "text", "group")),
                    "delivery identity collision")
        else:
            state["messages"][key] = value

    def command(self, command: Command, grant: Grant):
        self.core.repository.assert_writer(self.core.writer)
        source = command.source
        source.validate()
        require(source.workspace == self.config.workspace and source.author == self.config.owner
                and source.channel == self.config.command, "unauthorised intake channel/owner")
        require(grant.fingerprint == command.fingerprint and bool(grant.authority_reference)
                and self.verify_grant(grant, command) is True, "exact authenticated owner scope required")
        require(command.action in ("intake", "observe", "revise", "cancel", "pause"), "unsupported action")
        if command.action in ("intake", "revise"):
            require(isinstance(command.brief, Brief), "brief required")
            command.brief.validate()
            require(bool(command.brief.explicit_worker), "explicit worker assignment required")
        if command.action == "intake":
            for record in self.core.repository.all():
                require(not any(s["key"] == source.key and s["version"] != source.version
                                for s in record.sources), "edited instruction requires explicit revise")
        with self.journal.transaction() as state:
            old = state["commands"].get(command.key)
            if old:
                require(old["digest"] == command.fingerprint, "source identity reused with changed payload")
                if old["state"] == "applied":
                    return old["job"]
                # No cross-store atomic transaction: never blindly repeat a reserved mutation.
                raise ValueError("reserved command requires reconcile_command before replay")
            state["commands"][command.key] = dict(digest=command.fingerprint, state="reserved", job="")
            self._message(state, "ack/" + command.key, source.channel, source.thread,
                          "Received; authority and execution gates remain separate from receipt.", command.key)
        mutation_evidence = packed(dict(command_fingerprint=command.fingerprint,
                                        supplied_evidence=command.evidence))
        auth = Authorization(command.action, command.job_id, source, "slack-command:" + command.fingerprint)
        if command.action == "intake":
            record = self.core.intake(command.job_id, command.nonce, source, command.brief)
        elif command.action == "observe":
            record = None
        else:
            require(command.lineage is not None and command.lineage.job_id == command.job_id,
                    "exact current lineage required")
            if command.action == "revise":
                record = self.core.revise(command.lineage, auth, command.brief, command.nonce, command.evidence)
            elif command.action == "cancel":
                require(bool(command.evidence.strip()), "stop and residual-effects evidence required")
                record = self.core.cancel(command.lineage, auth, mutation_evidence)
            else:
                require(bool(command.evidence.strip()), "pause evidence required")
                record = self.core.pause(command.lineage, auth, mutation_evidence)
        job = record.row.job_id if record else ""
        with self.journal.transaction() as state:
            state["commands"][command.key].update(state="applied", job=job)
        return job

    def reconcile_command(self, command: Command):
        """Read core evidence only; unresolved reservations stay stopped for root review."""
        self.core.repository.assert_writer(self.core.writer)
        with self.journal.transaction() as state:
            entry = state["commands"][command.key]
            require(entry["digest"] == command.fingerprint, "command mismatch")
            if entry["state"] == "applied":
                return entry["job"]
            for record in self.core.repository.all():
                if command.action != "intake" and record.row.job_id != command.job_id:
                    continue
                mutation_evidence = packed(dict(command_fingerprint=command.fingerprint,
                                                supplied_evidence=command.evidence))
                matched = (command.action == "intake" and any(
                    s["key"] == command.source.key and s["version"] == command.source.version
                    for s in record.sources)) or any(
                        (e.evidence == "slack-command:" + command.fingerprint or
                         e.data.get("reason") == "slack-command:" + command.fingerprint or
                         e.evidence == mutation_evidence)
                        for e in record.events)
                if matched:
                    entry.update(state="applied", job=record.row.job_id)
                    return record.row.job_id
            if command.action == "observe":
                entry.update(state="applied", job="")
                return ""
            raise ValueError("no conclusive core evidence; root reconciliation required")

    def sync(self, job_id):
        """Rebuild durable outbox from canonical events, including after a restart.

        Progress/admission/start create no messages. Returns/completion/revision,
        cancellation/blocking and genuine decisions are material.
        """
        record = self.core.repository.read(job_id)
        with self.journal.transaction() as state:
            for event in record.events:
                material = event.kind in (EventKind.RETURN, EventKind.COMPLETION,
                                          EventKind.ESCALATION, EventKind.REVISION)
                material |= (event.kind == EventKind.TRANSITION and
                             event.data.get("status") in (Status.BLOCKED, Status.CANCELLED))
                if not material:
                    continue
                # Canonical event content is immutable; delayed events explicitly historical.
                decision_payload = (record.deliveries[event.key].text
                                    if event.kind == EventKind.ESCALATION else "")
                text = packed(dict(decision=decision_payload, job=job_id, lineage=event.lineage.key, at=event.at,
                                   kind=event.kind, evidence=event.evidence, data=event.data,
                                   historical_event=True))
                self._message(state, event.key + "/activity", self.config.activity, "", text, job_id)
                self._message(state, event.key + "/owner", self.config.owner_dm, "", text, job_id)
                if event.kind == EventKind.ESCALATION:
                    self._message(state, event.key + "/attention", self.config.attention, "", text, job_id)

    def audit_surface(self, job_id):
        self.sync(job_id)
        with self.journal.transaction() as state:
            pending = [m for m in state["messages"].values()
                       if m["group"] == job_id and m["state"] != "verified"]
            if pending:
                incident = state["incidents"].setdefault(job_id, dict(
                    fingerprint="material-event-recorded-but-not-surfaced", recovery_used=False,
                    circuit=False, evidence=""))
                # Polling is not recurrence. A failed corrective send opens the circuit.
                return dict(incident)
            return None

    def recover(self, group, evidence, authorize: Callable[[str, str], bool]):
        """One shared changed-condition retry/fallback budget; cannot move destinations."""
        require(bool(evidence) and authorize(group, evidence) is True, "root recovery evidence required")
        with self.journal.transaction() as state:
            incident = state["incidents"][group]
            require(not incident["circuit"] and not incident["recovery_used"], "coordination circuit/budget")
            incident.update(recovery_used=True, evidence=evidence)
            for message in state["messages"].values():
                if message["group"] == group and message["state"] != "verified":
                    message["correction"] = True

    def deliver(self, key, provider):
        """Inspect first, persist send reservation before I/O, verify exact destination.

        A sending/unknown/accepted message can ONLY be resent following conclusive
        absence AND explicit bounded recovery. Lookup exceptions never permit send.
        """
        self.core.repository.assert_writer(self.core.writer)
        message = self.journal.snapshot()["messages"][key]
        try:
            observed = provider.inspect(key, message["destination"], message["thread"])
        except Exception:
            observed = Readback("unknown")
        exact = (observed.state == "found" and bool(observed.reference) and
                 all(getattr(observed, k) == message[k] for k in ("key", "destination", "thread", "text")))
        with self.journal.transaction() as state:
            current = state["messages"][key]
            if exact:
                current.update(state="verified", reference=observed.reference)
                return "verified"
            if current["state"] == "verified":
                return "verified"  # retain prior verified evidence, never replay deletion
            if observed.state != "absent":
                current["state"] = "unknown"
                return "unknown"
            incident = state["incidents"].get(current["group"], {})
            if current.get("attempted_correction") and not current.get("correction"):
                # Restart after corrective send: conclusive absence is recurrence,
                # even when process death prevented the normal failure marker.
                incident["circuit"] = True
            if incident.get("circuit") or (current["attempts"] and not current.get("correction")):
                return current["state"]
            current.update(state="sending", attempts=current["attempts"] + 1,
                           attempted_correction=bool(current.get("correction")), correction=False)
        try:
            reference = provider.send(key, message["destination"], message["thread"], message["text"])
            outcome = "accepted" if reference else "unknown"
        except RejectedDelivery:
            reference, outcome = "", "failed"
        except Exception:
            reference, outcome = "", "unknown"
        # BaseException (process death) leaves durable 'sending', forcing reconciliation.
        with self.journal.transaction() as state:
            state["messages"][key].update(state=outcome, reference=reference)
        try:
            observed = provider.inspect(key, message["destination"], message["thread"])
        except Exception:
            observed = Readback("unknown")
        exact = (observed.state == "found" and bool(observed.reference) and
                 all(getattr(observed, k) == message[k] for k in ("key", "destination", "thread", "text")))
        with self.journal.transaction() as state:
            current = state["messages"][key]
            if exact:
                current.update(state="verified", reference=observed.reference)
            else:
                incident = state["incidents"].setdefault(current["group"], dict(
                    fingerprint="material-event-recorded-but-not-surfaced", recovery_used=False,
                    circuit=False, evidence=""))
                if incident["recovery_used"]:
                    incident["circuit"] = True
            return current["state"]
