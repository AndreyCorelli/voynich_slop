# Fresh Voynich block screen

This screen reconnects the synthetic calibration work with manuscript data:
two preselected non-overlapping blocks, full corrected Latin/Swabian dictionaries,
H1 before H2, unchanged contraction rules, ordinary recovery and frozen
continuation scoring only after SAT. The experiment is bounded and exploratory,
not a language-likelihood or decipherment test.

## Frozen selection and novelty gate

Use cached Zandbergen–Landini atomic EVA transcription records. EVA characters
are the existing observation units, not a claim that each is one manuscript
glyph. No new token grouping or spelling normalization is introduced.

Exclude whole folios f1r and f3r used in earlier recovery/prediction work and all
ten earlier cross-section target folios. Select the first contiguous 44 eligible
records on each of the first two remaining distinct folios. Missing/excluded
words and tokens outside the existing cipher alphabet interrupt runs. Selection
does not use length, repetition or language scores. This freshness scope excludes
known earlier target pages; it does not mean corpus statistics were unseen in
all earlier analyses.

Split each selected block into 22 training words followed immediately by 22
continuation words, on the same folio, with no skipped records. Measure novelty
before fitting. The frozen gate requires at least eleven continuation word
occurrences absent from training; failed blocks would be preserved and the run
stopped, not replaced to improve novelty.

| Block | Folio | Training records | Immediate continuation records | Novel occurrences | Distinct novel types |
| --- | --- | --- | --- | --- | --- |
| 1 | f1v | 215–236 | 237–258 | 21/22 | 20 |
| 2 | f2r | 327–348 | 349–370 | 19/22 | 19 |

Indices are zero-based. Both blocks pass the novelty gate. Their adjacent early
folios are not statistically independent or a broad manuscript sample.

A per-block bigram/endpoints/repetition control uses the unchanged Euler-trail
generator, seed 2323, bounded 128 draws. A control must change training. The f1v
control is unavailable: no changed collision-free draw was found. The f2r
control changes one training word and preserves every word's overlapping
bigram counts, endpoints, lengths, glyph counts and exact repetition partition.
Its continuation is unchanged. No alternate control or folio is substituted.

## Matched models and budget

Use the corrected full Latin vocabulary (5,655 spellings) and Swabian 123
vocabulary (3,181 spellings), not the twelve-word calibration vocabularies.
Letter profiles preserve their alphabets/dictionaries; mixed profiles add only
the fixed optional whole-word `et`/`in` units from the recent synthetic pilots.
Mixed tokenization counts are 5,656 and 3,182. No other abbreviations are added.

Within each language/profile/ciphertext, H1 and H2 differ only in maximum
homophone count. Both allow prefix-free code lengths 1–3, free choices, no nulls
and observed codeword domains. All H1 arms run before H2; there is no
outcome-dependent profile promotion, seed tuning or larger budget.

Each arm receives one five-second solver check. Construction time is recorded
separately, and actual timeout runtime can exceed the nominal cap slightly.
Sixteen real arms plus eight f2r control arms give 24 fits. The eight unavailable
f1v control arms are not counted as UNKNOWN or UNSAT.

A SAT key would be frozen before scoring its continuation, with repeated and
novel ciphertext words reported separately. Real SAT keys would also score the
structured continuation under that same key; the separately fitted control
arm supplies an additional comparison. UNKNOWN is unresolved and receives no
prediction score; UNSAT excludes only the stated finite dictionary/cipher model.

The synthetic suite establishes useful small-fixture behavior, not solving
performance or prediction calibration at these full vocabulary sizes. Earlier
full-vocabulary synthetic recovery remained unresolved. This screen must not be
presented as a validated full-vocabulary language discriminator.

## Recorded outcome

| Folio | Dictionary/profile | H1 | H2 |
| --- | --- | --- | --- |
| f1v | Latin letters | UNKNOWN | UNKNOWN |
| f1v | Latin mixed | UNSAT | UNKNOWN |
| f1v | Swabian letters | UNSAT | UNKNOWN |
| f1v | Swabian mixed | UNSAT | UNSAT |
| f2r | Latin letters | UNSAT | UNKNOWN |
| f2r | Latin mixed | UNKNOWN | UNKNOWN |
| f2r | Swabian letters | UNKNOWN | UNKNOWN |
| f2r | Swabian mixed | UNKNOWN | UNKNOWN |

All eight fitted f2r structural-control arms are UNKNOWN. Totals: **five UNSAT,
nineteen UNKNOWN, zero SAT** across 24 checks. The remaining eight f1v control
arms are unavailable because construction failed; they are not solver outcomes.

No key was obtained, so no continuation was decoded or assigned a prediction
score. High continuation novelty makes the selected blocks suitable for that
question, but cannot resolve a missing fitted key. UNKNOWN does not mean poor
prediction, a rejected cipher hypothesis or a low language probability.

The five UNSAT results exclude only their precise dictionary, tokenization,
bounds and observation models on these training blocks. H1/H2 nesting is
consistent. Adding a mixed unit also changes the plaintext alphabet/codebook
capacity, so profile comparisons are not a pure nested H bound and should not
be collapsed into a blanket exclusion of German or Latin.

Checks total 111.14 solver seconds; formula construction adds 71.25 seconds.
Timeout checks are approximately five seconds; construction is not covered by
that timeout. No budget was enlarged or key repair performed. Independent
validation reproduces selection, novelty, controls and request identities and
confirms that non-SAT outcomes have no prediction scores; it does not rerun the
UNSAT proofs.

## Decision

Preserve these fresh blocks and checkpoints. The limitation is full-vocabulary
recovery performance, not a demonstrated inability to predict their continuations.
The synthetic calibration cannot yet be transferred to this scale. Before
interpreting a longer manuscript run, require a matched full-vocabulary positive
to yield a useful frozen key under the intended budget. Do not choose another
folio or language based on these timeouts, or count unavailable controls as
negative evidence.

## Reproduction and provenance

Implementation: `benchmarks/fresh_voynich_screen.py`.
Frozen selection, novelty metrics, vocabulary/rule identities, control audit,
complete requests/results and validation:
`experiments/results/fresh-voynich-screen/`.

```sh
.venv/bin/python -m benchmarks.fresh_voynich_screen
.venv/bin/python -m benchmarks.fresh_voynich_screen --run
.venv/bin/python -m pytest -q tests/integration/test_fresh_voynich_screen.py \
  tests/integration/test_structured_negative_controls.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/fresh-voynich-screen/validate.py
```

Preparation rejects corpus, template, inventory or code changes. Completed arms
are checkpointed and skipped on rerun; UNKNOWN outcomes are preserved. Interrupted
arms repeat from their start. Earlier selections and results remain unchanged.
Ten focused tests pass for folio/exclusion barriers, fixed novelty and dictionary
sizes, nested requests, matched control invariants and frozen prediction scoring.
