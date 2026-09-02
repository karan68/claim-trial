from __future__ import annotations

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / ".demo-hostile.lock"


def contender() -> tuple[int, bool]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "fixture.py"), "try", str(LOCK_PATH)],
        capture_output=True,
        check=False,
        text=True,
        timeout=1,
    )
    try:
        acquired = json.loads(completed.stdout).get("acquired") is True
    except json.JSONDecodeError:
        acquired = False
    return completed.returncode, acquired


def main() -> None:
    holder = subprocess.Popen(
        [sys.executable, str(ROOT / "fixture.py"), "hold-inherited", str(LOCK_PATH)],
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    parent_exited = False
    contended = False
    reacquired = False
    ready = False
    try:
        readable, _, _ = select.select([holder.stdout], [], [], 3)
        if readable:
            line = holder.stdout.readline()
            try:
                ready = isinstance(json.loads(line).get("child_pid"), int)
            except json.JSONDecodeError:
                pass
        if ready:
            holder.terminate()
            try:
                holder.wait(timeout=3)
                parent_exited = True
            except subprocess.TimeoutExpired:
                pass
            before_code, before_acquired = contender()
            contended = before_code == 1 and not before_acquired
    finally:
        try:
            os.killpg(holder.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            holder.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            after_code, after_acquired = contender()
            if after_code == 0 and after_acquired:
                reacquired = True
                break
            time.sleep(0.02)
    disproven = ready and parent_exited and contended and reacquired
    print(
        json.dumps(
            {
                "evidence": [
                    f"parent_exited={str(parent_exited).lower()}",
                    f"contention_before_cleanup={str(contended).lower()}",
                    f"reacquired_after_cleanup={str(reacquired).lower()}",
                ],
                "observed": (
                    "The parent exited, but its inherited child kept the lock until cleanup."
                    if disproven
                    else "The hostile cancellation schedule did not produce conclusive evidence."
                ),
                "status": "FAIL" if disproven else "UNKNOWN",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()