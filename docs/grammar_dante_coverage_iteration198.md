# Dante prose reserve coverage — iteration198

**The allowed Dante prose has enough candidates for the planned transfer evaluation:**26,083 admitted lexical words yield76 eligible word pairs, involving76 endpoint types. This is a coverage result, not restoration accuracy. All POS/Case and other grammatical fields remain unprojected; no models or predictions run.

## Frozen scope and admission

Use only the existing reserved authorDante allowlist for *De vulgari eloquentia* (DVE) and *Monarchia* (Mon). Attributed letters remain unprojected, as do disputed/mixed/quarantined sections. The primary combined-author graph is fixed in advance; individual-work graphs are diagnostics, not alternative evaluation sets chosen for their outcomes.

Apply197/193 rules unchanged: decode token ID/FORM and sentence ID only, lowercase/strip diacritics/j→i/v→u, retain single ASCII lexical forms, reject whole sentences with multiword-token rows, and preserve punctuation/nonlexical/sentence boundaries. Remove reserved sentences with an exact normalized lexical sentence or any within-sentence12-word verbatim window matching any admitted193 development author; remove internal duplicate sentences and apply30,000/work and30,000/author round-robin budgets. Retain the frequency5/two-distinct-context graph criterion. Freeze these rules before FORM projection, with no annotation access or eligibility relaxation.

UDante's pinned README/license declarations still conflict. The exact unresolved flag is preserved in `provenance-status.json`; no terms are reconciled or redistribution/relicensing rights asserted by this local coverage diagnostic. Dante appeared in earlier raw-text experiments, so the reserve concerns new annotations/current model evaluation, not globally unseen literature.

## Admission results

| Stage / loss | Sentences | Lexical tokens |
|---|---:|---:|
| Secure-prose metadata allowlist |1,103|not a normalized word count|
| Excluded multiword-token sentences |135|not admitted|
| MWT-free before overlap/dedup |968|26,122|
| Development-overlap exclusion |1|25|
| Internal duplicate exclusion |1|14|
| Final admitted |966|26,083|
| Budget exclusions |0|0|

The overlap is `Mon-285`, containing a normalized12-word window found in admitted Cicero sentence86568; it is not a whole-sentence match. The internal duplicate is `Mon-195`. Both are removed before constructing the primary graph. This checks the admitted development texts and within-sentence verbatim overlap, not all earlier raw-library exposures or paraphrases; excluded MWT sentences are not claimed overlap-free.

## Frozen graph coverage

| Text / stage | Lexical tokens | Frequency≥5 types | Two-context pairs | Endpoint types |
|---|---:|---:|---:|---:|
| Combined before overlap/dedup |26,122|767|77|76|
| Combined after overlap/dedup — primary |26,083|764|76|76|
| DVE alone, diagnostic |9,376|285|6|11|
| Mon alone, diagnostic |16,707|535|39|51|

The primary text has6,772 lexical types,126 distinct shared frames and400 distinct queried endpoint occurrences. Among pairs sharing at least one context, support multiplicities are1:1,277 pairs;2:60;3:12;4:3;5:1. Only the76 pairs with at least two contexts enter the fixed primary graph; the1,277 single-context pairs are not substituted or scored.

DVE alone cannot support a full top-ten list; Mon alone can. The combined primary pool supplies enough candidates but is one author-level transfer test, not two independent author replications. Having76 candidates says nothing yet about their case applicability, equality, POS or word identities.

## Next: one frozen Case-evaluation pass

Use the four already frozen196 models trained on all four eligible development authors (Aquinas, Caesar, Cicero, Jerome): `point_rich`, `point_control`, `rank_rich`, `rank_control` in the saved Tacitus fold. These same four models are identical in the Palladius fold; the original193 comparison models are different and are not substituted. This avoids fitting or choosing a model after Dante FORM coverage was inspected. The models' rich19/control3 features, source scaling, .1 ridge and source policy remain unchanged.

Before decoding any reserved Case, freeze a new evaluation protocol, all primary target features, all four model outputs and tied top10/20 selections. Evaluate every model on the same76 pairs; report applicability, conditional case equality, joint yield and pair/type coverage, plus AUC for rankings and NLL/Brier/calibration for pointwise probabilities. Include the fixed source-prior comparator and all-candidate baseline. No target-selected winner, threshold/feature/source change or policy routing; empty/sparse secondary diagnostics cannot replace the primary graph. POS fields need not be opened for this Case-only test. Report the result as one annotation-reserved author transfer with prior raw exposure, preserving any failures as well as successes.

## Verification and artifacts

Independent review rebuilds all1,103 allowlisted and966 admitted sentence records, exact/12-word overlap, deduplication and work budgets from ID/FORM only. Its occurrence-first per-word context-set intersections independently reconstruct the three stage graphs and two work graphs, including all support multiplicities. All21 input/freeze/provenance hashes pass, the unresolved declaration flag matches collection metadata, and no grammatical fields, predictions or models are evaluated. Dedicated audit passed; no broad project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration198/` includes frozen design/proposal, allowlist/admitted FORM records, overlap/loss records, graphs/summary, provenance flag, support histograms, independent audit and verification manifest. Code: `benchmarks/grammar_dante_coverage_iteration198.py` and `benchmarks/grammar_dante_coverage_iteration198_review.py`.
