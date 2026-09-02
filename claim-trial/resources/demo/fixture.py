from __future__ import annotations

import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time


def open_lock(path: str):
    return Path(path).open("a+")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"success", "hold-inherited", "try"}:
        raise SystemExit("usage: fixture.py {success|hold-inherited|try} LOCK_PATH")
    mode, path = sys.argv[1:]
    with open_lock(path) as lock_file:
        if mode == "try":
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print(json.dumps({"acquired": False}, sort_keys=True))
                return 1
            print(json.dumps({"acquired": True}, sort_keys=True))
            return 0
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        if mode == "success":
            return 0
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            pass_fds=(lock_file.fileno(),),
        )
        print(json.dumps({"child_pid": child.pid}, sort_keys=True), flush=True)
        while True:
            time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())