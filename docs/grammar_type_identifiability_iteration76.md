# Oracle identifiability and repeated-type pooling — iteration 76

**Two results to preserve: these grammatical features do not uniquely identify words in this inventory, while repeated contexts improve soft POS predictions.** Both proposed diagnostics were run on the already explored1,273content tokens/844word types. No additional nuclei or blind restoration percentage were established.

## 1. Perfect grammar: how identifiable are the words?

For each word type, intersect the100,000-form dictionary with every reference POS/Case/Number reading observed for that type. Each occurrence must be admitted by a joint candidate reading; different occurrences can use different readings. Compare tolerant missing-field wildcards with a strict control requiring every nonempty reference feature to be explicit in the dictionary. Empty reference fields impose no extra condition. No target-aware inventory filtering or insertion of missing originals occurs.

| Scope | Types | Inventory contains original | Original survives all reference readings | Unique correct candidates | Median final pool, tolerant / strict |
|---|---:|---:|---:|---:|---:|
| All content types | 844 | 630 | 610 | **0 / 0** | 1,653 / 1,628 |
| Repeated types | 206 | 180 | 175 | **0 / 0** | 1,415 / 1,390 |

There are214absent originals and20present originals whose dictionary readings fail the reference requirements. Missing candidates are retained as failures, not dropped. No candidate pool is empty or singleton, under either convention.

Only25types have more than one distinct reference POS/Case/Number profile. Repetition reduces the candidate pool for22types; for most surface forms it simply repeats the same grammatical constraints. Thus intersection across occurrences rarely adds new hard information here. The aggregate median does not move from first occurrence to final intersection in either scope.

Source-frequency ranking within the strict oracle pools puts7/844originals first and30/844in the top10 (repeated types6/206and21/206). Tolerant pools give2/844and17/844. These frequency-assisted oracle ranks are **not uniquely identified or recovered nuclei**. Inventory and grammar are both supplied privileges. This is a resource-dependent identifiability result for POS/Case/Number, not a theorem about all grammatical features or every Latin inventory.

## 2. Infer grammatical classes across repeated occurrences

Keep the iteration70model fixed. Group occurrences by word equality as a surrogate for repeated opaque cipher types; no word identity feature is added to the model. Average their posterior distributions over joint POS/Case/Number profiles. Compare local predictions, an all-occurrence mean and a leave-one-occurrence-out mean using only the other contexts. Use the identical procedures for saved shuffled-context and source-prior controls. Reference labels enter evaluation only.

The206repeated types cover635tokens. Correct surrounding plaintext and sentence boundaries remain supplied, so this is an easier diagnostic than actual cipher-side inference.

| POS evidence | Accuracy | NLL |
|---|---:|---:|
| Local context | 51.18% | 1.0858 |
| Pooled contexts | **64.09%** | **1.0232** |
| Other occurrences only | 57.95% | 1.0475 |
| Local shuffled context | 40.79% | 1.2590 |
| Pooled shuffled contexts | 51.65% | 1.1657 |
| Other shuffled occurrences only | 47.87% | 1.1959 |
| Source prior | 20.31% | 1.2565 |

Pooling helps shuffle too: accuracy improves10.87points there, versus12.91points for real context. The result supports denoising and consistency of repeated-type soft evidence; it does not isolate the entire pooling gain as an effect of grammatical order. POS type-balanced NLL also improves,1.1048local→1.0473pooled; other-occurrence-only1.0816.

Exact joint-profile accuracy improves21.42%local→24.25%pooled, versus14.17%pooled shuffle and14.49%prior. Other-occurrence-only accuracy is24.57%, but its type-balanced profile NLL2.7742is slightly worse than local2.7676. Pooling heterogeneous readings can therefore lose information even when some aggregate metrics improve.

**No demonstrated narrowing:** fixed90%posterior credible sets get wider with pooling. Mean POS set size3.20→3.41, with reference coverage96.85%→98.11%; joint-profile size12.97→14.57, coverage88.66%→92.13%. These are descriptive credible sets, not independently calibrated confidence guarantees. The benefit is better soft classification/coverage, not sharper hard candidate sets. Homographic types can genuinely admit several profiles; forcing one reading would be inappropriate.

## Decision and next work

Retain repeated-type posterior pooling as a **promising soft grammatical-class proposal**, not an adopted decoder or lexical recovery result. Preserve the zero-singleton oracle finding alongside it. More POS/Case/Number scoring refinements alone have a weak prospect of exact word identification in these pools.

The next useful test should measure whether these pooled distributions improve a grammatical decision—such as subject eligibility or agreement—over local and pooled-shuffle controls, with source-only calibration. Propagate uncertainty instead of using64%POS accuracy as hard labels. Any claimed nucleus will require additional discriminating information beyond these three features. The proposed joint-agreement experiment remains untested.

## Verification

Independent raw-signature reconstruction replays all844oracle pools and frequency ranks; all1,273input token posteriors are checked. Audit verifies1,540prior manifest input hashes. Four new tests cover strict missing-feature handling, stable credible sets, exclusion of the current occurrence and singleton exclusion; all34focused tests pass. No refitting, new target annotation queries, grammar reserve or sealed lexical final-test scoring occurs.

Artifacts: `experiments/results/grammar-restoration/iteration76/`; runner/audit: `benchmarks/grammar_type_identifiability_iteration76*.py`.
