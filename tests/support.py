from dataclasses import replace

from dispatcher.adapters import FakeExecutor, FakeMessenger, RunObservation
from dispatcher.engine import Authorization, Dispatcher
from dispatcher.model import (Brief, Check, Gate, Gates, Lineage, ReturnClass, ReturnEnvelope,
                              RouteCandidate, SourceCommand, Verification)
from dispatcher.store import InMemoryRepository


NOW = "2026-10-04T06:00:00+00:00"
REQUIRED = frozenset({"python"})


def source(message="100.1", **kwargs):
    return replace(SourceCommand("T0C63317YDV", "U0C6LCCH9QR", "command", message,
                                  "100.1", "1", f"synthetic://command/{message}", True), **kwargs)


def brief(**kwargs):
    return replace(Brief("Build bounded core", "repository", "pure Python core",
                         ("engine", "tests"), "No live integrations or ledger writes",
                         "Synthetic owner instruction", "protocol supplied", "activity",
                         "2026-10-04T07:00:00+00:00; review control, not deadline",
                         "inspect original run before retry", "inspect code and tests",
                         "fake native result", parent_evidence_or_reason="AI-only bounded preparation",
                         explicit_worker="Codex"), **kwargs)


def gates(**kwargs):
    check = Gate(True, "synthetic verified evidence")
    return replace(Gates(check, check, check, check, check, check, check, NOW), **kwargs)


def routes(**kwargs):
    return (replace(RouteCandidate("Codex", "fake-codex", REQUIRED, True, True, True, True,
                                    Gate(True, "synthetic access"), Gate(True, "synthetic readiness"),
                                    NOW, "synthetic route probe"), **kwargs),)


def authorization(action, job_id="AJ-0007"):
    return Authorization(action, job_id, source("200.1"), f"Explicit synthetic {action} instruction")


class Harness:
    def __init__(self, job_id="AJ-0007", custom_brief=None):
        self.now = NOW
        self.repo = InMemoryRepository()
        self.engine = Dispatcher(self.repo, clock=lambda: self.now)
        self.executor = FakeExecutor()
        self.messenger = FakeMessenger()
        self.job_id = job_id
        self.engine.intake(job_id, "VA-DISPATCHER-0007-01", source(), custom_brief or brief())

    @property
    def record(self):
        return self.repo.read(self.job_id)

    @property
    def lineage(self):
        return self.record.lineage

    def ready(self):
        return self.engine.ready(self.lineage, gates(), routes(), REQUIRED)

    def dispatch(self):
        return self.engine.dispatch(self.lineage, gates(), routes(), REQUIRED, self.executor)

    def start(self):
        return self.engine.start(self.lineage, self.observation())

    def observation(self, **kwargs):
        return replace(RunObservation(self.record.current_attempt.worker_run, "running", NOW,
                                      "synthetic observed first code inspection", True, True), **kwargs)

    def working(self):
        self.ready()
        self.dispatch()
        return self.start()

    def envelope(self, **kwargs):
        attempt = self.record.current_attempt
        envelope = ReturnEnvelope(self.lineage, self.record.nonce, attempt.worker,
                                      attempt.worker_run, "result-1", NOW, "implemented core",
                                      "synthetic://artifact/core-v1", "synthetic inspected artifact",
                                      "Not applicable", "Not applicable", "Not applicable",
                                      "Recommendation only; not assigned", ReturnClass.FULL, True,
                                      self.record.brief.criteria, (), "Dẹkun", "Not applicable",
                                      "Completed", self.record.next_check)
        if kwargs.get("claimed_class") == ReturnClass.BLOCKED:
            envelope = replace(envelope, criteria_met=(), criteria_unmet=self.record.brief.criteria,
                               failed_gate="synthetic failed gate", execution_state="Unknown")
        elif kwargs.get("claimed_class") == ReturnClass.PARTIAL:
            envelope = replace(envelope, criteria_met=self.record.brief.criteria[:1],
                               criteria_unmet=self.record.brief.criteria[1:])
        return replace(envelope, **kwargs)

    def verification(self, **kwargs):
        def checked(evidence):
            return Check(True, "synthetic coordinator inspection", evidence)
        return replace(Verification(self.lineage, "Dẹkun", NOW,
                                    {c: checked(f"synthetic checked {c}") for c in self.record.brief.criteria},
                                    checked("synthetic artifact inspection"), checked("synthetic destination readback"),
                                    checked("synthetic unittest evidence"), checked("synthetic no prohibited changes"),
                                    checked("synthetic no unresolved prerequisites"), checked("synthetic no side effects"),
                                    checked("No parent update: bounded AI-only preparation"),
                                    checked("synthetic authenticated source and current run inspected"),
                                    "Synthetic only; no live integrations", True), **kwargs)

    def review(self):
        self.working()
        return self.engine.receive(self.envelope())

    def done(self):
        self.review()
        return self.engine.complete(self.lineage, self.verification())
