# Claim Trial

Claim Trial tests one bounded technical claim at one exact local Git commit. It runs an ordinary baseline and a hostile probe in separate disposable worktrees, then returns `SUPPORTED`, `DISPROVEN`, or `INCONCLUSIVE` with the observation that caused the verdict.

It does not execute inside your source checkout. Probe commands receive a minimal environment without ambient credentials. Commands are still trusted local shell code: review them before running, do not let them daemonize or create a new process session, and never put secrets in parameters or output.

## Try It

The zero-argument run uses a bundled demonstration. A normal completion releases a POSIX file lock, but cancellation leaves an inherited child holding it:

```sh
rote play run ./main.ts
```

Expected headline: `DISPROVEN`.

## Test Your Claim

Both commands must be non-interactive and print one JSON object as their final non-empty stdout line:

```json
{"status":"PASS","observed":"what the probe established","evidence":["optional short fact"]}
```

`status` must be `PASS`, `FAIL`, or `UNKNOWN`:

- Baseline `PASS` plus hostile `PASS` returns `SUPPORTED`.
- Baseline `PASS` plus hostile `FAIL` returns `DISPROVEN`.
- Any `UNKNOWN`, timeout, malformed protocol, nonzero command exit, or source change returns `INCONCLUSIVE`.

Run a custom trial:

```sh
rote play run ./main.ts \
  mode=custom \
  repo_path=/absolute/path/to/repo \
  ref=HEAD \
  claim='Cancellation releases the operation lock.' \
  baseline_command='python3 tests/baseline_probe.py' \
  hostile_command='python3 tests/cancellation_probe.py' \
  timeout_seconds=10
```

In custom mode, the repository and ref are resolved before execution. Each command runs against the same exact commit in its own detached worktree. Claim Trial kills the probe process group, removes the worktree, compares Git-visible source state before and after, caps each stdout/stderr file at 1 MiB, bounds reported output, and reports uncertainty instead of guessing. Demo mode instead verifies the packaged fixture content while each probe owns and removes its temporary repository.

## Scope

Claim Trial evaluates only the two probes you provide. `SUPPORTED` means the declared hostile probe passed at the tested commit; it is not universal proof. `DISPROVEN` means that probe produced a counterexample. Git-visible integrity covers HEAD, refs, local config, worktree metadata, tracked changes, and untracked files; ignored files are outside that claim. Process-group cleanup does not contain a command that deliberately daemonizes into a new session. Claim Trial does not discover tests, design experiments, install dependencies, access credentials, or establish business truth.

## Develop

```sh
python3 -m unittest discover -s ../tests -v
rote play validate ./main.ts
rote play lint ./main.ts
```