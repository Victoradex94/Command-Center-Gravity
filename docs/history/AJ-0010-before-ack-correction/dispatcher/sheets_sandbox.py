"""AJ-0010 fixture planner and guarded two-operation driver.

Planning is pure and confers no permission. The live coordinator must establish
one owner, actual private access and the existing tool route before setup. This
module never creates a workbook, claims authority, cleans up or recovers a write.
"""

from dataclasses import dataclass, replace
import json

from .google_sheets import SOURCE_CODEC, SandboxTarget
from .model import AGENT_JOB_COLUMNS, AgentJob, Lineage, Status, require, timestamp
from .sheets_writer import Outcome, SheetsWriter, WriteRequest, WriterToken


CREATE_ID = "AJ-0010/sandbox/create-v1"
UPDATE_ID = "AJ-0010/sandbox/update-v1"
SOURCE = "synthetic:AJ-0010:VA-LIVE-SHEETS-0010-01"
AUTHORITY = "slack:1791113671.468969/AJ-0010/sandbox"
ROUTE = "existing-google-drive-mcp-agent-bridge"


def fixture_requests(sheet_id: int) -> list[dict]:
    """One separately counted setup batch, only in the freshly verified blank file."""
    require(type(sheet_id) is int and sheet_id >= 0, "metadata-derived sheet ID required")
    def grid(r0, r1, c0, c1):
        return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
                "startColumnIndex": c0, "endColumnIndex": c1}
    def values(range_, rows):
        return {"updateCells": {"range": range_, "fields": "userEnteredValue", "rows": [
            {"values": [{"userEnteredValue": {"stringValue": v}} for v in row]} for row in rows]}}
    requests = [{"updateSheetProperties": {"properties": {"sheetId": sheet_id,
        "title": "Agent Jobs Sandbox", "gridProperties": {"rowCount": 6, "columnCount": 18,
        "frozenRowCount": 1}}, "fields": "title,gridProperties"}},
        values(grid(0, 1, 0, 17), [AGENT_JOB_COLUMNS]),
        values(grid(0, 6, 17, 18), [[f"AJ-0010 sentinel R{i}"] for i in range(1, 7)]),
        {"repeatCell": {"range": grid(0, 6, 0, 18), "cell": {"userEnteredFormat": {
            "numberFormat": {"type": "TEXT"}, "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat"}},
        {"repeatCell": {"range": grid(0, 1, 0, 17), "cell": {"userEnteredFormat": {
            "textFormat": {"bold": True}, "backgroundColor": {"red": .9, "green": .9, "blue": .9}}},
            "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColor"}}]
    for col, options in ((4, [s.value for s in Status]), (13, ["Yes", "No"])):
        requests.append({"setDataValidation": {"range": grid(1, 6, col, col + 1), "rule": {
            "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": s} for s in options]},
            "strict": True, "showCustomUi": True}}})
    return requests


@dataclass(frozen=True)
class SandboxPlan:
    create: WriteRequest
    update: WriteRequest


def plan(observed_at: str) -> SandboxPlan:
    timestamp(observed_at)
    source = json.dumps({"codec": SOURCE_CODEC, "source_keys": [SOURCE],
                        "brief": "Synthetic isolated sandbox only; no production job."},
                       ensure_ascii=False, sort_keys=True)
    row = AgentJob("AJ-0010", "", "Synthetic ledger transport fixture", "Codex sandbox fixture",
        Status.INTAKE, "Normal", observed_at, "2026-10-04", "Synthetic standalone; no Master task",
        source, "=literal RAW text; Vic’Adex", "Synthetic verification pending",
        "Synthetic create; not production AJ-0010 state", "No", "Sandbox approved; not a new decision",
        observed_at, "SpecRevision=1; RunEpoch=1; Attempt=1; Nonce=VA-LIVE-SHEETS-0010-01; "
        "RecordRevision=1; ProtocolVersion=v1.1.0; CatalogueVersion=1.0.0")
    lineage = Lineage("AJ-0010", 1, 1, 1)
    create = WriteRequest(CREATE_ID, "AJ-0010", None, tuple(row.to_cells()), (SOURCE,), AUTHORITY,
        "AJ-0010/SpecRevision1/RunEpoch1/Attempt1/VA-LIVE-SHEETS-0010-01",
        "private-isolated-single-owner-sandbox", ROUTE, intended_lineage=lineage)
    cells = list(create.cells)
    cells[4], cells[10], cells[11], cells[12] = (
        "Ready", "Synthetic update verified literally", "Synthetic update readback pending",
        "Synthetic update; not production AJ-0010 state")
    cells[16] = cells[16].replace("RecordRevision=1", "RecordRevision=2")
    return SandboxPlan(create, replace(create, operation_id=UPDATE_ID, expected_revision=1,
                                      expected_lineage=lineage, cells=tuple(cells)))


def execute_once(writer: SheetsWriter, token: WriterToken, fixture: SandboxPlan) -> dict:
    """Only under established authority. UNKNOWN blocks the second operation."""
    require(fixture.create.operation_id == CREATE_ID and fixture.update.operation_id == UPDATE_ID,
            "stable sandbox operation IDs required")
    require(not writer.state()["operations"], "existing history must be reconciled; never restart this driver")
    require(not writer.snapshot().rows, "sandbox already contains logical rows")
    create = writer.write(fixture.create, token)
    if create.outcome != Outcome.SUCCESS:
        return {"create": create, "update": None, "hold": "create settlement unproved; freeze same operation"}
    update = writer.write(fixture.update, token)
    return {"create": create, "update": update, "hold": "" if update.outcome == Outcome.SUCCESS else
            "update settlement unproved; freeze same operation"}


def reconcile_existing(writer: SheetsWriter) -> dict:
    """Restart path: no claim, write, recover, retirement or new operation."""
    operations = writer.state()["operations"]
    require(set(operations) <= {CREATE_ID, UPDATE_ID}, "unexpected sandbox history")
    return {operation: writer.reconcile(operation) for operation in operations}
