# Iteration 104: added unlabeled Caesar context improves exact pair repair

**Preserve this positive conditional finding:** with the same 100 annotated Caesar sentences and unchanged classifier, core and cutoff, added unlabeled prose increases exact synthetic pair repairs from **4 correct / 1 wrong to 9 correct / 0 wrong**. All fifteen error pairs rank first after expansion, versus seven originally. No new annotations or lexical nuclei are recovered; the eight candidate anchor names and 195 context anchors are supplied, and the tested error is one global bijective cross-class swap.

## Frozen context selection and preprocessing

Use only the six existing cached HTML files for Gallic V–VII and Civil I–III, verifying their recorded raw hashes. Extract consecutive numbered prose chapters; discard navigation and numeric labels. Normalize lowercase, v/u and j/i; tokenize letters and split at `.`, `!` or `?`. Retain all resulting nonempty segments. This heuristic splits abbreviations and does not reproduce treebank sentence segmentation.

Before model scoring, exclude an entire book if its prose shares any contiguous 80 normalized letters with any of the scored sentences, ignoring whitespace, punctuation and token boundaries. This excludes Gallic VI, which contains the scored passage. Gallic V, VII and Civil I–III remain. No Gallic I–IV file or sealed lexical test is opened. This overlap check is a deterministic exclusion rule, not proof against every possible edited near-duplicate.

Freeze three views: original 100 sentences; original plus Civil I–III (secondary); original plus all five admitted books (primary). Do not select among them using outcomes. The primary view has 2,494 segments and 52,691 tokens, versus 100 sentences / 1,514 tokens originally; the Civil view has 1,674 segments / 33,839 tokens. The original 100 sentences remain an identical prefix in every public view.

All views share one word-to-opaque-ID mapping. Every synthetic anchor swap applies globally to original and added occurrences. Keep the source-trained classifier, 195 given context anchors, eight candidate types, minimum-five-occurrences/three-sentences eligibility, all fifteen errors and three clean/same-class controls. Unknown words remain opaque. Reuse the frozen iteration-95 cutoff and iteration-103 gain-gap rule; do not recalibrate. The iteration-103 uncertainty policies remain OFF. Recompute 256 sentence-cluster bootstrap resamples per view only to describe ranking uncertainty.

## Pair-repair results

| Fixed rule or diagnostic | Original 100 | Plus Civil I–III | Primary expansion |
|---|---:|---:|---:|
| Iteration 95 cutoff: correct / wrong / abstained errors | 4 / 1 / 10 | 8 / 0 / 7 | 9 / 0 / 6 |
| Iteration 103 gain-gap: correct / wrong / abstained errors | 4 / 0 / 11 | 8 / 0 / 7 | 7 / 0 / 8 |
| Raw top-ranked correct pair | 7 / 15 | 15 / 15 | 15 / 15 |
| True pairs meeting support gate | 8 / 15 | 15 / 15 | 15 / 15 |
| Correct top pair with descriptive stability ≥0.90 | 4 / 15 | 14 / 15 | 15 / 15 |

All three clean/same-class controls abstain under both active rules in every view. OFF rules abstain throughout. Do not interpret the descriptive stability row as a calibrated or adopted policy.

At the original cutoff, the primary expansion retains all four original successes, repairs the formerly wrong `ex/sed` case, and adds four successes from abstentions (`ad/sed`, `de/que`, `de/sed`, `in/sed`). This is five additional exact repairs plus removal of the one wrong recommendation. The six remaining errors abstain despite correct ranking; their gains are below the fixed cutoff. No threshold is lowered after inspecting them.

More context is not uniformly beneficial under every rule: the Civil view loses the original `in/et` success at the old cutoff. With the stricter gain-gap rule, primary expansion loses both `ad/et` and `in/et` while adding five successes, giving a net gain of three. The `ad/et` primary gain (about 0.6513) falls just below the frozen 0.6554 gain-gap threshold; the `in/et` gain (about 0.6225) also falls below it. Preserve these counterexamples rather than selecting a view or rule post hoc.

## Mechanism and limits

The original sample contains only four `a` and two `sed` occurrences, so seven true error pairs lack supported endpoints. Primary expansion raises these counts to 256 and 177 and makes all fifteen pairs supported. Other types also gain substantial evidence: `ex` 10→582, `de` 9→246, `et` 19→1,033, `ad` 23→858 and `in` 44→1,122.

Raw attached `-que` forms are not split: the separate `que` count remains 48 throughout. This is a meaningful mismatch between added prose and the syntactically tokenized original sample, so improvements cannot be attributed to uniformly better sampling of every type. No word-specific enclitic exception is introduced. Despite this limitation, all primary error-pair rankings are correct and have bootstrap stability at least 0.9414. This remains a small correlated synthetic development diagnostic, not a guarantee of precision, author-general transfer, mapping discovery or arbitrary cipher restoration.

Original-sentence probability totals are unchanged for every case across views; improvements come from added occurrence evidence and eligibility, not changed local features on the scored passage. No new grammatical annotations were read or generated. This iteration measures anchor repair, not downstream PP membership: actual grammatical benefit on the fixed 100 sentences still needs to be measured.

## Verification and next experiment

Replay all 54 case bootstrap matrices, recompute 45 clean pair probability profiles and 1,620 endpoint-by-sentence count arrays, and reproduce 195 original Caesar pair scores against the prior cache under renamed opaque IDs. Check context-selection hashes, identical public scored prefixes and per-case original probability totals, global mappings and unchanged policies. All 57 focused tests pass. Artifacts, raw selection, public inputs, frozen policies, pair actions, complete counterexamples and audits are in `experiments/results/grammar-restoration/iteration104/`.

Next apply every frozen recommendation from all three views blindly to the original 100-sentence input, then evaluate the existing PP-membership models at their original thresholds against the already cached annotations. Compare original corruption, repair and clean reference, including wrong repairs and lost correct decisions. This will determine whether the additional exact anchor repairs restore more grammatical structure; pair correctness must not gate applying a recommendation. No reserve, fresh annotation or lexical test is needed.
