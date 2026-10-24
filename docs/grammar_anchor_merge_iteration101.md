# Iteration 101: why the short-block merge fails

The bad 200-sentence merge fails because count eligibility admits a misleading competitor profile. Merging does not alter any occurrence's features or class probabilities. This is a diagnostic of the frozen repair system, not a new restoration gain or an adopted repair policy.

## Frozen setup

Keep iteration 93's classifier, iteration 95's joint masking and gain cutoff (0.6174674057358475), and iteration 99's eight candidates. All 195 supplied context anchors remain available; opaque content identities supply no lexical features. Evaluate both 200-sentence merges, their four 100-sentence parents, and the existing 400/700/770 blocks. Each block has 15 synthetic cross-class swaps and three controls. No new annotations, reserve scoring, lexical search, PP integration, or threshold selection occurs. These source-test blocks are reused development data.

## Eligibility versus evidence

For both merges, the left parent's count-eligible set excludes `a`, the right parent's excludes `ex`, the intersection excludes both, and the union includes all eight. The following counterfactuals keep the merged probability evidence fixed and vary only eligibility. Cells are correct / wrong / abstained repairs across all 15 errors.

| Merged evidence | Left eligibility | Right eligibility | Intersection | Union (actual) |
|---|---|---|---|---|
| Bad merge 200-0 | 0 / 8 / 7 | 11 / 0 / 4 | 8 / 0 / 7 | 0 / 11 / 4 |
| Other merge 200-1 | 7 / 1 / 7 | 7 / 1 / 7 | 5 / 2 / 8 | 9 / 0 / 6 |

The misleading profile already exists in parent 100-1: forcing union eligibility changes its actual 10 correct / 1 wrong to 0 correct / 13 wrong. Four `ex` occurrences fail the minimum-five count gate there; merging supplies nine occurrences and admits the distractor. Eligibility counterfactuals override that gate for diagnosis only and never fabricate absent types. The artifacts also retain the common-endpoint stratum, because excluding a true partner can itself produce a wrong substitute. Choosing the right parent's set after observing results is not a valid policy; always taking the intersection also fails in the other merge.

## What the classifier sees

On clean input with `ex` and `et` jointly masked, mean P(CCONJ) for the source-modal ADP type `ex` is 0.4192 in 100-0 (five occurrences), 0.6738 in 100-1 (four), and 0.5323 after occurrence-weighted pooling. The other merge has seven occurrences but mean 0.3343. Thus count alone does not measure class reliability. The other two conjunction masks show the same direction; all masks and occurrences are retained in the traces.

One contributing cue is the preceding sentence boundary: its CCONJ-minus-ADP logit coefficient is approximately +1.28449, active in one of five occurrences in the first parent versus three of four in the second. Other contextual cues contribute too. These are exact per-occurrence logit contributions, not an additive decomposition of the nonlinear pooled gain; no boundary ablation or word-specific exception was tested.

A second issue is pair-dependent masking. In `swap_ad__et`, the true pair scores 0.777984 but the wrong `ad/ex` pair scores 0.827407. Of the 0.049423 advantage, 0.039565 comes from changing the shared endpoint's evidence under a different partner mask, and 0.009858 from replacing the partner. Partner-profile bias dominates most other wrong cases. This does not establish that independent masking is preferable: earlier independent controls also made errors.

Equal weighting of the two parents' nonempty type profiles is not a fix: the bad merge remains 0 / 11 / 4, while the good merge worsens from 9 / 0 / 6 to 6 / 2 / 7.

## Verification and next experiment

The audit replays all 162 trace cases, 108 factorial cases and 36 equal-parent cases; reconstructs 4,860 pooled endpoints; verifies 4,920 unchanged occurrence-feature/probability comparisons; and checks 9,032 prior input hashes. The focused suite passes 112 tests. An initial input-filter error aborted before factorial results or traces; its code and failure record are preserved in `iteration101-attempt0`, and the corrected run has its own frozen design.

Next test sentence-resampling uncertainty of relative pair evidence and ranking, preserving within-sentence dependence. Calibrate solely on source calibration corruption cases and sparse blocks, comparing against frozen count/gain/gap baselines with precision, coverage and clean-input guards. Do not select a threshold on this failing example or blacklist `ex`. Resampling may expose instability but cannot guarantee correction of systematic bias; an OFF policy remains a valid outcome. Pair-dependent masking merits a separate shared-evidence diagnostic if needed.

Artifacts: `experiments/results/grammar-restoration/iteration101/` contains the frozen design and tracker snapshot, full traces, factorial summaries, equal-parent control, exact gain decomposition, and replay audits. Earlier conditional grammatical restoration findings remain preserved; this iteration adds no recovered nuclei or demonstrated improvement in grammatical restoration.
