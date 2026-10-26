# Dante word×POS Case-profile audit — iteration200

**The contextual Case signal survives the stricter profile control.** Across the fixed Dante graph, conditional equality remains92.98%, above all199 word×POS-profile shuffles (maximum78.51%). The strongest supported component is pronoun/determiner comparisons: both-PD equality97.62% across14 applicable pairs, versus a maximum82.74%. This is evidence beyond word/POS Case frequencies, not POS prediction or named-case restoration.

The selection limitation also survives. The primary top ten includes only three of those fourteen both-PD pairs; all three have100% equality in every strict null as well as the real text. Their high equality therefore does not demonstrate contextual recovery. The useful graph association and the selector's success at finding it must remain separate claims.

## Frozen follow-up and annotation state

Reuse198's76-pair graph and all199 models, outputs and eleven selections unchanged. Freeze the existing all/PD-involving/both-PD/exactly-one-PD/neither-PD strata, wherePD means PRON or DET, before projecting UPOS. Read UPOS only from the198 admitted966 DVE+Mon sentences; reuse199 Case references and never feed target POS into model inputs or selection. Attributed letters, quarantines and Seneca grammatical references remain unprojected.

This consumes the admitted Dante POS reference for follow-up. Its Case reserve was already consumed in199; this is not a second fresh author evaluation. Prior raw-literature exposure, unresolved UDante declaration provenance, source models and primary graph are unchanged.

For each of199 fixed seeds19900–20098, shuffle Case—including missing values—within each (opaque word, POS) bucket. Keep graph, tags, lists and every bucket's Case inventory/frequencies fixed. There are6,772 lexical types,6,935 word×POS buckets,154 multi-POS types and445 buckets with variable Case values. All153 unordered pairs of17 UPOS tags, including zeros, are retained for every fixed list; no favorable family is selected after inspection.

## Full-graph composition and strict controls

An active stratum edge has at least one occurrence comparison in that stratum. It need not have two stratum-specific frames: the primary word-pair eligibility still requires two frames overall. A pair can be active in multiple strata, so active-edge counts are not additive; occurrence-comparison counts partition exactly into both/exactly-one/neither. Conditional equality averages within-frame matching fractions over Case-covered frames, then Case-applicable edges.

| Fixed stratum | Active edges | Case-applicable edges | Case comparisons / all comparisons | Conditional equality | Strict-null maximum | Nulls ≥ observed |
|---|---:|---:|---:|---:|---:|---:|
| All |76|19|96/336|92.98%|78.51%|0/199|
| PD-involving |27|17|80/123|92.16%|75.98%|0/199|
| Both PD |14|14|69/69|97.62%|82.74%|0/199|
| Exactly one PD |13|3|11/54|66.67%|100%|79/199|
| Neither PD |52|2|16/213|100%|100%|62/199|

Both-PD comparisons involve18 endpoint types and66/69 matching occurrence comparisons; the97.62% figure is the edge/frame macro measure, not that pooled95.65% ratio. The other small strata do not establish corresponding contextual recovery. The neither-PD Case comparisons are ADJ/VERB, not evidence for a general noun-phrase classifier. All tag-pair counts are reference measurements, not inferred POS labels.

Full-graph joint yield over all76 selected pairs is23.25%, versus a strict-null maximum19.63% (0/199 at least actual). Word×POS shuffles retain18–19 Case-applicable graph pairs, versus19 observed, so some conditional denominators still vary; every profile is nevertheless preserved exactly. Tail counts are descriptive controls under this exchangeability assumption, not universal confidence estimates. Edges share word types and contexts, and no deletion robustness claim is made here.

## Why the primary shortlist is not capturing this signal

The unchanged rich-ranker top ten contains6 Case-applicable pairs and12 Case-involved endpoint types, as in199. Its all-stratum equality83.33% is unexceptional against the stricter nulls (mean83.12%, maximum100%,120/199 at least observed). All199 strict nulls retain exactly6/10 applicability, so that outcome is compatible with preserved word/POS profiles.

The three both-PD shortlisted pairs have19/19 matching Case comparisons; all199 strict nulls also give those three100% equality. Only3/14 both-PD pairs are selected, and these three show no equality surplus over their word×POS profiles. The other shortlisted Case comparisons comprise one ADJ/PRON pair with0/4 matches and two ADJ/VERB pairs with16/16; the latter stratum is too small and compatible with its nulls. This explains why high shortlist equality alone is an inadequate success criterion.

The supported achievement is **a context-sensitive Case-compatibility association, especially within pronoun/determiner substitutions in shared slots**. The unsupported extension would be saying that the model identifies those informative pairs reliably or restores PRON/DET labels, named cases or exact words.

## Next algorithm proposal: learn contextual surplus

Return to the four non-sparse development authors and change the selector's supervised target from “any Case comparison exists” to **agreement above word×POS-profile expectation**. Keep their193 graphs and19/3 anonymous features, target-author exclusion and source-only scaling fixed; do not train on Dante or inject target POS/Case into prediction.

Define an edge target using the mean over its shared frames of the mean over all Cartesian comparisons of: observed matching-recognized-Case indicator minus the analytic matching probability from the two source word×POS Case profiles. Missing Case contributes zero matching probability; endpoint words are distinct, so the profile-preserving shuffle expectation is the product of their profile probabilities summed over recognized cases. This makes context-independent perfect pairs score zero in expectation and rewards surplus contextual agreement, while avoiding conditional-denominator artifacts. Preserve full profiles as the null specification rather than choosing labels after seeing target ranks.

Freeze a simple source-author-balanced ridge regression (.1 slope penalty, unpenalized intercept), rich19/control3, using the same four contrast-eligible source-author policy as196; each held-out development author is excluded from fitting and scaling. Compare with the existing196 matched classifier/ranker, reporting all four authors and top10/20 with ties. Primary metrics should be shortlist mean surplus and positive-surplus pair count, with applicability/equality/joint yield/type coverage as secondary costs; raw regression scores are not probabilities. No target-chosen winner or source subset. This tests whether the current bottleneck is the training target, without first changing features or calling another Dante probe fresh validation.

## Verification and artifacts

Independent review reprojects30,806 admitted integer-row POS values, reconstructs all380 real stratum-edge scores,55 real metric groups and1,683 tag-composition cells, and checks exact comparison partitions. It independently replays all199 strict shuffles,75,620 stratum-edge scores and10,945 null metric groups, with every word×POS Case profile preserved. All32 input/selection/prior-manifest hashes pass; all199 all-group baselines and model outputs stay unchanged. No model is fitted and no POS label is predicted. Dedicated audit passed; no broad project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration200/` contains frozen design/proposal/selections, POS references, stratum details/metrics, complete tag composition, bucket summary, all strict nulls/comparisons, independent audit and integrity manifest. Code: `benchmarks/grammar_dante_pos_profile_iteration200.py` and `benchmarks/grammar_dante_pos_profile_iteration200_review.py`.
