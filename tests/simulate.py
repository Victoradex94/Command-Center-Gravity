"""Run all deterministic scenario families and emit stable JSON (no elapsed times)."""

import json
import unittest

from tests import test_protocol, test_review_regressions


SCENARIOS = (
    ("01", "Intake, authentic acknowledgement, FYI and duplicates", test_protocol.Family01IntakeAndDuplicates),
    ("02", "Capability routing and Victor's explicit worker override", test_protocol.Family02RoutingAndOverride),
    ("03", "Gates, fast path, exclusive writer and uncertain writes", test_protocol.Family03GatesAndSingleWriter),
    ("04", "Substantive start, stale execution and transition rejection", test_protocol.Family04ActualStartAndStaleRuns),
    ("05", "Full return, attribution and verification before Done", test_protocol.Family05FullReturnAndVerification),
    ("06", "Partial/Blocked returns and authorized corrective attempts", test_protocol.Family06PartialBlockedAndCorrection),
    ("07", "Cancellation, pause, reassignment, revisions and late returns", test_protocol.Family07CancellationPauseAndSupersession),
    ("08", "Missing, failed and uncertain acknowledgement/return delivery", test_protocol.Family08DeliveryRecovery),
    ("09", "Attention escalation, parent reconciliation and permission limits", test_protocol.Family09EscalationParentAndPermissions),
    ("AJ-0006", "Wrong path then explicitly approved corrected attempt (fixture only)",
     test_protocol.AJ0006WrongPathAndApprovedCorrection),
    ("review", "Independent review regression cases", test_review_regressions.IndependentReviewRegressions),
)


def main() -> int:
    scenarios = []
    for identifier, description, case in SCENARIOS:
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(case).run(result)
        scenarios.append({"id": identifier, "scenario": description, "expected": "PASS",
                          "observed": "PASS" if result.wasSuccessful() else "FAIL",
                          "tests": result.testsRun,
                          "failures": [str(test) for test, _ in result.failures],
                          "errors": [str(test) for test, _ in result.errors]})
    print(json.dumps({"synthetic": True, "live_integration_proof": False,
                      "scenarios": scenarios, "tests": sum(s["tests"] for s in scenarios)}, indent=2))
    return int(any(s["observed"] != "PASS" for s in scenarios))


if __name__ == "__main__":
    raise SystemExit(main())
