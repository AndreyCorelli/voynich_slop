# Iteration 116: held-out-type endpoint reliability

**Do not adopt this reliability layer.** No tested veto passes the frozen safety and coverage guards. Preserve a separate, post-hoc observation: the raw held-out class scores retain useful ordering even though their probabilities and the learned reliability calibrator are poor.

## Strict split and scope

The new class model trains on13 non-catalogue source types (10ADP/3CCONJ), with at most20 occurrences per type. All16 catalogue identities/classes are hidden in every input to this new model. Three class-stratified folds produce out-of-fold predictions for the13 training types, with each held fold excluded from training labels and hidden in the inputs. A final class model fits all13 types.

A small reliability classifier uses six pooled statistics from those out-of-fold predictions: mean logit, variance, fraction voting CCONJ, mean entropy, log occurrence count, and log sentence count. Scaling uses only the13 training profiles. Controls include raw pooled probabilities, the training class prior, a type-label shuffle, and a class-balanced reliability model (30 rows per class through deterministic replication). No learned feature contains identity or proposed class.

The16 catalogue types are deterministically split into disjoint eight-type calibration and evaluation sets, each4ADP/4CCONJ. The proposed-pair generator remains the older frozen93 model plus111 gate; **that older generator was trained on catalogue types**. Type exclusion here applies to the newly trained endpoint/reliability layer, not the entire inherited pipeline.

To keep calibration/evaluation candidate types separate, each split uses its own eight-candidate pool. Existing pair scores and sentence bootstraps are restricted and reranked for that pool. Each split retains all16 within-pool cross-class errors and three controls over complete input, eight catalogue omissions, and eight literal deletions:323 conditions. These results are not a full16-candidate-bank replication.

Each arm only vetoes an existing proposal, using the weaker endpoint's predicted opposite/proposed class margin. Cutoffs are calibrated on the calibration types before evaluation predictions: at least90% precision separately in all three regimes, no clean/unsupported wrong calls, at least80% of baseline correct repairs retained in each regime, at least four complete correct repairs, and four distinct correct error cases in each negative pool. No qualifying setting means OFF.

## Outcome

| Calibration regime | Frozen8-pool baseline correct / wrong | Best safe learned reliability correct / wrong | Minimum retained correct |
|---|---:|---:|---:|
| Complete |14 /0|10 /0|12|
| Catalogue omission |84 /2|60 /0|68|
| Literal loss |91 /2|75 /0|73|

The learned model removes the calibration mistakes only at too high a coverage cost. Class balancing gives the same best safe counts. Neither the raw-score nor prior control has a nonempty fully safe setting; the shuffle control also fails coverage. All five calibrated vetoes select OFF.

The evaluation baseline makes10/0 complete,61/0 catalogue, and62/0 literal repairs. The OFF vetoes make no repairs. There are no baseline wrong calls in this particular evaluation split, so it cannot independently demonstrate rejection of false repairs. These are correlated, repeatedly used source contexts with newly excluded endpoint types, not fresh-data confirmation.

## Preserved ranking signal, failed probability calibration

| Eight evaluation types | Class accuracy at.5 | Mean negative log likelihood | AUC (post-hoc) |
|---|---:|---:|---:|
| Raw new class model |50%|.7881|.9375|
| Learned reliability |50%|8.4367|.6875|
| Class-balanced reliability |50%|8.4876|.6875|
| Training class prior |50%|.8644|.5000|
| Type-label shuffle |37.5%|6.0025|.4375|

The raw model predicts every evaluation type as ADP at.5, yet places the CCONJ type above the ADP type in15/16 cross-class comparisons. Calibration-type raw AUC is13/16=.8125. These AUC checks were added after seeing the poor accuracy/probabilities; they are exploratory, and the16 comparisons share only eight types. They are not16 independent observations or a significance claim.

The learned six-feature calibrators produce extreme, poorly calibrated probabilities and much worse loss than the simple class prior. Training on only13 out-of-fold type profiles while transferring to more frequent, differently masked types is a substantial limitation; this experiment does not isolate which feature or shift causes the failure. Hiding all16 common anchor types also removes much of the context used in earlier models. Do not infer that every endpoint reliability method is futile.

Next: test a much smaller, monotone probability calibration of the surviving raw score, rather than fitting six pooled features to13 types. Freeze its source calibration and coverage guards before evaluation; any reuse of the inspected eight evaluation types must be labeled developmental. A global shift still cannot change the original summed pair gain, but it can change an endpoint-specific veto. No word-specific exception or clean oracle subtraction is justified.

No previous repair policy changes. No new grammatical restoration, lexical nuclei, author evaluation, new grammar annotations, reserve features, or sealed lexical evaluation is claimed. Verification:27 focused tests pass; the audit checks21 input hashes, all split/provenance constraints, all646 restricted pair rankings and margins,141 physical type profiles,90 cutoff settings, and refits all three small reliability models. Artifacts are in `experiments/results/grammar-restoration/iteration116/`.
