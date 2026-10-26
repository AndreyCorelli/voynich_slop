# Iteration216: relevance weighting repairs retention, not shortlist precision

**Preserve the retention result:** source supported-center retention rises10/39→38/39 evaluation instances; held-out retention rises3/13→11/13. Yet hard-filter top5 reaches only1/5 Aquinas,0/5 Caesar,2/5 Cicero and1/5 Jerome. Applicability discrimination worsens in every author, and admissions expand substantially. This is a useful conditional modeling result, not a reliable extractor or restored words.

## Frozen experiment

Same305 centers, twelve anonymous features and binary recognized-Case existence labels as211. Compare unchanged full12 baseline against one source-only loss weighting. Each of the three source authors receives equal total mass; within each, each nonempty group receives equal mass: supported Case-bearing, other Case-bearing, no recognized Case. Weights are uniform within groups. Every supported source center is checked to be Case-bearing. Caesar has no supported group, so its two remaining groups each receive half its author mass.

Source support labels determine source weights only; the held-out author's support labels enter neither fit nor scaling. Logistic weighted mean NLL plus.05 squared slope norm, free intercept, source-only weighted standardization. Freeze features before labels and weights/models/all author predictions/gates/lists before evaluation. Fixed.5 hard gate then unchanged207 full12 support order; fixed applicability×support product; tied top3/top5; no threshold/model/author selection, raw annotation or reserve use. Reweighting changes both the objective and scaling, and the induced probability prior; no calibrated-confidence claim.

## Retention and admission

| Author | Baseline eligible | Balanced eligible | Truly Case-bearing admitted, baseline→balanced | Supported retained, baseline→balanced |
|---|---:|---:|---|---|
| Aquinas |35|95|28→57|0/7→6/7|
| Caesar |14|21|10→11|0/0→0/0|
| Cicero |6|13|5→9|0/3→2/3|
| Jerome |96|102|61→63|3/3→3/3|

Across source fits, the same13 supported centers are evaluated three times each:39 instances are dependent, not39 independent examples. Their retention increases10/39→38/39; held-out retention3/13→11/13 is development evidence on reused authors. Simply accepting everything would retain13/13, so retention alone does not establish useful selectivity. Balanced gates admit231/305 centers versus151/305 baseline; the gain must be separated from general permissiveness.

## Shortlist yield and costs

Each cell shows supported/selected top3, then top5.

| Author | Baseline hard | Balanced hard | Baseline product | Balanced product |
|---|---|---|---|---|
| Aquinas |0/3;0/5|1/3;1/5|0/3;1/5|1/3;1/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |0/3;0/5|2/3;2/5|1/3;2/5|1/3;2/5|
| Jerome |1/3;1/5|0/3;1/5|0/3;0/5|0/3;1/5|

Despite retaining6/7 supported Aquinas centers, its balanced hard top5 captures only one: support ranking and remaining false admissions still prevent the oracle5/5 result. Jerome retains all three but loses the baseline top3 hit. No author-specific routing or universal adoption follows.

Applicability AUC baseline→balanced: Aquinas.6304→.5694, Caesar.8561→.7955, Cicero.8807→.7789, Jerome.6498→.6173. NLL improves only Aquinas(.8250→.7167), worsening Caesar(.5789→.6572), Cicero(.5700→.5995), Jerome(.8853→.9496). Case-bearing false admissions increase7→38,4→10,1→4,35→39. Improving supported retention does not imply improved broad applicability classification.

The source objective can therefore recover much of the previously neglected subpopulation under the same features and model family; earlier failure was not explained solely by transfer or complete feature incapacity. This does not isolate weighting from its changed scaling/prior, prove improved discrimination within the useful subclass, or establish calibrated confidence. No POS, named cases or Latin nuclei are restored.

## Audit and next control

Independent group membership/author weights, source scaling and four Newton refits reproduce all models;32 prediction groups,32 tied lists, scalar applicability/support metrics, source retention, exact214/215 baselines and28 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration216/`.

Next test whether the retention gain exceeds mere permissiveness. Compare frozen balanced gates with baseline-applicability top-K admission where K equals the balanced gate's anonymous predicted admission count, keeping all cutoff ties and reporting any size excess. Add an intercept-only baseline adjustment using source original versus balanced Case-label priors, with no target labels or refit. Keep support ordering/top3/top5 fixed and report admissions, true/false Case coverage, supported retention and actual shortlist yield. These controls separate changed ranking from a broader gate; do not claim improvement from retention alone.
