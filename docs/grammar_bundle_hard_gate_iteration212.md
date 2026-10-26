# Iteration212: hard applicability gating rejects the supported subpopulation

The fixed.5 gate does not rescue the learned applicability model. Both full12 and count4 reject **all seven supported Aquinas centers**; full12 also rejects all three Cicero centers. This is a failure to retain the Case-bearing subpopulation relevant to the support teacher, not merely an unfortunate soft-product formula. No hard gate is adopted.

## Frozen experiment

Use unchanged211 applicability predictions at probability>=.5, then rank eligible centers by the matching original207 support scores. Both full12/count4, all four authors, tied top3/top5 and all false exclusions are reported. Freeze memberships/lists before loading support labels for evaluation. No fitting, threshold scan, feature changes, raw text, new annotations or reserve use. Compare original207, soft-product211 and oracle210 results without selecting a per-author winner. The oracle and inferred gates remain distinct.

## What the gate retains

| Author | Full12 eligible | True Case-bearing eligible | Supported retained | Count4 eligible | True Case-bearing eligible | Supported retained |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |35|28|0/7|86|63|0/7|
| Caesar |14|10|0/0|14|10|0/0|
| Cicero |6|5|0/3|8|7|1/3|
| Jerome |96|61|3/3|93|57|2/3|

Full12 retains3/13 supported centers across the three positive authors; count4 also retains3/13, with different membership. Zero supported Caesar centers is the teacher's limitation, not a measured gate recall of zero. Retaining many genuinely Case-bearing centers therefore does not imply retention of useful contextual evidence.

Aquinas supported-center applicability probabilities range.02789–.28242 for full12 and.18558–.43225 for count4. These are not all borderline. Cicero full12 probabilities are.39922–.44450; count4 spans.39747–.51223. Jerome spans.50935–.64139 full12 and.48710–.53777 count4. These ranges are descriptive after the frozen test; they do not authorize tuning a threshold to the target supported centers.

## Supported-center shortlists

Cells show supported/selected top3, then top5.

| Author | Full12 hard gate | Count4 hard gate | Original full12 | Full12 soft product | Full12 oracle |
|---|---|---|---|---|---|
| Aquinas |0/3;0/5|0/3;0/5|0/3;1/5|0/3;1/5|3/3;5/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |0/3;0/5|0/3;0/5|0/3;1/5|1/3;2/5|2/3;2/5|
| Jerome |1/3;1/5|1/3;2/5|0/3;1/5|0/3;0/5|1/3;1/5|

Jerome's count4 result is a limited improvement over its original0/3;0/5 and soft-product0/3;0/5. It retains two supported centers at gated ranks1 and4. Full12 retains all three at ranks2,15,25; its residual failure is ranking, while Aquinas/full12 Cicero fail already at admissibility. Count4 Cicero retains one supported center at rank7, outside top5. These are separate mechanisms; neither a universal threshold change nor author-specific routing follows.

Applicability truth is cached recognized Case on at least one occurrence; support truth is205's gold-reference conditional evidence test. Neither names a Latin word or a POS. Non-Case centers may contain other useful grammatical information. No new reliable grammar or nuclei restoration is established.

## Verification and next diagnostic

Independent thresholding, sorted tie groups, all16 lists,26 supported-center retention/rank records, scalar metrics and exact original/product/oracle comparators pass, alongside48 hashes. Artifacts: `experiments/results/grammar-restoration/iteration212/`.

Next audit which reference grammatical subpopulations the classifier accepts versus rejects: fixed global and queried POS distributions for all eligible centers, true Case-bearing centers, supported retained/rejected centers and admitted unsupported heads. Include all authors/both frozen predictors, center-level and occurrence-weighted summaries, and source-scaled feature/logit contrasts. Use only cached development annotations, no identities, new models, thresholds or reserves. Test whether the binary applicability objective transfers to an easier but irrelevant subclass before proposing another learner. This is a reference diagnostic, not POS restoration.
