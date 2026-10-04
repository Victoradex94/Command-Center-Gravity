"""Local durable writer journal. One shared path, POSIX host, trusted callers only."""

from contextlib import closing, contextmanager
import fcntl
import json
from pathlib import Path
import sqlite3
import threading

from .model import require


_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


class WriterJournal:
    """SQLite FULL commits plus an advisory lock spanning provider calls.

    Intent commits precede calls; provider effects are NEVER in the SQLite
    transaction. All cooperating users must use the same path/lock on one host.
    This is not a Sheets lock, distributed lease, or provider idempotency key.
    """

    def __init__(self, path: str, scope: str, coordinator: str = "Dẹkun"):
        self.path = str(Path(path).resolve())
        require(bool(scope.strip()) and bool(coordinator.strip()), "journal scope/owner required")
        with _LOCKS_GUARD:
            self._thread_lock = _LOCKS.setdefault(self.path, threading.RLock())
        with self.locked():
            with self._connect() as db:
                db.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)")
                row = db.execute("SELECT body FROM journal WHERE id=1").fetchone()
                if row:
                    state = json.loads(row[0])
                    require(state["schema"] == 2 and state["scope"] == scope
                            and state["coordinator"] == coordinator, "journal identity mismatch")
                else:
                    self.save({"schema": 2, "scope": scope, "coordinator": coordinator,
                               "owner": None, "epoch": 0, "operations": {}, "audit": [],
                               "circuits": {}, "permission_stops": {}, "renewals": {}})

    @contextmanager
    def _connect(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db

    @contextmanager
    def locked(self):
        with self._thread_lock, open(self.path + ".lock", "a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def load(self) -> dict:
        with self._connect() as db:
            return json.loads(db.execute("SELECT body FROM journal WHERE id=1").fetchone()[0])

    def save(self, state: dict) -> None:
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO journal VALUES (1, ?)",
                       (json.dumps(state, sort_keys=True, ensure_ascii=False),))
