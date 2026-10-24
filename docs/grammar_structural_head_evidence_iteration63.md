# Iteration 63: learned phrase and clause evidence

Candidate-conditioned structural probes improve auxiliary-label prediction but do not improve grammatical-unit restoration. The primary contextual joint arm has full-source exact-unit F1 **56.80% versus 56.86%**, with selected-sentence F1 unchanged at **64.85%**. Copular units fall from 259 to 255/650. Retain the original scorer.

The more useful result is diagnostic: the clause probe generally distinguishes the true head from arbitrary wrong candidates, but usually ranks it below the wrong candidates already preferred by the baseline. Aggregate structural-label accuracy hides this failure.

## Design and controls

The experiment preserves the same 4,070 Cicero/Palladius source sentences, five fit/calibration/test sentence partitions, 3,365 gold units (519 selected), original iteration-57 unit scores, and iteration-56 carrier predictions. The single carrier-ambiguous frame remains excluded. No candidate injection, hard filtering, unit-score refitting or type-offset tuning occurs.

For each gold-endpoint training frame, two independent logistic outputs predict the iteration-58 oracle distinctions:

- **Phrase:** the candidate head is not an amod/det/nmod/appos/flat/fixed/compound/case dependent.
- **Clause:** the candidate head and finite carrier have compatible gold clause anchors, using the same anchor definition and permissive unknown handling as iteration 58.

These are auxiliary labels derived from training annotations. Clause anchors can encode target attachment; they are not directly observable inference information. Inference receives only POS and positions. No words, lemmas, morphology or dependency heads/relations enter the probes. A token shares its own clause by identity, so the clause probability for head equal to carrier is fixed to one without consulting annotations.

The **coarse control** uses head/carrier POS and their interaction, distance buckets, direction and head-POS/distance interaction. The **context model** adds ±2 POS windows and immediate POS combinations around both endpoints, intervening POS counts, and a head-POS/carrier-previous-POS interaction. This changes information as well as model size; it is not a parameter-count-matched architecture comparison.

Candidate heads are deduplicated across copular/auxiliary roles. Each training frame contributes equal total weight, shared across its heads; the two binary losses are averaged. L2 is fixed at 0.001, minimum feature count at three, with a fixed optimizer. Only outer fit sentences provide probe training labels. There is no second learned scorer consuming in-sample probe outputs.

Probe log probabilities, clipped at 1e-6, add soft evidence to frozen unit scores. The same head receives the same addition across types. Each coarse/context model has phrase-only, clause-only and joint calibration arms; weights range over 0, 0.5, 1, 2, 4. Calibration maximizes exact units with true subject/carrier endpoints and prefers smaller weights on ties. Zero is available. The primary arm is context joint, specified before evaluation.

## Actual pipeline

| Arm | Full-source exact units | Full-source F1 | Selected exact units | Selected F1 |
|---|---:|---:|---:|---:|
| Original baseline | 2,098 | 56.86% | 346 | 64.85% |
| Coarse phrase | 2,098 | 56.86% | 346 | 64.85% |
| Coarse clause / joint | 2,094 | 56.75% | 346 | 64.85% |
| Context phrase / joint | 2,096 | 56.80% | 346 | 64.85% |
| Context clause | 2,098 | 56.86% | 346 | 64.85% |

All arms emit the same 4,015 full-source and 548 selected predictions. Context joint chooses zero weights in four folds and phrase weight 0.5 in fold four; clause weight is zero throughout. Coarse joint activates clause weight 0.5 only in fold two. The additions selected on calibration fail to transfer beneficially: context joint changes 15 predictions, gaining three exact units and losing five; coarse joint changes 20, gaining five and losing nine. These are reused development partitions, not fresh confirmation.

| Gold type | Baseline correct / F1 | Context joint correct / F1 |
|---|---:|---:|
| Direct | 1,690 / 63.51% | 1,692 / 63.48% |
| Copular | 259 / 37.48% | 255 / 37.17% |
| Auxiliary | 149 / 44.08% | 149 / 44.02% |

With true endpoints and true type, copular head recovery declines from 420 to 416/650; auxiliary recovery stays 269/292. True-endpoint, unknown-type recovery falls from 2,870 to 2,867/3,365. These diagnostics are not pipeline restoration gains.

## The hard-candidate mismatch

Probe evaluation covers 10,832 candidate heads in the 650 gold copular frames. These are candidate-weighted measurements, not token-wide or sentence-macro accuracy.

| Auxiliary task | Coarse accuracy / Brier loss | Context accuracy / Brier loss |
|---|---:|---:|
| Phrase | 90.60% / 0.0721 | 92.14% / 0.0593 |
| Clause | 82.06% / 0.1324 | 86.38% / 0.0983 |

Both tasks are learned better with context, yet neither delivers a unit gain. Comparing each true copular head with wrong copular heads exposes why:

| Context cue ranks gold head higher | All 10,182 wrong-head comparisons | 479 baseline-outranker comparisons |
|---|---:|---:|
| Phrase probability | 4,402 (43.23%) | 280 (58.46%) |
| Clause probability | 9,256 (90.91%) | 140 (29.23%) |

The 479 comparisons are candidate pairs across erroneous frames, not 479 separate errors. A useful clause cue must resolve these close competitors, rather than just suppress distant easy candidates. Of 145 baseline outrankers that the gold clause oracle could exclude while preserving the true head, the learned context clause cue prefers gold in only 69 comparisons. Phrase evidence does better on the analogous oracle-blockable subset (166/193), but that does not make it reliable across the remaining candidates or preserve already correct decisions.

A post hoc distance description, with no fitting or retuning, finds that 350/479 outrankers are closer to the carrier than the true head, 72 equally distant and 57 farther. Mean wrong-head distance is 2.08 tokens versus true-head distance 3.73. This supports the interpretation that generic locality is insufficient for these cases; it does not establish a causal decomposition of the probe's features.

## Verification and decision

Artifacts are in `experiments/results/grammar-restoration/iteration63/`, with separate design, model and prediction freezes. The independent replay refits all ten probes, replays 30 calibration policies, 44,286 active inference decisions and 20,190 true-type decisions, verifies all 10,832 saved candidate cue records, and recomputes both evaluations. Inference mutation checks hide lexical and annotation fields. Earlier prediction fields and carrier endpoints remain unchanged. **93 relevant tests pass.**

The initially frozen audit used exact equality for refitted floating-point models. Sparse feature reduction order can vary between processes; the replay audit uses numerical tolerances for weights, losses and probabilities while preserving exact policy/decision checks. The initial audit remains frozen. No experimental weights, policies or predictions were altered; use `benchmarks.grammar_structural_head_evidence_iteration63_replay` for audit reproduction.

Do not adopt these additions. This experiment tests soft independent phrase/clause probes from POS context, not a jointly decoded parse or a supervised clause-boundary sequence model. The next structural model should be judged first on baseline outrankers and on preservation of correct units; high aggregate label accuracy is not an adequate gate. A coherent clause/phrase assignment across a sentence remains a distinct, untested direction, while further tuning of these additive probes has little support here.

The 200-sentence reserve remains unscored. No prior target queries were scored. Source POS is available in this experiment; these results do not establish Voynich grammatical restoration.
