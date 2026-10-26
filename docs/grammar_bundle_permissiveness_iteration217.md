# Iteration217: relevance gain exceeds permissiveness, precision remains weak

**Preserve the controlled retention gain:** with exactly95 admissions in Aquinas, relevance weighting retains6 supported centers versus2 for the original applicability ranking. With13 admissions in Cicero it retains2 versus1. A source-prior-only adjustment also falls short. Reweighting changes which useful centers survive, rather than merely broadening the filter; however it retains more non-Case centers, and top-five precision remains low.

## Frozen controls

Use unchanged216 predictions,207 full12 support order and305 centers. Compare baseline.5, balanced.5, baseline applicability top-K admission with K equal to the balanced filter's anonymously predicted count, and a baseline intercept-only prior adjustment. Preserve all ties, including any admission-size excess; no excess occurs in these four targets. Both priors are computed from the other three authors: original equal-author Case-bearing prevalence, and216's source-weighted prevalence. Add their log-odds difference to the baseline logit, then filter at.5.

Freeze priors, gates and tied top3/top5 lists before aggregating target labels. Target annotations enter neither K nor the prior adjustment. No refits, threshold search, new annotation, raw text, reserves or author-specific winner selection. This is reused-development diagnostic evidence, not fresh validation or calibrated-confidence restoration.

## Admissions and retained support

Cells show admitted centers / supported centers retained / false Case admissions. False Case admission means zero recognized global Case, not an ungrammatical word.

| Author | Baseline | Balanced | Size-matched baseline | Prior-only baseline |
|---|---|---|---|---|
| Aquinas |35 /0 /7|95 /6 /38|95 /2 /30|55 /0 /15|
| Caesar |14 /0 /4|21 /0 /10|21 /0 /10|19 /0 /8|
| Cicero |6 /0 /1|13 /2 /4|13 /1 /3|11 /1 /3|
| Jerome |96 /3 /35|102 /3 /39|102 /3 /38|101 /3 /37|

At the same total231 admissions, balanced retains11/13 supported centers versus6/13 for the size-matched baseline. Its non-Case admissions total91 versus81. More supported centers therefore survive at the expense of broad Case selectivity; no simple “better applicability classifier” claim follows. Prior-only admits186 centers and retains4/13. Caesar has no supported centers in the teacher and cannot contribute a support-retention comparison.

## Supported-center shortlist precision

Cells show supported/selected top3, then top5; every listed shortlist has the requested size.

| Author | Baseline | Balanced | Size-matched baseline | Prior-only baseline |
|---|---|---|---|---|
| Aquinas |0/3;0/5|1/3;1/5|0/3;1/5|0/3;0/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |0/3;0/5|2/3;2/5|1/3;1/5|1/3;1/5|
| Jerome |1/3;1/5|0/3;1/5|0/3;1/5|0/3;1/5|

The controlled retention improvement is strongest in Aquinas, but its top5 does not improve over the size-matched control. Cicero improves1/5→2/5. Jerome and Caesar show no top5 benefit. Retention is a useful component property, while remaining false admissions and support ordering still prevent reliable extraction. No exact words, named cases or POS are recovered by this comparison; all support labels remain gold-reference conditional detections.

## Verification and next diagnostic

Independent source priors, odds-ratio probability adjustment, gate membership, sorting/tie replay,32 shortlists, scalar metrics, exact216 baselines and26 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration217/`.

Next inspect the **support ranker's** source-side head using unchanged207 models, rather than further adjusting the applicability threshold. Evaluate each model on all four authors, explicitly source-in-sample versus held-out, with original candidates and the clearly oracle globalCase>0 candidate set. Freeze scores before metrics; retain both rich12/count4, all authors, tied top3/top5 and all supported rank intervals. This separates support-objective/source-fit limitations from support transfer and from irrelevant non-Case competition. Oracle results are diagnostic only, and source results are not validation.
