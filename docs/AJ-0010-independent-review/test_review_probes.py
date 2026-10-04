"""Independent offline AJ-0010 probes. No live provider calls."""
import io
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, "/workspace/Command-Center-Gravity")
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
from tests.test_google_sheets import AdapterTests, result
from dispatcher.google_sheets import GoogleSheetsAdapter, ReceiptJournal, PREFIX, digest
from dispatcher.sheets_tool_bridge import StdioToolBridge
from dispatcher.sheets_writer import Effect, Outcome
from dispatcher.model import ProtocolError, ReconciliationRequired

class IndependentProbes(AdapterTests):
    # Inherit setup but deliberately do not inherit the author's test cases below.
    def test_crash_after_provider_apply_before_receipt_finish_is_frozen(self):
        original = self.fake.__call__
        class AbruptDeath(BaseException): pass
        def call(name, arguments):
            response = original(name, arguments)
            if name.endswith("batch_update_spreadsheet"):
                raise AbruptDeath()
            return response
        self.adapter.call = call
        with self.assertRaises(AbruptDeath):
            self.adapter.submit(self.sub)
        self.assertEqual(len(self.fake.writes), 1)
        self.assertEqual(self.adapter.receipts.get(self.sub)["response"], None)
        restarted = GoogleSheetsAdapter(self.target, self.fake, ReceiptJournal(self.path, self.target))
        self.assertEqual(restarted.inspect(self.sub).effect, Effect.UNKNOWN)
        self.assertFalse(restarted.inspect(self.sub).settled)
        with self.assertRaises(ProtocolError):
            restarted.submit(self.sub)
        self.assertEqual(len(self.fake.writes), 1)

    def test_stale_receipt_intent_cannot_be_rebound(self):
        self.adapter.submit(self.sub)
        for changed in (replace(self.sub, operation_id="new-operation"),
                        replace(self.sub, authority_ref="different-authority"),
                        replace(self.sub, route="different-route")):
            with self.subTest(changed=changed):
                with self.assertRaises(ProtocolError):
                    self.adapter.inspect(changed)
        self.assertEqual(len(self.fake.writes), 1)

    def test_mismatched_batch_response_applied_cells_remain_unknown(self):
        original = self.fake.__call__
        def call(name, arguments):
            response = original(name, arguments)
            if name.endswith("batch_update_spreadsheet"):
                response["structuredContent"]["spreadsheetId"] = "other-target"
            return response
        self.adapter.call = call
        self.adapter.submit(self.sub)
        observation = self.adapter.inspect(self.sub)
        self.assertEqual(observation.effect, Effect.UNKNOWN)
        self.assertFalse(observation.settled)
        self.assertEqual(len(self.fake.writes), 1)

    def test_finality_stays_false_after_repeated_observations(self):
        writer = self.writer()
        token = writer.claim("Dẹkun", self.req.authority_ref)
        first = writer.write(self.req, token)
        self.assertEqual(first.outcome, Outcome.UNCERTAIN)
        for _ in range(3):
            current = self.writer().reconcile(self.req.operation_id)
            self.assertEqual(current.outcome, Outcome.UNCERTAIN)
            self.assertEqual(current.fingerprint, first.fingerprint)
            self.assertEqual(current.recovery_used, 0)
        self.assertEqual(len(self.fake.writes), 1)

class IndependentBridgeProbe(unittest.TestCase):
    def test_prior_instance_reply_must_not_bind_to_restart(self):
        arguments = {"fileId": "sandbox"}
        output = io.StringIO()
        previous_reply = []
        class BoundReader:
            def readline(self):
                emitted = json.loads(output.getvalue().splitlines()[-1])
                reply = {"sequence": emitted["sequence"], "binding": emitted["binding"],
                         "result": result({"shared": False})}
                if "session" in emitted:
                    reply["session"] = emitted["session"]
                previous_reply.append(json.dumps(reply) + "\n")
                return previous_reply[-1]
        first = StdioToolBridge(BoundReader(), output)
        first(PREFIX + "get_file_metadata", arguments)
        restarted = StdioToolBridge(io.StringIO(previous_reply[0]), io.StringIO())
        with self.assertRaises(ProtocolError):
            restarted(PREFIX + "get_file_metadata", arguments)

if __name__ == "__main__":
    suite=unittest.TestSuite()
    for cls, names in ((IndependentProbes, [
            "test_crash_after_provider_apply_before_receipt_finish_is_frozen",
            "test_stale_receipt_intent_cannot_be_rebound",
            "test_mismatched_batch_response_applied_cells_remain_unknown",
            "test_finality_stays_false_after_repeated_observations"]),
            (IndependentBridgeProbe, ["test_prior_instance_reply_must_not_bind_to_restart"])):
        for name in names: suite.addTest(cls(name))
    result_=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result_.wasSuccessful())
