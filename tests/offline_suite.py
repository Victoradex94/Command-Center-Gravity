"""Run every local test with outbound networking and executable launches blocked.

POSIX fork crash tests inherit this audit hook. No SDK/connector is installed or
called. This is a test guard, not a security sandbox against hostile Python code.
"""

import sys
import unittest


BLOCKED_EVENTS = {"socket.connect", "socket.connect_ex", "socket.getaddrinfo",
                  "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto",
                  "socket.sendmsg", "http.client.connect", "urllib.Request",
                  "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}


def reject_external(event, args):
    if event in BLOCKED_EVENTS:
        raise RuntimeError("offline suite blocks external I/O: " + event)


def main():
    sys.addaudithook(reject_external)
    # Harmless guard self-check: audit dispatch only; no socket/API invocation.
    try:
        sys.audit("socket.connect", None, ("offline.invalid", 0))
    except RuntimeError:
        print("OFFLINE GUARD: active; synthetic audit probe blocked", flush=True)
    else:
        raise AssertionError("offline guard failed")
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"OFFLINE RESULT: tests={result.testsRun} failures={len(result.failures)} "
          f"errors={len(result.errors)}; no production adapter is present", flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
