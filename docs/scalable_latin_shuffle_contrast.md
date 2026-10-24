# Latin objective diagnosis: frequency-matched ordering contrast

This experiment investigates why wrong frequency-ranked dictionaries beat nearly
correct Latin references under the larger-corpus word model. It uses the frozen
5,935,259-token corpus and 2,666,235-form inventory from the
[larger-corpus/morphology experiment](scalable_latin_corpus_morphology.md).
Neither topic, hidden vocabulary, original sentence boundaries nor guessed anchor
translations enter inference. Latin and injective whole-word substitution remain
benchmark assumptions. No Voynich restoration is performed.

## What the decomposition establishes

For a complete candidate decoding, split the old score into

`LM score = sum_tokens log q(decoded_word) + residual`,

where q is its existing full-inventory source unigram distribution. The residual
contains the remaining context and endpoint terms; it is not a semantic score.
On all three development works, the frequency key wins overall even though the
feasible reference has the better residual:

| Development work | Wrong key's unigram advantage | Reference's residual advantage | Reference minus wrong key, original score |
|---|---:|---:|---:|
| Apuleius I | 10,351.79 | 2,505.07 | -7,846.72 |
| Curtius III | 13,117.93 | 5,775.58 | -7,342.35 |
| Suetonius, Augustus | 21,442.63 | 11,971.13 | -9,471.50 |

This is direct evidence of a frequency-driven reversal in these comparisons.
It does not prove that frequency pressure explains all Latin recovery failures,
or that subtracting the frequency term alone will yield correct translations.
Unlike a complete true plaintext, the feasible references replace inventory-missing
forms with distinct training-unobserved proxies. Their token coverage is 94.25%,
98.19% and 97.13%; those proxy penalties remain an interpretation limit.

## Revised ordering objective

For a fixed candidate dictionary, compare the decoded text with eight fixed
random permutations of that same decoded sequence:

`C(key) = LL(decoded) - mean_k LL(shuffle_k(decoded))`.

Each permutation keeps the first and last token fixed and shuffles only interior
positions. It preserves every word count and every incoming/outgoing word margin,
so all unigram, row-backoff, BOS and EOS contributions cancel exactly. There are
no inferred sentence boundaries. Shuffles depend on positions and document
length, never on plaintext identities, cipher names, truth or a candidate key.
Each actual document gets its own contrast; arbitrary score chunks never reset it.

For the source absolute-discount bigram, use signed public edge multiplicities
`K * observed_count - sum_k shuffled_count`. The exactly equivalent pair value is

`log1p(max(source_edge_count - discount, 0) /
        (discount * source_distinct_successors * q(next_word)))`.

Only observed source edges have a nonzero value. The zero signed row and column
margins justify cancellation of the remaining terms. This implementation avoids
subtracting two large nearly equal language-model scores and gives an entirely
training-unobserved key exactly zero, rather than rewarding an unsupported match.
This is an **unnormalized ordering contrast**, not conditional text likelihood,
a calibrated probability, an exact permutation partition function, or proof of
linguistic validity.

Primary bank seed 2701 and check bank seed 9901, eight permutations each, are
fixed before development outcomes. The second bank tests sensitivity to sampled
null edges; it is not an independent author or a held-out language model.

## Development gates and bounded regularization follow-up

Both fixed banks pass all checks on all three works: positive reference contrast,
reference above frequency and null keys, above median of three random injective
keys, and above median corruptions at 10%, 25% and 50% of word types.

| Work | Feasible reference contrast | Frequency-key contrast |
|---|---:|---:|
| Apuleius I | 2,383.77 | 53.93 |
| Curtius III | 5,800.88 | 231.14 |
| Suetonius, Augustus | 11,835.43 | 401.36 |

These are seed-2701 scores; the alternate bank gives the same gate decisions.
Passing these controls is a prerequisite for decoding, not evidence that the
optimizer will find the reference or that the reference is its global optimum.

A matched 500-proposal development smoke on Apuleius, frequency initialization,
seed 3, gave 7.82% literal token recovery for the original surface score versus
2.42% for pure contrast. Because removing all frequency pressure also removes
useful lexical evidence, a separately recorded exploratory follow-up adds

`S_gamma(key) = C(key) + gamma * sum_tokens log q(decoded_word)`.

The development-only grid is gamma 0, .1, .25 and .5. Select the largest weight
that passes reference discrimination on at least two of three works under both
banks, retaining the positive *ordering-component* check. A total regularized
score need not be positive. The selected gamma is **.25**: it passes Curtius and
Suetonius, while .1 passes all three and .5 fails promotion. This is a follow-up
to the observed development smoke, not a wholly predeclared independent study.
The selection is saved before validation recovery is read. No Gellius or Caesar
recovery result chooses the weight.

The same 500-proposal smoke with gamma .25 gives 7.17% recovery. All smoke runs
are retained; the favorable-seeming partial recovery is not treated as a success.
No further gamma tuning is performed on validation.

## Inference and evaluation protocol

Compare original surface, pure contrast and gamma-.25 contrast on the reserved
Gellius I stream: 9,670 tokens, word order and word boundaries only. Use three
seeds 3/5/7, frequency initialization, 4,000 proposals, the same sparse budgets,
full inventory and original annealing settings. The 600-second per-chain budget
is configurable; completed proposal caps are reported. Identical initial keys
and matching protocols are checked explicitly, apart from objective identity and
scope. Source-count frequency starts share a dictionary, so unanimous agreement
can reflect shared errors. These are not independent random-start confirmations.

Contrast retrieval ranks observed context candidates by the source edge bonus,
while baseline retrieval keeps its original conditional-probability ranking.
All candidate moves receive the exact full dictionary score across actual and
null edges, including displaced owners. Full-inventory random exploration remains
positive; no guessed vocabulary or type is removed. Thus this comparison includes
objective-appropriate retrieval, not just replacing the acceptance score while
keeping a demonstrably mismatched context ranking.

Public cipher inputs and private evaluation material are separate. Each trial
now gets its own fixture copy; private truth is unavailable at its standard path
during inference. An initial parallel evaluation collided with another trial's
private-directory rename. The already completed baseline searches were preserved
and re-evaluated after isolating trial fixtures; no failed seed was discarded or
restarted. A regression test covers this isolation. The solver's input remains
public-only, and source/fixture identities are retained.

All selected/current/archive keys undergo independent occurrence-level full
rescoring and checkpoint validation. Report literal token recovery, agreement-
first top10/20/50 exact word-type precision, unanimous-three-run/public-count>=100
anchors, majority-pool correctness and the alternate null-bank ordering score.
No old confidence calibrator applies, and grammar/meaning are not inferred from
literal scores. Fixed 100-token original/restored excerpts are saved at the start
and midpoint, without choosing favorable passages after recovery.

The validation reference itself passes the basic discrimination comparison:
original LM reference -91,018.47 versus frequency -83,291.22; pure contrast
reference 8,896.45 versus frequency 303.67; gamma-.25 reference -13,975.79 versus
frequency -18,481.46. This still does not establish search quality: optimized
wrong keys can outscore these references.

## Validation results

All nine validation chains complete their 4,000-proposal caps. Search protocols
match and initial complete dictionaries are identical across methods for each
seed. The full numerical comparison and checks are in `summary.json`.

| Objective | Seed 3 | Seed 5 | Seed 7 | Mean literal tokens | Score-selected run | Correct / top 50 |
|---|---:|---:|---:|---:|---:|---:|
| Original surface | 7.78% | 6.88% | 6.70% | **7.12%** | 6.88% | **3/50** |
| Pure ordering contrast | 3.57% | 5.77% | 6.74% | 5.36% | 6.74% | 1/50 |
| Contrast + .25 unigram weight | 6.04% | 4.83% | 8.24% | 6.37% | **8.24%** | 2/50 |

The regularized score-selected key improves by 1.37 percentage points, but its
mean regresses by .75 points and top-50 exact precision falls. Pure contrast's
mean falls by 1.76 points. No best seed is chosen using truth: the displayed
selected runs are chosen by each method's own objective. A favorable selected
key is insufficient evidence of a robust improvement across restarts or works.

The primary frequent unanimous mapping set changes as follows:

| Objective | Correct / selected types | Correct token coverage | Wrong mappings |
|---|---:|---:|---|
| Original surface | 2/5 | 508/9,670 = 5.25% | est→non, non→est, quod→ut |
| Pure contrast | 1/1 | 277/9,670 = 2.86% | None selected |
| Regularized contrast | 1/1 | 277/9,670 = 2.86% | None selected |

The surviving mapping is `et→et`; the baseline also recovers `in→in`. This is a
cleaner but smaller observed nucleus, not validated high confidence: one correct
type on one work cannot establish a reliable error rate. The entire eligible
majority pools contain 6/2,176 correct types for baseline, 2/2,426 for pure
contrast and 6/2,486 for regularized contrast. Ranking alone still cannot create
a reliable 50-word dictionary from these hypotheses.

Optimized wrong keys also score well on the alternate bank. Their pure ordering
scores there range from 16,810 to 17,466 for contrast variants, above the feasible
reference's 8,884. Thus success on the simple reference-versus-frequency gate
does not ensure that more general incorrect dictionaries are disfavored. The
second-bank results make exploitation of only the primary sampled shuffle edges
an insufficient explanation; they do not isolate all remaining failure causes.

**Decision:** preserve the objective and diagnostics as experimental options;
change no defaults. This identifies an actual frequency-driven reversal and fixes
that comparison, but does not establish an overall recovery improvement. The
reference gate is necessary screening rather than a sufficient validity test.
Longer-range constraints, a better model of lexical identity, candidate/search
limitations and other objective formulations remain open. The earlier class and
association failures are not silently reclassified as successful.

Search times total 162.15 seconds for baseline, 508.99 for pure contrast and
577.69 for regularized contrast; smoke runs add about 41 seconds. These exclude
resource loading and external evaluation. Independent processes overlapped, so
their sum is not elapsed wall time or a controlled speed benchmark. Peak process
RSS ranges approximately 1.79–2.24 GB. Signed null edges make contrast about three
times as expensive per completed chain. Comparisons match proposal caps, not
actual compute time; no additional equal-time sweep is justified by this result.

Validation is one author/work, shorter than the target manuscript scale. There
is no sealed-test or Caesar recovery evaluation, no semantic recovery claim,
and no claim that the new baseline percentage is comparable to historical Caesar
results on different text.

## Implementation and reproduction

New `scalable/shuffle_contrast.py` implements identity-independent permutation
banks, signed counts, exact pair values, optional unigram regularization and
serialization. `incremental.py` adds a signed graph event path; event indexes
bind the complete contrast objective identity, including bank and regularizer.
The common loader and public runner recognize the objective explicitly as an
unnormalized heuristic. Ordinary bigram, trigram, class, factor and association
paths retain their defaults.

Tests compare the optimized formula to direct original-LM-minus-shuffle scoring,
verify zero signed margins and symbol-renaming invariance, check singleton and
multiple documents, enumerate tiny injective keys and all replacement/swap/cycle
deltas, and check serialization, bank mismatch rejection, exact checkpoint
continuation, regularized deltas and public-only end-to-end inference.
All **154 relevant tests pass**. Every real saved key/archive also passes the
independent full-score and checkpoint checks.

The driver is `benchmarks/scalable_latin_shuffle_contrast.py`, with stages
`screen`, `smoke`, `validation`, `regularize` and `summarize`. Run those stages
sequentially in the order `screen`, `smoke`, `regularize`, `validation`, `summarize`,
passing the same new `--output` root to each. Screening requires exclusive new
output. `regularization-design.json` records the follow-up grid before its runs;
the driver creates the fixed follow-up protocol automatically in a fresh
reproduction. Completed validation inference is reused for evaluation without
rerunning searches. Artifacts are under
`experiments/results/scalable-latin-shuffle-contrast/v1/`:

- `design.json`, `development.json`, `decision.json`: decomposition, controls,
  fixed banks and initial promotion decision.
- `regularization-design.json`, `regularization-selection.json`: exploratory
  development-only weight choice and all rejected weights.
- `resources/`, `resources-regularized/`: parent counts and objective metadata.
- `fixtures/`, `isolated-fixtures/`: public ciphers and separate private evaluation.
- `smoke-*`, `validation-*`: protocols, traces, checkpoints, original/restored
  excerpts, numerical validation and literal/anchor evaluations.
- `smoke.json`, `validation-comparison.json`, `regularized-comparison.json`,
  `summary.json`: complete retained comparisons.
