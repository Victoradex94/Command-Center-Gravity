"""One-request-at-a-time JSON-lines bridge to an agent's existing MCP tools.

No network, auth discovery, tool invocation, polling, or retries occur here.
The supervising agent must invoke the exact supported tool and return its actual
MCP response. EOF/malformed replies leave mutation settlement unknown. This is
an explicit agent-mediated route, never a direct/unattended executor connection.
"""

import json
import os
from typing import TextIO

from .google_sheets import PREFIX, digest
from .model import require


class StdioToolBridge:
    ALLOWED = frozenset(PREFIX + name for name in (
        "get_file_metadata", "get_spreadsheet_metadata", "get_spreadsheet_cells",
        "batch_update_spreadsheet"))

    def __init__(self, reader: TextIO, writer: TextIO):
        self.reader, self.writer = reader, writer
        self.sequence = 0
        self.session = os.urandom(16).hex()  # freshness only; never a new operation/attempt

    def __call__(self, tool: str, arguments: dict) -> dict:
        require(tool in self.ALLOWED, "unsupported bridge tool")
        self.sequence += 1
        request = {"session": self.session, "sequence": self.sequence, "tool": tool, "arguments": arguments}
        request["binding"] = digest(request)
        self.writer.write(json.dumps(request, ensure_ascii=False) + "\n")
        self.writer.flush()
        line = self.reader.readline()
        require(bool(line), "bridge disconnected; reconcile original operation")
        reply = json.loads(line)
        require(reply.get("session") == self.session and reply.get("sequence") == self.sequence
                and reply.get("binding") == request["binding"]
                and isinstance(reply.get("result"), dict), "unbound/malformed tool reply")
        return reply["result"]
