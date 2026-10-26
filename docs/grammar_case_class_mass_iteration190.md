# Iteration 190 — preserving source class mass does not resolve the evidence gap

**Negative control outcome:** restoring original positive/negative training contributions barely changes the entropy-screened shortlists:11 improve,3 worsen and1,364 tie among1,378 omissions. Worst applicability moves3/10→4/10, and16 cases still fall below8/10. Reduced positive-class mass alone does not account for the residual failures; specific source information remains a plausible limitation, not yet a proven causal mechanism.

## Frozen change

Use exact188 double-endpoint masks, anonymous features, full-source scales, rich19/control3 columns, ridge.1, intercept, optimizer, thresholds and retained-source range policies. Assign positive examples fixed total mass18/52, negative examples34/52, equally shared within each retained class. This is preservation of the original empirical source proportions, not50/50 balancing. The original unomitted objective equals180 exactly.

Freeze all omission/range masks, source fits, target probabilities and selections before target scoring. Primary: paired rich entropy-refilled top10 applicability versus188, with full-population probability losses and coverage costs. All1,378 masks and policies are retained; no target-derived choice of class weights or thresholds. Same training masks imply unchanged entropy/all-coordinate acceptance and useful-evidence loss.

## Rich entropy-refill comparison

| Outcome | Ordinary omitted-fit class mass (188) | Fixed original class mass (190) |
|---|---:|---:|
| Mean top10 applicability | 89.23% | 89.29% |
| Worst top10 applicability | 3/10 | 4/10 |
| Lists with9 applicable pairs | 1,305 | 1,303 |
| Lists with8 applicable pairs | 52 | 59 |
| Lists below8 | 21 | 16 |
| Mean top10 joint yield | 73.93% | 73.97% |
| Worst top10 joint yield | 20.00% | 30.00% |

Per-omission applicability improves by one in11 cases and worsens by one in3;1,364 unchanged. Without entropy screening, the worst remains3/10, with12 improvements and5 regressions. The previous worst `omit1160` goes from3 to4 applicable pairs after screening, a limited change rather than a repaired shortlist.

The existing entropy rule still rejects0–4 useful candidate pairs per omission, and its accepted candidates remain112–122/126. Coverage masks are byte-for-byte identical to188; improvements cannot be attributed to accepting more candidates or changing geometry. All-coordinate screening remains a fixed descriptive control, not an adopted alternative.

## Full-target probability behavior

| Rich model metric across omissions | Ordinary class mass (188) | Fixed class mass (190) |
|---|---:|---:|
| Mean NLL | .4510 | .4493 |
| NLL range | .4229–.6098 | .4263–.5783 |
| AUC range | .7256–.8611 | .7164–.8611 |

NLL improves in804 fits and worsens in574. The narrower loss range comes with a lower minimum AUC; it is not uniform improvement. All1,378 rich fits still beat their matched frequency/support controls on NLL. Probability/calibration, threshold lists, all trim/refill policies and paired changes are retained; accepted-subset losses must not be mistaken for full-population gains.

Joint yield and applicability retain their diagnostic definitions. No named cases, general POS tags, token accuracy, lexical identities or nuclei are recovered. This is a supervised source-training control on reused same-author data, not fresh generalization.

## Numerical retry and verification

The first source-fitting attempt stopped on SciPy's `ABNORMAL` line-search status **before model freeze or any target prediction/scoring**. It is preserved under `iteration190/`, including its frozen code/design and failed-attempt manifest. The same scientific objective was rerun under `iteration190-retry/` with an explicit max-gradient<=1e-6 stationarity requirement and a declared BFGS fallback only if needed; no fallback was needed. Two stored control-fit records (the same duplicate training-mask solution) retain a line-search-stop status with gradient4.86e-9 and pass independent Newton validation. Target outcomes did not select an optimizer or statistical setting.

Independent replay verified all1,378 masks and class-mass inventories,2,158 unique Newton solutions, source scales, gradients, every target prediction,41,370 list metric groups, all original180 baselines, exact188 acceptance masks and every paired comparison. The unscored failed attempt's hashes were also verified. The broader test suite was not rerun for this reference-only diagnostic; no new annotations, reserves or sealed data were used.

## Interpretation and next diagnostic

Preserving the amount of positive contribution helps a few weak fits but leaves the main ranking limitation. Lost positive feature contexts, changed within-class representativeness and small correlated training data remain entangled. This result does not warrant class-weight tuning against the target or adopting fixed-mass training as a confidence repair.

Next freeze a **source-positive add-back diagnostic** on all21 weak188 masks: restore each omitted positive source example individually, keep total class mass and full-source scales fixed, and keep each mask's base acceptance ranges fixed. This separates added source-example information from changing class total weight or range acceptance. Report every addition and regression, without choosing a target-favorable training set or claiming a deployable rescue. All labels are existing source labels; no target labels enter fitting.

Runner: `benchmarks/grammar_case_class_mass_iteration190_retry.py`; failed frozen runner: `benchmarks/grammar_case_class_mass_iteration190.py`; reviewer: `benchmarks/grammar_case_class_mass_iteration190_review.py`. Successful full artifacts and verification manifest: `experiments/results/grammar-restoration/iteration190-retry/`; preserved unscored attempt: `experiments/results/grammar-restoration/iteration190/`.
