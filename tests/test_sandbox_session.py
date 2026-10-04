"""Offline exercise of the exact serial live driver with a SIMULATED connector."""

from contextlib import redirect_stdout
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dispatcher.google_sheets import SandboxTarget
from dispatcher.model import ProtocolError
from dispatcher.sheets_sandbox import AUTHORITY, CREATE_ID, SOURCE, UPDATE_ID
from tests.test_google_sheets import FakeConnector
from tools.aj0010_sandbox_session import SessionAuthority, load_plan, main


FIXTURE = Path(__file__).resolve().parents[1] / "docs/AJ-0010-fixture-plan.json"


class SandboxSessionTests(unittest.TestCase):
    def run_session(self, mode, directory, fake, config):
        args = ["session", mode, str(config), str(FIXTURE), str(directory)]
        with patch("sys.argv", args), patch("tools.aj0010_sandbox_session.StdioToolBridge") as constructor:
            bridge = constructor.return_value
            bridge.session = "SIMULATED-SESSION"
            bridge.side_effect = fake
            with redirect_stdout(io.StringIO()):
                main()

    def fixture(self, directory):
        target = SandboxTarget("SIMULATED-sandbox", 123, "Agent Jobs Sandbox", "fixture@example.invalid",
                               "root-fixture", (SOURCE,))
        config = directory / "config.json"
        config.write_text(json.dumps(asdict(target)))
        return FakeConnector(target), config

    def test_complete_serial_driver_and_readonly_process_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            fake, config = self.fixture(directory)
            self.run_session("execute", directory, fake, config)
            actual = json.loads((directory / "execute-result.json").read_text())
            self.assertEqual(actual["submissions"], 2)
            self.assertEqual(actual["outcomes"]["create"]["outcome"], "SUCCESS")
            self.assertEqual(actual["outcomes"]["update"]["outcome"], "SUCCESS")
            with self.assertRaises(ProtocolError):
                self.run_session("execute", directory, fake, config)
            self.run_session("reconcile", directory, fake, config)
            restart = json.loads((directory / "reconcile-result.json").read_text())
            self.assertEqual(restart["submissions"], 2)
            self.assertEqual(restart["recovery_used"], 0)
            self.assertEqual(set(restart["outcomes"]), {CREATE_ID, UPDATE_ID})
            self.assertTrue(all(r["outcome"] == "SUCCESS" for r in restart["outcomes"].values()))
            self.assertEqual(tuple(restart["current_snapshot"]["rows"][0]["cells"]), load_plan(FIXTURE).update.cells)
            self.assertEqual(len(fake.writes), 2)

    def test_driver_retains_uncertain_create_and_skips_update(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            fake, config = self.fixture(directory)
            fake.mode = "apply-timeout"
            self.run_session("execute", directory, fake, config)
            result = json.loads((directory / "execute-result.json").read_text())
            self.assertEqual(result["outcomes"]["create"]["outcome"], "UNCERTAIN")
            self.assertIsNone(result["outcomes"]["update"])
            self.run_session("reconcile", directory, fake, config)
            self.assertEqual(len(fake.writes), 1)

    def test_authority_is_exact_scope_reference_root_and_disabled_on_reconcile(self):
        authority = SessionAuthority("SCOPE", True)
        self.assertEqual(authority.inspect(AUTHORITY, "SCOPE", "Dẹkun").state, "valid")
        for ref, scope, actor in (("unknown", "SCOPE", "Dẹkun"), (AUTHORITY, "OTHER", "Dẹkun"),
                                  (AUTHORITY, "SCOPE", "worker")):
            self.assertEqual(authority.inspect(ref, scope, actor).state, "unknown")
        self.assertEqual(SessionAuthority("SCOPE", False).inspect(AUTHORITY, "SCOPE", "Dẹkun").state, "unknown")
        with self.assertRaises(RuntimeError): authority.inspect_renewal(AUTHORITY, "SCOPE", "Dẹkun")
        with self.assertRaises(RuntimeError): authority.inspect_lineage_change(AUTHORITY, "SCOPE", "Dẹkun")

    def test_fixture_hash_rejects_changed_values(self):
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp) / "fixture.json"
            altered.write_bytes(FIXTURE.read_bytes().replace(b"Synthetic ledger", b"Changed ledger"))
            with self.assertRaises(ProtocolError): load_plan(altered)
