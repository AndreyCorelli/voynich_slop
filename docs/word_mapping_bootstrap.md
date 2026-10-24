# Experimental bootstrap decoder

This implementation adds uncertain surface proposals, weak morphological
compatibility and coordinated dictionary moves. The motivation is the
[neighbor-quality diagnostic](word_mapping_context_rank.md): current neural
word proposals are poor when surrounding decoding is mostly wrong.

The implementation is in `src/voynich_smt/bootstrap_mapping.py`; the runner is
`benchmarks/word_mapping_bootstrap.py`. Legacy search/scoring files are unchanged,
so previously frozen experiments remain replayable. This is an experimental
search alternative, not a replacement default or a neural model fine-tune.

## Candidate uncertainty

For each ciphertext type, build a 32-form proposal shortlist by closeness
between its observed token frequency and smoothed training-form frequency, in
log space. Add every form assigned to that type in the retained dictionary
archive. Sample with soft weights combining frequency closeness and archive
support. This biases proposals without excluding any training form: the usual
full-vocabulary mutation operators retain nonzero probability.

Candidate-guided arms retain up to 30 dictionary hypotheses with a minimum
assignment distance of `max(2, floor(number_of_types / 10))`. Other arms use the
legacy minimum distance of one. Thus the candidate-guidance ablation includes
both shortlist proposals and the more diverse archive policy. Archive support
is exported as descriptive uncertainty, with no calibrated probability claims
and no hard assignment locks. The final dictionary still uses the best declared
objective, not majority voting.

## Weak compatibility factors

For each adjacent decoded pair inside a segment, average noun/modifier
compatibility over all unique morphology signatures. A signature retains POS,
case, number and gender; duplicate analyses do not change its weight. Noun
versus adjective/participle pairs contribute +1 for compatible known features
and -1 for a known disagreement. Other POS combinations and unavailable
analyses contribute zero. Unknown counterpart features provide no constraint;
common gender C matches masculine/feminine, but not neuter.

The average is a heuristic, not a parse or an analysis posterior. Adjacent words
need not be syntactically related, and ambiguity can dilute evidence. No surface
is rejected on morphological grounds. The objective adds a weighted sum of
these local factors to the existing fixed n-gram objective. The first diagnostic
uses weight 2.0, without claiming this weight is optimal. Transactional updates
rescore only affected factors and validate against full recomputation.

## Coordinated moves

Select an observed adjacent pair of different ciphertext types and propose
replacement forms for both. If either target form belongs to another type,
move that outside owner to a vacated old form. Up to four type assignments can
change together, preserving injectivity. This permits a compatible pair to
appear even when neither single replacement improves agreement. Existing
single replacements, owner swaps and morphology-based mutations remain
available.

The prototype uses simulated annealing as an optimizer; its asymmetric,
guided proposals are not posterior sampling. Every restart has a separate,
deterministic initialization stream, shared across arms, so frequency,
lemma-aware and random starting dictionaries are paired exactly despite later
proposal sequences diverging.

## Matched development experiment

Use the three separate long-context development bundles with the entire
12,327-form training catalog. Do not use the overlapping pooled bundle. For
each bundle and seed (101, 202), compare:

| Arm | Guided shortlist probability | Agreement weight | Joint move probability |
| --- | ---: | ---: | ---: |
| Baseline | 0 | 0 | 0 |
| Uncertain candidates | 0.6 | 0 | 0 |
| Agreement | 0 | 2.0 | 0 |
| Joint moves | 0 | 0 | 0.25 |
| Combined | 0.6 | 2.0 | 0.25 |

In the combined arm, joint moves are selected first. Of remaining proposals,
60% are shortlist replacements; the remainder use legacy operators. Joint
replacement forms independently use the same guided/unrestricted mixture.

Each run has three 20,000-mutation restarts (frequency, lemma-aware, random),
activates every ciphertext type and enforces injectivity. The 30 runs execute
90 restarts and 1,800,000 mutations. Equal mutation counts do not imply equal
compute; search seconds and operator statistics are recorded separately.

Truth is loaded only after all searches finish. Evaluate exact token/type
recovery, archive-oracle recovery, true versus winning objective/compatibility,
and whether archive-majority support predicts correctness. These metrics do
not enter optimization. Same-author development results do not establish
cross-author recovery; candidate screening and short text remain limitations.
The final test is neither optimized nor scored.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.word_mapping_bootstrap
.venv/bin/python -m benchmarks.word_mapping_bootstrap --validate
```

Use `--resume` for existing/interrupted outputs. Manifests freeze configuration,
source code, public fixtures, training resources and morphology. Every archived
objective is checked by independent full n-gram and agreement recomputation;
checkpoints restore exact proposal RNG state and descriptive hypotheses are
reconstructed. Completed checkpoints can regenerate missing derived exports.

Outputs live in `experiments/results/word-mapping/bootstrap-calibration/`.
Tests cover ambiguity, missing analyses, common gender, segment boundaries,
local multi-type scoring, stale transactions, injective joint completion,
paired restart starts, exact checkpoint replay, truth-free search, ablations,
protocol rejection, tamper detection and missing-export recovery.

## First ablation results

All 30 runs and 1.8 million mutations completed. Mean exact token accuracy
across the six paired bundle/seed runs:

| Arm | Selected dictionary recovery | Archive-oracle recovery | Improved / worsened versus baseline |
| --- | ---: | ---: | ---: |
| Baseline | 2.312% | 2.378% | — |
| Uncertain candidates | 1.221% | 3.195% | 2 / 3 |
| Agreement | 1.188% | 1.188% | 0 / 3 |
| Joint moves | 2.093% | 2.093% | 1 / 2 |
| Combined | 1.969% | 3.100% | 2 / 4 |

Search calls recorded approximately 129.2 seconds total, excluding resource
loading, proposal-shortlist construction, evaluation and validation. Candidate
guidance improves the archive's best available recovery, but the declared
objective does not select those candidates. No new arm improves average selected
recovery over the matched baseline.

The signed-average agreement score has a specific weakness: real Latin pairs
with ambiguous case readings receive disagreement penalties even when a
compatible reading exists. Mean true-text agreement across the bundles is
-20.45, whereas agreement-only winners achieve +4.56 despite worse recovery.
Thus increasing this compatibility score is not equivalent to improving Latin
decoding. Arbitrary adjacency and independent feature readings remain weak
syntactic assumptions.

Archive agreement is also unreliable: among baseline type assignments with
at least 90% archive-majority support, only 11 of 1,421 are correct (0.77%).
Agreement-only gives 4 of 1,291 (0.31%). These are descriptive, correlated archive
observations, not independent probability estimates. Candidate-guided archives
are more diverse and have almost no assignments in that support range. The
results do not support freezing assignments based on archive support.

All first-stage checkpoints, archived objectives, hypothesis exports and
reconstructed recovery reports validate independently.

## Ambiguity marginalization follow-up

A separate implementation, `src/voynich_smt/bootstrap_marginal.py`, retains the
first-stage code/results unchanged. For each local pair, replace the signed
average with:

```text
marginal_pair = log(mean(exp(2 * compatibility_of_each_analysis_pair))) / 2
objective = ngram_log_likelihood + 2 * sum(marginal_pair)
```

The normalized log-sum-exp gives compatible readings more weight while
preserving incompatible and neutral alternatives. It avoids treating every
alternative case reading as equally strong negative evidence. The reduction
is computed stably and remains bounded between -1 and +1. It still marginalizes
each adjacent factor separately, not a consistent parse across the sentence;
it can still favor inappropriate adjacency or excessive ambiguity.

The follow-up repeats baseline, agreement-only and combined arms with the
same cases, seeds, starts and mutation budget: 18 runs, 54 restarts and
1,080,000 mutations. Both stages together execute 2,880,000 mutations.

```sh
.venv/bin/python -m benchmarks.word_mapping_bootstrap_marginal
.venv/bin/python -m benchmarks.word_mapping_bootstrap_marginal --validate
```

Follow-up outputs are in
`experiments/results/word-mapping/bootstrap-marginal-calibration/`.

Follow-up means across six paired runs:

| Arm | Selected recovery | Archive oracle | Improved / worsened versus baseline |
| --- | ---: | ---: | ---: |
| Baseline replay | 2.312% | 2.378% | — |
| Marginal agreement | 1.909% | 1.909% | 1 / 3 |
| Marginal combined | 2.340% | 3.831% | 3 / 2 |

All six baseline archives are identical to the first-stage baseline archives.
The marginal combined mean exceeds baseline by only **0.028 percentage points**,
with three paired wins, two losses and one tie. Exact type accuracy decreases
from 0.798% to 0.661%. This is not a convincing recovery improvement. Search
calls recorded about 78.5 seconds for the follow-up.

Marginalization reduces the true text's ambiguity penalty (mean compatibility
-5.48 versus -20.45 under signed averaging), but winning marginal-agreement
mappings still score +20.03 while recovering fewer words. Improving this local
heuristic does not establish coherent Latin. Better agreement relations or a
contextual analysis model would be needed before claiming a grammatical score.

The strongest useful change is retaining more diverse hypotheses: the marginal
combined archive contains dictionaries averaging 3.831% oracle recovery versus
2.378% for the baseline archive. Selection and overall candidate quality still
limit recovery. No assignment locks or neural-guided search are enabled, and
the existing default annealer remains unchanged.

The implementation and negative/mixed calibration results are reviewable;
these results do not pass the recovery gate or justify manuscript interpretation
or a larger run of the same scoring objective.

Both stages validate independently: 48 search checkpoints, 144 restarts and
2,880,000 mutations, with all archived objectives, hypothesis exports and
reconstructed evaluations checked. All 137 focused tests pass. The final test
remains untouched.
