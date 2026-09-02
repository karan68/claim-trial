# Rote Playoffs: Source of Truth

**Status:** `claim-trial@0.1.0` published and canonical smoke verified
**Last verified:** 2026-09-02
**Event window:** September 1-6, 2026
**Submission deadline:** September 6, 2026 at 20:00 London / 19:00 UTC / September 7 at 00:30 IST

## Decision

Build and submit **`claim-trial`** first.

`claim-trial` turns a technical claim about an exact code revision into a bounded, replayable trial and returns one honest verdict:

- `SUPPORTED`
- `DISPROVEN`
- `INCONCLUSIVE`

It is the strongest choice because it captures work the entrant demonstrably performs repeatedly: convert broad technical claims into falsifiable hypotheses, find the controlling code path, run the cheapest discriminating experiment against an exact revision, and preserve the evidence and residual uncertainty.

No one can be 100% certain of winning a judged contest. Adoption, competing entries, and judges are outside our control. We are, however, sufficiently certain that `claim-trial` is the best current decision under the verified rules and live field. Do not reopen the flagship choice without new evidence that trips a kill criterion in this document.

## Published Outcome

- **Public Play:** https://play.modiqo.ai/karan68/claim-trial@0.1.0
- **Public source:** https://github.com/karan68/claim-trial
- **Released code commit:** `486908529e20b0f50e418f3614d7f8f632958d34`
- **Captured exploration:** `cap_Al0udtXDu754TF3fCVlGbrek`
- **Captured trajectory:** `sha256:949ea5115148f5c0dfac1f6d38c069cbc0a24b7fcf5011082f0820f459713c2c`
- **Registry archive digest:** `sha256:d74533b279ae9afdeccdd2d91f35b95af95ad5ccc45211b27092808a4bdeb988`
- **Installed package digest:** `installed-package-sha256-v1:e3f13ec08df9cd8dd47d07f060a01c5d80c5786d571a3aa99643ada201005277`

Verified release gates:

- 17 focused engine and integration tests pass.
- Dependency preflight passes for Python, Git, and POSIX `sh`.
- Rote validation passes with quality score `0.88`.
- Rote presentation lint passes with complete fixture coverage and no findings.
- Public inspection reports `play_run_eligible: true`, public visibility, no blockers, no adapters, and no credentials.
- Canonical public URI installed from an absent local state and returned `DISPROVEN`, an exact deterministic demo commit, Git-visible source unchanged, and cleanup complete.
- Final 20-run stress: 20 `DISPROVEN`, zero failures, one deterministic commit, zero temporary directories, and zero leaked processes.
- Custom-mode run preserved source HEAD and status; invalid refs fail closed; timeout and malformed evidence return `INCONCLUSIVE`; output is capped at 1 MiB per stream.
- Two adversarial implementation reviews completed; the second found no ship-blocking defect, and its remaining parallel-custom test gap was added and passed.

The public page states that the pinned Play can be resolved and run by anyone. Community registry commands are not shipped in the current CLI, so the event entry uses the available public `karan68` namespace, consistent with other live user-owned entries.

## Why the Previous Decision Changed

The earlier flagship, `data-roundtrip-witness`, was selected by finding an uncrowded problem in the registry. That optimized novelty and buildability but violated the event's controlling product doctrine:

> Choose inside work you already do and repeatedly pay to rediscover.

The Playoffs is not primarily an automation-design contest. The expected creation story is:

1. Ask the agent to perform useful work naturally.
2. Guide a real run using expertise.
3. Correct at least one wrong turn.
4. Let rote retain the successful path.
5. Publish a Play that returns useful work quickly on fresh input.

A clever scanner invented for the event is weaker than a method recovered from authentic repeated work.

## Official Winning Standard

Every candidate is evaluated against these ten dimensions, each scored from 1 to 5:

1. **Authenticity:** Is this work we already perform and pay to rediscover?
2. **Fast payback:** Does one run return useful information quickly?
3. **Habit gravity:** Would someone reasonably rerun it weekly or for every relevant change?
4. **Teachable expertise:** Does human correction materially improve the retained method?
5. **Play shape:** Are there multiple meaningful actions, changing inputs, and a stable result?
6. **Trust:** Can a stranger understand inputs, effects, limitations, and evidence after inspection?
7. **Runnable by strangers:** Does it avoid credentials, private services, and fragile environment assumptions?
8. **Differentiation:** Does it produce an outcome existing public Plays do not?
9. **Four-day feasibility:** Can the complete public Play be tested and published in time?
10. **Six-month value:** Will the method remain useful after the event is forgotten?

A high score is insufficient if the idea fails authenticity, stranger execution, or publication eligibility.

## Brutal Scorecard

| Rank | Candidate | Authenticity | Fast payback | Habit | Teaching | Play shape | Trust | Stranger run | Different | Feasible | Six months | Total / 50 | Decision |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `claim-trial` (narrow v1) | 5 | 4 | 5 | 5 | 5 | 5 | 3 | 4 | 4 | 5 | **45** | **BUILD FIRST** |
| 2 | `invisible-diff` | 4 | 5 | 4 | 3 | 4 | 5 | 5 | 3 | 5 | 4 | **42** | Build only as quick second entry |
| 3 | `data-roundtrip-witness` | 3 | 4 | 3 | 2 | 5 | 5 | 5 | 4 | 4 | 3 | **38** | Backup, not flagship |
| 4 | `send-safe` | 2 | 5 | 3 | 2 | 4 | 3 | 5 | 3 | 4 | 3 | **34** | Reject standalone v1 |
| 5 | `meeting-fairness` | 1 | 3 | 2 | 2 | 5 | 4 | 5 | 5 | 4 | 2 | **33** | Reject |
| 6 | `tarball-delta-witness` | 2 | 3 | 2 | 2 | 5 | 4 | 4 | 3 | 3 | 2 | **30** | Reject |
| 7 | Full npm `package-witness` | 2 | 1 | 2 | 2 | 4 | 2 | 2 | 3 | 1 | 2 | **21** | Hard reject |
| 8 | Running exploitability / generic repo security audit | 4 | 3 | 4 | 3 | 4 | 3 | 4 | 1 | 3 | 4 | **33** | Hard reject due to crowding |

Scores are strategic estimates, not mathematical guarantees. The rank and rejection rationale control the decision.

## Winner: `claim-trial`

### One-Sentence Promise

Given a local repository, exact revision, bounded technical claim, and a trusted verification command or probe, produce a replayable evidence record showing whether the observation supports, disproves, or cannot adjudicate the claim.

### Authentic Repeated Work

This method is grounded in work already performed repeatedly:

- Measured a per-line PostgreSQL ingestion path at 771 lines/s and a batched alternative at 67,904 lines/s, disproving throughput adequacy with an 88x contrast.
- Demonstrated that a PostgreSQL-invalid JSON line permanently poisoned retries and prevented later lines from ingesting.
- Reproduced advisory-lock leakage after cancellation and bounded startup refusal caused by the leaked lock.
- Proved a TLS setting silently overrode `sslmode=require` and established cleartext transport through `pg_stat_ssl`.
- Tested quota behavior under concurrent rollout rather than trusting local unit tests.
- Proved stale-plan refusal and transaction atomicity for Projection Witness against exact commits and real PostgreSQL.
- Distinguished product failures, infrastructure failures, and unproven claims instead of collapsing all red results together.

The valuable expertise is not “run tests.” It is choosing an experiment that can actually falsify the claim and refusing to overstate what the observation proves.

### Narrow v1 Scope

Supported claim classes:

1. **Performance:** throughput, latency, or bounded-resource claims.
2. **Concurrency:** race, lock, cancellation, stale-state, or idempotency claims.
3. **Security behavior:** authentication refusal, downgrade prevention, or authorization-boundary claims.
4. **Replay behavior:** retry, recovery, idempotency, or no-op-on-rerun claims.

Out of scope:

- UX or subjective quality claims.
- General architecture reviews.
- Arbitrary vulnerability discovery.
- Claims requiring production secrets or private customer data.
- Multi-service distributed causality without a locally reproducible probe.
- Automatic source edits or fixes.
- Unbounded fuzzing, load tests, or model calls.

### Inputs

Required:

- `repo_path`: absolute path to a local Git repository.
- `ref`: exact local commit or ref to test.
- `claim`: concise technical claim.
- `claim_class`: `performance`, `concurrency`, `security`, or `replay`.
- `probe_command`: trusted, non-interactive command selected during the guided run.
- `expected`: explicit observation that would support the claim.

Optional:

- `baseline_ref`: comparison revision for performance or regression claims.
- `setup_command`: bounded local preparation command.
- `timeout_seconds`: hard per-command wall-clock limit.
- `repeat_count`: 1-3 repetitions; no adaptive retrying after results are seen.
- `hostile_probe_command`: one predeclared ablation targeting the assumption most likely to invalidate the claim.

The Play must reject option-like refs, missing commits, interactive commands, invalid timeouts, and source paths outside the resolved repository.

### Stable Output Contract

```json
{
  "schema": "claim-trial.v1",
  "verdict": "SUPPORTED | DISPROVEN | INCONCLUSIVE",
  "claim": "string",
  "claim_class": "performance | concurrency | security | replay",
  "tested_commit": "40-character SHA",
  "baseline_commit": "40-character SHA or null",
  "expected": "string",
  "observed": "string",
  "probe": {
    "command": "string",
    "exit_code": 0,
    "timed_out": false,
    "duration_ms": 0,
    "repetitions": 1
  },
  "hostile_probe": {
    "status": "passed | failed | not_supplied | indeterminate",
    "observation": "string"
  },
  "environment": {
    "os": "string",
    "architecture": "string",
    "tool_versions": ["string"]
  },
  "evidence": ["bounded evidence line"],
  "discarded_trial": {
    "attempt": "string",
    "rejected_because": "string"
  },
  "limitations": ["string"],
  "residual_risk": ["string"],
  "rerun_command": "string"
}
```

`SUPPORTED` is deliberately weaker and more honest than `PROVEN`. A finite experiment can support a bounded claim; it rarely proves a universal one.

### Play DAG

```text
validate_inputs ───────┐
resolve_exact_refs ────┼─> prepare_isolated_worktree
capture_environment ───┘            │
                                    ├─> run_probe
                                    └─> run_hostile_probe (optional)
                                             │
                              compare_expected_observed
                                             │
                                  adjudicate_claim
                                             │
                              render_evidence_record
                                             │
                                  verify_source_unchanged
```

Each step must have an explicit timeout. Expected absence degrades to a labeled `INCONCLUSIVE`; malformed input and integrity failures fail closed.

### Safety and Trust Contract

- Read-only against the source checkout.
- All execution occurs in a disposable detached worktree or temporary directory.
- No network by default.
- No dependency installation unless a setup command is explicitly supplied and disclosed.
- Commands are user-supplied and trusted; the Play does not claim to sandbox arbitrary shell code.
- Captured stdout and stderr are bounded and secret-shaped values are redacted from presentation.
- The original repository status and HEAD are fingerprinted before and after execution.
- Temporary state is removed on terminal paths.
- A timeout, missing dependency, nondeterministic result, incomplete environment, or contradictory repetitions produces `INCONCLUSIVE`, never `SUPPORTED`.

### Differentiation From Existing Plays

| Existing Play | What it does | `claim-trial` difference |
|---|---|---|
| `sakshamsai26/claim-vs-reality-auditor` | Static Git-evidence classification; does not run tests | Executes a bounded discriminating probe and hostile ablation |
| `saikiranpulagalla/git-handoff-proof` | Runs one supplied command against exact Git state | Adjudicates an explicit claim against expected and observed evidence |
| `manju-builds/merge-canary` | Compares one command on a topic ref and temporary merge | Tests claim classes, hostile assumptions, and residual uncertainty |
| `jvxplaymaker/playbench` | Benchmarks with and without a Play | Evaluates code claims, not Play token or quality impact |
| Generic PR/readiness audits | Apply predefined static checklists | Starts with one falsifiable claim and preserves experiment evidence |

The differentiation disappears if v1 accepts arbitrary prose, generates generic review advice, or becomes a wrapper around one test command. Keep the explicit hypothesis, hostile ablation, expected observation, and adjudication record.

### The Required Wrong Turn

The captured exploration should retain one real non-discriminating attempt, for example:

- Initial attempt: run the existing unit test suite.
- Correction: passing unit tests do not distinguish the throughput claim.
- Better trial: measure the exact ingestion path and a controlled batched comparison against the same database and schema.

The wrong turn must be genuine. Do not stage a fake mistake for the recording.

### Canonical Demonstration

Use a tiny bundled repository or fixture with a claim that appears supported by a normal test but fails under the hostile probe.

Recommended demo:

- Claim: “Cancellation cannot leave the operation lock held.”
- Ordinary probe: successful operation releases the lock.
- Hostile probe: cancel while the lock-owning operation is in flight, then attempt a bounded second acquisition.
- Broken fixture verdict: `DISPROVEN` with the leaked-lock observation.
- Fixed fixture verdict: `SUPPORTED`, while retaining the limitation that only the declared cancellation schedule was tested.

This demonstrates expertise, correction, exact evidence, and rerun value in one compact story.

### Kill Criteria

Stop or narrow immediately if any of these is true after the first captured exploration:

1. Rote crystallizes the work into a monolithic or legacy body with fewer than two meaningful steps.
2. The probe cannot run from a clean disposable worktree.
3. The verdict requires free-form model judgment rather than explicit expected-versus-observed rules.
4. A stranger cannot run the bundled canonical fixture without credentials or manual setup.
5. Source-checkout integrity cannot be verified before and after the run.
6. The first complete canonical run exceeds ten minutes.
7. The public versioned URI cannot pass one isolated `rote play run` smoke test.
8. A new live-registry entry provides the same explicit hypothesis, hostile ablation, exact-ref execution, and adjudication contract before publication.

If criterion 1, 2, 3, or 7 cannot be repaired in one bounded attempt, pivot to `invisible-diff` rather than disguising the failure with documentation.

## Second Entry: `invisible-diff`

### Verdict

Best of the original four ideas, but not the flagship. Build only after `claim-trial` has a passing canonical local run.

### Promise

Inspect only added or staged source text for invisible Unicode controls, normalization collisions, and narrowly scoped identifier confusables.

### Inputs and Verdict

- Repository path.
- Scope: `staged`, `working-tree`, or explicit local range.
- Output: `CLEAN`, `REVIEW`, or `BLOCK`.

Every finding includes changed path, line, escaped code point, Unicode name, reason code, and confidence class.

### Why It Survived

- Fast, credential-free, read-only, and useful before every commit.
- Directly aligned with adversarial source review.
- Easy for strangers to run.
- Deterministic fixture suite is feasible in less than a day.

### Why It Did Not Win

- Unicode scanners already exist outside the registry.
- Human teaching contributes less than curated rules do.
- The Play risks looking like a polished utility created for the event rather than retained expert work.
- Naive confusable detection creates trust-destroying false positives.

### Required Scope Limits

- Scan changed lines only.
- Apply confusable and normalization checks to identifier-like tokens, keys, and structural labels.
- Do not flag arbitrary multilingual prose.
- Block bidi overrides and high-risk invisible controls; review rather than block ambiguous confusables.
- Return `INCOMPLETE` rather than `CLEAN` when the diff cannot be fully read.

## Backup: `data-roundtrip-witness`

### Verdict

Technically strong, but demoted because it was discovered from registry whitespace rather than proven repeated personal work.

### Promise

Before CSV or JSON crosses into JavaScript or a spreadsheet, identify valid data whose meaning may not survive the target representation.

### Supported v1 Signals

- Duplicate JSON keys.
- Integers outside JavaScript's exact range of `-(2^53 - 1)` through `2^53 - 1`.
- Decimal precision changes under binary64.
- Spreadsheet formula prefixes.
- Leading-zero identifiers and date-like lexical patterns as potential coercion signals.
- Empty, quoted-empty, and literal `NULL` distinctions in CSV.
- Unicode normalization collisions in headers and keys.
- Invalid UTF-8, malformed JSON/CSV, and problematic BOMs.

### Honest Language

Use “potential coercion signal” and “profile risk model.” Never claim a specific spreadsheet definitely changed the value unless the Play actually observes that application.

### Why It Lost

- It is primarily a scanner we designed, not a method recovered from repeated work.
- The correction story is weaker; most expertise is encoded before exploration.
- Weekly habit value depends on the user regularly exchanging CSV/JSON across systems.
- Expanding to databases, Office behavior, arbitrary encodings, or repair would destroy four-day feasibility.

Keep it only as a post-event product or emergency fallback after both higher-ranked entries fail.

## Rejected: `send-safe`

### Original Promise

Inspect a file immediately before sharing and return `SHARE`, `CHECK`, or `BLOCK`.

### Why It Was Attractive

- Universal language and immediate value.
- Local, credential-free, and privacy-forward.
- Potentially frequent habit.

### Why It Is Rejected

- “Safe to share” is too broad to earn from deterministic checks.
- Binary/PDF/Office metadata coverage quickly becomes incomplete.
- A `SHARE` verdict creates excessive trust liability when context and intended audience determine sensitivity.
- It overlaps secret scanners and privacy checklists.
- No verified evidence shows this is a repeated personal workflow.

A future version could survive only with narrow formats and the weaker verdict `NO_LISTED_FINDINGS / REVIEW / BLOCK`, but it is not worth event time.

## Rejected: `meeting-fairness`

### Original Promise

Score recurring meeting burden across timezones and propose a minimax rotation.

### Why It Was Attractive

- Unusual, socially meaningful, deterministic, and visually demonstrable.
- No calendar authentication required for a manual-input MVP.
- Little direct registry overlap.

### Why It Is Rejected

- No evidence that this is work the entrant repeatedly performs.
- Manual timezone and working-hour input creates more work than it removes for small teams.
- Without calendar integration it is a calculator, not a strong recurring workflow.
- With calendar integration it becomes credential-heavy and harder for strangers to run.
- “Fairness” depends on personal preferences, holidays, caregiving, and meeting importance that a minimax equation cannot establish.

Novelty does not compensate for weak authentic habit value.

## Rejected: `tarball-delta-witness`

### Original Promise

Compare two npm package tarballs and report newly shipped files, scripts, native binaries, size changes, and integrity metadata.

### Why It Is Rejected

- Useful mainly during dependency upgrades, not a daily or broad weekly habit.
- Existing dependency-vetting entries crowd the category.
- Registry and packaging edge cases add network and ecosystem failure modes.
- It remains adjacent to package-security scanners even when narrowly scoped.
- It was a compromise after the stronger package claim proved infeasible, not a naturally repeated method.

## Hard Reject: Full npm `package-witness`

### Original Promise

Prove that published npm bytes correspond to source and provenance.

### Why It Is Rejected

- npm provenance proves build identity, not absence of malicious code or semantic source equivalence.
- Transpilation, generated files, monorepos, lifecycle scripts, platform artifacts, and non-reproducible builds prevent a universal source-to-tarball proof.
- An honest tool would return unknown too often.
- A dishonest tool would overclaim safety.
- Four days is insufficient for credible ecosystem coverage.

Do not revive this idea during the event.

## Hard Reject: Running Exploitability and Generic Audits

### Original Direction

Prioritize dependencies by whether vulnerable code is actually reachable or otherwise produce a broad repository/security readiness report.

### Why It Is Rejected

- The live registry is saturated with dependency, PR, CI, repository-readiness, environment, secret, and security scanners.
- Static reachability across languages is difficult to make sound.
- Broad checklists often confuse “not found” with “not checked.”
- Differentiation would rely on description rather than a materially different result.

The live registry must be rechecked immediately before naming and publishing, but not used as an excuse to reopen crowded categories.

## Build and Publication Order

### Phase 0: Field Readiness

1. Use WSL2; native Windows is unsupported.
2. Install Play and verify Python 3.10+ and `uv`.
3. Sign in and claim the public handle.
4. Run `Hello` and one additional public Play.
5. Post `warmed up` in Discord.
6. Start the journey viewer before captured work.

### Phase 1: Capture Authentic Work

Start naturally in the harness:

```text
$play verify whether cancellation can leave this operation's lock held at this exact revision
```

Do not begin by asking the agent to implement `claim-trial`. Let it perform the work. Correct the first non-discriminating approach, enforce the bounded hostile probe, and settle only after one genuinely successful evidence-producing run.

### Phase 2: Crystallize the Narrow Contract

1. Keep four claim classes only.
2. Parameterize exact ref, claim, expected observation, bounded command, timeout, and optional hostile probe.
3. Preserve a stable JSON result and concise human view.
4. Ensure expected absence degrades to `INCONCLUSIVE`.
5. Verify the source checkout is unchanged.
6. Inspect the generated DAG; reject a monolith.

### Phase 3: Test

Minimum fixture matrix:

- Supporting ordinary probe.
- Disproving ordinary probe.
- Hostile ablation disproves a claim that the ordinary probe appears to support.
- Timeout.
- Nondeterministic repetitions.
- Missing tool.
- Dirty source checkout remains unchanged.
- Invalid ref and option-like ref.
- Secret-shaped output redaction.
- Cleanup after success, failure, and interruption.
- Canonical representation parity between human summary and JSON result.

### Phase 4: Publish Early

1. Choose **Community**.
2. Use immutable semantic versions.
3. Inspect the exact public contract.
4. Run the versioned public URI from an isolated temporary directory.
5. Ask real participants to inspect and run the bundled fixture.
6. Improve only from observed friction; every public change requires a version bump.
7. Schedule a rerun that catches a real changed revision, not merely a recurrence screenshot.

### Phase 5: Second Entry

Build `invisible-diff` only after the flagship's public URI passes the isolated smoke test. Do not trade flagship reliability for entry count.

## Time Budget

| Block | Maximum time | Exit condition |
|---|---:|---|
| WSL/Play readiness | 2 hours | Warm-up and public identity confirmed |
| First authentic captured trial | 4 hours | One bounded claim adjudicated with a real correction |
| Crystallization and core implementation | 8 hours | Multi-step DAG and stable output run locally |
| Hostile fixtures and cleanup tests | 6 hours | Required matrix passes |
| Publication debugging | 4 hours | Versioned public URI runs in isolation |
| Adoption feedback and one revision | 4 hours | At least one stranger completes a run |
| `invisible-diff` second entry | 6 hours | Only after flagship gate |
| Reserve | Remaining time | Demo evidence, docs, or one root-cause repair |

After one definitive expensive failure, stop and identify the root cause. Do not repeatedly tune commands after seeing outcomes; that invalidates the trial and wastes the event window.

## Non-Negotiable Claims Discipline

- Never say “proved” when the trial only sampled bounded behavior.
- Never say “safe” when only listed checks passed.
- Never treat missing evidence as success.
- Never hide a skipped, timed-out, or unreadable stage.
- Never run an undeclared write against the source repository.
- Never adapt thresholds after observing the candidate result.
- Never claim isolation for arbitrary commands unless a real sandbox enforces it.
- Never publish before one clean external URI run.

## Current Confidence

- **100% confidence that contest victory cannot be guaranteed honestly.**
- **90% confidence that `claim-trial` is the strongest strategic choice from the reviewed set under the official doctrine.**
- **75% confidence that its differentiation will remain durable until publication.** This depends on preserving the narrow claim classes, hostile ablation, exact-ref evidence, and explicit expected-versus-observed adjudication.
- **Primary execution risk:** a broad exploration may crystallize poorly because arbitrary technical investigations do not share one stable path.
- **Mitigation:** use one canonical cancellation/lock claim, fixed input/output contract, bounded commands, and a deterministic bundled fixture.

## Decision Log

### 2026-09-02

- Corrected the live-field assumption from a stale 66-Play feed to 249 public Plays.
- Rejected the initial exploitability/security direction due to category saturation.
- Selected `data-roundtrip-witness` after technical and registry review.
- Reopened that decision after applying the official “work you already do” doctrine.
- Demoted all contest-invented concepts.
- Locked narrow `claim-trial` as the flagship because it captures verified repeated expertise.
- Locked `invisible-diff` as the only planned second entry.

## Next Action

Do not change immutable version `0.1.0`. Ask real participants to inspect and run the zero-argument public URI, record only genuine adoption feedback, and prepare `0.1.1` only for a concrete defect or major comprehension failure. The remaining contest work is adoption and observation, not more architecture.
