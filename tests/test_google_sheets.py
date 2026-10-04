"""SIMULATED MCP fixtures. These tests never contact Google or prove live access."""

from copy import deepcopy
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from dispatcher.google_sheets import (CELL_FIELDS, FILE_FIELDS, PREFIX, PRODUCTION_ID,
    SOURCE_CODEC, TITLE, GoogleSheetsAdapter, ReceiptJournal, SandboxTarget, digest,
    private_owner_only, tool_payload)
from dispatcher.model import AGENT_JOB_COLUMNS, Lineage, ProtocolError, ReconciliationRequired, Status
from dispatcher.sheets_tool_bridge import StdioToolBridge
from dispatcher.sheets_sandbox import (CREATE_ID, UPDATE_ID, SOURCE, execute_once,
                                       fixture_requests, plan, reconcile_existing)
from dispatcher.sheets_writer import Effect, Outcome, SheetsWriter, Submission
from dispatcher.writer_journal import WriterJournal
from dispatcher.mock_sheets import MockAuthority
from tests.test_sheets_writer import request


def result(value):
    return {"isError": False, "structuredContent": deepcopy(value),
            "content": [{"type": "text", "text": "Action completed."}]}


def file_metadata(file_id, email, folder=False):
    return {"id": file_id, "name": "My Drive" if folder else TITLE,
            "mimeType": "application/vnd.google-apps.folder" if folder else "application/vnd.google-apps.spreadsheet",
            "trashed": False, "shared": False, "ownedByMe": True,
            "owners": [{"me": True, "emailAddress": email}],
            "permissions": [{"id": "owner", "type": "user", "role": "owner", "emailAddress": email}],
            "capabilities": {"canEdit": True}, **({} if folder else {"parents": ["root-fixture"]})}


class FakeConnector:
    def __init__(self, target):
        self.target, self.calls, self.mode = target, [], "apply"
        self.file = file_metadata(target.spreadsheet_id, target.owner_email)
        self.root = file_metadata(target.root_folder_id, target.owner_email, True)
        self.props = {"sheetId": target.sheet_id, "title": target.sheet_title,
                      "sheetType": "GRID", "gridProperties": {"rowCount": target.rows,
                      "columnCount": target.columns, "frozenRowCount": 1}}
        self.meta = {"spreadsheetId": target.spreadsheet_id, "properties": {"title": TITLE},
                     "sheets": [{"properties": self.props}]}
        self.cells = [[{} for _ in range(18)] for _ in range(target.rows)]
        for i, col in enumerate(AGENT_JOB_COLUMNS):
            self.cells[0][i] = {"userEnteredValue": {"stringValue": col},
                                "userEnteredFormat": {"textFormat": {"bold": True}}}
        for i, row in enumerate(self.cells):
            row[17] = {"userEnteredValue": {"stringValue": f"AJ-0010 sentinel R{i + 1}"}}
            if i:
                for cell in row[:17]:
                    cell["userEnteredFormat"] = {"numberFormat": {"type": "TEXT"}, "wrapStrategy": "WRAP"}
                row[4]["dataValidation"] = {"condition": {"type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": s.value} for s in Status]}, "strict": True}
                row[13]["dataValidation"] = {"condition": {"type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": s} for s in ("Yes", "No")]}, "strict": True}

    @property
    def writes(self):
        return [c for c in self.calls if c[0] == PREFIX + "batch_update_spreadsheet"]

    def __call__(self, name, args):
        self.calls.append((name, deepcopy(args)))
        if name == PREFIX + "get_file_metadata":
            return result(self.root if args["fileId"] == "root" else self.file)
        if name == PREFIX + "get_spreadsheet_metadata":
            return result(self.meta)
        if name == PREFIX + "get_spreadsheet_cells":
            return result({**self.meta, "sheets": [{"properties": self.props,
                "data": [{"rowData": [{"values": r} for r in self.cells]}]}]})
        if name == PREFIX + "batch_update_spreadsheet":
            if self.mode == "cancel":
                return {"isError": True, "content": [{"type": "text", "text": "user cancelled MCP tool call"}]}
            if self.mode == "raise":
                raise TimeoutError("SIMULATED timeout")
            update = args["requests"][0]["updateCells"]
            row = self.cells[update["range"]["startRowIndex"]]
            for cell, val in zip(row, update["rows"][0]["values"]):
                cell.update(val)
            if self.mode == "apply-timeout":
                raise TimeoutError("SIMULATED response lost after application")
            if self.mode == "malformed":
                return {"isError": False, "content": [{"type": "text", "text": "Action completed."}]}
            return result({"spreadsheetId": self.target.spreadsheet_id, "replies": [{}]})
        raise AssertionError(name)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = SandboxTarget("synthetic-only", 123, "Agent Jobs Sandbox", "fixture@example.invalid",
                                    "root-fixture", ("synthetic:AJ-0010",))
        self.fake = FakeConnector(self.target)
        self.path = str(Path(self.temp.name) / "receipts.sqlite")
        self.adapter = GoogleSheetsAdapter(self.target, self.fake, ReceiptJournal(self.path, self.target))
        req = request(operation="AJ-0010/sandbox/create-v1", job="AJ-0010", source_key=self.target.source_keys[0])
        cells = list(req.cells)
        cells[9] = json.dumps({"codec": SOURCE_CODEC, "source_keys": list(self.target.source_keys),
                               "note": "SIMULATED synthetic source"})
        cells[10] = "=literal, not a formula\nVic’Adex"
        self.req = replace(req, cells=tuple(cells), route="existing-google-drive-mcp-agent-bridge")
        self.sub = Submission(self.req.operation_id, self.req.operation_id + "/0", self.req.digest,
                              self.target.scope, 2, None, self.req.cells, self.req.source_keys,
                              self.req.route, self.req.authority_ref)

    def writer(self):
        return SheetsWriter(WriterJournal(str(Path(self.temp.name) / "writer.sqlite"), self.target.scope),
                            self.adapter, MockAuthority())

    def test_exact_narrow_literal_request_and_structural_readback(self):
        before = self.adapter.capture()
        self.adapter.submit(self.sub)
        after = self.adapter.capture()
        self.assertEqual(len(self.fake.writes), 1)
        args = self.fake.writes[0][1]
        update = args["requests"][0]["updateCells"]
        self.assertEqual(update["fields"], "userEnteredValue")
        self.assertEqual(update["range"], {"sheetId": 123, "startRowIndex": 1, "endRowIndex": 2,
                                           "startColumnIndex": 0, "endColumnIndex": 17})
        self.assertEqual(tuple(v["userEnteredValue"]["stringValue"] for v in update["rows"][0]["values"]), self.req.cells)
        self.assertTrue(self.adapter.unchanged_structure(before, after, 2))
        obs = self.adapter.inspect(self.sub)
        self.assertEqual(obs.effect, Effect.APPLIED)
        self.assertTrue(obs.settled)
        self.assertTrue(obs.effects_resolved)

    def test_scope_and_production_target_rejected(self):
        with self.assertRaises(ProtocolError):
            replace(self.target, spreadsheet_id=PRODUCTION_ID)
        with self.assertRaises(ProtocolError):
            self.adapter.snapshot("other-scope")
        with self.assertRaises(ProtocolError):
            self.adapter.submit(replace(self.sub, scope="other-scope"))
        self.assertEqual(self.fake.calls, [])

    def test_wrong_dimensions_or_expansion_rejected(self):
        for position in (1, 7, True):
            with self.assertRaises(ProtocolError):
                self.adapter.request(replace(self.sub, position=position))
        self.fake.props["gridProperties"]["rowCount"] = 7
        with self.assertRaises(ProtocolError):
            self.adapter.snapshot(self.target.scope)

    def test_source_sidecar_cannot_override_j(self):
        with self.assertRaises(ProtocolError):
            self.adapter.submit(replace(self.sub, source_keys=("forged",)))
        self.assertEqual(self.fake.writes, [])

    def test_update_maps_exact_revision_two_without_touching_other_cells(self):
        # Mapping fixture only: bypassing the writer is NOT an authorised live route.
        self.adapter.submit(self.sub)
        before = self.adapter.capture()
        row = self.adapter.snapshot(self.target.scope).rows[0]
        cells = list(self.req.cells)
        cells[4], cells[10] = "Ready", "SIMULATED update"
        cells[16] = cells[16].replace("RecordRevision=1", "RecordRevision=2")
        sub = replace(self.sub, operation_id="update", attempt_id="update/0", digest="fixture-update",
                      before=row, cells=tuple(cells))
        self.adapter.submit(sub)
        after = self.adapter.capture()
        self.assertTrue(self.adapter.unchanged_structure(before, after, 2))
        current = self.adapter.snapshot(self.target.scope).rows[0]
        self.assertEqual(current.cells, tuple(cells))
        self.assertEqual(current.revision, 2)
        self.assertEqual(current.lineage, row.lineage)
        self.assertEqual(len(self.fake.writes), 2)

    def test_validation_options_cannot_be_removed_or_widened(self):
        for col in (4, 13):
            old = deepcopy(self.fake.cells[1][col]["dataValidation"])
            self.fake.cells[1][col]["dataValidation"]["condition"]["values"].append({"userEnteredValue": "Paused"})
            with self.assertRaises(ProtocolError):
                self.adapter.submit(self.sub)
            self.fake.cells[1][col]["dataValidation"] = old
        self.assertEqual(self.fake.writes, [])

    def test_unknown_or_legacy_j_rejected(self):
        for value in ("legacy prose", '{"codec":"other"}',
                      json.dumps({"codec": SOURCE_CODEC, "source_keys": ["untrusted"]})):
            cells = list(self.sub.cells)
            cells[9] = value
            with self.assertRaises((ProtocolError, ValueError)):
                self.adapter.request(replace(self.sub, cells=tuple(cells)))

    def test_formula_chips_and_rich_text_rejected_before_write(self):
        for cell in ({"userEnteredValue": {"formulaValue": "=1"}},
                     {"chipRuns": [{"startIndex": 0}]}, {"textFormatRuns": [{"startIndex": 0}]}):
            with self.subTest(cell=cell):
                self.fake.cells[1][2] = cell
                with self.assertRaises(ProtocolError):
                    self.adapter.submit(self.sub)
        self.assertEqual(self.fake.writes, [])

    def test_privacy_missing_shared_inherited_other_owner_or_shared_drive_rejected(self):
        original = deepcopy(self.fake.file)
        cases = [{"shared": True}, {"driveId": "shared-drive"}, {"permissions": []},
                 {"owners": [{"me": False, "emailAddress": self.target.owner_email}]},
                 {"parents": ["shared-parent"]}, {"capabilities": {"canEdit": False}}]
        inherited = deepcopy(original["permissions"])
        inherited[0]["permissionDetails"] = [{"inherited": True}]
        cases.append({"permissions": inherited})
        for change in cases:
            with self.subTest(change=change):
                self.fake.file = {**original, **change}
                with self.assertRaises(ProtocolError):
                    self.adapter.submit(self.sub)
        self.assertEqual(self.fake.writes, [])

    def test_shared_root_rejected(self):
        self.fake.root["shared"] = True
        with self.assertRaises(ProtocolError):
            self.adapter.capture()

    def test_actual_normalized_metadata_shape_private_root_and_file(self):
        def normalized(file):
            return {"id": file["id"], "title": file["name"], "mime_type": file["mimeType"],
                    "parent_ids": file.get("parents"), "drive_id": None, "shared": False,
                    "permissions": file["permissions"],
                    "source_visibility_status": "permission_metadata_available"}
        self.fake.root, self.fake.file = normalized(self.fake.root), normalized(self.fake.file)
        self.adapter.capture()
        original = deepcopy(self.fake.file)
        for change in ({"shared": True}, {"source_visibility_status": "unknown"},
                       {"permissions": []}, {"parent_ids": None}, {"drive_id": "shared-drive"}):
            self.fake.file = {**original, **change}
            with self.assertRaises(ProtocolError):
                self.adapter.capture()
        self.fake.file = original
        del self.fake.file["drive_id"]
        with self.assertRaises(ProtocolError):
            self.adapter.capture()

    def test_header_or_sentinel_damage_rejected(self):
        for row, col in ((0, 0), (3, 17)):
            old = self.fake.cells[row][col]
            self.fake.cells[row][col] = {"userEnteredValue": {"stringValue": "changed"}}
            with self.assertRaises(ProtocolError):
                self.adapter.snapshot(self.target.scope)
            self.fake.cells[row][col] = old

    def test_truncated_missing_wrong_offset_and_wrong_id_reads_rejected(self):
        original = self.fake.__call__
        for change in ("truncate", "offset", "id", "data"):
            def call(name, args):
                response = original(name, args)
                if name.endswith("get_spreadsheet_cells"):
                    p = response["structuredContent"]
                    if change == "id": p["spreadsheetId"] = "wrong"
                    elif change == "data": p["sheets"][0]["data"] = []
                    elif change == "offset": p["sheets"][0]["data"][0]["startRow"] = 1
                    else: p["sheets"][0]["data"][0]["rowData"].pop()
                return response
            self.adapter.call = call
            with self.assertRaises(ProtocolError):
                self.adapter.snapshot(self.target.scope)

    def test_malformed_outer_success_is_not_provider_success(self):
        for response in ({"content": [{"text": "success"}]}, {"isError": False},
                         {"isError": False, "structuredContent": {"error": "denied"}}):
            with self.assertRaises(ProtocolError):
                tool_payload(response)

    def test_duplicate_submit_blocked_after_restart(self):
        self.adapter.submit(self.sub)
        restarted = GoogleSheetsAdapter(self.target, self.fake, ReceiptJournal(self.path, self.target))
        with self.assertRaises(ProtocolError):
            restarted.submit(self.sub)
        with self.assertRaises(ProtocolError):
            restarted.inspect(replace(self.sub, digest="changed"))
        self.assertEqual(len(self.fake.writes), 1)

    def test_crash_after_prepare_before_send_is_unknown_not_noop(self):
        self.adapter.receipts.prepare(self.sub, self.adapter.capture(), self.adapter.request(self.sub))
        self.assertEqual(self.adapter.inspect(self.sub).effect, Effect.UNKNOWN)
        with self.assertRaises(ProtocolError):
            self.adapter.submit(self.sub)
        self.assertEqual(len(self.fake.writes), 0)

    def test_absent_receipt_empty_row_does_not_prove_noop(self):
        obs = self.adapter.inspect(self.sub)
        self.assertEqual(obs.effect, Effect.UNKNOWN)
        self.assertFalse(obs.settled)

    def test_generic_cancel_timeout_malformed_and_applied_timeout_remain_unknown(self):
        for mode in ("cancel", "raise", "malformed", "apply-timeout"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                fake = FakeConnector(self.target)
                fake.mode = mode
                adapter = GoogleSheetsAdapter(self.target, fake,
                    ReceiptJournal(str(Path(directory) / "receipt.sqlite"), self.target))
                try: adapter.submit(self.sub)
                except TimeoutError: pass
                obs = adapter.inspect(self.sub)
                self.assertEqual(obs.effect, Effect.UNKNOWN)
                self.assertFalse(obs.settled)
                self.assertEqual(obs.cancellation, "tool" if mode == "cancel" else "none")
                self.assertFalse(obs.cancellation_authenticated)
                if mode in ("raise", "apply-timeout"):
                    self.assertEqual(obs.signal, "timeout")
                self.assertEqual(len(fake.writes), 1)

    def test_metadata_or_neighbour_drift_blocks_observed_application(self):
        self.adapter.submit(self.sub)
        original = deepcopy(self.fake.cells)
        for row, col, key, value in ((1, 4, "dataValidation", {}),
                                    (1, 3, "userEnteredFormat", {}),
                                    (4, 10, "note", "changed")):
            self.fake.cells[row][col][key] = value
            self.assertEqual(self.adapter.inspect(self.sub).effect, Effect.UNKNOWN)
            self.fake.cells = deepcopy(original)

    def test_row_move_or_conflict_between_preflight_and_submit_blocks_call(self):
        self.fake.cells[1][0]["userEnteredValue"] = {"stringValue": "AJ-OTHER"}
        with self.assertRaises((ProtocolError, ValueError)):
            self.adapter.submit(self.sub)
        self.assertEqual(len(self.fake.writes), 0)

    def test_journal_identity_not_retargetable(self):
        with self.assertRaises(ProtocolError):
            ReceiptJournal(self.path, replace(self.target, spreadsheet_id="other"))

    def test_writer_freezes_update_restarts_reconciles_without_replay_or_budget_reset(self):
        self.fake.mode = "apply-timeout"
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        first = writer.write(self.req, token)
        self.assertEqual(first.outcome, Outcome.UNCERTAIN)
        self.assertEqual(len(self.fake.writes), 1)
        self.assertEqual(writer.write(self.req, token), first)
        update = replace(self.req, operation_id="AJ-0010/sandbox/update-v1", expected_revision=1)
        with self.assertRaises(ReconciliationRequired):
            writer.write(update, token)
        restart = self.writer()
        reconciled = restart.reconcile(self.req.operation_id)
        self.assertEqual(reconciled.outcome, Outcome.UNCERTAIN)
        self.assertEqual(reconciled.fingerprint, first.fingerprint)
        self.assertEqual(reconciled.recovery_used, 0)
        self.assertEqual(len(self.fake.writes), 1)
        self.assertEqual(restart.read("AJ-0010").revision, 1)
        self.assertEqual(restart.read("AJ-0010").lineage, Lineage("AJ-0010", 1, 1, 1))

    def test_acknowledged_create_update_and_restart_both_operations_without_replay(self):
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        baseline = self.adapter.capture()
        self.assertEqual(writer.write(self.req, token).outcome, Outcome.SUCCESS)
        self.assertEqual(writer.read("AJ-0010").cells, self.req.cells)
        self.assertEqual(writer.read("AJ-0010").revision, 1)
        cells = list(self.req.cells)
        cells[4], cells[10] = "Ready", "SIMULATED second acknowledged mutation"
        cells[16] = cells[16].replace("RecordRevision=1", "RecordRevision=2")
        update = replace(self.req, operation_id=UPDATE_ID, cells=tuple(cells), expected_revision=1,
                         expected_lineage=self.req.intended_lineage)
        self.assertEqual(writer.write(update, token).outcome, Outcome.SUCCESS)
        self.adapter = GoogleSheetsAdapter(self.target, self.fake, ReceiptJournal(self.path, self.target))
        restart = self.writer()
        for operation in (self.req.operation_id, update.operation_id):
            self.assertEqual(restart.reconcile(operation).outcome, Outcome.SUCCESS)
        self.assertEqual(restart.read("AJ-0010").cells, tuple(cells))
        self.assertEqual(restart.read("AJ-0010").revision, 2)
        self.assertEqual(restart.read("AJ-0010").lineage, self.req.intended_lineage)
        self.assertEqual(len(self.fake.writes), 2)
        self.assertTrue(self.adapter.unchanged_structure(baseline, self.adapter.capture(), 2))

    def test_crash_after_durable_ack_before_writer_marker_adopts_without_replay(self):
        class ProcessCrash(BaseException): pass
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        original = self.adapter.inspect
        def crash(sub): raise ProcessCrash()
        self.adapter.inspect = crash
        with self.assertRaises(ProcessCrash):
            writer.write(self.req, token)
        self.assertEqual(writer.state()["operations"][CREATE_ID]["outcome"], Outcome.UNCERTAIN)
        self.adapter.inspect = original
        restart = self.writer()
        self.assertEqual(restart.reconcile(CREATE_ID).outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.fake.writes), 1)

    def test_positive_ack_read_failure_then_readonly_reconciliation_succeeds(self):
        failed_read = True
        def call(name, args):
            if failed_read and self.fake.writes and name.endswith("get_file_metadata"):
                raise TimeoutError("SIMULATED read outage after retained acknowledgement")
            return self.fake(name, args)
        self.adapter.call = call
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        first = writer.write(self.req, token)
        self.assertEqual(first.outcome, Outcome.UNCERTAIN)
        failed_read = False
        reconciled = self.writer().reconcile(CREATE_ID)
        self.assertEqual(reconciled.outcome, Outcome.SUCCESS)
        self.assertEqual(reconciled.fingerprint, first.fingerprint)
        self.assertEqual(reconciled.recovery_used, 0)
        self.assertEqual(len(self.fake.writes), 1)

    def test_delayed_matching_application_after_cancel_never_substitutes_for_ack(self):
        self.fake.mode = "cancel"
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        first = writer.write(self.req, token)
        self.assertEqual(first.outcome, Outcome.UNCERTAIN)
        # Simulate a late provider effect without issuing another request.
        for cell, value in zip(self.fake.cells[1], self.req.cells):
            cell["userEnteredValue"] = {"stringValue": value}
        late = self.writer().reconcile(CREATE_ID)
        self.assertEqual(late.outcome, Outcome.UNCERTAIN)
        self.assertEqual(late.fingerprint, first.fingerprint)
        self.assertEqual(late.recovery_used, 0)
        self.assertEqual(len(self.fake.writes), 1)

    def test_unfamiliar_async_wrong_target_and_wrong_reply_count_stay_unknown(self):
        changes = [
            {"spreadsheetId": "wrong"}, {"replies": []}, {"replies": [{}, {}]},
            {"replies": [{"updateCells": {}}]}, {"status": "pending"},
            {"operation": {"done": False}}, {"updatedSpreadsheet": {"spreadsheetId": "wrong"}},
            {"commentUpdateState": "ALL_FAILED_UNKNOWN_REASON"},
            {"updatedSpreadsheet": {}}, {"updatedSpreadsheet": False},
            {"updatedSpreadsheet": []}, {"updatedSpreadsheet": "pending"}]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                fake = FakeConnector(self.target)
                def call(name, args):
                    response = fake(name, args)
                    if name.endswith("batch_update_spreadsheet"):
                        response["structuredContent"].update(change)
                    return response
                adapter = GoogleSheetsAdapter(self.target, call,
                    ReceiptJournal(str(Path(directory) / "receipts.sqlite"), self.target))
                adapter.submit(self.sub)
                observation = adapter.inspect(self.sub)
                self.assertEqual(observation.effect, Effect.UNKNOWN)
                self.assertFalse(observation.settled)
                self.assertEqual(len(fake.writes), 1)

    def test_connector_null_optional_resource_needs_ack_and_exact_readback(self):
        def call(name, args):
            response = self.fake(name, args)
            if name.endswith("batch_update_spreadsheet"):
                response["structuredContent"]["updatedSpreadsheet"] = None
            return response
        self.adapter.call = call
        self.adapter.submit(self.sub)
        observation = self.adapter.inspect(self.sub)
        self.assertEqual(observation.effect, Effect.APPLIED)
        self.assertTrue(observation.settled)
        self.fake.cells[1][10]["userEnteredValue"] = {"stringValue": "SIMULATED drift"}
        self.assertFalse(self.adapter.inspect(self.sub).settled)
        self.assertEqual(len(self.fake.writes), 1)

    def test_contradictory_or_async_outer_wrapper_cannot_settle(self):
        for change in ({"status": "pending"}, {"_meta": {"pendingRetry": True}},
                       {"content": [{"type": "text", "text": "user cancelled MCP tool call"}]}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                fake = FakeConnector(self.target)
                def call(name, args):
                    response = fake(name, args)
                    if name.endswith("batch_update_spreadsheet"): response.update(change)
                    return response
                adapter = GoogleSheetsAdapter(self.target, call,
                    ReceiptJournal(str(Path(directory) / "receipts.sqlite"), self.target))
                adapter.submit(self.sub)
                self.assertFalse(adapter.inspect(self.sub).settled)
                self.assertEqual(len(fake.writes), 1)

    def test_partial_values_after_positive_ack_remain_unknown(self):
        self.adapter.submit(self.sub)
        self.fake.cells[1][10]["userEnteredValue"] = {"stringValue": "SIMULATED partial/changed value"}
        observation = self.adapter.inspect(self.sub)
        self.assertEqual(observation.effect, Effect.UNKNOWN)
        self.assertFalse(observation.settled)
        self.assertEqual(len(self.fake.writes), 1)

    def test_exposed_unresolved_prior_invocation_blocks_new_operation(self):
        self.fake.mode = "apply-timeout"
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        first = writer.write(self.req, token)
        self.fake.mode = "apply"
        with self.assertRaises(ReconciliationRequired):
            writer.write(replace(self.req, operation_id="different-label"), token)
        self.assertEqual(first.outcome, Outcome.UNCERTAIN)
        self.assertEqual(writer.reconcile(CREATE_ID).outcome, Outcome.UNCERTAIN)
        self.assertEqual(len(self.fake.writes), 1)


class BridgeTests(unittest.TestCase):
    def test_exact_request_response_binding_and_no_retry(self):
        output = io.StringIO()
        bridge = StdioToolBridge(io.StringIO(), output)
        request_data = {"session": bridge.session, "sequence": 1,
                        "tool": PREFIX + "get_file_metadata", "arguments": {"fileId": "sandbox"}}
        reply = {"session": bridge.session, "sequence": 1, "binding": digest(request_data),
                 "result": result({"id": "sandbox"})}
        bridge.reader = io.StringIO(json.dumps(reply) + "\n")
        self.assertEqual(bridge(request_data["tool"], request_data["arguments"]), reply["result"])
        self.assertEqual(json.loads(output.getvalue()), {**request_data, "binding": digest(request_data)})
        with self.assertRaises(ProtocolError):
            bridge(PREFIX + "create_file", {})

    def test_independent_review_old_bridge_reply_rejected_after_restart(self):
        prior = StdioToolBridge(io.StringIO(), io.StringIO())
        data = {"session": prior.session, "sequence": 1,
                "tool": PREFIX + "get_file_metadata", "arguments": {"fileId": "sandbox"}}
        stale = {"session": prior.session, "sequence": 1, "binding": digest(data),
                 "result": result({"id": "sandbox", "shared": False})}
        restarted = StdioToolBridge(io.StringIO(json.dumps(stale) + "\n"), io.StringIO())
        self.assertNotEqual(prior.session, restarted.session)
        with self.assertRaises(ProtocolError):
            restarted(data["tool"], data["arguments"])

    def test_eof_or_wrong_response_never_retries(self):
        for line in ("", "{}\n"):
            output = io.StringIO()
            with self.assertRaises(ProtocolError):
                StdioToolBridge(io.StringIO(line), output)(PREFIX + "get_file_metadata", {})
            self.assertEqual(len(output.getvalue().splitlines()), 1)


class SandboxTests(unittest.TestCase):
    def test_fixture_has_exact_headers_seven_statuses_and_no_job_seed(self):
        requests = fixture_requests(123)
        values = [r["updateCells"] for r in requests if "updateCells" in r]
        self.assertEqual(len(values), 2)  # headers and R sentinels only
        self.assertEqual(values[0]["range"]["endRowIndex"], 1)
        self.assertEqual(tuple(c["userEnteredValue"]["stringValue"] for c in values[0]["rows"][0]["values"]), AGENT_JOB_COLUMNS)
        self.assertEqual(values[1]["range"]["startColumnIndex"], 17)
        rules = [r["setDataValidation"]["rule"] for r in requests if "setDataValidation" in r]
        self.assertEqual([v["userEnteredValue"] for v in rules[0]["condition"]["values"]], [s.value for s in Status])

    def test_plan_has_exact_ids_lineage_sources_values_and_only_one_revision_advance(self):
        fixture = plan("2026-10-04T12:00:00+00:00")
        for req in (fixture.create, fixture.update):
            SheetsWriter._validate(req)
            self.assertEqual(req.source_keys, (SOURCE,))
            self.assertEqual(req.intended_lineage, Lineage("AJ-0010", 1, 1, 1))
            self.assertIn("Nonce=VA-LIVE-SHEETS-0010-01", req.cells[16])
        self.assertEqual(fixture.create.operation_id, CREATE_ID)
        self.assertEqual(fixture.update.operation_id, UPDATE_ID)
        self.assertIsNone(fixture.create.expected_revision)
        self.assertEqual(fixture.update.expected_revision, 1)
        self.assertIn("RecordRevision=2", fixture.update.cells[16])

    def test_driver_stops_at_uncertain_then_same_journal_readonly_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            target = SandboxTarget("fixture", 123, "Agent Jobs Sandbox", "fixture@example.invalid", "root-fixture", (SOURCE,))
            fake = FakeConnector(target)
            fake.mode = "apply-timeout"
            adapter = GoogleSheetsAdapter(target, fake, ReceiptJournal(str(Path(directory) / "receipts.sqlite"), target))
            path = str(Path(directory) / "writer.sqlite")
            writer = SheetsWriter(WriterJournal(path, target.scope), adapter, MockAuthority())
            fixture = plan("2026-10-04T12:00:00+00:00")
            token = writer.claim("Dẹkun", fixture.create.authority_ref)
            outcomes = execute_once(writer, token, fixture)
            self.assertEqual(outcomes["create"].outcome, Outcome.UNCERTAIN)
            self.assertIsNone(outcomes["update"])
            with self.assertRaises(ProtocolError):
                execute_once(writer, token, fixture)
            restarted = SheetsWriter(WriterJournal(path, target.scope), adapter, MockAuthority())
            self.assertEqual(reconcile_existing(restarted)[CREATE_ID].outcome, Outcome.UNCERTAIN)
            self.assertEqual(len(fake.writes), 1)
