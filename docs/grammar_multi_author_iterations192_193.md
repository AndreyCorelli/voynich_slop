# Development multi-author transfer — iterations 192–193

The previous same-author result now has **partial cross-author support**: with fixed features/ridge and author-held-out training, the rich model selects 8/10 case-comparable pairs for Caesar and 9/10 for Cicero and Jerome. It is **not a uniform improvement**: Aquinas yields only5/10 versus9/10 for the frequency/support control, and Jerome's probability calibration is poor. This is potentially useful grammatical candidate ranking, not named-case recovery, exact POS restoration, a lexical nucleus or Voynich decipherment.

## Frozen admission and models

Development authors are Aquinas, Caesar, Cicero, Jerome, Palladius and Tacitus. New data use the collection's explicit development sentence allowlist; legacy data use PROIEL's corrected author metadata and exclude the original200 reserved sentences. Perseus is not admitted, so the legacy Augustus/Petronius ID errors do not enter these splits. Seneca/Dante labels and FORM features remain unprojected, and disputed/mixed works and LLCT are excluded. CIRCSE contains reserved sentences in the same files as Tacitus: their bytes are necessarily read/buffered, but their token fields are not decoded into FORM or annotation inputs.

Admission uses FORM only: lowercase, strip combining diacritics, j→i/v→u, retain single ASCII-letter forms. Entire sentences containing multiword-token rows are excluded; other nonlexical forms create boundaries. No frame crosses punctuation/nonlexical tokens or sentence boundaries; endpoints must have lexical neighbors. Repeated exact normalized lexical sentences are removed within each author; cross-author exact duplicates are removed from every author. This is sentence deduplication, not a guarantee against shared phrases or paraphrases; reserved texts have not yet undergone the separately required label-blind overlap check.

Sorted works receive sentences round robin, with whole-sentence token budgets. Iteration192 caps each work at7,500 and each author at30,000 lexical tokens; the frozen follow-up193 raises only the per-work budget to30,000. Eligibility remains frequency≥5 and at least two distinct shared two-sided frames. All19 iteration180 features, query-occurrence exclusion, .1 slope ridge, three-feature frequency/support control and constant prior are retained. Training gives each nonempty source author equal total weight and uses weighted source-only scaling. Each target author is excluded from its model's training; fixed .5 and top10/20 selections include all probability ties. All fold predictions are saved before final metric aggregation; no entropy abstention, hyperparameter search or target-selected repair is adopted.

This changes tokenization/boundaries, samples and training weights from180; it is not an isolated numerical replication. All authors are development data, some previously used by other experiments; held-out folds mean model-training exclusion, not globally novel authors. The endpoint features include anonymous boundary markers for outside-query contexts, but boundaries cannot produce eligible shared frames.

## Results of the larger-budget run (193)

“Applicable” means at least one Cartesian comparison in the pair's shared frames has recognized Case on both occurrences. It does not assert that the pair is an actual syntactic dependency or shares one named case throughout the text.

| Held-out author | Lexical tokens | Eligible pairs / applicable | Rich top10 applicable | Control top10 applicable | Rich AUC / control | Rich NLL / control / prior |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |30,000|565 /191|5/10|9/10|.785 / .762|.549 / .560 / .644|
| Caesar |27,386|51 /22|8/10|8/10|.925 / .870|.510 / .552 / .744|
| Cicero |30,000|93 /29|9/10|9/10|.942 / .891|.438 / .505 / .621|
| Jerome |30,000|300 /129|9/10|6/11*|.625 / .609|.814 / .754 / .742|
| Palladius |10,706|1 /0|0/1|0/1|undefined|.131 / .293 / .475|
| Tacitus |2,728|0 /0|empty|empty|undefined|undefined|

*The control's boundary tie retains11 pairs; no arbitrary tie breaking. The prior ties across all candidates, so it cannot produce a meaningful exact ten-pair ranking.*

Rich shortlisted applicable pairs involve7/15/11/12 types for Aquinas/Caesar/Cicero/Jerome, respectively. Conditional frame-macro case equality is80.0%/99.31%/72.22%/100%; joint yield over all ten selected pairs is40.0%/79.44%/65.0%/90.0%. These conditional equality figures have no new word-profile permutation control in this run and do not establish named morphology. Rich threshold.5 selects169/8/8/154 pairs, of which113/6/7/71 are applicable: ranking and probability reliability must be assessed separately. In particular, Jerome's Brier loss is.2904 and NLL exceeds even the constant prior.

The smaller-budget192 retry yields555/1/13/3/0/0 pairs, respectively; rich top lists contain Aquinas5/10, Caesar1/1, Cicero4/10 and Jerome1/3. Its sparse authors are not evidence of successful restoration. Increasing the budget makes three classical author graphs testable, but does not cure short-source coverage or the Aquinas shortlist failure. Neither experiment establishes the four-text shared exact-word milestone.

## Interpretation and next diagnostic

Preserve the Caesar/Cicero/Jerome shortlist results as **development evidence for transferable applicability ranking**. Keep the Aquinas failure equally visible: bulk AUC/NLL improvement can coexist with a worse useful shortlist. Palladius contributes a single negative training example yet, under equal-author weighting, receives the same total source mass as a rich source graph; this is an explicit potential weighting/coverage confound, not a demonstrated cause of the failures.

Before opening reserved authors, freeze a source-author influence diagnostic: remove each training author in turn, with all current target graphs/features fixed, and report top-ten applicability, NLL and coverage against both controls. The important questions are whether the promising shortlists rely on one source author, whether the singleton Palladius mass harms calibration, and whether Aquinas errors persist across source combinations. Do not choose a winning source subset against target labels; any deployment rule would require a separately frozen validation. A complementary training-only minimum-evidence policy can be proposed after the influence audit, with sparse sources reported rather than silently discarded.

## Verification and execution record

The original192 runner stopped on an empty target array before saving models/predictions or evaluating target metrics. Its frozen artifacts/code are preserved with a failure manifest. The192 retry adds empty-prediction handling only; both that run and193 then saved complete models/predictions but stopped during summary construction because the inherited metric divided by zero for zero eligible types. A separate frozen finalizer computes all summaries from those saved predictions, explicitly using null coverage for an empty type universe; no model/selection is changed to address either software failure.

Independent audits reconstruct every eligible graph incidence and all19 features, verify source-only weighted scales and gradients, refit24 logistic models by Newton's method across the two runs, and replay predictions, selections and scalar classification/calibration metrics. Separate raw-selected-row Case audits verify75,524 and136,280 integer rows and all572 and1,010 edge scores. Role, original-reserve, duplicate-role and raw-file hash checks pass. Case references are available procedurally for development folds but target labels are never consumed in their fitting; this is not physical label isolation. No reserved evaluation or broad project test-suite claim is made.

Artifacts: `experiments/results/grammar-restoration/iteration192/` (initial preserved stop), `iteration192-retry/` and `iteration193/`; final metrics are `finalized-summary.json`, `finalized-selections.json`, `finalized-sizes.json`. The first audit's pending raw-case note is resolved by each separate `case-audit.json`. Runners and audits are `benchmarks/grammar_multi_author_iteration192.py`, `grammar_multi_author_iteration192_retry.py`, `grammar_multi_author_iteration193.py`, `grammar_multi_author_review192_193.py`, and `grammar_multi_author_case_audit192_193.py`.
