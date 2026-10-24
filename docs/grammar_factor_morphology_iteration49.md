# Iteration 49: sharing morphology features

Predicting eligibility, number and person separately makes candidate sets substantially smaller when it also allows training on partially specified and other-case annotations. At the conservative allocated 1% setting, unique correct subject–predicate links increase from 19 to 30, with zero unique wrong links observed. Reference-link retention falls from 323/326 to 322/326: this is a useful tradeoff, not strict dominance or a confirmed replacement.

## Design and controls

The experiment reuses iteration 48's 4,070 Cicero/Palladius sentences, 326 selected subject–predicate constructions, and five sentence partitions. Each outer fold uses three partitions for fitting, one for calibration and one for testing. Predictors receive readable normalized Latin words and supplied POS; construction selection remains supplied. Test morphology is unavailable to fitting and calibration. These are reused development partitions, not fresh confirmation or a cipher restoration experiment.

The word/suffix estimator is unchanged: longest supported suffix of length 1–4, minimum five training tokens, mass-two smoothing and an add-half group prior. Separate predictors estimate nominative/finite eligibility, number and person; nouns and proper nouns have fixed third person. Independent component products give joint probabilities, while accepted feature sets form Cartesian candidate sets. Agreement then filters subject–predicate pairs.

Two supervision conditions distinguish factorization from increased label support:

- **Matched:** eligibility uses only tokens scorable by the old joint task; number/person use only its positive nominative/finite tuples.
- **Expanded:** each component uses every applicable known annotation, including number on other-case words and person independently of case. Missing components do not discard the other labels.

For example, fold-zero pronoun training support rises from 369 to 4,082 number labels and from 369 to 2,006 person labels. Expanded eligibility has 4,082 labels versus 3,238. Sparse calibration classes still exist, especially for person.

All ten policies were specified before evaluation. `set95`/`set99` allocate 5%/1% error to **each** learned component; they do not have the old joint model's nominal error budget. `total95`/`total99` divide that budget by two nominal or three pronoun/verbal components. Calibration is label-conditional within component/POS group. These nominal budgets do not establish structural coverage guarantees under sentence clustering, annotation missingness or development reuse.

## Results

All rows apply agreement to the same 326 constructions. “Retained” counts the reference token pair with any surviving morphology; “exact” additionally requires its annotated morphology. Unique correct/wrong counts refer to token links. Mean links measures remaining ambiguity.

| Supervision / policy | Exact | Retained | Unique correct | Unique wrong | Empty | Mean links |
|---|---:|---:|---:|---:|---:|---:|
| Old joint set99 | 321 | 323 | 19 | 0 | 0 | 19.13 |
| Matched top1 | 214 | 214 | 84 | 11 | 69 | 2.42 |
| Matched set95 | 274 | 274 | 90 | 5 | 18 | 4.04 |
| Matched set99 | 318 | 320 | 43 | 1 | 0 | 8.63 |
| Matched total95 | 307 | 307 | 61 | 4 | 1 | 6.63 |
| Matched total99 | 322 | 324 | 17 | 0 | 0 | 17.23 |
| Expanded top1 | 217 | 217 | 87 | 13 | 61 | 2.59 |
| Expanded set95 | 273 | 273 | 86 | 7 | 17 | 4.60 |
| Expanded set99 | 316 | 317 | 58 | 2 | 1 | 8.38 |
| Expanded total95 | 306 | 306 | 73 | 4 | 3 | 6.13 |
| Expanded total99 | 320 | 322 | 30 | 0 | 0 | 12.60 |

Expanded total99 reduces mean links by 34% and mean pronoun candidate-set size from 6.91 to 2.42 (65%). On the same 5,389 old joint-scorable pronoun tokens, coverage is 5,377/5,389 (99.78%). Nominal coverage is 10,741/10,813 (99.33%) and verbal coverage is 12,442/12,485 (99.66%). These token-level measurements include the OTHER state and are distinct from link retention.

The matched total99 control retains one more link than the old model but resolves fewer unique correct links (17 versus 19); its pronoun set size remains 6.91. Extra component annotations therefore appear important to the observed efficiency gain. Factorization alone at this conservative setting does not provide comparable discrimination.

The harder, originally ambiguous 270-construction cohort yields only three unique correct links under expanded total99 versus two under the old joint set99 model. Most of the overall gain occurs outside that cohort. Both-reference-forms-seen cases retain 123/123 links with 14 unique correct; cases with an unseen reference form retain 199/203 with 16 unique correct.

## Paired losses and limits

Expanded total99 adds 13 unique correct outcomes and loses two previous unique outcomes, for a net gain of 11. It newly loses two reference links and rescues one, for a net loss of one retained link. Both new failures are number exclusions on proper names annotated singular:

| Sentence | Subject | Predicted number set | Annotated number | Predicate |
|---|---|---|---|---|
| 78355 | osaces | Plur | Sing | accepit |
| 86360 | salamis | Plur | Sing | citetur |

Their number sets exclude singular before agreement, so the reference links cannot survive. A suffix/generalization problem is a hypothesis, not established by these two examples. No exceptions were added after inspecting them. Zero observed unique wrong links is a sample result, not a safety guarantee.

The next focused diagnostic is whether source-only proper-name or out-of-distribution uncertainty can preserve singular alternatives without surrendering the set-size improvement. Any such rule needs a matched coverage/ambiguity comparison and fresh confirmation before adoption. The present result still depends on readable Latin forms, supplied POS and selected overt-subject constructions; it does not establish recovery of grammatical structure from Voynich text.

## Reproduction and verification

Implementation: `src/voynich_smt/factor_morphology.py`; run `python -m benchmarks.grammar_factor_morphology_iteration49`, then the `_audit` and `_validate` modules. Artifacts are under `experiments/results/grammar-restoration/iteration49/`; the run refuses to overwrite an existing output directory.

Validation checks 27 frozen hashes, refits 10 models, recalibrates 40 policies, and replays 30,378 word-type predictions, 6,080 sentence supports and 6,520 reference summaries. Mutating held-out morphology and dependency annotations leaves candidate domains unchanged. The relevant regression suite passes 389 tests. The 200-sentence reserve remains unscored, and no prior target queries were scored. Iteration 48's verification manifest remains intact.
