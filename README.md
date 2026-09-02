# Claim Trial

Claim Trial turns one technical claim into a bounded, replayable experiment at one exact Git commit.

It runs an ordinary baseline and one hostile probe in separate disposable worktrees, compares their declared observations, verifies Git-visible source state, and returns one honest result:

- `SUPPORTED`: the baseline and hostile probe both passed.
- `DISPROVEN`: the baseline passed and the hostile probe produced a counterexample.
- `INCONCLUSIVE`: evidence was missing, malformed, timed out, failed, or the source changed.

## Run The Demo

After publication:

```sh
rote play run https://play.modiqo.ai/karan68/claim-trial@0.1.0 --yes
```

The bundled demonstration tests whether cancellation releases a POSIX lock. A normal path passes, but the hostile cancellation path leaves an inherited child holding the lock. Expected verdict: `DISPROVEN`.

## Use Your Repository

See [claim-trial/README.md](claim-trial/README.md) for the two-line probe protocol and custom invocation. Probe commands are trusted local shell code. Claim Trial does not discover or design experiments; its job is to execute the experiment you chose without silently moving the revision or overstating incomplete evidence.

## Verified Gates

- 17 focused engine and integration tests.
- Clean Rote validation and presentation lint.
- Real custom-mode run with unchanged source HEAD/status.
- Invalid-ref hard-fault and hostile-timeout tests.
- 20 consecutive seven-step demo runs: 20 `DISPROVEN`, one deterministic commit, zero failures, zero leaked temp directories, zero leaked processes.
- Two adversarial implementation reviews; final review found no ship-blocking defect.

The captured exploration and strategic decisions are documented in [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md).