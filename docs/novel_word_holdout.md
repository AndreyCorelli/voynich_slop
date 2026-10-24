# Novel-word H1/H2 prediction comparison

The preceding model comparison included many repeated ciphertext words. This
fixed fixture comparison makes **every continuation word novel**, in both
expanded plaintext spelling and ciphertext, while ensuring all its generating
codewords have been observed in training.

## Construction and fixed scope

Use the unchanged twelve-word Latin/Swabian reference vocabularies and the
letter/mixed contraction profiles. Select the first lexicographic three-type
subset whose units are covered by the remaining types under both shortest
letter and mixed tokenizations. Training uses each remaining type twice;
continuation uses each reserved type once. Reference unigram frequency orders
the selected types, with lexical tie-breaking. This ordering does not guide
recovery or select witnesses.

| Language | Training types | Reserved continuation types |
| --- | --- | --- |
| Latin | et, ad, cum, se, non, qui, ut, ex, ab | in, a, eo |
| Swabian | und, sie, ich, er, nit, in, als, du, ist | das, die, der |

Each fixture has eighteen training words and three distinct continuation words.
Held-out spellings remain in the solver's dictionary: this is withheld evidence,
not out-of-dictionary recognition. No generating continuation type occurs in
training. Prefix-free generation also guarantees no held ciphertext word equals
a training ciphertext word, independently checked in every case.

This is an **engineered vocabulary fixture**, not a contiguous passage or blind
natural-language evaluation. Word types are reserved specifically to permit
code coverage. It tests compositional generalization to new words within the
small closed dictionary, not grammar, historical language identification or
manuscript decipherment.

Preparation initially attempted four reserved types. Exhaustive subset checking
found no jointly covered Latin subset under both profiles before any fits ran.
That failed protocol is preserved in `preflight-four-types.json`; three types
are used consistently for both languages. No solver or continuation result
informed this adjustment, and no vocabulary, rule or seed was broadened.

For each language and profile, generate H1 and H2 ciphertexts using seed 2121,
length-two prefix-free codes over six glyphs. H1 training choices are all zero;
H2 choices alternate per unit. Two training occurrences of every training type
guarantee both generating homophones for units in continuation. Continuation
choices use seed 2222. All eight true keys decode every held word perfectly.

Each positive is fitted once under H1 and once under H2, keeping dictionary,
alphabets and observations fixed. Recovery permits code lengths 1–3, observed
codeword domains and free selection. Sixteen ordinary fits receive five seconds
each, with no enumeration, statistical guidance or budget escalation. Returned
keys are frozen before scoring; failed/non-SAT fits are not assigned zero scores.

Both mixed rules are whole-word units (`et`/`in`). Reserving the contracted word
would introduce a unit unavailable from any other spelling, violating coverage.
The selected mixed holdouts therefore exercise training contraction but contain
no contracted units themselves. This does not test extrapolating a contraction
to an unseen spelling containing that unit. Such a test would need a different,
predefined within-word inventory and adequate vocabulary, not an ad hoc addition
here.

## Recorded novel-word results

Every numeric score below counts exact generating words, all absent from
training. There is no repetition contribution.

| Generating positive | H1 recovery | H2 recovery |
| --- | --- | --- |
| Latin letters H1 | 3/3 | 1/3 |
| Latin mixed H1 | 3/3 | 0/3 |
| Swabian letters H1 | 3/3 | 2/3 |
| Swabian mixed H1 | 2/3 | 2/3 |
| Latin letters H2 | UNSAT | 2/3 |
| Latin mixed H2 | UNSAT | 3/3 |
| Swabian letters H2 | UNSAT | 3/3 |
| Swabian mixed H2 | UNSAT | 3/3 |

All own-model positives fit, and the nested-model checks are consistent.
Twelve SAT witnesses independently reproduce training and satisfy their models.
Four H1 fits on H2-generated fixtures are UNSAT. No timeout; sixteen fits take
15.92 solver seconds combined, individually 0.20–3.28 seconds.

For H1 positives, the simpler model equals or exceeds the broader model's first
witness in each case. H2 remains necessary to fit the H2 positives. This reveals
a generalization cost of extra flexibility in these fixed examples, rather
than implying every H2 witness is worse or H1 is universally the right model.
The broader model contains the true H1 key; its poor first-witness score reflects
ambiguous fitting and witness selection, not absence of a useful solution.

The Latin mixed H1 positive's H2 witness cannot fully decode any novel held
word, despite complete generating-code coverage. Other fits recover all or some
novel words. Coverage is a prerequisite for this diagnostic, not a guarantee
that recovery assigns the correct ownership or segmentation. Candidate sampling
is not uniform; these are one-key, one-seed examples and no significance or
probability estimate is made. Dictionary-hit counts happen to equal exact
counts in this run, but they are retained separately in the reports.

## Artifacts and validation

Implementation: `benchmarks/novel_word_holdout.py`.
Protocol, type selection, identities, complete requests/truth, frozen recovered
keys, predictions and validation: `experiments/results/novel-word-holdout/`.
Earlier comparison artifacts remain unchanged. Preparation rejects reference,
inventory or code changes; completed arms are skipped on rerun.

Ten focused tests pass, including deterministic coverage-constrained selection,
rejection of impossible splits, disjoint expanded/ciphertext words, true-code
coverage, own-model certificates and nested request identity. Independent
validation recomputes generating encoding/decoding, coverage, novelty, all SAT
fits and frozen predictions without additional solves.

```sh
.venv/bin/python -m benchmarks.novel_word_holdout --run
.venv/bin/python -m pytest -q tests/integration/test_novel_word_holdout.py \
  tests/integration/test_single_code_baseline.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/novel-word-holdout/validate.py
```

## Decision

Keep the simplest sufficient model as the baseline, requiring novel-word
prediction evidence before accepting a more flexible explanation. Retain H2
as a challenger because it is required by its own positives. The calibrated
suite now checks coverage, repeats, novel words and structured corruptions.
Before larger searches, freeze it as a model-selection gate; neither a language
preference nor another solver-budget increase follows from these fixtures.
