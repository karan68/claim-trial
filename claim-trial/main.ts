/**
 * Claim Trial
 *
 * Test one technical claim at an exact Git revision with an ordinary baseline
 * and one hostile probe. The source checkout is never used for execution.
 *
 * @rote-frontmatter
 * ---
 * name: claim-trial
 * description: Tests one technical claim at an exact local Git revision. Runs a baseline and hostile probe in separate disposable worktrees, returns SUPPORTED, DISPROVEN, or INCONCLUSIVE with bounded evidence, and verifies the source checkout stayed unchanged. Run with no arguments for the bundled cancellation-lock demonstration.
 * source: https://github.com/karan68/claim-trial
 * provenance:
 *   author: Karan Yadav <mekaranyadav8@gmail.com>
 * metadata:
 *   version: 0.1.0
 *   rote_version: 0.78.0
 *   status: released
 *   kind: atomic
 *   flow_type: parallel
 *   execution_model: steps_with_presentation
 *   format: typescript
 *   requires_endpoints: []
 *   requires_sessions: false
 *   contract:
 *     atomic: true
 *     input:
 *       type: none
 *     output:
 *       format: json
 *       destination: stdout
 *     composable: true
 *   discoverability:
 *     tags:
 *     - effect-local-process
 *     - technical-verification
 *     - falsification
 *     - git
 *     - testing
 * parameters:
 * - name: mode
 *   param_type: string
 *   required: false
 *   default: demo
 *   description: demo runs the bundled inherited-lock counterexample; custom tests your repository
 * - name: repo_path
 *   param_type: string
 *   required: false
 *   default: ''
 *   description: Absolute local Git repository path; required only in custom mode
 * - name: ref
 *   param_type: string
 *   required: false
 *   default: HEAD
 *   description: Local Git commit, tag, or branch resolved to one exact commit
 * - name: claim
 *   param_type: string
 *   required: false
 *   default: Cancellation releases the operation lock.
 *   description: Bounded positive claim tested by the hostile probe
 * - name: baseline_command
 *   param_type: string
 *   required: false
 *   default: ''
 *   description: Trusted non-interactive shell command for custom mode; final stdout line must follow the probe protocol
 * - name: hostile_command
 *   param_type: string
 *   required: false
 *   default: ''
 *   description: Trusted non-interactive hostile probe for custom mode; final stdout line must follow the probe protocol
 * - name: timeout_seconds
 *   param_type: integer
 *   required: false
 *   default: '10'
 *   description: Per-probe timeout from 1 through 120 seconds
 * presentation_fixtures:
 *   prepare_target: resources/presentation-fixtures/prepare_target/fixture.yaml
 *   baseline_probe: resources/presentation-fixtures/baseline_probe/fixture.yaml
 *   hostile_probe: resources/presentation-fixtures/hostile_probe/fixture.yaml
 *   adjudicate_claim: resources/presentation-fixtures/adjudicate_claim/fixture.yaml
 *   verify_source: resources/presentation-fixtures/verify_source/fixture.yaml
 *   finalize_trial: resources/presentation-fixtures/finalize_trial/fixture.yaml
 *   cleanup_target: resources/presentation-fixtures/cleanup_target/fixture.yaml
 * steps:
 *   prepare_target:
 *     type: process.exec
 *     timeout_ms: 10000
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - prepare
 *     - --
 *     - $mode
 *     - $repo_path
 *     - $ref
 *     - $claim
 *     - $baseline_command
 *     - $hostile_command
 *     - $timeout_seconds
 *     - '@resource{demo/fixture.py}'
 *   baseline_probe:
 *     type: process.exec
 *     timeout_ms: 125000
 *     depends_on:
 *     - prepare_target
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - run-probe
 *     - --
 *     - baseline
 *     - '@prepare_target{.stdout.text | fromjson | .mode}'
 *     - '@prepare_target{.stdout.text | fromjson | .demo_source}'
 *     - '@prepare_target{.stdout.text | fromjson | .repo_root}'
 *     - '@prepare_target{.stdout.text | fromjson | .tested_commit}'
 *     - '@prepare_target{.stdout.text | fromjson | .baseline_command}'
 *     - '@prepare_target{.stdout.text | fromjson | .timeout_seconds}'
 *   hostile_probe:
 *     type: process.exec
 *     timeout_ms: 125000
 *     depends_on:
 *     - prepare_target
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - run-probe
 *     - --
 *     - hostile
 *     - '@prepare_target{.stdout.text | fromjson | .mode}'
 *     - '@prepare_target{.stdout.text | fromjson | .demo_source}'
 *     - '@prepare_target{.stdout.text | fromjson | .repo_root}'
 *     - '@prepare_target{.stdout.text | fromjson | .tested_commit}'
 *     - '@prepare_target{.stdout.text | fromjson | .hostile_command}'
 *     - '@prepare_target{.stdout.text | fromjson | .timeout_seconds}'
 *   adjudicate_claim:
 *     type: process.exec
 *     timeout_ms: 10000
 *     depends_on:
 *     - baseline_probe
 *     - hostile_probe
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - adjudicate
 *     - --
 *     - $claim
 *     - '@baseline_probe{.stdout.text}'
 *     - '@hostile_probe{.stdout.text}'
 *   verify_source:
 *     type: process.exec
 *     timeout_ms: 10000
 *     depends_on:
 *     - prepare_target
 *     - baseline_probe
 *     - hostile_probe
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - verify-source
 *     - --
 *     - '@prepare_target{.stdout.text | fromjson | .mode}'
 *     - '@prepare_target{.stdout.text | fromjson | .demo_source}'
 *     - '@prepare_target{.stdout.text | fromjson | .repo_root}'
 *     - '@prepare_target{.stdout.text | fromjson | .source_head}'
 *     - '@prepare_target{.stdout.text | fromjson | .source_status_sha256}'
 *     - '@prepare_target{.stdout.text | fromjson | .source_refs_sha256}'
 *     - '@prepare_target{.stdout.text | fromjson | .source_config_sha256}'
 *     - '@prepare_target{.stdout.text | fromjson | .source_worktrees_sha256}'
 *   finalize_trial:
 *     type: process.exec
 *     timeout_ms: 10000
 *     depends_on:
 *     - prepare_target
 *     - adjudicate_claim
 *     - verify_source
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - finalize
 *     - --
 *     - '@prepare_target{.stdout.text}'
 *     - '@adjudicate_claim{.stdout.text}'
 *     - '@verify_source{.stdout.text}'
 *   cleanup_target:
 *     type: process.exec
 *     timeout_ms: 10000
 *     depends_on:
 *     - prepare_target
 *     - finalize_trial
 *     argv:
 *     - python3
 *     - '@resource{claim_trial.py}'
 *     - cleanup
 *     - --
 *     - '@prepare_target{.stdout.text}'
 * ---
 */

const { FlowOutput, isProcessExecBody, loadPresentationContext, stepName } =
  await import("__ROTE_PRESENTATION_SDK__");

const out = new FlowOutput();
const ctx = await loadPresentationContext();

if (ctx.run.status === "failed") {
  out.human("CLAIM TRIAL\n\nINCONCLUSIVE\n\nA required stage failed. Inspect the failed step and rerun after correcting the input or environment.");
  out.summary("INCONCLUSIVE: a required Claim Trial stage failed");
  out.result({
    schema: "claim-trial.v1",
    run_id: ctx.run.run_id,
    verdict: "INCONCLUSIVE",
    reason: "A required stage failed.",
  });
} else {
  const finalObservation = ctx.requireAvailable(stepName("finalize_trial"));
  const cleanupObservation = ctx.requireAvailable(stepName("cleanup_target"));
  if (!isProcessExecBody(finalObservation.body) || !isProcessExecBody(cleanupObservation.body)) {
    throw new Error("Claim Trial did not record process observations");
  }
  if (
    finalObservation.body.status.exit.kind !== "code" ||
    finalObservation.body.status.exit.code !== 0 ||
    cleanupObservation.body.status.exit.kind !== "code" ||
    cleanupObservation.body.status.exit.code !== 0
  ) {
    throw new Error("Claim Trial finalization or cleanup failed");
  }
  const finalText = finalObservation.body.stdout?.text;
  const cleanupText = cleanupObservation.body.stdout?.text;
  if (finalText === undefined || cleanupText === undefined) {
    throw new Error("Claim Trial captured no final output");
  }
  const trial = JSON.parse(finalText);
  const cleanup = JSON.parse(cleanupText);
  if (
    trial?.schema !== "claim-trial.v1" ||
    !["SUPPORTED", "DISPROVEN", "INCONCLUSIVE"].includes(trial.verdict) ||
    cleanup?.schema !== "claim-trial.cleanup.v1"
  ) {
    throw new Error("Claim Trial returned an invalid output contract");
  }
  if (cleanup.demo_owned === true && cleanup.cleaned !== true) {
    throw new Error("Claim Trial did not clean its bundled demo repository");
  }

  const cleanupLabel = cleanup.demo_owned ? "complete" : "not needed";
  out.human([
    "CLAIM TRIAL",
    "",
    trial.verdict,
    "",
    `Claim: ${trial.claim}`,
    `Reason: ${trial.reason}`,
    `Exact revision: ${trial.tested_commit}`,
    "",
    `Baseline: ${trial.baseline.status} - ${trial.baseline.observed}`,
    `Hostile: ${trial.hostile.status} - ${trial.hostile.observed}`,
    `Git-visible source unchanged: ${trial.source_unchanged ? "yes" : "no"}`,
    `Cleanup: ${cleanupLabel}`,
    "",
    `Discarded trial: ${trial.discarded_trial.reason}`,
    `Limit: ${trial.limitations[0]}`,
  ].join("\n"));
  out.summary(`${trial.verdict}: ${trial.claim} at ${trial.tested_commit.slice(0, 12)}`);
  out.result({
    ...trial,
    run_id: ctx.run.run_id,
    cleanup: {
      cleaned: cleanup.cleaned,
      demo_owned: cleanup.demo_owned,
    },
  });
}