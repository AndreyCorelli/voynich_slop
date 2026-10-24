# Iteration 48: source-only morphology candidates on held-out sentences

**A source-trained morphology lattice preserves useful agreement information without held-sentence morphology labels, but recovery is modest.** The broadest calibrated sets preserve323/326 reference links after agreement and identify19 unique correct links, versus10 before agreement, with zero unique wrong links observed. Single-best tags identify more links but lose109 references and produce11 unique wrong links.

This removes the same-source oracle morphology dictionary from inference. Readable Latin word forms, gold POS, sentence boundaries and the existence/selection of eligible overt-subject constructions remain supplied. It is not morphology induction from anonymous cipher words or blind sentence parsing.

## Data boundaries and fixed model

Reuse the4070 source Cicero/Palladius sentences and326 iteration46 constructions. Partition by SHA256(sentence ID) into five folds. For each outer fold:

- Hold that fold out for testing.
- Use the next fold for calibration.
- Fit the word/suffix model on the remaining three folds.

The current test sentence contributes no morphology labels to its dictionary, model or cutoffs. Other occurrences of the same form in training are permitted; form generalization is audited separately. Cross-validation reuses labels across different models in the usual way, but no example is tested with a model or calibration policy that saw its own sentence. The data have been inspected in previous experiments, so this is source cross-validation on development data, not fresh independent confirmation.

Model inputs at inference are **word and POS only**. It jointly predicts task eligibility and agreement features:

| POS group | Labels |
|---|---|
| NOUN/PROPN | OTHER, nominative singular third person, nominative plural third person |
| PRON | OTHER plus six nominative number/person states |
| VERB/AUX | OTHER plus six finite number/person states |

OTHER means non-nominative or nonfinite for the corresponding group. Thus gold case and finite-verb eligibility are no longer supplied to candidate generation. Tokens with missing/non-atomic training labels are excluded from model fitting, calibration and scorable token metrics; every applicable test token still receives predictions. All reference endpoints have scorable labels.

Use source word counts, with mass2 interpolation toward the longest1–4-character suffix having at least five labeled training tokens. Smooth suffix counts by mass2 toward an add-half POS-group prior. Word keys retain POS; suffix priors share NOUN/PROPN and VERB/AUX groups. Settings are fixed before prediction, with no outcome-based tuning.

Compare five declared policies:

- **Dictionary:** all labeled readings observed for that word/POS in fitting data; explicit all-state fallback if unseen.
- **Top1:** the highest-probability joint state.
- **Set95 / Set99:** label-conditional calibrated sets using the finite split-conformal quantile formula with alpha0.05/0.01. Calibration never adds dictionary entries. A class with insufficient calibration support has threshold0 and remains included.
- **All:** every task state, an uninformative control.

The calibration procedure does not establish guaranteed joint relation coverage under clustered sentences, selective annotation availability or development-data reuse. The numbers95/99 name the calibration settings, not achieved structural accuracy.

## Candidate coverage and unique links

All figures refer to the fixed326 constructions; no cases are removed after seeing candidate coverage.

| Policy | Raw reference links | Reference links after agreement | Exact readings after agreement | Unique correct links: raw → agreement | Unique wrong after agreement | Empty after agreement |
|---|---:|---:|---:|---:|---:|---:|
| Dictionary | 312 | 311 | 310 | 30 → **39** | 1 | 4 |
| Top1 | 224 | 217 | 217 | 50 → **86** | **11** | 66 |
| Set95 | 322 | 297 | 292 | 18 → **37** | 1 | 3 |
| Set99 | **326** | **323** | **321** | 10 → **19** | **0** | **0** |
| All | 326 | 326 | 325 | 6 → 6 | 0 | 0 |

Set99 retains99.1% of reference links after agreement and adds **nine unique correct links** over its own raw candidates. That is a useful local effect, not high overall recovery: only19/326 constructions have a unique correct link. Mean candidate links fall from28.74 to19.13 under agreement, versus32.79 for All.

Top1's86 unique correct links must not be reported alone: it also loses109 reference links, produces11 unique wrong links, and leaves66 empty sets. Agreement can sharpen an incorrect morphology commitment. Dictionary and Set95 provide different coverage/ambiguity tradeoffs; no winner is selected using these query outcomes.

Exact reading survival is separate from link survival. Of the five Set99 exact tuples rejected, one is the previously documented stored plural-subject/singular-verb mismatch. Four upstream reference reading tuples are absent even before agreement. Three reference links are then lost under agreement; another remains available through an alternative feature reading.

## Comparison with the oracle diagnostic

Iteration46, which supplied oracle word-type morphology and nominative/finite eligibility, had83 unique correct links after agreement. Set99 has19. This is a major remaining gap.

On the **same270 examples that were ambiguous under the clean oracle baseline**, Set99 identifies only **two** unique correct links. Its nine overall additional links are therefore **not nine of the earlier28 recovered links retained**: removing oracle eligibility changes the raw candidate graph and creates new ambiguities even in formerly easy cases.

With the true subject token supplied, Set99 newly resolves49 predicate choices; with the true predicate supplied, it newly resolves one subject. The corresponding oracle-morphology counts were61 and35. Predicate discrimination retains a useful signal under an anchor, but subject identification is much weaker with predicted nominative eligibility. The anchors remain oracle interventions, not automatically discovered facts.

## Seen and genuinely unseen forms

Among reference constructions,123 have both endpoint word/POS forms present in fitting data,173 have exactly one absent, and30 have both absent. For these endpoints, every present form has a labeled fitting occurrence; the main labeled-seen cohort agrees with genuine form presence. This need not hold for all test tokens.

| Form cohort | Examples | Set99 reference links after agreement | Unique correct: raw → agreement | Unique wrong |
|---|---:|---:|---:|---:|
| Both present | 123 | 123 | 5 → 8 | 0 |
| One absent | 173 | 170 | 3 → 6 | 0 |
| Both absent | 30 | 30 | 2 → **5** | 0 |

The both-absent cohort demonstrates some transfer through source suffixes/priors rather than exact-word lookup. It is small and was audited after primary prediction; it is not a separate confirmation set or evidence that anonymous endings can already be aligned to Latin morphology.

Source authors remain distinct in reporting: Set99 retains248/250 Cicero links and75/76 Palladius links; it uniquely identifies12 and7 respectively. Both authors contribute to training/calibration in each source split, so this is not held-author generalization.

## Token coverage and why the broad sets remain ambiguous

Scorable held-out token counts are10813 nominal,5389 pronominal and12485 verbal. Coverage concerns the task class, not dependency correctness. Candidate-set size includes OTHER.

| POS group | Top1 coverage | Set95 coverage / mean size | Set99 coverage / mean size | Maximum size |
|---|---:|---:|---:|---:|
| NOUN/PROPN | 89.3% | 95.2% / 1.40 | **99.1% / 2.03** | 3 |
| PRON | 96.5% | 96.5% / 4.24 | **99.8% / 6.91** | 7 |
| VERB/AUX | 97.4% | 95.4% / 1.98 | **99.5% / 2.54** | 7 |

A high top1 token score, especially on common OTHER classes, does not establish relation recovery. Joint reference coverage requires both endpoints and their compatible states.

The clearest bottleneck is sparse calibration of **joint** classes. At99%, all six nominative pronoun number/person classes have too few calibration examples for nonzero exclusion thresholds in every fold. Even confidently non-nominative pronouns therefore retain those rare candidate states. Some verbal and nominal plural classes are also forced in for particular folds. The pronoun sets are nearly uninformative, expanding the subject graph.

This is the cost of conservative label-conditional calibration in this data regime, not evidence that every such reading is grammatically plausible. Full per-fold class counts and thresholds are saved. No cutoff is tightened after observing structural results.

## What to test next

Source-only, high-coverage candidate retrieval is feasible under supplied POS and readable Latin forms. It preserves a small structural advantage from agreement. The current limitation is efficient morphology uncertainty, especially rare joint pronoun classes and nominative eligibility; a larger attachment optimizer would not resolve those missing distinctions by itself.

A focused next test is to predict/calibrate **eligibility, number and person with shared evidence**, rather than treating every complete tuple as a separate sparse class. Number/person annotations from non-nominative and nonfinite forms can potentially contribute training support where appropriate. Compare against the frozen joint-class policies on the same source partitions, and require improved reference coverage/cardinality before claiming structural progress. Do not assume factorization is safe: retain exact-reading losses and unique wrong links as primary checks.

No candidate policy here provides a guaranteed morphology lattice, and no full grammatical structure has been restored from ciphertext.

## Verification and artifacts

383 regression tests pass. Validation reconstructs all five source-only models and ten calibration policies, verifies disjoint fit/calibration/test sentences, replays15189 word-type predictions,3040 sentence/arm supports and3260 reference summaries, and checks inference invariance to changing held-out morphology and dependency fields. Set95⊆Set99⊆All holds. All22 frozen-input hash checks pass; prior target queries and the reserved200 remain unscored.

Run `python -m benchmarks.grammar_source_morphology_iteration48` (refuses overwrite), then `python -m benchmarks.grammar_source_morphology_iteration48_validate` and `python -m benchmarks.grammar_source_morphology_iteration48_audit`. Core code is `src/voynich_smt/source_morphology.py`. Artifacts under `experiments/results/grammar-restoration/iteration48/` include frozen source partitions, word/suffix models, calibration counts/cutoffs, probabilities and candidate sets, encoded morphology supports, per-reference and token metrics, form-availability/failure audits and validation. Previous artifacts and the shared todo remain unchanged.
