# Iteration 123: scalar ADP confidence has an insufficient ordering

No global ADP-confidence cutoff meets both frozen requirements on the current source-test inputs: at least 90% PP precision and retention of 80% of the ungated correct PP selections. This is an oracle-only feasibility diagnostic, not a selected deployment policy.

The experiment keeps the iteration-118 class probabilities, iteration-120 opaque inputs, original PP model and primary cutoff 0.80 fixed. Predicted conjunctions remain conjunctions; predicted prepositions below the confidence cutoff become unknown. All sixteen target lexical identities remain hidden. All ten attained cutoff settings (nine distinct assignments) were enumerated before scoring; predictions were frozen before consulting cached PP labels.

| State | Correct PP | Wrong PP | Precision | Correct retention |
|---|---:|---:|---:|---:|
| Ungated | 235 | 34 | 87.36% | 100% |
| First effective abstention | 185 | 31 | 85.65% | 78.72% |
| Maximum correct coverage among settings reaching 90%, with fewer errors | 183 | 12 | 93.85% | 77.87% |
| Required | ≥188 | — | ≥90% | ≥80% |

The first removed type is correctly classified `de`, whose ADP confidence is 0.5311. Mistaken ADP assertions for `c` and `uel` have higher confidence, 0.5472 and 0.5548. Thus every effective abstention already falls below the coverage requirement. The high-precision state loses 52 correct selections while removing 22 errors; it adds no new correct selections. These named types explain the diagnostic and are not proposed word-specific exceptions.

The same exhaustive check on the union of calibration and test confidence breakpoints found no jointly feasible absolute cutoff across seventeen intervals. Interval endpoints and interior representatives were replayed with the inclusive confidence rule. This rules out solving the present failure merely by choosing another scalar cutoff under these constraints. It does not rule out better class models, richer evidence, or other structural models.

The positive structural result from iteration 120 remains: inferred opaque classes substantially improve PP recovery over unknown classes. Iteration 122's source-selected gate remains a failed transfer attempt. No policy, PP threshold, annotation, reserve evaluation, lexical restoration claim, or default changed here. These repeatedly used development labels do not provide fresh confirmation.

Next proposed experiment: balance ADP/CCONJ loss during first-stage class-model training on the existing thirteen noncatalogue types (ten ADP, three CCONJ), retaining the strict sixteen-type exclusion. Unlike another scalar intercept, this can change feature weights and confidence ordering. Freeze the model and its type-held-out calibration before downstream evaluation; retain the same precision and coverage requirements.

Validation: independent audit verified 35 input hashes, recomputed 18 PP score vectors, checked 144 confusion/transition groups, and replayed all ten cutoffs and seventeen joint intervals. All 33 focused tests passed. Full curves, secondary settings, fixed-cohort metrics, and frozen artifacts are in `experiments/results/grammar-restoration/iteration123/`.
