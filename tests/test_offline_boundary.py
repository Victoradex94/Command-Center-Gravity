"""Repository-specific evidence for the no-live-connector acceptance criterion."""

import ast
from pathlib import Path
import unittest

from tests.offline_suite import BLOCKED_EVENTS, reject_external


class OfflineBoundaryTests(unittest.TestCase):
    def test_dispatcher_imports_only_local_and_nonnetwork_standard_library(self):
        allowed = {"contextlib", "copy", "dataclasses", "datetime", "enum", "fcntl",
                   "hashlib", "json", "os", "pathlib", "re", "sqlite3", "threading", "typing"}
        root = Path(__file__).resolve().parents[1] / "dispatcher"
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertIn(alias.name.split(".")[0], allowed, str(path))
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module.split(".")[0], allowed, str(path))

    def test_offline_guard_rejects_network_and_executable_events(self):
        for event in BLOCKED_EVENTS:
            with self.subTest(event=event), self.assertRaises(RuntimeError):
                reject_external(event, ())
        reject_external("sqlite3.connect", ())
