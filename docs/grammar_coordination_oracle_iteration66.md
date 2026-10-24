# Iteration 66: why competition loses coordinated subjects

All nine exact coordination units lost by iteration 65 have a rival in the same annotated conjunction component. Eight losses are abstentions and one a rerouting. Each relevant rival is a nominal labeled `conj`, which has no independent subject target in the existing `nsubj`-head-only task. There are no offsetting coordination gains. This is a representation/eligibility conflict, not evidence that coordination requires indiscriminately waiving competition.

## Frozen oracle test

Keep the iteration-65 primary cutoffs, penalties, source partitions, full candidate scores, head/type model and targets unchanged. Empty the outgoing carrier domain of any nominal whose source dependency base is `conj`; assert that its existing gold carrier is NONE. All remaining subjects can choose their original carriers, alternatives or NONE. This uses gold dependency labels and is **only an oracle**. It neither projects new targets onto conjuncts nor claims that conjuncts have no grammatical subject role.

| Metric | Independent baseline | Competition65 | Conj-exclusion oracle |
|---|---:|---:|---:|
| Full-source exact-unit F1 | 56.86% | 58.89% | 60.24% |
| Full-source correct units | 2,098 | 2,026 | 2,045 |
| Full-source false units | 1,917 | 1,490 | 1,380 |
| Selected exact-unit F1 | 64.85% | 66.87% | 67.27% |
| Selected correct units | 346 | 337 | 337 |
| Coordinated-subject exact units /122 | 48 | 39 | 48 |

The oracle restores each of the nine inspected losses, adds 19 net correct units overall and removes 110 net false units relative to competition65. It does not recover more coordination units than the old baseline, and it still recovers fewer correct units overall than that baseline. The source set, 3,365 gold units/519 selected, and all evaluation labels remain unchanged. No fitting, calibration, cutoff adjustment or penalty change occurs.

The conclusion is task-specific: distinguish phrase heads from nominal conjuncts before charging them as competing subject assignments. Simply exempting all coordinated tokens from competition could preserve extra predictions that are false under this task. A future task representing a coordinated phrase as the subject would require explicit new labels and separate evaluation, not silent target changes.

## Next experiment and verification

The oracle shows enough room to test observable conjunct-role evidence. The next experiment fits a binary nominal-conjunct probe on outer fit sentences only, using POS context/conjunction markers, compares against a POS-only control, and calibrates its soft evidence weight on calibration sentences. It must preserve coordination and overall exact-unit performance against the frozen iteration-65 policy and its controls. Gold dependency labels must not enter inference.

Artifacts are in `experiments/results/grammar-restoration/iteration66/`, including all nine cases with rival assignments and source words. Separate design and prediction freezes preserve provenance. Independent audit replays all 17,674 unambiguous assignments, checks unchanged older fields and recomputes attribution/evaluation. Source data are reused development partitions with readable words/POS upstream. The 200-sentence reserve remains unscored and no prior target queries were scored. This oracle result is not deployable restoration performance.
