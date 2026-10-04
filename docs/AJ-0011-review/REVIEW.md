# AJ-0011 independent review

Reviewer: independent_review child agent; implementation not edited by reviewer.
Scope: dispatcher/slack.py against accepted Dispatcher state machine and AJ-0011 user constraints. All probes use tests.offline_suite.reject_external; no external calls, credentials, ledger writes, commit or push.

## Findings

- R1 (high): escalation notifications omit actual decision, recommendation, consequence and deadline. SlackBoundary.sync initially serialized only Event.evidence/data, whereas Dispatcher.escalate stores the decision snapshot in record.deliveries[event.key].text. Reproduced by test_escalation_has_actual_decision. A top-level message without the decision does not satisfy useful surfacing.
- R2 (high): applied cancel/pause cannot reconcile a crash before local applied marker. reconcile_command initially searched Event.evidence for the command fingerprint, but Dispatcher.cancel/pause do not place the authorization fingerprint there. Reproduced independently by test_cancel_crash_reconciliation and test_pause_crash_reconciliation. State stayed reserved after the core mutation succeeded; no replay occurred (safe but recovery incomplete). Already-Blocked pause must also carry an immutable fingerprint, because that path emits only reconciliation.

## Initial evidence

Command: PYTHONPATH=. python docs/AJ-0011-review/probes.py

initial.stderr: initial three reproductions, one failure and two errors.
expanded-initial.stderr: six probes, the same three reproductions plus passing unknown-inspection/no-send, mismatched destination rejection, and crash-after-send/original-destination readback without replay.

Pending implementation correction and re-review. The probes are standalone review evidence outside ordinary unittest discovery; they assert correct behavior and should pass after fixes.

## Re-review and additional restart probe

R1 and R2 are corrected in the implementation and all six original probes pass. The additional already-Blocked pause crash probe also passes, verifying the path with no transition event.

R3 (medium): a corrective send that crashes before its local result marker, followed by authoritative absent readback, leaves the journal in `sending` with recovery exhausted but circuit false. It does not replay, but fails the explicit recurrence/circuit requirement. `correction-crash.stderr` retains the eight-probe run with this sole failure. The new probe requires circuit opening only after confirmed absence, not on uncertain readback.

## Final disposition

All three findings are corrected and independently rechecked:

- R1: sync includes the canonical immutable escalation delivery payload. Decision, recommendation, consequence and deadline are retained in attention notifications.
- R2: cancel and pause store a packed command fingerprint and supplied evidence in canonical events. Reconciliation locates successful mutations after the local marker crash, including already-Blocked pause.
- R3: the journal retains attempted_correction before send. Authoritative absence after a crashed corrective send opens the circuit, without replay; unknown lookup remains unresolved.

Final command `PYTHONPATH=. python docs/AJ-0011-review/probes.py`: 8 tests, all passing; final-probes.stdout/stderr retained.

Final command `python -m tests.offline_suite`: 215 tests, 0 failures, 0 errors; final-full-offline.stdout/stderr retained. An intermediate integration test exposed the accepted exclusive-writer restart gate; the implementation author corrected the fixture to explicitly reclaim the mock writer epoch. The accepted writer was not relaxed. The intermediate full-offline logs remain retained.

Reviewed implementation SHA-256: `401146db3859a56a87cb0b53054baad4d6111d77258523df437060c4f8f23eff` (dispatcher/slack.py).
Reviewed suite SHA-256: `7b5dc5d7506aa6376ac7004e7269210baa9decb54c8f5698e62de3469707bef5` (tests/test_slack.py).
Reviewed adapter documentation SHA-256: `9a308c1fe830e357d2eb1d6fd5da05a8b2ca1264aeab6a912610dcc34a7cd9f2` (docs/AJ-0011-slack-adapter.md).

No outstanding in-scope finding. Appropriate for root acceptance of the bounded local/mock milestone. This is not live Slack certification: trusted grant and provider ports, complete authoritative negative lookup, single coordinator ownership, exact provenance and safe rendering remain future integration gates as documented. No commit or push was performed by the reviewer.
