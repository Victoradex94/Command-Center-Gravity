"""JobRepository bridge: accepted dispatcher core using the exclusive writer.

Coordinator mutations still go through Dispatcher guards. Recovery is an explicit
SheetsWriter action, never an automatic engine retry. Full aggregate persistence
is a local journal sidecar, not a new Agent Jobs field or tab.
"""

from copy import deepcopy
import hashlib
import re
from typing import Callable

from .model import Conflict, Lineage, ReconciliationRequired, packed, require
from .record_codec import decode_record, encode_record
from .sheets_writer import Outcome, SheetsWriter, WriteRequest, WriterToken
from .store import Record


class SheetsRepository:
    def __init__(self, writer: SheetsWriter, token: WriterToken, *, authority_ref: str,
                 context_ref: str, condition: str, route: str,
                 lineage_change_reference: Callable[[Lineage, Lineage], str] | None = None):
        self.writer, self.token = writer, token
        self.authority_ref, self.context_ref = authority_ref, context_ref
        self.condition, self.route = condition, route
        self.lineage_change_reference = lineage_change_reference

    def assert_writer(self, writer: str) -> None:
        require(writer == self.token.actor, "coordinator exclusive writer required")
        self.writer.assert_owner(self.token)

    def read(self, job_id: str) -> Record:
        row = self.writer.read(job_id)
        if row is None:
            raise KeyError(job_id)
        state = self.writer.state()
        for op in reversed(tuple(state["operations"].values())):
            if not op["submissions"]:
                continue
            request = op["request"]
            if request["job_id"] == job_id and tuple(request["cells"]) == row.cells and request["aggregate"]:
                if op["outcome"] != Outcome.SUCCESS:
                    raise ReconciliationRequired("reconcile original write before adopting aggregate")
                if tuple(request["source_keys"]) != row.source_keys:
                    raise ReconciliationRequired("current source identity differs from verified aggregate")
                record = decode_record(request["aggregate"])
                require(tuple(record.row.to_cells()) == row.cells and record.version == row.revision,
                        "aggregate/current row mismatch")
                return record
        raise ReconciliationRequired("no verified local aggregate for current row; import codec is not implemented")

    def all(self) -> tuple[Record, ...]:
        snapshot = self.writer.snapshot()
        return tuple(self.read(row.cells[0]) for row in snapshot.rows)

    def commit(self, record: Record, expected_version: int | None,
               expected_lineage: Lineage, writer: str) -> Record:
        self.assert_writer(writer)
        require(record.row.job_id == record.lineage.job_id, "aggregate Job ID/lineage mismatch")
        if expected_version is not None:
            current = self.read(record.row.job_id)
            if current.version != expected_version or current.lineage != expected_lineage:
                raise Conflict("current RecordRevision/lineage conflict")
        else:
            require(record.lineage == expected_lineage, "create lineage mismatch")
        intended = deepcopy(record)
        intended.version = (expected_version or 0) + 1
        revision = re.sub(r"(?:^|;\s*)RecordRevision=\d+(?=;|$)", "", intended.row.run_revision_id).strip("; ")
        intended.row.run_revision_id = revision + f"; RecordRevision={intended.version}"
        cells = tuple(intended.row.to_cells())
        sources = tuple(sorted({s["key"] for s in intended.sources}))
        aggregate = encode_record(intended)
        change_ref = ""
        if expected_version is not None and intended.lineage != expected_lineage:
            require(self.lineage_change_reference is not None,
                    "configure explicit lifecycle-decision reference for lineage change")
            change_ref = self.lineage_change_reference(expected_lineage, intended.lineage)
        digest = hashlib.sha256(packed([cells, sources, aggregate, self.authority_ref,
                                       self.context_ref, self.condition, self.route, change_ref]).encode()).hexdigest()
        operation = f"dispatcher/{record.row.job_id}/{intended.version}/{digest}"
        request = WriteRequest(operation, record.row.job_id, expected_version, cells, sources,
                               self.authority_ref, self.context_ref, self.condition, self.route, aggregate,
                               expected_lineage if expected_version is not None else None,
                               intended.lineage, change_ref)
        result = self.writer.write(request, self.token)
        if result.outcome == Outcome.UNCERTAIN:
            raise ReconciliationRequired(f"reconcile operation {operation}")
        if result.outcome == Outcome.FAILED:
            raise Conflict(result.reason)
        return self.read(record.row.job_id)

    def reconcile(self, job_id: str, writer: str) -> Record:
        require(writer == self.token.actor, "coordinator reconciliation identity required")
        operations = [op for op in self.writer.state()["operations"].values()
                      if op["request"]["job_id"] == job_id and op["outcome"] != Outcome.SUCCESS and op["submissions"]]
        for op in operations:
            result = self.writer.reconcile(op["request"]["operation_id"])
            if result.outcome != Outcome.SUCCESS:
                raise ReconciliationRequired(result.reason)
        return self.read(job_id)
