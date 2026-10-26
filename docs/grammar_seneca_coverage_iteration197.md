# Seneca reserved-text coverage — iteration197

**The reserved Seneca sample cannot test the current two-frame model:** its frozen primary graph contains zero eligible word pairs. This is a coverage failure, not an accuracy result. Seneca's POS/Case and other grammatical fields remain unprojected; no models or predictions run, no thresholds change and no eligibility rule is relaxed.

## Frozen label-blind admission

Use the collection's explicit Seneca allowlist from pinned CIRCSE r2.17, covering *Hercules Furens*, *Agamemnon* and *Oedipus*. Only sentence IDs, token IDs and FORM are decoded; other token fields and text comments are ignored. CIRCSE files also contain development Tacitus material, but only allowlisted Seneca sentences enter this projection. UDante raw data remain untouched.

Keep193 normalization (lowercase, NFD diacritic removal, j→i/v→u, single ASCII-letter lexical forms), whole-sentence rejection for multiword-token rows, and punctuation/nonlexical/sentence boundaries. Compare normalized lexical sentence sequences against all six193 admitted development-author pools: reject any reserved sentence with an exact whole-sentence match or a shared within-sentence12-word verbatim window. Remove only reserved matches, preserve the first within-Seneca exact duplicate, and apply the original whole-sentence30,000/work and30,000/author budgets with work round robin. The primary graph retains frequency≥5 and at least two distinct shared two-sided lexical-neighbor contexts.

These rules are frozen before Seneca FORM projection. Pre-overlap and post-overlap/pre-budget graphs and individual-work graphs are predeclared diagnostics, not alternative model inputs selected after observing the results. At least ten eligible pairs would permit a later top-ten evaluation; zero candidates supplies no model-accuracy evidence.

## Admission and coverage

| Stage / loss | Sentences | Lexical tokens |
|---|---:|---:|
| Metadata allowlist |1,365|not a normalized word count|
| Excluded multiword-token sentences |375|not admitted|
| MWT-free before overlap/dedup |990|10,284|
| Development-overlap exclusions |0|0|
| Within-Seneca duplicates removed |4|8|
| Final admitted |986|10,276|
| Budget exclusions |0|0|

No exact sentence or12-word development overlap is detected among the990 MWT-free lexical sentences. This checks the admitted development texts, not all historical raw-library exposure, paraphrases or excluded MWT sentences. Seneca is an annotation/current-model reserve, not a guarantee of globally unseen literature.

The final text contains4,820 lexical types,366 reaching frequency5. **Zero pairs share two distinct eligible contexts**, both before and after deduplication. A supplementary FORM-only support histogram, frozen in the review design after the empty primary result, finds only13 pairs sharing one context; none reaches two. These13 are not substituted into the primary graph or scored. The result exposes limited repeated-context coverage without identifying whether sample length, genre, vocabulary or tokenization loss is the principal cause.

| Admitted work | Sentences | Lexical tokens | Frequency≥5 types | Two-frame pairs |
|---|---:|---:|---:|---:|
| *Agamemnon* |317|3,185|71|0|
| *Hercules Furens* |392|4,249|105|0|
| *Oedipus* |277|2,842|52|0|
| Combined primary graph |986|10,276|366|0|

The375 rejected sentences comprise27.47% of the metadata allowlist. Rejecting split tokens preserves the current one-model-word interpretation but has a substantial coverage cost here. Combining the works does not create any qualifying pair, and increasing the budget would not help this already uncapped admitted sample. Neither point licenses an annotation-driven tokenization workaround on the reserved text.

## Implication and next proposal

Do not open Seneca's grammatical labels for this graph: there is nothing to score. Preserve the earlier development shortlist and ranking findings with the new limit that the current repeated-context method may not yield any constraints on short, lexically diverse material. This does not refute Latin or measure a decipherment model's error rate.

Next run the same **label-blind coverage check on the reserved securely attributed Dante prose**, using the existing reserve/work policy and quarantines, the identical budget/normalization/overlap/graph rules, and no Case/POS projection. This tests the remaining longer prose reserve before proposing further model changes. Preserve UDante's conflicting license declarations as unresolved provenance and make no redistribution/relicensing claim; this is a local admission diagnostic, not a resolution of that discrepancy. Do not use disputed/mixed sections to improve candidate counts. If this sample also lacks usable coverage, return to development-only tests of denser context representations or one-frame candidates with matched controls, rather than relaxing rules and presenting the reserved sample as a frozen replication.

The later one-shot model-evaluation proposal remains all four matched pointwise/ranking rich/control variants trained on the same four eligible development authors, with models and evaluation protocol frozen before any reserved labels are opened. No winner is chosen from this coverage check.

## Verification and artifacts

Independent review separately parses ID/FORM, rebuilds every admission/overlap/duplicate record and work budget, and reconstructs graphs by intersecting per-word context sets rather than the runner's per-frame pair expansion. All1,365 allowlisted and986 admitted sentences, three stage graphs and three individual-work graphs match exactly. All20 input/freeze/provenance hashes pass. No POS/Case/other gold fields are decoded, no models/predictions run, and no broad project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration197/` contains the frozen design/proposal and allowlist, admitted FORM records, overlap/loss records, primary/diagnostic graphs, coverage summary, supplementary support histogram, independent audit and verification manifest. Code: `benchmarks/grammar_seneca_coverage_iteration197.py` and `benchmarks/grammar_seneca_coverage_iteration197_review.py`.
