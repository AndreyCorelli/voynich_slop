# Iteration 170 — remove a context word across all frames

The conditional case association survives every single context-word removal in both Cicero passages, but the smaller passage no longer beats every matched shuffle maximum. This supports retaining the relation as a possible morphological input; it does not establish named-case recovery, case-bearing detection, POS restoration, or lexical nuclei.

## Frozen diagnostic

Use exactly the earlier and replication floor-five, two-distinct-frame graphs. Enumerate every opaque context ID from actual graph frames before consulting case labels: 74 in the earlier passage and 119 in the replication passage. Remove each ID from either side of every frame as primary; left-only and right-only removals are fixed controls. Apply identical removals to all sixteen shuffle graphs, reapply two-frame support, and retain every outcome, including empty outcomes. These are graph removals, not changes to the original token streams or independent experimental replications. Detailed scores were saved in compressed JSON before summaries.

## Results

| Passage | Removal | IDs tested | Remaining case edges | Conditional agreement range | Above matched null maximum |
|---|---|---:|---:|---:|---:|
| Earlier | Either side | 74 | 12–18 | 66.67–76.67% | 72/74 |
| Earlier | Left only | 74 | 12–18 | 66.67–76.47% | 74/74 |
| Earlier | Right only | 74 | 15–18 | 70.59–76.47% | 73/74 |
| Replication | Either side | 119 | 26–36 | 63.46–77.04% | 119/119 |
| Replication | Left only | 119 | 30–36 | 66.16–74.55% | 119/119 |
| Replication | Right only | 119 | 29–36 | 68.27–75.23% | 119/119 |

No actual removal leaves an empty case set. Unchanged baselines exactly reproduce iterations 166 and 168: 72.22% on 18 case edges and 70.41% on 36 case edges. These percentages average frame agreement within an edge and then average covered edges; only occurrence pairs with recognized cached case labels are evaluated.

The two primary exceptions are earlier `either15` (66.67%, 12 case edges) and `either73` (70%, 15 case edges). Each is exceeded by one shuffle at 75% on just two case edges (`word16412` and `word16402`, respectively); `right73` has the same latter exception at 70.59% on 17 actual case edges. The exceptions combine a drop in actual agreement with higher null maxima than the original 50%; they must not be removed post hoc. Opaque IDs and every control score remain in the artifacts.

## Interpretation and next check

No single context word eliminates the measured case association, and the larger passage retains separation under every intervention. Universal superiority to the sixteen null maxima fails in the smaller passage, so iteration 169's stronger statement cannot be extended to context-word removals. Coverage remains narrow, evaluation conditional on gold case availability, and both passages are previously used development data from one author.

Next audit grammatical-family concentration: evaluate the unchanged graph separately for pronoun/determiner-involving edges and other case-bearing POS families using existing cached occurrence labels, with the same splits in the nulls. Freeze the family definitions and report all sparse/empty strata before scoring; these labels are diagnostic references, never an inference filter. This tests whether the apparent general morphological input is largely a pronoun/determiner phenomenon before incorporating it into any decoder.

## Verification and artifacts

Independent replay reconstructs the ID universe, frame removal conditions, direct Cartesian case counts, every detailed edge record, summaries, matched-null contrasts, ranges, and exact historical baselines. All input and score hashes passed; no new annotations or reserved/sealed data were used. Dedicated benchmark audits passed; the broader test suite was not rerun for this reference-only diagnostic.

Artifacts: `experiments/results/grammar-restoration/iteration170/` includes frozen design, interventions, compressed full scores, summaries, contrasts, ranges, audit, and verification manifest. Runner: `benchmarks/grammar_context_concentration_iteration170.py`; independent reviewer: `benchmarks/grammar_context_concentration_iteration170_review.py`.
