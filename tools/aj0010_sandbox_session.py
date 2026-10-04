"""Bounded agent-mediated AJ-0010 session; never creates/shares a workbook.

Invoked only by the authorised supervising agent after private fixture setup.
The exact current root instruction is a trusted session attestation, not OAuth
or a general permission service. Unknown references, renewals and lifecycle
changes are refused. No SDK, credential, subprocess or automatic recovery.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

from dispatcher.google_sheets import GoogleSheetsAdapter, ReceiptJournal, SandboxTarget
from dispatcher.model import Lineage, require
from dispatcher.sheets_sandbox import (AUTHORITY, SOURCE, SandboxPlan, execute_once,
                                       reconcile_existing)
from dispatcher.sheets_tool_bridge import StdioToolBridge
from dispatcher.sheets_writer import Authority, SheetsWriter, WriteRequest
from dispatcher.writer_journal import WriterJournal


FIXTURE_HASH = "c448dd13a66e038f1bc9bd554dba124002a05b5ff80780cc6a1a0c4edf746e48"
SESSION_EVIDENCE = (
    "AJ-0010 root continuation accepted positive-ack correction; Victor approval "
    "1791113671.468969; root confirmed this executor sole sandbox owner and existing "
    "agent-mediated MCP route. Exact saved fixture only, one create and one update; "
    "no production ledger, permissions, credentials, new route, recovery or successor."
)


def save_new(path, value):
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


class SessionAuthority:
    def __init__(self, scope, mutation_enabled):
        self.scope, self.mutation_enabled = scope, mutation_enabled

    def inspect(self, reference, scope, actor):
        valid = (self.mutation_enabled and reference == AUTHORITY
                 and scope == self.scope and actor == "Dẹkun")
        return Authority(reference, scope, actor, "valid" if valid else "unknown",
                         bool(valid), SESSION_EVIDENCE if valid else "No current session grant")

    def inspect_renewal(self, reference, scope, actor):
        raise RuntimeError("No authority renewal authorised in this sandbox session")

    def inspect_lineage_change(self, reference, scope, actor):
        raise RuntimeError("No execution-lineage change authorised in this sandbox session")


def load_plan(path):
    data = Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest() == FIXTURE_HASH, "saved fixture changed")
    fixture = json.loads(data)
    def request(name):
        values = fixture[name]
        values["cells"], values["source_keys"] = tuple(values["cells"]), tuple(values["source_keys"])
        for field in ("expected_lineage", "intended_lineage"):
            if values[field] is not None: values[field] = Lineage(**values[field])
        return WriteRequest(**values)
    return SandboxPlan(request("create"), request("update"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("execute", "reconcile"))
    parser.add_argument("config")
    parser.add_argument("fixture")
    parser.add_argument("evidence_dir")
    args = parser.parse_args()
    directory = Path(args.evidence_dir)
    require(directory.is_dir(), "pre-existing coordinated evidence directory required")
    target_data = json.loads(Path(args.config).read_text())
    target_data["source_keys"] = tuple(target_data["source_keys"])
    target = SandboxTarget(**target_data)
    require(target.source_keys == (SOURCE,), "exact AJ-0010 synthetic source required")
    fixture = load_plan(args.fixture)
    writer_path, receipt_path = directory / "writer.sqlite", directory / "receipts.sqlite"
    if args.mode == "execute":
        require(not writer_path.exists() and not receipt_path.exists(),
                "existing session must be reconciled; never create replacement journals")
    else:
        require(writer_path.exists() and receipt_path.exists(), "both original journals required")
    bridge = StdioToolBridge(sys.stdin, sys.stdout)
    sequence = 0
    def call(tool, arguments):
        nonlocal sequence
        sequence += 1
        stem = directory / f"{args.mode}-tool-{sequence:03d}"
        save_new(str(stem) + "-request.json", {"tool": tool, "arguments": arguments,
                                              "bridge_session": bridge.session, "sequence": sequence})
        response = bridge(tool, arguments)
        save_new(str(stem) + "-response.json", response)
        return response
    adapter = GoogleSheetsAdapter(target, call, ReceiptJournal(str(receipt_path), target))
    writer = SheetsWriter(WriterJournal(str(writer_path), target.scope), adapter,
                          SessionAuthority(target.scope, args.mode == "execute"))
    before = adapter.capture()
    save_new(directory / (args.mode + "-before.json"), before)
    if args.mode == "execute":
        token = writer.claim("AJ-0010 executor sole sandbox proxy", AUTHORITY)
        outcomes = execute_once(writer, token, fixture)
        outcomes = {key: asdict(value) if hasattr(value, "__dataclass_fields__") else value
                    for key, value in outcomes.items()}
    else:
        outcomes = {key: asdict(value) for key, value in reconcile_existing(writer).items()}
    after = adapter.capture()
    save_new(directory / (args.mode + "-after.json"), after)
    state = writer.state()
    result = {"mode": args.mode, "scope": target.scope, "outcomes": outcomes,
              "current_snapshot": asdict(adapter._snapshot(after)),
              "submissions": sum(len(op["submissions"]) for op in state["operations"].values()),
              "recovery_used": sum(op["recovery_used"] for op in state["operations"].values())}
    save_new(directory / (args.mode + "-writer-state.json"), state)
    save_new(directory / (args.mode + "-result.json"), result)
    print(json.dumps({"kind": "session_complete", "mode": args.mode,
                      "submissions": result["submissions"], "outcomes": outcomes}), flush=True)


if __name__ == "__main__":
    main()
