from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any


DEMO_CLAIM = "Cancellation releases the operation lock."
MAX_CAPTURE_BYTES = 65_536
MAX_COMMAND_CHARS = 4_000
MAX_OBSERVED_CHARS = 1_000
MAX_OUTPUT_BYTES = 1_048_576
PROTOCOL_STATUSES = {"PASS", "FAIL", "UNKNOWN"}


class TrialError(RuntimeError):
    pass


def compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def emit(value: object) -> None:
    print(compact_json(value))


def run_process(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    environment: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise TrialError(f"command failed ({completed.returncode}): {detail or arguments[0]}")
    return completed


def git(repo: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return run_process(["git", "-C", str(repo), *arguments], check=check)


def git_text(repo: Path, *arguments: str) -> str:
    return git(repo, *arguments).stdout.decode("utf-8", errors="strict").strip()


def source_snapshot(repo: Path) -> dict[str, str]:
    head = git_text(repo, "rev-parse", "HEAD")
    status = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    refs = git(repo, "show-ref", "--head", check=False).stdout
    config = git(repo, "config", "--local", "--null", "--list").stdout
    worktrees = git(repo, "worktree", "list", "--porcelain").stdout
    return {
        "config_sha256": hashlib.sha256(config).hexdigest(),
        "head": head,
        "refs_sha256": hashlib.sha256(refs).hexdigest(),
        "status_sha256": hashlib.sha256(status).hexdigest(),
        "worktrees_sha256": hashlib.sha256(worktrees).hexdigest(),
    }


def resolve_repo(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise TrialError("repo_path must be absolute")
    if not candidate.is_dir():
        raise TrialError("repo_path is not a directory")
    root = Path(git_text(candidate, "rev-parse", "--show-toplevel")).resolve()
    if not root.is_dir():
        raise TrialError("Git repository root is unavailable")
    return root


def resolve_commit(repo: Path, reference: str) -> str:
    if not reference or reference.startswith("-") or "\x00" in reference or len(reference) > 200:
        raise TrialError("ref must be a non-option local Git reference")
    commit = git_text(
        repo,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{reference}^{{commit}}",
    )
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise TrialError("ref did not resolve to a full commit SHA")
    return commit


def validate_text(value: str, label: str, maximum: int) -> str:
    if not value.strip():
        raise TrialError(f"{label} is required")
    if "\x00" in value or len(value) > maximum:
        raise TrialError(f"{label} is invalid or too long")
    return value.strip()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(file_digest(path).encode())
    return digest.hexdigest()


def remove_temp_root(root: Path, *allowed_prefixes: str) -> None:
    root = root.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if root.parent != temp_root or not any(root.name.startswith(prefix) for prefix in allowed_prefixes):
        raise TrialError("refusing to remove an unexpected temporary path")
    last_error: OSError | None = None
    for attempt in range(10):
        try:
            shutil.rmtree(root)
            return
        except FileNotFoundError:
            return
        except OSError as error:
            last_error = error
            if attempt < 9:
                time.sleep(0.02)
    raise TrialError(f"temporary cleanup failed: {last_error}")


def initialize_demo(demo_source: Path, demo_root: Path | None = None) -> Path:
    if not demo_source.is_dir():
        raise TrialError("bundled demo resources are missing")
    demo_root = demo_root or Path(tempfile.mkdtemp(prefix="claim-trial-demo-"))
    repo = demo_root / "repo"
    shutil.copytree(demo_source, repo)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Claim Trial Demo")
    git(repo, "config", "user.email", "claim-trial@example.invalid")
    git(repo, "add", ".")
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
        }
    )
    run_process(
        ["git", "-C", str(repo), "commit", "-q", "-m", "Claim Trial deterministic demo"],
        environment=environment,
    )
    return repo


def prepare_target(arguments: argparse.Namespace) -> dict[str, Any]:
    timeout_seconds = arguments.timeout_seconds
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise TrialError("timeout_seconds must be between 1 and 120")
    if arguments.mode == "demo":
        if arguments.repo_path or arguments.baseline_command or arguments.hostile_command:
            raise TrialError("demo mode does not accept repo_path or probe commands")
        if arguments.ref != "HEAD":
            raise TrialError("demo mode uses its bundled HEAD revision")
        claim = validate_text(arguments.claim, "claim", 500)
        if claim != DEMO_CLAIM:
            raise TrialError("demo mode tests only its declared cancellation claim")
        demo_source = Path(arguments.demo_source).resolve()
        demo_source = demo_source.parent if demo_source.is_file() else demo_source
        repo = initialize_demo(demo_source)
        baseline_command = "python3 demo_baseline.py"
        hostile_command = "python3 demo_hostile.py"
        demo_owned = True
    elif arguments.mode == "custom":
        claim = validate_text(arguments.claim, "claim", 500)
        repo = resolve_repo(arguments.repo_path)
        baseline_command = validate_text(
            arguments.baseline_command, "baseline_command", MAX_COMMAND_CHARS
        )
        hostile_command = validate_text(
            arguments.hostile_command, "hostile_command", MAX_COMMAND_CHARS
        )
        demo_owned = False
    else:
        raise TrialError("mode must be demo or custom")
    if demo_owned:
        try:
            tested_commit = resolve_commit(repo, arguments.ref)
        finally:
            remove_temp_root(repo.parent, "claim-trial-demo-")
        snapshot = {
            "config_sha256": tested_commit,
            "head": tested_commit,
            "refs_sha256": tested_commit,
            "status_sha256": tree_digest(demo_source),
            "worktrees_sha256": tested_commit,
        }
        repo_root = ""
        demo_source_value = str(demo_source)
    else:
        tested_commit = resolve_commit(repo, arguments.ref)
        snapshot = source_snapshot(repo)
        repo_root = str(repo)
        demo_source_value = ""
    return {
        "baseline_command": baseline_command,
        "claim": claim,
        "demo_owned": demo_owned,
        "demo_source": demo_source_value,
        "hostile_command": hostile_command,
        "mode": arguments.mode,
        "repo_root": repo_root,
        "schema": "claim-trial.prepare.v1",
        "source_config_sha256": snapshot["config_sha256"],
        "source_head": snapshot["head"],
        "source_refs_sha256": snapshot["refs_sha256"],
        "source_status_sha256": snapshot["status_sha256"],
        "source_worktrees_sha256": snapshot["worktrees_sha256"],
        "tested_commit": tested_commit,
        "timeout_seconds": timeout_seconds,
    }


def scrubbed_environment(temp_root: Path) -> dict[str, str]:
    environment = {
        "CI": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(temp_root / "home"),
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "TMPDIR": str(temp_root / "tmp"),
    }
    for name in ("LANG", "LC_ALL", "TZ"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    Path(environment["HOME"]).mkdir()
    Path(environment["TMPDIR"]).mkdir()
    return environment


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tail(path: Path) -> tuple[str, int, str]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - MAX_CAPTURE_BYTES))
        data = handle.read(MAX_CAPTURE_BYTES)
    return data.decode("utf-8", errors="replace"), size, file_digest(path)


def parse_protocol(stdout_tail: str) -> tuple[str, str, list[str]]:
    lines = [line for line in stdout_tail.splitlines() if line.strip()]
    if not lines:
        return "UNKNOWN", "probe emitted no protocol line", []
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return "UNKNOWN", "probe's final non-empty line was not JSON", []
    if not isinstance(payload, dict) or payload.get("status") not in PROTOCOL_STATUSES:
        return "UNKNOWN", "probe protocol status was missing or invalid", []
    observed = payload.get("observed")
    if not isinstance(observed, str) or not observed.strip():
        return "UNKNOWN", "probe protocol observation was missing", []
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        return "UNKNOWN", "probe protocol evidence was invalid", []
    return (
        payload["status"],
        observed.strip()[:MAX_OBSERVED_CHARS],
        [item[:MAX_OBSERVED_CHARS] for item in evidence[:8]],
    )


def terminate_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def limit_probe_output() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES))


def run_probe(arguments: argparse.Namespace) -> dict[str, Any]:
    command = validate_text(arguments.command, "probe command", MAX_COMMAND_CHARS)
    if arguments.timeout_seconds < 1 or arguments.timeout_seconds > 120:
        raise TrialError("timeout_seconds must be between 1 and 120")
    temp_root = Path(tempfile.mkdtemp(prefix=f"claim-trial-{arguments.role}-"))
    if arguments.mode == "demo":
        demo_source = Path(arguments.demo_source).resolve()
        repo = initialize_demo(demo_source, temp_root)
    elif arguments.mode == "custom":
        repo = Path(arguments.repo_root).resolve()
        if not repo.is_dir():
            raise TrialError("prepared repository is unavailable")
    else:
        raise TrialError("prepared mode is invalid")
    tested_commit = resolve_commit(repo, arguments.tested_commit)
    checkout = temp_root / "checkout"
    stdout_path = temp_root / "stdout"
    stderr_path = temp_root / "stderr"
    process: subprocess.Popen[bytes] | None = None
    timed_out = False
    exit_code: int | None = None
    cleanup_errors: list[str] = []
    try:
        git(repo, "worktree", "add", "--detach", "--quiet", str(checkout), tested_commit)
        environment = scrubbed_environment(temp_root)
        with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
            process = subprocess.Popen(
                ["sh", "-c", command],
                cwd=checkout,
                env=environment,
                preexec_fn=limit_probe_output,
                start_new_session=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
            try:
                exit_code = process.wait(timeout=arguments.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_group(process)
                exit_code = process.wait(timeout=1)
            finally:
                terminate_group(process)
        stdout_tail, stdout_bytes, stdout_sha256 = read_tail(stdout_path)
        _, stderr_bytes, stderr_sha256 = read_tail(stderr_path)
        if timed_out:
            protocol_status = "UNKNOWN"
            observed = f"probe timed out after {arguments.timeout_seconds} seconds"
            evidence: list[str] = []
        elif exit_code != 0:
            protocol_status = "UNKNOWN"
            observed = f"probe command exited with code {exit_code}"
            evidence = []
        else:
            protocol_status, observed, evidence = parse_protocol(stdout_tail)
        result = {
            "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
            "evidence": evidence,
            "exit_code": exit_code,
            "observed": observed,
            "protocol_status": protocol_status,
            "role": arguments.role,
            "schema": "claim-trial.probe.v1",
            "stderr_bytes": stderr_bytes,
            "stderr_sha256": stderr_sha256,
            "stdout_bytes": stdout_bytes,
            "stdout_sha256": stdout_sha256,
            "tested_commit": tested_commit,
            "timed_out": timed_out,
        }
    finally:
        if process is not None:
            terminate_group(process)
        if checkout.exists():
            removed = git(repo, "worktree", "remove", "--force", str(checkout), check=False)
            if removed.returncode != 0:
                cleanup_errors.append("Git worktree removal failed")
        git(repo, "worktree", "prune", check=False)
        remove_temp_root(
            temp_root,
            "claim-trial-baseline-",
            "claim-trial-hostile-",
        )
    if cleanup_errors:
        raise TrialError("; ".join(cleanup_errors))
    return result


def decode_object(value: str, schema: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise TrialError("upstream step did not emit valid JSON") from error
    if not isinstance(payload, dict) or payload.get("schema") != schema:
        raise TrialError(f"upstream step did not emit {schema}")
    return payload


def adjudicate(arguments: argparse.Namespace) -> dict[str, Any]:
    baseline = decode_object(arguments.baseline, "claim-trial.probe.v1")
    hostile = decode_object(arguments.hostile, "claim-trial.probe.v1")
    claim = validate_text(arguments.claim, "claim", 500)
    if baseline["protocol_status"] != "PASS":
        verdict = "INCONCLUSIVE"
        reason = "The baseline precondition did not pass."
    elif hostile["protocol_status"] == "PASS":
        verdict = "SUPPORTED"
        reason = "The declared hostile probe passed."
    elif hostile["protocol_status"] == "FAIL":
        verdict = "DISPROVEN"
        reason = "The declared hostile probe produced a counterexample."
    else:
        verdict = "INCONCLUSIVE"
        reason = "The hostile probe did not produce a conclusive protocol result."
    return {
        "baseline": baseline,
        "claim": claim,
        "discarded_trial": {
            "attempt": "ordinary baseline",
            "reason": "A normal path establishes the precondition but cannot test hostile behavior.",
        },
        "hostile": hostile,
        "reason": reason,
        "schema": "claim-trial.adjudication.v1",
        "verdict": verdict,
    }


def verify_source(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.mode == "demo":
        current = {
            "config_sha256": arguments.source_config_sha256,
            "head": arguments.source_head,
            "refs_sha256": arguments.source_refs_sha256,
            "status_sha256": tree_digest(Path(arguments.demo_source).resolve()),
            "worktrees_sha256": arguments.source_worktrees_sha256,
        }
    elif arguments.mode == "custom":
        current = source_snapshot(Path(arguments.repo_root).resolve())
    else:
        raise TrialError("prepared mode is invalid")
    expected = {
        "config_sha256": arguments.source_config_sha256,
        "head": arguments.source_head,
        "refs_sha256": arguments.source_refs_sha256,
        "status_sha256": arguments.source_status_sha256,
        "worktrees_sha256": arguments.source_worktrees_sha256,
    }
    unchanged = current == expected
    return {
        "current": current,
        "expected": expected,
        "schema": "claim-trial.source-verification.v1",
        "unchanged": unchanged,
    }


def finalize(arguments: argparse.Namespace) -> dict[str, Any]:
    prepared = decode_object(arguments.prepared, "claim-trial.prepare.v1")
    adjudication = decode_object(arguments.adjudication, "claim-trial.adjudication.v1")
    verification = decode_object(
        arguments.verification, "claim-trial.source-verification.v1"
    )
    verdict = adjudication["verdict"] if verification["unchanged"] else "INCONCLUSIVE"
    reason = (
        adjudication["reason"]
        if verification["unchanged"]
        else "The source checkout changed during the trial."
    )
    limitation = (
        "This verdict applies only to the exact commit and declared probes."
        if verdict != "SUPPORTED"
        else "One declared hostile probe passed; this is evidence, not universal proof."
    )
    return {
        "baseline": {
            "observed": adjudication["baseline"]["observed"],
            "status": adjudication["baseline"]["protocol_status"],
        },
        "claim": adjudication["claim"],
        "discarded_trial": adjudication["discarded_trial"],
        "hostile": {
            "observed": adjudication["hostile"]["observed"],
            "status": adjudication["hostile"]["protocol_status"],
        },
        "limitations": [limitation],
        "mode": prepared["mode"],
        "reason": reason,
        "schema": "claim-trial.v1",
        "source_unchanged": verification["unchanged"],
        "tested_commit": prepared["tested_commit"],
        "verdict": verdict,
    }


def cleanup(arguments: argparse.Namespace) -> dict[str, Any]:
    prepared = decode_object(arguments.prepared, "claim-trial.prepare.v1")
    return {
        "cleaned": True,
        "demo_owned": prepared["demo_owned"],
        "schema": "claim-trial.cleanup.v1",
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Deterministic Claim Trial engine")
    commands = root.add_subparsers(dest="operation", required=True)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("mode", choices=("demo", "custom"))
    prepare.add_argument("repo_path")
    prepare.add_argument("ref")
    prepare.add_argument("claim")
    prepare.add_argument("baseline_command")
    prepare.add_argument("hostile_command")
    prepare.add_argument("timeout_seconds", type=int)
    prepare.add_argument("demo_source")

    probe = commands.add_parser("run-probe")
    probe.add_argument("role", choices=("baseline", "hostile"))
    probe.add_argument("mode", choices=("demo", "custom"))
    probe.add_argument("demo_source")
    probe.add_argument("repo_root")
    probe.add_argument("tested_commit")
    probe.add_argument("command")
    probe.add_argument("timeout_seconds", type=int)

    judge = commands.add_parser("adjudicate")
    judge.add_argument("claim")
    judge.add_argument("baseline")
    judge.add_argument("hostile")

    verify = commands.add_parser("verify-source")
    verify.add_argument("mode", choices=("demo", "custom"))
    verify.add_argument("demo_source")
    verify.add_argument("repo_root")
    verify.add_argument("source_head")
    verify.add_argument("source_status_sha256")
    verify.add_argument("source_refs_sha256")
    verify.add_argument("source_config_sha256")
    verify.add_argument("source_worktrees_sha256")

    finish = commands.add_parser("finalize")
    finish.add_argument("prepared")
    finish.add_argument("adjudication")
    finish.add_argument("verification")

    clean = commands.add_parser("cleanup")
    clean.add_argument("prepared")
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.operation == "prepare":
            result = prepare_target(arguments)
        elif arguments.operation == "run-probe":
            result = run_probe(arguments)
        elif arguments.operation == "adjudicate":
            result = adjudicate(arguments)
        elif arguments.operation == "verify-source":
            result = verify_source(arguments)
        elif arguments.operation == "finalize":
            result = finalize(arguments)
        else:
            result = cleanup(arguments)
        emit(result)
        return 0
    except (OSError, TrialError, ValueError) as error:
        print(f"claim-trial: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())