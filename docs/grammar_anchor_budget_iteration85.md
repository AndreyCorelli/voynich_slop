# Anchor-budget curve and conservative calibration — iteration 85

**A smaller supplied-anchor set retains useful partial grammatical signal, but high-precision support remains limited.** With 20 supplied preposition/conjunction anchors, the source-calibrated empirical policy returns **191 correct PP-governed memberships and 19 wrong: 90.95% precision, 24.58% recall**. Every selected position has a hidden form. This is conditional on correct supplied anchors, not discovery of their mappings.

At the 195-anchor upper setting, a stricter source-calibration diagnostic returns **357 correct and 33 wrong: 91.54% precision, 45.95% recall**. It qualifies at no smaller budget. Its binomial assumptions are not established for correlated tokens or author transfer, so this is observed development performance, not a guaranteed precision level.

## Entire frozen curve

All anchor lists use source-fit information only. Rank forms by source-fit frequency, with lexical ties. The small-budget pool contains the 41 forms whose source-modal tag is ADP/CCONJ/SCONJ and whose frequency is at least five. Budgets 0/5/10/20/41 were declared before evaluation. The 195-anchor reference additionally includes the other function categories of iteration84.

| Supplied anchors | Visible test tokens | Learned PP F1 | Nearest-left F1 | Empirical selective precision / recall | Conservative policy |
|---|---:|---:|---:|---:|---|
| 0 | 0.00% | 16.17% | 14.48% | No qualifying source policy | None |
| 5 | 8.38% | 46.95% | 44.07% | No qualifying source policy | None |
| 10 | 12.89% | 60.52% | 59.05% | 88.24% / 19.31% (150/20) | None |
| 20 | 15.21% | 65.41% | 65.21% | **90.95% / 24.58% (191/19)** | None |
| All 41 prepositions/conjunctions | 16.20% | 68.88% | **69.03%** | 89.45% / 31.66% (246/29) | None |
| 195 function anchors | 33.42% | **73.68%** | 69.03% | 86.89% / 59.72% (464/70) | **91.54% / 45.95% (357/33)** |

Counts in parentheses are correct/wrong. Every budget is reported; no best target budget or threshold is selected. The nearest-left controls have no qualifying selective source policy at any budget. The learned model does not beat proximity at every budget: at 41 anchors it is slightly worse, and at 20 its F1 advantage is only 0.20 percentage points. Most broad classification benefit there is already available from proximity.

The first five source-ranked anchors are `et, in, ut, ad, cum`; the ten-anchor list adds `de, que, sed, si, a`. The exact 20-anchor source-defined list is:

`et, in, ut, ad, cum, de, que, sed, si, a, aut, ex, c, atque, uel, ac, ab, per, nisi, sine`.

Tags are source-modal, not reference token tags; for example `cum` is supplied as SCONJ. Corpus-normalized forms such as `c` are retained as selected, without word-specific corrections. Full lists and tags are frozen in `anchor-budgets.json`.

## Opaque-input and split controls

Use the same source49 fit/calibration/test splits and all stored positions as84: 31,884/10,917/9,956 tokens, with 777 test positives. Hidden forms retain equality only; dictionary/POS/suffix/length/finite lookups remain forbidden. Sentence boundaries and the chosen exact function-anchor identities/source-modal tags are supplied. The task is governed-node membership under the fixed case-linked ADP/inheritance rule, not a full phrase span, attachment or Case-value reconstruction.

For each new budget, train the same three context-POS probes and three PP/head-category probes. Pool fit probabilities strictly within each held-out POS fold, preserving84's corrected cross-fitting. Cal/test pooling uses its own split. Parameters, features and hyperparameters are not tuned across budgets. The 195-anchor models are reused unchanged from84's strict control; it is an upper reference, not a fresh fit.

**All budgets' models and calibration policies are frozen before any new test predictions.** Source calibration alone selects the F1 and empirical precision90 thresholds under the existing grid/support rule. These remain reused development data, and the 195-anchor F1/empirical-policy outcomes were already known from84; no independent-confirmation claim is made.

## Conservative precision diagnostic

For every fixed threshold in the 101-point grid, compute a one-sided Clopper–Pearson lower bound on source-calibration precision using alpha=0.05/101. Require the lower bound to be at least 0.90, at least 20 predictions and ten word types. Select the qualifying threshold with the most source true positives, with fixed tie rules. The adjustment is per arm/budget across its threshold grid, not a simultaneous guarantee across every model or budget.

Only the 195-anchor learned model qualifies. Threshold **0.80** has source-calibration 463 correct/28 wrong (94.30% empirical precision), with lower bound 90.03%, across 302 types. The held-out 357/33 result improves precision over the empirical90 policy's 464/70, with reduced recall: 59.72%→45.95%.

The interval calculation treats selected token outcomes as binomial trials; repeated words/sentences are correlated and source/test distributions can differ. Therefore it is a conservative **diagnostic criterion**, not a formal transfer guarantee. No qualifying policy means insufficient support under this criterion, not proof that precision90 is impossible.

## Hidden forms and author scope

For the 20-anchor empirical policy, all 210 selected positions are hidden forms; hidden-form recall is 24.61% (the all-token denominator gives 24.58%). Source calibration at threshold0.81 had 236 correct/26 wrong (90.08% precision;179 types), then test191/19. Thus the threshold was not chosen to produce the observed test90.95%.

For the 195-anchor conservative policy, hidden forms alone give **267 correct/31 wrong: 89.60% precision, 44.43% recall**. Its aggregate91.54% also benefits from easier visible-anchor positions. Do not describe it as90%precision on hidden forms.

| Frozen policy | Cicero correct / wrong | Cicero precision | Palladius correct / wrong | Palladius precision |
|---|---:|---:|---:|---:|
| 20 anchors, empirical source policy | 188 / 18 | 91.26% | 3 / 1 | 75.00% |
| 195 anchors, conservative source policy | 350 / 32 | 91.62% | 7 / 1 | 87.50% |

Cicero dominates (9,573 test tokens versus383 Palladius). Palladius selections are tiny and do not establish robust precision transfer. Neither policy is adopted as a general parser.

## Decision and next work

Preserve both conditional findings: a few dozen correct supplied function mappings can support selective grammatical labels on opaque forms, and stricter source calibration can trade coverage for better observed precision. Preserve the strong proximity control, missing conservative support at small budgets and author/hidden-form failures alongside them.

Before further tuning on this source split, freeze the 20-anchor empirical and 195-anchor conservative settings for transfer to a separately annotated author set, using already declared material if suitable cached labels exist. Keep both settings and all failures visible; do not choose a new budget or threshold on that transfer outcome. No reserve access is authorized by this proposal. Anchor correctness remains assumed, and no additional lexical nuclei have been discovered.

## Verification

All six budgets' predictions and policies replay. All new fits pass objective/gradient checks; sentence-fold exclusion and strict pooling provenance are verified. The full reference models match84's frozen models. Audit verifies1,704 prior input hashes; all calibrations are frozen before the new evaluation phase.

Five new tests cover fit-only budget ranking, excluded pronoun anchors in small budgets, exact binomial bounds, and rejection/acceptance under the support criterion; all78 focused tests pass. No Caesar scoring, new target annotations, grammar reserve, sealed lexical final test or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration85/`; implementation: `src/voynich_smt/anchor_budget.py`; runner/audit: `benchmarks/grammar_anchor_budget_iteration85*.py`.
