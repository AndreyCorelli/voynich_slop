# Fresh 48+6 natural-passage controls

Iteration 1 preregisters three further Caesar passages beyond all prior tested
material, before fitting. Each contains 48 contiguous training words and six
held-out words. Selection uses raw-record validity, alphabet membership, at least
three distinct novel holdout types and training coverage of all holdout letters.
It uses no morphology membership, solver result or holdout prediction. Blocks
are nonoverlapping with prior tests and each other.

Intervals are zero-based and half-open: **[10484,10538)**,
**[10538,10592)** and **[10592,10646)**. The one-record shift before the first
block follows the structural eligibility rule; no coverage-based shifting or
passage replacement occurs. Canonical i/u normalization remains unchanged.

Both existing full morphology inventories are audited after passage selection.
Strict admission requires zero missing training forms; held-out coverage is
reported separately and does not gate fitting. No target forms are added,
deleted or rescued.

| Passage | Default missing training | Default missing holdout | Broader coverage |
| --- | --- | --- | --- |
| 1 | impedimenta, prouolauerunt | proturbatis | All training/holdout covered |
| 2 | hostes, uexillum | None | All training/holdout covered |
| 3 | hostium, subsidio, exercitati | praescribere | All training/holdout covered |

All default-inventory arms are **NOT_ADMITTED**. All three broader-inventory
positives and their paired shuffles are admitted. These policies are unchanged;
the broader inventory has 6.33 million forms and a full 24-letter alphabet.

New key seeds 5801–5803 generate injective fixed-two-glyph substitutions. Public
assumptions remain known code boundaries and plaintext word lengths, one code
per letter and no nulls. Pattern filtering uses ciphertext equality signatures
only. The complete inventory is retained, apart from these exact logical
subsets. First SAT keys are frozen before scoring and never replaced using
holdout accuracy. Shuffle seeds 5901–5903 preserve each word's code counts,
length and exact within-word equality signature. These are randomized controls,
not guaranteed negatives.

Each fit retains a 30-second solver budget and 60-second fresh-worker limit,
including filtering/construction, with durable phase checkpoints. Every case,
including coverage exclusions and unresolved solver results, is reported.

```sh
.venv/bin/python -m benchmarks.latin_pattern_natural_long --run
.venv/bin/python -m benchmarks.latin_pattern_natural_long --validate
```

Artifacts: `experiments/results/latin-pattern-natural-long`. The dedicated
selection test checks 48+6 size, contiguous source indices, nonoverlap, novelty
and letter coverage. Existing selected-inventory, cipher, exact-pattern and
language-equivalence tests cover the unchanged fitting path. Validation
regenerates frozen selection and coverage, verifies generating explanations,
shuffle invariants, candidate counts, recovered keys and first-key scores.

## Iteration 1 results

| Passage | Training exact | Holdout exact | Novel holdout occurrences | Positive solver | Shuffle solver/status |
| --- | --- | --- | --- | --- | --- |
| 1 | 48/48 | 6/6 | 6 | 0.295 s, SAT | 0.140 s, UNSAT |
| 2 | 48/48 | 6/6 | 5 | 0.520 s, SAT | 0.131 s, UNSAT |
| 3 | 48/48 | 6/6 | 5 | 0.513 s, SAT | 0.206 s, UNSAT |

All positive SAT explanations independently verify. Totals: **144/144 training
word occurrences, 18/18 held-out occurrences**, including **16/16 novel held-out
occurrences**. Two holdouts repeat training types and are reported separately
from novel predictions. Observed training letters: 19, 20 and 20.

Filtering takes 2.32–2.81 seconds; construction 7.92–11.31 seconds. Positive
solving takes 0.295–0.520 seconds. All three randomized controls return UNSAT;
all per-word pattern subsets are nonempty and equal between paired arms.
There are no UNKNOWN or process timeouts. The dedicated selection test passes,
and complete six-arm artifact validation passes. Default inventory exclusions
remain visible rather than omitted from coverage reporting.

## Analysis and iteration decision

The prior adaptive improvement is reproduced on fresh, nonoverlapping natural
blocks without reusing the inspected holdout. The longer training policy gives
correct first-key continuation predictions on all three admitted broader-
inventory cases. It also retains rejection of frequency/pattern-matched shuffles.
This supports the policy within the current fixed-boundary injective model.

**Stop after iteration 1 of the allowed five.** No incorrect prediction, timeout
or accepted shuffle identifies a specific defect requiring another refinement.
Adding more tuning on these successful fixtures would not address the main
remaining model assumptions. Earlier 24-word errors and all vocabulary coverage
failures remain frozen; none are overwritten or reclassified.

Three passages from the same Caesar stream are not independent historical
languages or a population accuracy estimate. Novelty/letter coverage structurally
assist passage selection. The broader inventory remains necessary; all default
arms exclude the true training explanation. These new observed keys have not
received second-key uniqueness audits. Accurate first-key recovery is reported
without assuming uniqueness or claiming manuscript evidence.

The next priority is a **two-homophone-per-letter calibration with public code
boundaries first**. This relaxes the one-code-per-letter assumption while retaining
a controlled segmentation baseline. Exact distinct-code/distinct-letter pattern
filtering would become unsound: different homophones can decode to the same
letter. A sound weaker filter and independent synthetic controls are required
before applying that extension to natural texts or hiding boundaries. This is
recommended, not implemented in this experiment.
