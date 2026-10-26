# Source-author influence — iteration194

**Preserve the partial grammatical transfer:** the rich model's top ten retains7–8 case-comparable pairs for Caesar,8–9 for Cicero and8–9 for Jerome across every single training-author omission. The result does not depend entirely on one training author. **Aquinas remains a systematic shortlist failure:** rich4–6/10 versus frequency/support9–10/10; removing the singleton-negative Palladius source is not a general repair. These are reused development targets and correlated training perturbations, not fresh validations or exact word recovery.

## Frozen diagnostic

Reuse iteration193's admission, opaque graphs,19 features, recognized-case references and target candidate sets without reading new raw data or annotations. For every target author, run the original baseline plus all five single-source-author omissions; the target never trains itself. Preserve the same .1 ridge and three-feature frequency/support control, recompute standardization from the remaining sources, and give every nonempty source author equal total training weight. Keep the source-prior control, threshold.5 and top10/20 including exact probability ties. Freeze all36 model sets and predictions before computing target metrics; no winning source subset is selected.

Five omitted-Tacitus trials are exact no-ops because its graph has no eligible pairs. The36 trials contain only16 distinct nonempty source sets;72 independently replayed rich/control fits must not be called72 independent pieces of evidence. All baseline predictions match193 exactly, and all baseline metrics match within numerical tolerance.

## All source omissions for the four non-sparse targets

Each cell is **rich applicable count / frequency-support applicable count** in its top-ten shortlist. Both lists contain ten except Jerome's control, which retains11 tied candidates in every trial except withoutAquinas (ten).

| Target | Baseline | Without Aquinas | Without Caesar | Without Cicero | Without Jerome | Without Palladius | Without Tacitus |
|---|---:|---:|---:|---:|---:|---:|---:|
| Aquinas |5 /9|—|4 /9|5 /9|6 /9|6 /10|5 /9|
| Caesar |8 /8|8 /8|—|7 /8|8 /8|8 /8|8 /8|
| Cicero |9 /9|8 /8|9 /9|—|8 /9|9 /9|9 /9|
| Jerome |9 /6|9 /6|9 /6|9 /6|—|8 /6|9 /6|

Palladius still has a single negative target pair and Tacitus none; neither supports a restoration performance claim. Their complete trials, source contributions and metrics remain in the artifacts rather than being silently removed from the experiment.

Applicability means at least one recognized-case occurrence comparison in shared two-sided frames. It does not imply that every occurrence has a case, that the words are syntactically linked, or that the algorithm identifies a case name. Conditional case equality and joint yield are separate: the rich model's minimum joint yield over all these trials is70% Caesar,55% Cicero,80% Jerome and40% Aquinas. This run adds no new word-profile null experiment, so these equality figures alone do not demonstrate new contextual morphology.

## What the audit resolves

The singleton Palladius row originally carries25% of training mass for each non-sparse target. Removing it improves rich Aquinas5→6/10, keeps Caesar8/10 and Cicero9/10, but reduces Jerome9→8/10. Its loss effects also disagree: NLL improves for Aquinas/Caesar but worsens for Cicero/Jerome. Thus disproportionate sparse-source mass is a real design concern, but its removal is not the common explanation or a justified universal repair.

Jerome's rich NLL remains worse than its matching source-prior control in every omission: rich.797–.875, despite8–9/10 applicable pairs at the very top. Stable useful ranking and unreliable probabilities coexist; model agreement cannot automatically be interpreted as calibrated confidence. Aquinas's4–6/10 rich shortlist remains weak across source combinations while the simpler control always has9–10/10. This points to a systematic model/target mismatch rather than one bad training author's inclusion, without identifying its cause.

The useful result is **source-perturbation stability of selective grammatical candidates in three texts**, not broad POS recovery, an exact shared nucleus or Voynich decipherment. It is stronger than a single favorable source combination, and still falls short of a reliable four-text output.

## Next proposal

Freeze a **consensus-core diagnostic** on these already saved predictions: intersect top-ten selections across all source omissions separately for the rich model and the frequency/support control, then intersect those two cores. Compare all three fixed policies with their baseline lists, reporting retained pair/type coverage, false positives, conditional case equality and joint yield for every author. No gold labels choose a policy or refill a small core; an empty core is a result. This directly asks whether the current partial signal can provide a smaller, more trustworthy grammatical constraint set, while testing the risk of stable errors—especially Aquinas—and retaining the rich-only Jerome signal separately. It remains development analysis; any rule adopted for reserved authors needs a subsequent frozen protocol and the pending text-overlap/provenance checks.

## Verification and artifacts

Independent audit reconstructs all36 trial/source sets and source counts/weights, verifies weighted scales and gradients, refits72 logistic models with Newton's method, checks predictions against those refits, and replays scalar classification/calibration metrics, all324 shortlist metric groups, contrasts and detailed selected rows. The shortlist aggregation uses the previously reviewed empty-safe reference metric implementation. All37 input/freeze/baseline hashes pass, all five empty-source omissions reproduce their baselines exactly, and no new raw data or reserved labels are loaded. Dedicated audit passed; no broader project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration194/{design-freeze,trials,models,predictions,summary,selections,shortlist-details,contrasts,audit}.json`, plus frozen proposal snapshot and verification manifest. Code: `benchmarks/grammar_source_author_influence_iteration194.py` and `benchmarks/grammar_source_author_influence_iteration194_review.py`. Earlier frozen reports and datasets are unchanged.
