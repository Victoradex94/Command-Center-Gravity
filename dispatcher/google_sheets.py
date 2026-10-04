"""Bounded native Google Sheets transport; no credentials, SDK or hidden retries.

The injected tool caller is an already-authorised MCP connection, NOT an HTTP
client or authentication provider. The AJ-0010 route is agent-mediated. Only
the explicitly configured private sandbox is supported; no legacy-ledger import.
"""

from contextlib import closing
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import sqlite3
from typing import Callable

from .model import AGENT_JOB_COLUMNS, Status, require
from .sheets_writer import CurrentRow, Effect, Observation, Snapshot, Submission


TITLE = "Command Centre — Ledger Writer Sandbox"
PRODUCTION_ID = "19mGYxNeyldQEK4N194Q8Yz7L6m_z7LSvFmHGzwuqA84"
PREFIX = "mcp__codex_apps__google_drive_"
CELL_FIELDS = "userEnteredValue,userEnteredFormat,dataValidation,note,chipRuns,textFormatRuns"
FILE_FIELDS = "id,name,mimeType,trashed,shared,ownedByMe,driveId,parents,owners,permissions,capabilities(canEdit)"
SOURCE_CODEC = "vicadex.sandbox.source.v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def tool_payload(result: dict) -> dict:
    """Outer success/text is insufficient. Never parse reassuring prose as data."""
    require(isinstance(result, dict) and result.get("isError") is False,
            "connector error or missing explicit success flag")
    value = result.get("structuredContent")
    require(isinstance(value, dict) and "error" not in value,
            "complete structured connector response required")
    return value


def private_owner_only(file: dict, email: str, *, file_id: str) -> None:
    require(file.get("id") == file_id and file.get("shared") is False,
            "private exact Drive object required")
    if "mime_type" in file:
        # Actual MCP files.get normalization omits owners/capabilities/trashed.
        # Use its explicit visibility status and effective owner-only permissions;
        # never invent omitted ownedByMe/canEdit/inheritance flags.
        require(file.get("source_visibility_status") == "permission_metadata_available"
                and "drive_id" in file and file["drive_id"] is None,
                "complete normalized My Drive permission metadata required")
    else:
        require(file.get("trashed") is False and file.get("ownedByMe") is True
                and not file.get("driveId") and file.get("capabilities", {}).get("canEdit") is True,
                "private owned editable My Drive object required")
        owners = file.get("owners")
        require(isinstance(owners, list) and len(owners) == 1
                and owners[0].get("me") is True and owners[0].get("emailAddress") == email,
                "authenticated owner identity required")
    permissions = file.get("permissions")
    require(isinstance(permissions, list) and len(permissions) == 1,
            "complete owner-only permissions required")
    permission = permissions[0]
    require(permission.get("type") == "user" and permission.get("role") == "owner"
            and permission.get("emailAddress") == email and not permission.get("deleted")
            and not any(p.get("inherited") for p in permission.get("permissionDetails", [])),
            "shared or inherited access cannot be excluded")


def file_field(file: dict, provider: str, normalized: str):
    return file.get(normalized if "mime_type" in file else provider)


@dataclass(frozen=True)
class SandboxTarget:
    spreadsheet_id: str
    sheet_id: int
    sheet_title: str
    owner_email: str
    root_folder_id: str
    source_keys: tuple[str, ...]
    rows: int = 6
    columns: int = 18

    def __post_init__(self):
        require(bool(self.spreadsheet_id) and self.spreadsheet_id != PRODUCTION_ID,
                "production workbook is never a sandbox target")
        require(type(self.sheet_id) is int and self.sheet_id >= 0
                and bool(self.sheet_title) and bool(self.owner_email) and bool(self.root_folder_id),
                "grounded sandbox identity required")
        require(type(self.rows) is int and 2 <= self.rows <= 100
                and self.columns == 18, "bounded A:Q ledger plus R sentinels required")
        require(isinstance(self.source_keys, tuple) and bool(self.source_keys)
                and all(isinstance(s, str) and bool(s.strip()) for s in self.source_keys)
                and len(set(self.source_keys)) == len(self.source_keys), "source allowlist required")

    @property
    def scope(self) -> str:
        return f"google-sheets/{self.spreadsheet_id}/{self.sheet_id}"

    @property
    def a1(self) -> str:
        return "'" + self.sheet_title.replace("'", "''") + f"'!A1:R{self.rows}"


class ReceiptJournal:
    """Durable exact-call receipts; absence is UNKNOWN, never no-op evidence.

    INSERT uniqueness prevents re-emission after a crash, even before the call.
    Cooperating writers must retain this DB AND the accepted writer journal.
    """

    def __init__(self, path: str, target: SandboxTarget):
        self.path, self.target = path, target
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS identity (id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS receipts (attempt TEXT PRIMARY KEY, body TEXT NOT NULL)")
            row = db.execute("SELECT body FROM identity WHERE id=1").fetchone()
            encoded = json.dumps(asdict(target), sort_keys=True)
            require(row is None or row[0] == encoded, "receipt journal target mismatch")
            if row is None:
                db.execute("INSERT INTO identity VALUES (1, ?)", (encoded,))

    def connect(self):
        # Callers use both closing and transaction contexts below via helper.
        from contextlib import contextmanager

        @contextmanager
        def connection():
            with closing(sqlite3.connect(self.path)) as db:
                db.execute("PRAGMA synchronous=FULL")
                with db:
                    yield db
        return connection()

    def prepare(self, sub: Submission, baseline: dict, request: dict) -> None:
        body = {"submission": asdict(sub), "baseline": baseline, "request": request,
                "response": None, "exception_type": None}
        with self.connect() as db:
            db.execute("INSERT INTO receipts VALUES (?, ?)",
                       (sub.attempt_id, json.dumps(body, sort_keys=True)))

    def get(self, sub: Submission) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT body FROM receipts WHERE attempt=?", (sub.attempt_id,)).fetchone()
        if row is None:
            return None
        body = json.loads(row[0])
        require(digest(body["submission"]) == digest(asdict(sub)), "receipt identity/digest mismatch")
        return body

    def finish(self, sub: Submission, *, response=None, exception_type=None) -> None:
        body = self.get(sub)
        require(body is not None and body["response"] is None and body["exception_type"] is None,
                "receipt cannot be replaced")
        body.update(response=response, exception_type=exception_type)
        with self.connect() as db:
            db.execute("UPDATE receipts SET body=? WHERE attempt=?",
                       (json.dumps(body, sort_keys=True), sub.attempt_id))


class GoogleSheetsAdapter:
    """One batch/updateCells per submission with literal stringValue semantics.

    There is no CAS, provider operation lookup, automatic retry or failure-to-noop
    conversion. An original synchronous Google acknowledgement plus complete
    readback can settle that invocation. It does not prove physical exactly-once,
    absence of hidden connector retries, CAS or future immunity to external edits.
    Lost/malformed receipts remain UNKNOWN even if cells later match.
    """

    def __init__(self, target: SandboxTarget, call: Callable[[str, dict], dict],
                 receipts: ReceiptJournal):
        require(receipts.target == target, "adapter/receipt target mismatch")
        self.target, self.call, self.receipts = target, call, receipts

    def _read(self, action: str, args: dict) -> dict:
        return tool_payload(self.call(PREFIX + action, args))

    def _scope(self, scope: str):
        require(scope == self.target.scope, "adapter scope mismatch")

    def _sources(self, value: str) -> tuple[str, ...]:
        data = json.loads(value)
        require(isinstance(data, dict) and data.get("codec") == SOURCE_CODEC,
                "unsupported source convention; legacy import is not implemented")
        keys = data.get("source_keys")
        require(isinstance(keys, list) and bool(keys)
                and all(isinstance(s, str) and s in self.target.source_keys for s in keys)
                and len(set(keys)) == len(keys), "unrecognised source identity")
        return tuple(keys)

    @staticmethod
    def _literal(cell: dict) -> str:
        require(not cell.get("chipRuns") and not cell.get("textFormatRuns"),
                "rich values cannot be preserved by a literal update")
        value = cell.get("userEnteredValue", {})
        if value == {}:
            return ""
        require(isinstance(value, dict) and set(value) == {"stringValue"}
                and isinstance(value["stringValue"], str), "literal string cells required")
        return value["stringValue"]

    def capture(self) -> dict:
        t = self.target
        file = self._read("get_file_metadata", {"fileId": t.spreadsheet_id, "fields": FILE_FIELDS})
        private_owner_only(file, t.owner_email, file_id=t.spreadsheet_id)
        require(file_field(file, "name", "title") == TITLE
                and file_field(file, "mimeType", "mime_type") == "application/vnd.google-apps.spreadsheet"
                and file_field(file, "parents", "parent_ids") == [t.root_folder_id],
                "sandbox identity/parent changed")
        root = self._read("get_file_metadata", {"fileId": "root", "fields": FILE_FIELDS})
        private_owner_only(root, t.owner_email, file_id=t.root_folder_id)
        require(file_field(root, "mimeType", "mime_type") == "application/vnd.google-apps.folder",
                "My Drive root required")
        meta = self._read("get_spreadsheet_metadata", {
            "spreadsheet_id": t.spreadsheet_id, "include_conditional_format_rules": True})
        require(meta.get("spreadsheetId") == t.spreadsheet_id
                and meta.get("properties", {}).get("title") == TITLE
                and len(meta.get("sheets", [])) == 1, "exact single-tab workbook required")
        props = meta["sheets"][0]["properties"]
        require(props.get("sheetId") == t.sheet_id and props.get("title") == t.sheet_title
                and props.get("sheetType") == "GRID"
                and props.get("gridProperties", {}).get("rowCount") == t.rows
                and props.get("gridProperties", {}).get("columnCount") == t.columns,
                "complete bounded grid required; no implicit expansion")
        payload = self._read("get_spreadsheet_cells", {
            "spreadsheet_id": t.spreadsheet_id, "ranges": [t.a1], "cell_fields": CELL_FIELDS})
        require(payload.get("spreadsheetId") == t.spreadsheet_id
                and len(payload.get("sheets", [])) == 1, "wrong/truncated cell response")
        sheet = payload["sheets"][0]
        require(sheet.get("properties") == props and len(sheet.get("data", [])) == 1,
                "grid metadata changed or missing range data")
        grid = sheet["data"][0]
        require(grid.get("startRow", 0) == 0 and grid.get("startColumn", 0) == 0,
                "wrong grid offsets")
        rows = grid.get("rowData", [])
        # A sentinel in every R cell prevents trailing-empty truncation ambiguity.
        require(len(rows) == t.rows and all(len(r.get("values", [])) == 18 for r in rows),
                "full sentinel-bounded CellData rectangle required")
        cells = [r["values"] for r in rows]
        require(all(isinstance(c, dict) for row in cells for c in row), "malformed cell data")
        require(all(self._literal(row[17]) == f"AJ-0010 sentinel R{i + 1}" for i, row in enumerate(cells)),
                "sentinel mismatch")
        for row in cells[1:]:
            for column, options in ((4, [s.value for s in Status]), (13, ["Yes", "No"])):
                validation = row[column].get("dataValidation", {})
                require(validation.get("strict") is True
                        and validation.get("condition") == {"type": "ONE_OF_LIST", "values": [
                            {"userEnteredValue": option} for option in options]},
                        "exact seven-status/Yes-No validation required")
        return {"metadata": meta, "cells": cells, "file": file, "root": root}

    def _snapshot(self, captured: dict) -> Snapshot:
        matrix = [tuple(self._literal(c) for c in row[:17]) for row in captured["cells"]]
        require(matrix[0] == AGENT_JOB_COLUMNS, "exact 17-column header required")
        rows = []
        for position, cells in enumerate(matrix[1:], 2):
            if not any(cells):
                continue
            require(bool(cells[0]), "orphan nonempty ledger row")
            rows.append(CurrentRow(position, cells, self._sources(cells[9])))
        return Snapshot(self.target.scope, matrix[0], tuple(rows), True, True,
                        "MCP complete bounded grid; sha256=" + digest(captured))

    def snapshot(self, scope: str) -> Snapshot:
        self._scope(scope)
        return self._snapshot(self.capture())

    def request(self, sub: Submission) -> dict:
        self._scope(sub.scope)
        require(type(sub.position) is int and 2 <= sub.position <= self.target.rows
                and len(sub.cells) == 17 and all(isinstance(c, str) and len(c) <= 50000 for c in sub.cells),
                "single bounded 17-string data row required")
        require(self._sources(sub.cells[9]) == sub.source_keys, "source sidecar differs from actual J")
        return {"spreadsheet_id": self.target.spreadsheet_id, "requests": [{"updateCells": {
            "range": {"sheetId": self.target.sheet_id, "startRowIndex": sub.position - 1,
                      "endRowIndex": sub.position, "startColumnIndex": 0, "endColumnIndex": 17},
            "rows": [{"values": [{"userEnteredValue": {"stringValue": c}} for c in sub.cells]}],
            "fields": "userEnteredValue"}}]}

    def submit(self, sub: Submission) -> None:
        request = self.request(sub)
        require(self.receipts.get(sub) is None, "attempt already prepared; reconcile without replay")
        before = self.capture()
        snap = self._snapshot(before)
        at_position = next((r for r in snap.rows if r.position == sub.position), None)
        require(at_position == sub.before, "row moved/changed since writer preflight")
        require(not any((r.cells[0] == sub.cells[0] or set(r.source_keys) & set(sub.source_keys))
                        and r.position != sub.position for r in snap.rows), "duplicate ID/source")
        self.receipts.prepare(sub, before, request)
        try:
            response = self.call(PREFIX + "batch_update_spreadsheet", request)
        except Exception as exc:
            self.receipts.finish(sub, exception_type=type(exc).__name__)
            raise
        self.receipts.finish(sub, response=response)

    @staticmethod
    def unchanged_structure(before: dict, after: dict, position: int) -> bool:
        def masked(capture):
            value = deepcopy(capture)
            # Drive volatile metadata isn't requested. Retain actual ACLs.
            for cell in value["cells"][position - 1][:17]:
                cell.pop("userEnteredValue", None)
            return value
        return masked(before) == masked(after)

    def inspect(self, sub: Submission) -> Observation:
        self._scope(sub.scope)
        receipt = self.receipts.get(sub)
        effect, settled, signal = Effect.UNKNOWN, False, "provider-unknown"
        cancellation, failure_class = "none", "verification-evidence"
        evidence = "No verified original synchronous Google acknowledgement and full readback."
        if receipt is not None:
            evidence += " Receipt sha256=" + digest(receipt)
            if receipt["exception_type"] == "TimeoutError":
                signal, failure_class = "timeout", "transient-availability"
            response_text = json.dumps(receipt["response"], ensure_ascii=False).lower()
            if "user cancelled mcp tool call" in response_text:
                signal, cancellation, failure_class = "cancelled-call", "tool", "transport-routing"
            try:
                require(receipt["exception_type"] is None and cancellation == "none",
                        "contradictory exception/cancellation cannot establish completion")
                require(digest(receipt["request"]) == digest(self.request(sub)),
                        "receipt request differs from bound submission")
                require(isinstance(receipt["response"], dict)
                        and set(receipt["response"]) <= {"isError", "structuredContent", "content", "_meta"}
                        and receipt["response"].get("_meta") in (None, {}),
                        "unfamiliar connector envelope")
                response = tool_payload(receipt["response"])
                require(set(response) <= {"spreadsheetId", "replies", "updatedSpreadsheet", "commentUpdateState"}
                        and response.get("commentUpdateState") in (None, "NO_UPDATES_REQUESTED", "COMMENT_UPDATE_STATE_UNSPECIFIED"),
                        "unfamiliar/asynchronous or contradictory provider response")
                require(response.get("spreadsheetId") == self.target.spreadsheet_id
                        and response.get("replies") == [{}], "exact batch response required")
                # The supported MCP normalizes an omitted optional resource to
                # null when include_spreadsheet_in_response was not requested.
                # Only a supplied resource can contradict the target identity.
                if response.get("updatedSpreadsheet") is not None:
                    require(isinstance(response["updatedSpreadsheet"], dict)
                            and response["updatedSpreadsheet"].get("spreadsheetId") == self.target.spreadsheet_id,
                            "contradictory updated spreadsheet identity")
                after = self.capture()
                snap = self._snapshot(after)
                matching = [r for r in snap.rows if r.cells[0] == sub.cells[0]
                            or set(r.source_keys) & set(sub.source_keys)]
                require(matching == [CurrentRow(sub.position, sub.cells, sub.source_keys)],
                        "exact unique 17-cell/source/position readback required")
                require(self.unchanged_structure(receipt["baseline"], after, sub.position),
                        "neighbour/format/validation/metadata drift")
                effect, settled = Effect.APPLIED, True
                evidence = ("Synchronous batchUpdate response and exact 17-cell/source/position readback; "
                            "exposed structure/neighbours unchanged; receipt sha256=" + digest(receipt)
                            + "; readback sha256=" + digest(after)
                            + ". Original acknowledged invocation complete under Google batchUpdate contract; "
                            "not physical exactly-once, hidden-retry transparency, distributed exclusion or CAS.")
            except Exception as exc:
                evidence += " Verification unavailable: " + type(exc).__name__
                if signal == "provider-unknown" and receipt["response"] is not None:
                    signal = "readback-mismatch"
        return Observation(sub.attempt_id, sub.digest, sub.scope, effect, settled, settled,
                           True, evidence, signal, failure_class, cancellation)
