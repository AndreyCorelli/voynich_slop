# Richer training with plaintext lengths hidden

Two five-second solver fits are prepared on the preserved 36-type inputs from
[training diversity](training_diversity.md). Their length-only controls recovered
all 72 training words and predicted all three novel continuation words. The new
fits remove that length information and retain the original full dictionary,
training ciphertext, alphabets, H1 L1–3 model, free selection and observed code
domains. Word identities, key and segmentation remain hidden as before.

No public length heuristic or statistical guidance is added. The solver receives
only the unchanged public recovery request, with `word_lengths` omitted. Neither
training plaintext, generating key nor continuation is passed into fitting.
Truth witnesses are checked outside fitting, and verified first SAT keys are
frozen before continuation scoring. UNKNOWN is unscored and unresolved; it does
not contradict the preserved constructive positives.

Inputs, model code, source data and baseline report hashes are frozen in
`experiments/results/training-diversity-hidden/{protocol,prepared}.json`.
There are two fits, one per existing seed-3101 key (length two and mixed). The
cases were selected after their length-only successes, so this is a matched
oracle-removal diagnostic, not a blind success-rate estimate. There is no
resampling, budget increase, key enumeration or retry of completed fits.

Both fits have completed and been validated. Construction was 91–98 seconds per
case with known lengths and grew to 141–156 seconds with them hidden. The five-second budget
covers solver checks only. The report saves construction, solver and fit wall
times separately. Run locally:

```sh
.venv/bin/python -m benchmarks.training_diversity_hidden --run
```

Each completed case checkpoints to
`experiments/results/training-diversity-hidden/report.json`. Rerunning the same
command skips completed cases. If interrupted before a case completes, that case
will start again; construction/solver state is not checkpointed. Once both finish:

```sh
.venv/bin/python -m benchmarks.training_diversity_hidden --validate
```

Five focused tests pass. They verify request-only solver inputs without length
arguments, exact matching to original requests, unchanged five-second budgets,
72-word training inputs, no truth/holdout fields in prepared cases, UNKNOWN
remaining unscored, completed-case reuse and changed-identity rejection. Validation
is exercised with mocked UNKNOWN records, and both actual UNKNOWN records have
now been validated. For SAT, artifact validation independently checks witnesses,
training match counts and frozen predictions against preserved generating truth.

If hidden fits predict correctly, richer evidence helps without the length oracle
on these fixtures. If they time out, a verified predictive solution still exists;
the remaining obstacle is finding it within the fixed solver budget. SAT with poor
predictions would show that extra training evidence has not removed ambiguity
for the returned witness. None of these outcomes establishes a manuscript language
or guarantees uniqueness of the full recovered key.


## Recorded hidden-length results

| Key | Status | Requested timeout | Measured solver seconds | Construction seconds | Fit wall seconds |
|---|---|---:|---:|---:|---:|
| Length two / 3101 | UNKNOWN (`timeout`) | 5 s | 8.51 | 140.76 | 149.29 |
| Mixed / 3101 | UNKNOWN (`timeout`) | 5 s | 9.55 | 156.18 | 165.74 |

Neither result is scored. The matched length-only controls remain verified SAT
with 72/72 exact training words and 3/3 exact continuation words. Removing the
length oracle therefore prevents these runs from finding a witness within their
configured timeout; it does not invalidate the existing predictive witnesses.

The code sets Z3's timeout to 5,000 ms before a single ordinary feasibility
check. Both checks report `timeout` and return after more than five measured
seconds. No additional branch or optimization check is run. The configured
solver timeout was therefore not a strict wall-clock cap in these runs; the
observed measurements must accompany comparisons. The implementation does not
identify which internal solver work accounts for the overshoot. No new runs or
solver changes were made while recording these outcomes.

Actual artifact validation passed for both records. It checks source/model hashes,
matched requests and baselines, absence of oracle-length metadata and unscored
UNKNOWN semantics. It does not turn UNKNOWN into a proof of infeasibility.

A bounded next experiment is to apply the already frozen public midpoint length
schedule to these richer inputs, without truth-derived lengths. Keep the same
configured timeout and report construction and measured solver times. This
would test whether the known-length benefit can be obtained by the public
heuristic on richer evidence; it remains selected-fixture calibration, and the
mixed case's public guesses may differ from its generating lengths.
