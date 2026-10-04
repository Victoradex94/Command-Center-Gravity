"""Exact-commit transport and offline fixtures. No production remote adapter."""
import hashlib
from copy import deepcopy
from typing import Protocol


class Transport(Protocol):
    def head(self) -> str | None: ...
    def read(self, sha: str) -> dict[str, bytes]: ...
    def parent(self, sha: str) -> str | None: ...
    def construct(self, parent: str | None, files: dict[str, bytes]) -> str: ...
    def publish(self, expected: str | None, sha: str) -> str: ...


class MemoryGitTransport:
    """Deterministic commit fixture; configurable authoritative finality receipts."""
    def __init__(self):
        self.objects = {}
        self.remote = None
        self.mode = 'success'
        self.calls = 0
        self.commits = 0

    def head(self):
        return self.remote

    def parent(self, sha):
        return self.objects[sha][0]

    def read(self, sha):
        return deepcopy(self.objects[sha][1])

    def construct(self, parent, files):
        content = (parent or '').encode() + b''.join(
            k.encode() + b'\0' + files[k] for k in sorted(files))
        sha = hashlib.sha256(content).hexdigest()
        if sha not in self.objects:
            self.commits += 1
        self.objects[sha] = (parent, deepcopy(files))
        return sha

    def publish(self, expected, sha):
        self.calls += 1
        if self.remote != expected:
            return 'CONFLICT'
        if self.mode == 'reject':
            return 'FINAL_NOOP'
        if self.mode == 'unknown':
            return 'UNKNOWN'
        self.remote = sha
        if self.mode == 'lost':
            return 'UNKNOWN'
        if self.mode == 'permission':
            self.remote = expected
            return 'HUMAN_PERMISSION_CANCELLED'
        return 'SUCCESS'


