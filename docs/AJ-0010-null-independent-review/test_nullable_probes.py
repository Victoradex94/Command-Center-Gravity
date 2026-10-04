"""Independent nullable response mapping probes, simulated transport only."""
import sys
sys.path.insert(0,"/workspace/Command-Center-Gravity")
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
import json,unittest
from pathlib import Path
from tests.test_google_sheets import AdapterTests
from dispatcher.sheets_writer import Effect

class NullableProbes(unittest.TestCase):
    setUp=AdapterTests.setUp
    def response_call(self,change):
        def call(name,args):
            response=self.fake(name,args)
            if name.endswith("batch_update_spreadsheet"):change(response)
            return response
        self.adapter.call=call
    def test_null_positive_ack_still_requires_complete_permissions_and_values(self):
        self.response_call(lambda r:r["structuredContent"].update(updatedSpreadsheet=None))
        self.adapter.submit(self.sub)
        self.assertTrue(self.adapter.inspect(self.sub).settled)
        self.fake.file["shared"]=True
        observation=self.adapter.inspect(self.sub)
        self.assertFalse(observation.settled)
        self.assertEqual(observation.effect,Effect.UNKNOWN)
        self.assertEqual(len(self.fake.writes),1)
    def test_saved_seven_reply_setup_response_is_not_a_row_ack(self):
        saved=json.loads(Path("docs/AJ-0010-live/setup-original-response.json").read_text())
        self.assertIs(saved["structuredContent"]["updatedSpreadsheet"],None)
        self.assertEqual(saved["structuredContent"]["replies"],[{}]*7)
        def change(response):
            # Keep actual seven-reply shape, but bind synthetic target so reply count alone rejects.
            response.clear();response.update(saved)
            response["structuredContent"]=dict(saved["structuredContent"],spreadsheetId=self.target.spreadsheet_id)
        self.response_call(change)
        self.adapter.submit(self.sub)
        self.assertFalse(self.adapter.inspect(self.sub).settled)
        self.assertEqual(len(self.fake.writes),1)
    def test_null_is_not_an_ack_when_outer_error_is_true(self):
        def change(response):
            response["structuredContent"]["updatedSpreadsheet"]=None
            response["isError"]=True
        self.response_call(change)
        self.adapter.submit(self.sub)
        self.assertFalse(self.adapter.inspect(self.sub).settled)
        self.assertEqual(len(self.fake.writes),1)

if __name__=="__main__":unittest.main(defaultTest="NullableProbes",verbosity=2)
