from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "claim-trial"
RESOURCES = PACKAGE_ROOT / "resources"
import sys

sys.path.insert(0, str(RESOURCES))
import claim_trial


def namespace(**values):
    return argparse.Namespace(**values)


class ClaimTrialTest(unittest.TestCase):
    def prepare_demo(self):
        return claim_trial.prepare_target(
            namespace(
                mode="demo",
                repo_path="",
                ref="HEAD",
                claim=claim_trial.DEMO_CLAIM,
                baseline_command="",
                hostile_command="",
                timeout_seconds=3,
                demo_source=str(RESOURCES / "demo"),
            )
        )

    def run_role(self, prepared, role):
        return claim_trial.run_probe(
            namespace(
                role=role,
                mode=prepared["mode"],
                demo_source=prepared["demo_source"],
                repo_root=prepared["repo_root"],
                tested_commit=prepared["tested_commit"],
                command=prepared[f"{role}_command"],
                timeout_seconds=prepared["timeout_seconds"],
            )
        )

    def test_demo_disproves_claim_and_cleans_up(self):
        prepared = self.prepare_demo()
        baseline = self.run_role(prepared, "baseline")
        hostile = self.run_role(prepared, "hostile")
        adjudication = claim_trial.adjudicate(
            namespace(
                claim=prepared["claim"],
                baseline=json.dumps(baseline),
                hostile=json.dumps(hostile),
            )
        )
        verification = claim_trial.verify_source(
            namespace(
                repo_root=prepared["repo_root"],
                mode=prepared["mode"],
                demo_source=prepared["demo_source"],
                source_head=prepared["source_head"],
                source_status_sha256=prepared["source_status_sha256"],
                source_refs_sha256=prepared["source_refs_sha256"],
                source_config_sha256=prepared["source_config_sha256"],
                source_worktrees_sha256=prepared["source_worktrees_sha256"],
            )
        )
        result = claim_trial.finalize(
            namespace(
                prepared=json.dumps(prepared),
                adjudication=json.dumps(adjudication),
                verification=json.dumps(verification),
            )
        )
        cleanup = claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))
        self.assertEqual("PASS", baseline["protocol_status"])
        self.assertEqual("FAIL", hostile["protocol_status"])
        self.assertEqual("DISPROVEN", result["verdict"])
        self.assertTrue(result["source_unchanged"])
        self.assertTrue(cleanup["cleaned"])
        self.assertEqual("", prepared["repo_root"])

    def test_adjudication_requires_passing_baseline(self):
        baseline = {
            "schema": "claim-trial.probe.v1",
            "protocol_status": "FAIL",
            "observed": "baseline failed",
        }
        hostile = {
            "schema": "claim-trial.probe.v1",
            "protocol_status": "FAIL",
            "observed": "counterexample",
        }
        result = claim_trial.adjudicate(
            namespace(
                claim="A bounded claim.",
                baseline=json.dumps(baseline),
                hostile=json.dumps(hostile),
            )
        )
        self.assertEqual("INCONCLUSIVE", result["verdict"])

    def test_adjudication_supports_only_a_passing_hostile_probe(self):
        baseline = {
            "schema": "claim-trial.probe.v1",
            "protocol_status": "PASS",
            "observed": "precondition passed",
        }
        hostile = {
            "schema": "claim-trial.probe.v1",
            "protocol_status": "PASS",
            "observed": "hostile schedule passed",
        }
        result = claim_trial.adjudicate(
            namespace(
                claim="A bounded claim.",
                baseline=json.dumps(baseline),
                hostile=json.dumps(hostile),
            )
        )
        self.assertEqual("SUPPORTED", result["verdict"])

    def test_custom_mode_rejects_option_like_ref(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            with self.assertRaisesRegex(claim_trial.TrialError, "non-option"):
                claim_trial.prepare_target(
                    namespace(
                        mode="custom",
                        repo_path=str(repo),
                        ref="--help",
                        claim="A claim.",
                        baseline_command="true",
                        hostile_command="true",
                        timeout_seconds=3,
                        demo_source=str(RESOURCES / "demo"),
                    )
                )

    def test_cli_does_not_treat_option_like_ref_as_help(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RESOURCES / "claim_trial.py"),
                    "prepare",
                    "--",
                    "custom",
                    str(repo),
                    "--help",
                    "A claim.",
                    "true",
                    "true",
                    "3",
                    str(RESOURCES / "demo" / "fixture.py"),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual("", completed.stdout)
            self.assertIn("non-option", completed.stderr)

    def test_custom_mode_rejects_relative_repo_path(self):
        with self.assertRaisesRegex(claim_trial.TrialError, "absolute"):
            claim_trial.prepare_target(
                namespace(
                    mode="custom",
                    repo_path="relative/repo",
                    ref="HEAD",
                    claim="A claim.",
                    baseline_command="true",
                    hostile_command="true",
                    timeout_seconds=3,
                    demo_source=str(RESOURCES / "demo"),
                )
            )

    def test_demo_commit_is_deterministic(self):
        first = self.prepare_demo()
        second = self.prepare_demo()
        try:
            self.assertEqual(first["tested_commit"], second["tested_commit"])
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(first)))
            claim_trial.cleanup(namespace(prepared=json.dumps(second)))

    def test_probe_scrubs_ambient_environment(self):
        prepared = self.prepare_demo()
        os.environ["CLAIM_TRIAL_TEST_SECRET"] = "must-not-cross"
        try:
            command = (
                "python3 -c 'import json,os; "
                'print(json.dumps({\"status\":\"PASS\",\"observed\":'
                '\"scrubbed\" if \"CLAIM_TRIAL_TEST_SECRET\" not in os.environ else \"leaked\"}))\''
            )
            result = claim_trial.run_probe(
                namespace(
                    role="baseline",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command=command,
                    timeout_seconds=3,
                )
            )
            self.assertEqual("scrubbed", result["observed"])
        finally:
            os.environ.pop("CLAIM_TRIAL_TEST_SECRET", None)
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_timeout_is_inconclusive_protocol_evidence(self):
        prepared = self.prepare_demo()
        try:
            result = claim_trial.run_probe(
                namespace(
                    role="hostile",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command="python3 -c 'import time; time.sleep(5)'",
                    timeout_seconds=1,
                )
            )
            self.assertTrue(result["timed_out"])
            self.assertEqual("UNKNOWN", result["protocol_status"])
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_malformed_protocol_is_unknown(self):
        prepared = self.prepare_demo()
        try:
            result = claim_trial.run_probe(
                namespace(
                    role="hostile",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command="printf 'not-json\\n'",
                    timeout_seconds=3,
                )
            )
            self.assertEqual("UNKNOWN", result["protocol_status"])
            self.assertIn("not JSON", result["observed"])
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_large_output_is_hashed_and_parsed_from_bounded_tail(self):
        prepared = self.prepare_demo()
        try:
            command = (
                "python3 -c 'import json; print(\"x\" * 1000000); "
                "print(json.dumps({\"status\": \"PASS\", \"observed\": \"tail parsed\"}))'"
            )
            result = claim_trial.run_probe(
                namespace(
                    role="baseline",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command=command,
                    timeout_seconds=3,
                )
            )
            self.assertGreater(result["stdout_bytes"], claim_trial.MAX_CAPTURE_BYTES)
            self.assertEqual("PASS", result["protocol_status"])
            self.assertEqual("tail parsed", result["observed"])
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_output_over_hard_cap_is_unknown(self):
        prepared = self.prepare_demo()
        try:
            command = "python3 -c 'import sys; sys.stdout.write(\"x\" * 2000000)'"
            result = claim_trial.run_probe(
                namespace(
                    role="hostile",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command=command,
                    timeout_seconds=3,
                )
            )
            self.assertLessEqual(result["stdout_bytes"], claim_trial.MAX_OUTPUT_BYTES)
            self.assertEqual("UNKNOWN", result["protocol_status"])
            self.assertNotEqual(0, result["exit_code"])
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_probe_kills_descendants_after_parent_exits(self):
        prepared = self.prepare_demo()
        marker = f"claim-trial-descendant-{os.getpid()}"
        try:
            command = (
                "python3 -c 'import json,subprocess,sys; "
                f"subprocess.Popen([sys.executable, \"-c\", \"import time; time.sleep(30)\", \"{marker}\"]); "
                "print(json.dumps({\"status\": \"PASS\", \"observed\": \"parent complete\"}))'"
            )
            result = claim_trial.run_probe(
                namespace(
                    role="baseline",
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    repo_root=prepared["repo_root"],
                    tested_commit=prepared["tested_commit"],
                    command=command,
                    timeout_seconds=3,
                )
            )
            self.assertEqual("PASS", result["protocol_status"])
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                found = subprocess.run(
                    ["pgrep", "-f", marker], capture_output=True, check=False
                ).returncode == 0
                if not found:
                    break
                time.sleep(0.02)
            self.assertFalse(found)
        finally:
            claim_trial.cleanup(namespace(prepared=json.dumps(prepared)))

    def test_cleanup_does_not_remove_caller_path(self):
        payload = {
            "demo_owned": True,
            "repo_root": "/tmp/not-claim-trial/repo",
            "schema": "claim-trial.prepare.v1",
        }
        result = claim_trial.cleanup(namespace(prepared=json.dumps(payload)))
        self.assertTrue(result["cleaned"])

    def test_source_change_forces_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (repo / "tracked.txt").write_text("original")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
            prepared = claim_trial.prepare_target(
                namespace(
                    mode="custom",
                    repo_path=str(repo),
                    ref="HEAD",
                    claim="A claim.",
                    baseline_command="true",
                    hostile_command="true",
                    timeout_seconds=3,
                    demo_source=str(RESOURCES / "demo"),
                )
            )
            (repo / "unexpected.txt").write_text("changed")
            verification = claim_trial.verify_source(
                namespace(
                    repo_root=prepared["repo_root"],
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    source_head=prepared["source_head"],
                    source_status_sha256=prepared["source_status_sha256"],
                    source_refs_sha256=prepared["source_refs_sha256"],
                    source_config_sha256=prepared["source_config_sha256"],
                    source_worktrees_sha256=prepared["source_worktrees_sha256"],
                )
            )
            adjudication = {
                "schema": "claim-trial.adjudication.v1",
                "claim": prepared["claim"],
                "baseline": {"protocol_status": "PASS", "observed": "ready"},
                "hostile": {"protocol_status": "PASS", "observed": "passed"},
                "discarded_trial": {"attempt": "baseline", "reason": "not hostile"},
                "reason": "passed",
                "verdict": "SUPPORTED",
            }
            result = claim_trial.finalize(
                namespace(
                    prepared=json.dumps(prepared),
                    adjudication=json.dumps(adjudication),
                    verification=json.dumps(verification),
                )
            )
            self.assertFalse(result["source_unchanged"])
            self.assertEqual("INCONCLUSIVE", result["verdict"])

    def test_git_config_change_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (repo / "tracked.txt").write_text("original")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
            prepared = claim_trial.prepare_target(
                namespace(
                    mode="custom",
                    repo_path=str(repo),
                    ref="HEAD",
                    claim="A claim.",
                    baseline_command="true",
                    hostile_command="true",
                    timeout_seconds=3,
                    demo_source=str(RESOURCES / "demo"),
                )
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "claim-trial.changed", "true"],
                check=True,
            )
            verification = claim_trial.verify_source(
                namespace(
                    repo_root=prepared["repo_root"],
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    source_head=prepared["source_head"],
                    source_status_sha256=prepared["source_status_sha256"],
                    source_refs_sha256=prepared["source_refs_sha256"],
                    source_config_sha256=prepared["source_config_sha256"],
                    source_worktrees_sha256=prepared["source_worktrees_sha256"],
                )
            )
            self.assertFalse(verification["unchanged"])
            self.assertNotEqual(
                verification["current"]["config_sha256"],
                verification["expected"]["config_sha256"],
            )

    def test_custom_probes_run_in_parallel_without_worktree_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (repo / "tracked.txt").write_text("original")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
            prepared = claim_trial.prepare_target(
                namespace(
                    mode="custom",
                    repo_path=str(repo),
                    ref="HEAD",
                    claim="A claim.",
                    baseline_command="true",
                    hostile_command="true",
                    timeout_seconds=3,
                    demo_source=str(RESOURCES / "demo"),
                )
            )

            def run(role, command):
                return claim_trial.run_probe(
                    namespace(
                        role=role,
                        mode="custom",
                        demo_source="",
                        repo_root=str(repo),
                        tested_commit=prepared["tested_commit"],
                        command=command,
                        timeout_seconds=3,
                    )
                )

            passing = "printf '{\"status\":\"PASS\",\"observed\":\"passed\"}\\n'"
            failing = "python3 -c 'raise SystemExit(7)'"
            with ThreadPoolExecutor(max_workers=2) as pool:
                baseline_future = pool.submit(run, "baseline", passing)
                hostile_future = pool.submit(run, "hostile", failing)
                baseline = baseline_future.result(timeout=5)
                hostile = hostile_future.result(timeout=5)

            self.assertEqual("PASS", baseline["protocol_status"])
            self.assertEqual("UNKNOWN", hostile["protocol_status"])
            worktrees = subprocess.run(
                ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                capture_output=True,
                check=True,
                text=True,
            ).stdout
            self.assertEqual(1, worktrees.count("worktree "))
            self.assertTrue(claim_trial.verify_source(
                namespace(
                    repo_root=prepared["repo_root"],
                    mode=prepared["mode"],
                    demo_source=prepared["demo_source"],
                    source_head=prepared["source_head"],
                    source_status_sha256=prepared["source_status_sha256"],
                    source_refs_sha256=prepared["source_refs_sha256"],
                    source_config_sha256=prepared["source_config_sha256"],
                    source_worktrees_sha256=prepared["source_worktrees_sha256"],
                )
            )["unchanged"])


if __name__ == "__main__":
    unittest.main()