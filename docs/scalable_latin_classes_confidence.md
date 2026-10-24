# Learned Latin classes and independent confidence calibration

The aim remains a small reliable dictionary of frequent words, not a high language-
model score. This experiment uses no target topic, guessed translations, POS,
lemmas, handpicked function words or original sentence boundaries in inference.
Latin and the injective whole-word channel remain assumptions of the synthetic
benchmark. All original Caesar runs are preserved and reused for frozen evaluation.

## Source split and predeclared checks

The original 169,100-token non-Caesar training corpus and 2,557,237-form inventory
remain unchanged. The new held-outs are entire work IDs `phi0972.phi001` and
`phi0959.phi006` from the cached UD Perseus r2.17 test file. Neither work ID occurs
in the training source registry. They provide 4,857 tokens / 2,564 types for
development/calibration and 2,112 tokens / 1,496 types for reserved confirmation.
Both have zero exact normalized 12-word overlaps with training. The raw source
hash, explicit work selection, normalization and manifests are saved before runs.
They are short, discontinuously annotated work excerpts, not new 35k-token works.
Their shared source file does not mean their selected work IDs are the same.

The class model is fitted before either held-out fixture is prepared. The first
work supplies development gates and later confidence labels. The second is used
only for confirmation after freezing the confidence model. Caesar contributes
no fitting labels, model selection, thresholds or standardization statistics.
It is a previously inspected evaluation work, not a fresh blind test.

## Automatically learned classes

Source adjacent contexts around the 512 most frequent source forms produce a
sparse directional PPMI matrix. Rank-32 SVD embeddings, unit normalization and
weighted k-means produce 32 contextual classes. K-means weights are square roots
of source token counts; parameters and seed 23 are fixed before outcomes. These
are statistical word-type categories, not gold grammatical roles. No source POS,
lemmas or word spellings enter class learning. Unobserved forms get a separate
unknown class, retaining the full dictionary.

A normalized class bigram plus within-class word emission defines
`P(word | previous) = P(class(word) | class(previous)) * P(word | class(word))`.
Observed emissions follow source counts within their class; unobserved forms
share positive unknown-class mass. Source/base unigram probabilities match the
original word model. The full conditional distribution, including EOS, sums to
one. Class-aware retrieval includes per-class leaders so its single-context
queries remain exact; it does not filter the inventory.

A coarse class decoder is also implemented. Every cipher type has one class,
with source-vocabulary class capacities ensuring an injective word dictionary
can realize the assignments. Its score is the class Markov likelihood plus the
maximized per-class categorical cipher-word emission likelihood:

`S = class_sequence_log_probability + sum_type n log n - sum_class N log N`.

Moves update every affected occurrence and class token mass. Coarse assignments
can be lifted to distinct source words ranked within class before optional word
refinement. This prototype is tested numerically, but the real-text gate below
rejects it before any full Caesar class-decoding runs. Type-level contextual
classes do not establish context-dependent grammatical analyses.

### Development gate: rejected

On the development work, a reference mapping uses the source-learned class for
each known word and the unknown class for unsupported words. Higher is better:

| Coarse class control | Score |
|---|---:|
| Reference classes | -44,324.49 |
| Median of 10 corrupted references | -45,481.07 |
| Median of 10 shuffled streams | -44,540.98 |
| Median of 10 feasible random class assignments | -39,515.29 |
| Feasible collapse into class 25 | -43,596.56 |
| Collapse into unknown class | -57,125.60 |

All corrupted/random keys respect class capacities; shuffled streams preserve
word counts. Only capacity-feasible single-class collapses are considered. The
reference passes the predeclared corruption and median-shuffle checks but fails
the random and collapse checks. Passing a median-shuffle check does not mean
beating every shuffle. No costly coarse decipherment is run after this failure.

The normalized word-class model also fails its gate: its nearly correct feasible
reference scores -59,273.77, versus -37,580.52 for the wrong frequency-ranked key.
It beats the unobserved-form control (-93,989.35), but that alone is insufficient.
The 454 inventory-missing development types use distinct unobserved proxies only
for this evaluation reference; no forms are added or supplied to inference.

These failures reject this class/objective formulation on this development work.
They do not prove that contextual classes or Latin restoration are impossible.
Class uncertainty, unsupported forms, corpus mismatch and the fitted emission
objective remain possible contributors; they are not separated by this test.

## Confidence calibration attempt

Confidence is tested on the **unchanged original frequency-initialized decoder**,
not the rejected class model. Both independent work ciphers use seeds 3/5/7 and
4,000 proposals per chain, with the full original inventory/model. Their private
truth directories are unavailable during the real search. Features are extracted
from public outputs before truth is read.

Only strict-majority candidate mappings are eligible; this preserves injectivity
among the proposed partial mappings. Features are agreement fraction, relative
cipher frequency, relative frequency rank, change from supporters' initial keys,
archive stability, source unigram frequency, source/cipher frequency difference,
and contextual log likelihood/lift under supporters' complete keys. Word IDs,
word spellings, semantic labels and original boundaries are not classifier
features. Ties in the frequency-rank feature use arbitrary public cipher IDs;
this may add noise and is not a linguistic signal.

A logistic model with fixed L2 regularization 1 standardizes features using only
the calibration work. It fits 861 majority candidates, of which **only four are
correct**. No class balancing or truth-dependent threshold tuning changes the
natural type prevalence. The fitted model, scale, method signature and checksum
are saved before confirmation search/evaluation. The signature prevents applying
this calibrator to a changed source model/search configuration as if calibrated.

The fixed score thresholds are .5, .8 and .95. The primary high-trust validation
rule requires threshold .8 to select at least 20 confirmation types, with a
95% Wilson precision lower bound at least .8. This is a conservative experimental
gate, not a guarantee for a new language/cipher channel. Wilson intervals assume
independent observations; words and works can share errors, further limiting
interpretation.

### Results

| Dataset | Eligible majority types | Actually correct types in entire eligible pool | Top 50, usual vote/frequency rank | Top 50, fitted rank |
|---|---:|---:|---:|---:|
| Calibration work, in-sample | 861 | 4 | 2/50 | 4/50 |
| Reserved confirmation work | 385 | 3 | 2/50 | 3/50 |
| Caesar, frozen application | 3,375 | 4 | 3/50 | 3/50 |

Top-10 fitted precision is 3/10 on confirmation and 2/10 on Caesar. These are
word-type scores, not token accuracy. The top-50 Caesar result remains 6%.
With only four correct types in its current eligible pool, even an oracle could
obtain at most 4/50 in a fixed 50-entry list. Filtering cannot create additional
correct candidate hypotheses.

At the predeclared .5 score cutoff, both `et` and `in` are selected correctly on
all three works. In Caesar these cover **987/20,484 tokens (4.82%)** and exclude
the earlier wrong unanimous `non→de` and `a→quod` mappings. Their fitted scores
are .654 (`in`) and .544 (`et`), **not validated probabilities of correctness**.
Two correct types have a descriptive 95% Wilson interval of approximately
34.2%–100%; repeated recovery of the same two words across works does not provide
six independent word-type successes.

At .8 the confirmation work selects one correct mapping, `et`; its precision
interval is approximately 20.7%–100%. It fails both the minimum-support and lower-
bound requirements. The frozen .8 rule selects **zero Caesar mappings**. No .95
candidates are selected. Therefore **high trust is not validated**. The .5 result
is a useful observed filter, not a successful replacement of the primary rule.

Confirmation Brier score is .00349 versus .00774 for a constant predictor fixed
to calibration prevalence. Calibration Brier is .00188 versus .00462, and Caesar
Brier is .000882. Such aggregate scores are heavily affected by the abundance
of wrong types; they do not establish a usable 50-word nucleus or calibrated
high probabilities.

## Decision, implementation and limits

No algorithm defaults change. Preserve the normalized class model and coarse
prototype as experimental code, but reject this formulation at preflight.
Preserve the baseline confidence model as an exploratory ranking/filter with a
failed independent high-trust gate. Larger/more diverse independent calibration
and, more fundamentally, better candidate generation remain necessary before
claiming a substantial reliable dictionary. Confirmation is one short work;
transfer to Voynich is not established.

All **138 relevant tests pass**: class conditional normalization/full support,
unknown/no-unknown inventories, exact retrieval, full versus incremental word
and class-channel scores, capacity/injectivity, model serialization, checkpoint
continuation, public-only confidence extraction, method binding, identity-free
classifier inputs, empty selections and finite small-sample uncertainty.

The class resource build took 1.22 seconds. The six baseline search chains used
37.96 seconds for calibration and 18.44 seconds for confirmation, excluding
resource loading/feature extraction/evaluation. Class score gates prevented
unjustified longer decipherment runs. No dense cipher-by-million-form matrix
is constructed; profile/cluster vectors cover observed source forms only.

Reproduce in a fresh output directory/version:

```sh
.venv/bin/python -m benchmarks.scalable_latin_classes
.venv/bin/python -m benchmarks.scalable_latin_confidence
```

The current confidence driver explicitly requires the failed class gate so it
cannot silently pretend its baseline calibration applies to a new class method.
Original cached source files, contributor READMEs and licenses remain in place.
Outputs are under `experiments/results/scalable-latin-caesar/classes-confidence-v1/`:

- `design.json`, `resources/`, `gates.json`, `class-decision.json`: source model,
  class learning, score controls and rejected inference decision.
- `calibration/`, `confirmation/`: public fixtures and separate private truth /
  source-work/overlap provenance.
- `*-baseline/`: full inference, checkpoints, traces, literal/anchor evaluation,
  public numeric confidence features and private confidence evaluations.
- `calibrator.json`, `confirmation-decision.json`: frozen fit and validation failure.
- `caesar-confidence-public.json`, `caesar-confidence-predictions.json`: public-only
  application, saved before reading Caesar truth for evaluation.
- `caesar-confidence-evaluation.json`, `summary.json`: final results and limitations.
