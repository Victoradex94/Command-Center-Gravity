"""Retained F2 probe, adapted only for IR3 required attestation fields/path.

The exact original failing IR2 probe and outputs remain under docs/history.
The scenario and final provider-call assertion are unchanged.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
from dataclasses import replace
import json
import unittest
from unittest.mock import patch
from dispatcher.sheets_writer import AuthorityRenewal, Outcome
from dispatcher.model import ProtocolError
from tests.test_sheets_writer import WriterFixture, request, SCOPE

class RenewalScopeReview(WriterFixture):
    def test_unrelated_renewal_cannot_replace_revoked_original_recovery_authority(self):
        original=request('original-job', 'AJ-0010', source_key='original-source', authority_ref='review://original-A')
        self.mock.plan('tool-noop')
        self.assertEqual(self.writer.write(original,self.token).outcome,Outcome.FAILED)
        unrelated=request('unrelated-job', 'AJ-0020', source_key='unrelated-source', authority_ref='review://unrelated-B')
        self.authority.states[unrelated.authority_ref]='denied'
        self.assertEqual(self.writer.write(unrelated,self.token).outcome,Outcome.FAILED)
        renewal=AuthorityRenewal('review://renewal-B-only',SCOPE,'Dẹkun',unrelated.job_id,unrelated.source_keys,
                                 tuple(self.writer.state()['permission_stops']),True,
                                 'Explicit renewal only for AJ-0020 and unrelated-source',
                                 original_authority_ref=unrelated.authority_ref, intent_digest=unrelated.intent_digest)
        self.authority.renewals[renewal.reference]=renewal
        self.writer.review_renewal(renewal.reference,self.token)
        self.authority.states[original.authority_ref]='revoked'
        checked=[];inspect=self.authority.inspect
        def track(reference,scope,actor):
            checked.append(reference)
            return inspect(reference,scope,actor)
        outcome='blocked'
        with patch.object(self.authority,'inspect',side_effect=track):
            try:
                result=self.writer.recover(original.operation_id,self.change(original,authority_ref=renewal.reference),self.token)
                outcome=str(result.outcome)
            except ProtocolError:
                pass
        evidence={'original_job':original.job_id,'original_authority_state':self.authority.states[original.authority_ref],
                  'renewal_job':renewal.job_id,'renewal_sources':renewal.source_keys,'observed_result':outcome,
                  'checked_authority_references':checked,'provider_calls':len(self.mock.calls),
                  'recovery_effective_authority':self.mock.calls[-1]['authority_ref']}
        print(json.dumps(evidence,indent=2),flush=True)
        self.assertEqual(len(self.mock.calls),1,'A renewal for another job replaced revoked original authority and authorized a second provider call')

if __name__=='__main__':
    unittest.main(verbosity=2)
