from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
LOCK_PATH = ROOT / ".demo-baseline.lock"


def run(mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "fixture.py"), mode, str(LOCK_PATH)],
        capture_output=True,
        check=False,
        text=True,
        timeout=1,
    )


def main() -> None:
    completed = run("success")
    contender = run("try")
    acquired = False
    try:
        acquired = json.loads(contender.stdout).get("acquired") is True
    except json.JSONDecodeError:
        pass
    passed = completed.returncode == 0 and contender.returncode == 0 and acquired
    print(
        json.dumps(
            {
                "evidence": ["normal_exit", "contender_acquired"],
                "observed": (
                    "Normal completion released the lock."
                    if passed
                    else "The normal lock-release precondition failed."
                ),
                "status": "PASS" if passed else "UNKNOWN",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()