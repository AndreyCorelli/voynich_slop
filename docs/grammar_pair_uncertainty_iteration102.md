# Iteration 102: sentence-level uncertainty helps screening, but fails coverage

Sentence resampling identifies a small, cleaner repair subset. It does not meet the predeclared precision-and-coverage requirements, so both calibrated policies select OFF. Preserve the screening signal as a proposed modification; no new grammatical restoration or nucleus recovery is established.

## Frozen experiment

Use the frozen iteration-93 contextual classifier, joint pair masking and original minimum-five-occurrences/three-sentences eligibility. For each input block, draw 256 multinomial sentence-cluster resamples; use the same sentence multiplicities across all candidate pairs and corruption cases. Recompute occurrence-weighted endpoint probability means and pair gains from saved sentence totals. Eligibility is conditional on the original supported set: it is not rechecked inside each resample. A missing selected endpoint counts against stability, and ties do not count as wins.

Calibrate on all 603 iteration-98 source-calibration cases: the full 829 sentences and eight disjoint 100-sentence blocks, with all 64 synthetic cross-class swaps and three controls per block. The candidate pool has sixteen types, while 195 supplied anchors provide context. No lexical identities or annotations beyond the prior setup enter the predictor.

Primary policy: keep the original unique top pair only when gain and bootstrap top-rank frequency pass thresholds. Search all attainable nonnegative point-gain cutoffs and stability cutoffs 0.50/0.75/0.90/0.95/0.99/1.00. Secondary policy: threshold the fifth-percentile gain and require nonnegative fifth-percentile advantage over all other originally eligible pairs. The lower bound is the sorted-draw order statistic at floor(0.05 × 255), not a formal confidence interval for precision.

Keep iteration 98's guards unchanged: at least 90% empirical exact-pair precision in both full and sparse regimes; at least ten full and twenty pooled sparse calls; zero calls on clean/same-class controls; zero wrong repairs when the true partner is absent or unsupported. Choose maximum correct repairs, then fewer wrong repairs, higher gain cutoff and higher stability cutoff. Freeze policies before computing target-case features. Do not relax guards after seeing results.

## Calibration outcome

| Rule / diagnostic | Full correct / wrong | Sparse correct / wrong | Decision |
|---|---:|---:|---|
| Frozen iteration 95 gain cutoff | 50 / 0 | 96 / 172 | Baseline |
| Old cutoff plus 90% ranking stability | 24 / 0 | 11 / 0 | Descriptive screen; insufficient sparse coverage |
| Best worst-regime precision with required call counts, gain + stability | 19 / 0 | 31 / 8 | 79.49% sparse precision; fails |
| Largest zero-wrong lower-bound subset with ten full calls | 12 / 0 | 3 / 0 | Insufficient sparse coverage |

The descriptive 90% screen gives the same calibration decisions at gain cutoff zero and at the old 0.617467 cutoff. It is a transparent slice of the searched stability grid, not a newly selected operational policy. Its eleven sparse successes span correlated synthetic cases on reused blocks; zero observed wrong calls is not a precision guarantee. Recall is small: 11 of 512 sparse synthetic errors and 24 of 64 full errors.

Of 2,382 gain/stability policies, 606 meet call-count minima and none meets 90% precision in both regimes, even before clean/unavailable guards. The best worst-regime precision is 79.49%, versus iteration 98's 71.43% for gain/gap and 54.46% for gain alone under those minima. Seven of the eight remaining sparse errors in that descriptive best policy have unsupported true partners. This is an improved development tradeoff, not a qualifying policy. Of 186 lower-bound policies, none meets call-count minima. Both new policies and the old iteration-98 policies remain OFF.

## Existing source-test diagnostic

After freezing policies, compute the same uncertainty features for all 162 fixed-eight-core cases on the nine iteration-100 blocks. Both OFF policies abstain everywhere; the frozen iteration-95 baseline reproduces its prior recommendations. No new repair is applied to the PP model.

All eleven wrong recommendations in the designated bad 200-sentence merge have ranking stability between 0.4883 and 0.6953 and negative fifth-percentile rank advantages. Thus these particular mistakes are observably unstable, consistent with iteration 101's noisy-profile diagnosis. This does not establish target precision for a new rule: no target-selected threshold or descriptive 90%-screen target policy is adopted.

## Verification and next step

Replay all 765 bootstrap case matrices and selection summaries; recompute classifier probability totals for all 656 clean candidate pairs across calibration and evaluation blocks; verify all calibration references and point features against iteration 98; and refit both policies identically. Cross-process probability recomputation uses tolerance 1e-12 for floating-point summation differences (an initial exact-equality audit exposed differences around 1.8e-15). All 54 focused tests pass, including three new tests for weighted pooling, missing/tied bootstrap winners and stable systematic errors. No new annotations, author queries, reserve scoring or sealed lexical test access occurs.

Next test candidate-budget-matched calibration: restrict the cached calibration and bootstrap evidence to the already frozen eight-type core, retain all fifteen core error pairs and three controls, and repeat the same guards without lowering coverage requirements. This separates insufficient information from competition introduced by the sixteen-type pool. Candidate-core selection already used these calibration data, so success would still require separate confirmation; it must not be presented as an independent validation. Additional unlabeled author context remains a later route to increasing evidence without adding target annotations.

Artifacts and frozen design: `experiments/results/grammar-restoration/iteration102/`. Source: `src/voynich_smt/pair_uncertainty.py`; runner, audit and descriptive summary: `benchmarks/grammar_pair_uncertainty_iteration102*.py`.
