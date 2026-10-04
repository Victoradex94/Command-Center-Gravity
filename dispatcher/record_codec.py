"""Closed JSON codec for LOCAL dispatcher sidecar state; never pickle/import code.

This does not claim to reconstruct the complete aggregate from live J/M/Q cells.
Only the journal that wrote a row can supply its matching aggregate in v1.
"""

from dataclasses import fields, is_dataclass
from enum import Enum
import json

from .model import (AgentJob, Brief, Check, DeliveryState, EventKind, Lineage,
                    ReturnClass, ReturnEnvelope, Status, Verification, require)
from .store import Attempt, Delivery, Event, Record


_TYPES = {cls.__name__: cls for cls in (AgentJob, Brief, Check, Lineage, ReturnEnvelope,
                                     Verification, Attempt, Delivery, Event, Record)}
_ENUMS = {cls.__name__: cls for cls in (DeliveryState, EventKind, ReturnClass, Status)}


def _encode(value):
    if isinstance(value, Enum):
        return {"enum": type(value).__name__, "value": value.value}
    if is_dataclass(value):
        require(type(value).__name__ in _TYPES, "unsupported aggregate type")
        return {"type": type(value).__name__, "fields": {f.name: _encode(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, (tuple, set)):
        values = sorted(value) if isinstance(value, set) else value
        return {"collection": type(value).__name__, "values": [_encode(v) for v in values]}
    if isinstance(value, list):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {"mapping": [[k, _encode(v)] for k, v in sorted(value.items())]}
    require(value is None or type(value) in (str, int, bool, float), "unsupported aggregate value")
    return value


def _decode(value):
    if isinstance(value, list):
        return [_decode(v) for v in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {"enum", "value"}:
        require(value["enum"] in _ENUMS, "unknown enum")
        return _ENUMS[value["enum"]](value["value"])
    if set(value) == {"type", "fields"}:
        require(value["type"] in _TYPES, "unknown aggregate type")
        cls = _TYPES[value["type"]]
        require(set(value["fields"]) == {f.name for f in fields(cls)}, "incomplete aggregate fields")
        return cls(**{k: _decode(v) for k, v in value["fields"].items()})
    if set(value) == {"mapping"}:
        return {k: _decode(v) for k, v in value["mapping"]}
    require(set(value) == {"collection", "values"} and value["collection"] in ("set", "tuple"), "unknown codec tag")
    return (set if value["collection"] == "set" else tuple)(_decode(v) for v in value["values"])


def encode_record(record: Record) -> str:
    return json.dumps({"version": 1, "record": _encode(record)}, sort_keys=True, ensure_ascii=False, allow_nan=False)


def decode_record(raw: str) -> Record:
    data = json.loads(raw)
    require(set(data) == {"version", "record"} and data["version"] == 1, "unsupported codec version")
    record = _decode(data["record"])
    require(isinstance(record, Record), "record aggregate required")
    require(record.row.job_id == record.lineage.job_id, "aggregate lineage mismatch")
    record.row.to_cells()
    return record
