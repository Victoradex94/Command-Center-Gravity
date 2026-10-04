"""Persistent LOCAL fault fixture. No networking, Google API, or live credentials."""

from dataclasses import asdict
from contextlib import closing, contextmanager
import json
import sqlite3

from .model import AGENT_JOB_COLUMNS, Status, require
from .sheets_writer import (Authority, AuthorityRenewal, LineageChange, CurrentRow, Effect, Observation, SheetsWriter,
                            Snapshot, Submission)


class SimulatedCrash(BaseException):
    """Bypasses the writer's Exception handler like abrupt process loss."""


class MockAuthority:
    def __init__(self):
        self.states: dict[str, str] = {}
        self.renewals: dict[str, AuthorityRenewal] = {}
        self.lineage_changes: dict[str, LineageChange] = {}

    def inspect(self, reference: str, scope: str, actor: str) -> Authority:
        return Authority(reference, scope, actor, self.states.get(reference, "valid"),
                         True, "LOCAL fixture authority attestation",
                         "renewal" if reference in self.renewals else "ordinary")

    def inspect_renewal(self, reference: str, scope: str, actor: str) -> AuthorityRenewal:
        require(reference in self.renewals, "mock renewal must be explicitly configured")
        return self.renewals[reference]

    def inspect_lineage_change(self, reference: str, scope: str, actor: str) -> LineageChange:
        require(reference in self.lineage_changes, "mock lifecycle decision must be explicitly configured")
        return self.lineage_changes[reference]


class MockSheets:
    """Separate SQLite file survives writer restart; stronger than real Sheets.

    Local transactions provide atomic mock row apply and provider operation log.
    A live adapter cannot infer these guarantees from this fixture's behavior.
    Fault plans, resolve(), seed(), and set_columns() are test controls only.
    """

    MODES = {"apply", "reject", "tool-noop", "tool-pending", "human-noop",
             "denied-noop", "partial", "apply-timeout", "apply-crash", "before-crash"}

    def __init__(self, path: str, scope: str):
        self.path, self.scope = path, scope
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS fixture (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
            existing = db.execute("SELECT body FROM fixture WHERE id=1").fetchone()
            if existing:
                require(json.loads(existing[0])["scope"] == scope, "mock scope mismatch")
            else:
                self._save(db, {"scope": scope, "columns": AGENT_JOB_COLUMNS,
                                "rows": [], "operations": {}, "plans": [], "calls": [],
                                "structure": self._initial_structure()})

    @staticmethod
    def _initial_structure() -> dict:
        return {"grid": {"rows": 1000, "columns": 20, "frozen_rows": 1},
                "table": {"range": "A1:Q1000", "filter": "A1:Q1000", "column_order": list(AGENT_JOB_COLUMNS)},
                "row_metadata": {str(i): {"height": 21 + i, "hidden": i == 7} for i in range(1, 12)},
                "formats": {"A1:Q1": {"bold": True, "background": "navy"},
                            "A2:Q1000": {"wrap": True, "number_format": "TEXT"}},
                "validation": {"E2:E1000": {"strict": True, "values": [s.value for s in Status]},
                               "N2:N1000": {"strict": True, "values": ["Yes", "No"]}},
                "outside_values": {"R2": "neighbour outside A:Q", "Other tab!A1": "untouched"}}

    def structure(self) -> dict:
        """Read-only fixture evidence for metadata the mutation port cannot address."""
        with self._connect() as db:
            return self._load(db)["structure"]

    @contextmanager
    def _connect(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db

    @staticmethod
    def _load(db):
        return json.loads(db.execute("SELECT body FROM fixture WHERE id=1").fetchone()[0])

    @staticmethod
    def _save(db, data):
        db.execute("INSERT OR REPLACE INTO fixture VALUES (1, ?)", (json.dumps(data),))

    def plan(self, *modes: str) -> None:
        require(all(m in self.MODES for m in modes), "unknown mock fault")
        with self._connect() as db:
            data = self._load(db)
            data["plans"].extend(modes)
            self._save(db, data)

    def seed(self, rows: tuple[CurrentRow, ...]) -> None:
        with self._connect() as db:
            data = self._load(db)
            data["rows"] = [asdict(r) for r in rows]
            self._save(db, data)

    def set_columns(self, columns) -> None:
        with self._connect() as db:
            data = self._load(db)
            data["columns"] = list(columns)
            self._save(db, data)

    @property
    def calls(self) -> list[dict]:
        with self._connect() as db:
            return self._load(db)["calls"]

    def snapshot(self, scope: str) -> Snapshot:
        require(scope == self.scope, "mock scope mismatch")
        with self._connect() as db:
            data = self._load(db)
        rows = tuple(CurrentRow(r["position"], tuple(r["cells"]), tuple(r["source_keys"])) for r in data["rows"])
        return Snapshot(scope, tuple(data["columns"]), rows, True, True, "LOCAL complete mock snapshot")

    @staticmethod
    def _apply(data, sub: Submission, partial=False):
        require(2 <= sub.position <= data["structure"]["grid"]["rows"]
                and len(sub.cells) == 17 and all(isinstance(c, str) for c in sub.cells),
                "mock values-only request must fit one existing A:Q data row")
        cells = list(sub.cells)
        if partial:
            cells[10] = "MOCK partial effect"
        data["rows"] = [r for r in data["rows"] if r["position"] != sub.position]
        data["rows"].append({"position": sub.position, "cells": cells, "source_keys": sub.source_keys})

    def submit(self, submission: Submission) -> None:
        sub = submission
        require(sub.scope == self.scope, "mock target mismatch")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            data = self._load(db)
            # No silent provider deduplication: an engine replay fails this fixture.
            require(sub.attempt_id not in data["operations"], "duplicate provider submit")
            mode = data["plans"].pop(0) if data["plans"] else "apply"
            data["calls"].append(asdict(sub))
            target = next((r for r in data["rows"] if r["position"] == sub.position), None)
            expected = json.loads(json.dumps(asdict(sub.before))) if sub.before else None
            if target != expected:
                mode = "reject"
            effect, settled, cancellation = Effect.UNKNOWN, False, "none"
            if mode in ("apply", "apply-timeout", "apply-crash"):
                self._apply(data, sub)
                effect, settled = Effect.APPLIED, True
            elif mode == "partial":
                self._apply(data, sub, partial=True)
                effect = Effect.PARTIAL
            elif mode in ("reject", "tool-noop", "human-noop", "denied-noop"):
                effect, settled = Effect.NOOP, True
            elif mode == "tool-pending":
                effect = Effect.ACTIVE
            cancellation = {"tool-noop": "tool", "tool-pending": "tool",
                            "human-noop": "human", "denied-noop": "denied"}.get(mode, "none")
            obs = Observation(sub.attempt_id, sub.digest, sub.scope, effect, settled, settled, True,
                              "LOCAL provider operation log; " + mode,
                              "cancelled-call" if cancellation != "none" else "provider-rejection",
                              cancellation=cancellation,
                              cancellation_authenticated=cancellation in ("human", "denied"))
            data["operations"][sub.attempt_id] = {"submission": asdict(sub), "observation": asdict(obs)}
            self._save(db, data)
        if mode in ("apply-crash", "before-crash"):
            raise SimulatedCrash(mode)
        if mode != "apply":
            raise TimeoutError("user cancelled MCP tool call" if cancellation != "none" else "LOCAL response lost")

    def inspect(self, submission: Submission) -> Observation:
        with self._connect() as db:
            item = self._load(db)["operations"].get(submission.attempt_id)
        if item is None:
            return Observation(submission.attempt_id, submission.digest, self.scope, Effect.UNKNOWN,
                               False, False, True, "LOCAL absent log is NOT proof of no-op")
        obs = dict(item["observation"])
        obs["effect"] = Effect(obs["effect"])
        return Observation(**obs)

    def resolve(self, attempt_id: str, effect: Effect) -> None:
        """Fixture-only authoritative settlement, including a simulated late apply."""
        require(effect in (Effect.APPLIED, Effect.NOOP, Effect.UNKNOWN, Effect.PARTIAL), "unsupported settlement")
        with self._connect() as db:
            data = self._load(db)
            item = data["operations"][attempt_id]
            previous = item["observation"]["effect"]
            require(previous in (Effect.ACTIVE, Effect.UNKNOWN), "cannot erase settled/partial effects")
            if effect == Effect.APPLIED:
                self._apply(data, SheetsWriter._submission(item["submission"]))
            obs = item["observation"]
            obs["effect"] = effect
            obs["settled"] = obs["effects_resolved"] = effect in (Effect.APPLIED, Effect.NOOP)
            obs["evidence"] = "LOCAL authoritative settlement; no outstanding effects"
            self._save(db, data)
