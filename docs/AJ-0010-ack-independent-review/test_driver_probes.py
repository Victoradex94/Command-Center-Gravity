"""Bounded session driver probes using an in-memory simulated connector."""
import sys
sys.path.insert(0,"/workspace/Command-Center-Gravity")
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
import io,json,tempfile,unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from tools import aj0010_sandbox_session as driver
from tests.test_google_sheets import FakeConnector
from dispatcher.google_sheets import SandboxTarget,PRODUCTION_ID
from dispatcher.sheets_sandbox import SOURCE
from dispatcher.model import ProtocolError

class DriverProbes(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.target=SandboxTarget("synthetic-only",123,"Agent Jobs Sandbox","fixture@example.invalid","root-fixture",(SOURCE,))
        self.fake=FakeConnector(self.target)
        self.config=self.directory/"config.json"
        self.config.write_text(json.dumps(asdict(self.target)))
        self.fixture=Path("/workspace/Command-Center-Gravity/docs/AJ-0010-fixture-plan.json")
    def run_mode(self,mode,fixture=None):
        output=io.StringIO();fake=self.fake
        class Reader:
            def readline(self):
                request=json.loads(output.getvalue().splitlines()[-1])
                result=fake(request["tool"],request["arguments"])
                return json.dumps({"session":request["session"],"sequence":request["sequence"],"binding":request["binding"],"result":result})+"\n"
        argv=["tools.aj0010_sandbox_session",mode,str(self.config),str(fixture or self.fixture),str(self.directory)]
        with patch.object(sys,"argv",argv),patch.object(sys,"stdin",Reader()),patch.object(sys,"stdout",output):
            driver.main()
        return [json.loads(line) for line in output.getvalue().splitlines()]
    def test_execute_then_restart_reconcile_exact_fixture_two_total_writes(self):
        output=self.run_mode("execute")
        self.assertEqual(output[-1]["kind"],"session_complete")
        self.assertEqual(len(self.fake.writes),2)
        result=json.loads((self.directory/"execute-result.json").read_text())
        self.assertEqual(result["submissions"],2)
        self.assertEqual(result["recovery_used"],0)
        self.assertEqual(result["outcomes"]["create"]["outcome"],"SUCCESS")
        self.assertEqual(result["outcomes"]["update"]["outcome"],"SUCCESS")
        before=len(self.fake.calls)
        self.run_mode("reconcile")
        self.assertFalse(any(name.endswith("batch_update_spreadsheet") for name,args in self.fake.calls[before:]))
        self.assertEqual(len(self.fake.writes),2)
        stored=json.loads(self.fixture.read_text())
        reconciled=json.loads((self.directory/"reconcile-result.json").read_text())
        self.assertEqual(reconciled["current_snapshot"]["rows"][0]["cells"],stored["update"]["cells"])
    def test_ambiguous_create_blocks_update_and_reconcile_never_replays(self):
        self.fake.mode="apply-timeout"
        # Reader raises through bridge after simulated application; durable receipt records timeout.
        self.run_mode("execute")
        result=json.loads((self.directory/"execute-result.json").read_text())
        self.assertEqual(result["outcomes"]["create"]["outcome"],"UNCERTAIN")
        self.assertIsNone(result["outcomes"]["update"])
        self.fake.mode="apply"
        self.run_mode("reconcile")
        self.assertEqual(len(self.fake.writes),1)
    def test_execute_existing_journals_cannot_submit_again(self):
        self.run_mode("execute")
        before=len(self.fake.calls)
        original=(self.directory/"execute-result.json").read_bytes()
        with self.assertRaises(ProtocolError):self.run_mode("execute")
        self.assertEqual(len(self.fake.calls),before)
        self.assertEqual((self.directory/"execute-result.json").read_bytes(),original)
    def test_tampered_fixture_and_production_config_fail_before_any_tool_call(self):
        changed=self.directory/"changed-fixture.json"
        changed.write_bytes(self.fixture.read_bytes()+b" ")
        with self.assertRaises(ProtocolError):self.run_mode("execute",changed)
        config=asdict(self.target);config["spreadsheet_id"]=PRODUCTION_ID
        self.config.write_text(json.dumps(config))
        with self.assertRaises(ProtocolError):self.run_mode("execute")
        self.assertEqual(self.fake.calls,[])

if __name__=="__main__": unittest.main(defaultTest="DriverProbes",verbosity=2)
