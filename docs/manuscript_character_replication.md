# Frozen manuscript character-prediction replication

Seven plan → test → assessment iterations replicate the preceding-suffix prediction gain on **116 folios not previously scored by the statistical prediction experiments**. Two fixed cohorts gain 0.00766 and 0.00931 bits/EVA character, compared with the earlier 0.00915. The combined gain is **0.00848**, positive on **89/116 folios**. It survives artificial line-layout replacement and remains positive on unseen spellings. This is a replicated statistical dependence, not a language or cipher identification.

## Seven iterations

| Iteration | Plan/test | Assessment → next action |
|---|---|---|
| 1 | Freeze exclusions, 116 eligible folios, hash-split cohorts and all controls | Proceed to cohort A without new model selection. |
| 2 | First eligible 32-word block on each of 58 A folios | Gain replicates. Test disjoint-folio cohort B. |
| 3 | First eligible block on 58 B folios | Gain replicates again. Test artificial line layout. |
| 4 | Refit/score A and B under eight-word artificial lines | Both gains remain positive. Inspect preset transition gates. |
| 5 | Within-line and cross-line suffix variants on A/B | Most overall gain is within-line. Test refitted nulls. |
| 6 | Three independent-stream inventory-preserving nulls | Gains near zero. Score predeclared additional blocks. |
| 7 | All remaining complete eligible blocks on these folios | Disjoint words also show positive gain. Retain frozen effect without mechanism inference. |

## Results

Positive gain is lower loss than the position-aware within-word model. Main gains average folios equally, include end-of-word cost and use actual EVA-character count as denominator. Novel-spelling gains pool their character losses separately.

| Case | Words | Folios | Gain bits/character | Novel-spelling gain |
|---|---:|---:|---:|---:|
| Cohort A, transcription layout | 1,856 | 58 | +0.007656 | +0.001894 |
| Cohort B, transcription layout | 1,856 | 58 | +0.009310 | +0.003401 |
| A, eight-word lines | 1,856 | 58 | +0.006183 | +0.000910 |
| B, eight-word lines | 1,856 | 58 | +0.008168 | +0.002565 |
| A, within-line gate | 1,856 | 58 | +0.007306 | +0.001775 |
| B, within-line gate | 1,856 | 58 | +0.009135 | +0.003330 |
| A, cross-line gate | 1,856 | 58 | +0.000350 | +0.000118 |
| B, cross-line gate | 1,856 | 58 | +0.000175 | +0.000071 |
| Refitted null seed 30001 | 3,712 | 116 | −0.000233 | −0.001015 |
| Refitted null seed 30002 | 3,712 | 116 | −0.000511 | −0.000789 |
| Refitted null seed 30003 | 3,712 | 116 | +0.000162 | −0.000975 |
| Additional disjoint words | 7,328 | 56 | +0.013584 | +0.011402 |

The combined primary gain is 0.008483, with a **descriptive** folio bootstrap interval saved in `assessment.json`. Artificial-layout combined gain is 0.007175. Three null realizations are not a formal significance test or false-positive calibration. Additional-block scores use 56 of the same 116 folios, so they are a disjoint-word continuation check rather than an independent-folio replication; their larger gain is not evidence of an increasing effect with sample size.

## Frozen sampling and controls

Keep the original 1,024 training words and original selected second-order/position/all-transition suffix model. Exclude every development/evaluation folio from the earlier text-generation, word-context, line-context and open-spelling experiments, plus f1r used in the cipher pilot. A source scan finds 116 other folios with complete clean 32-word blocks. Sort them by SHA-256 of `replication-30001:` plus folio label; first 58 become A and remaining 58 B. Primary evaluation takes the first eligible block per folio; stage seven uses all subsequent eligible blocks.

Blocks respect folio boundaries and excluded-record barriers. A/B folios are disjoint, and all 11,040 primary/additional word occurrences are disjoint. Source words, positions and line identities (`folio:locus:physical_line`) are retained and checked against raw processed records. Folio metadata is recorded but not used for result-based selection.

“Previously unscored” is scoped to the listed statistical experiments. Earlier manuscript-wide descriptive audits inspected the complete manuscript, and this is not full data blindness or proof that no older solver artifact touched any selected word. The model and sampling plan are frozen before likelihood scoring; no gate/layout variant replaces the primary model after evaluation.

Layout sensitivity changes both training and evaluation to four eight-word lines per block while keeping words fixed. Gate variants condition only within-line or cross-line transitions; their gains use all characters as denominator, rather than comparing per-transition losses across strata.

Refitted nulls reorder words without replacement within folio × position-bin × length pools. They preserve exact word inventories, slot lengths, layout and novelty counts. Train/evaluation random streams are independently seeded. Model and baseline are refitted to each null; baseline folio losses remain invariant. There are 12 scored cases, 33,312 case-word evaluations, and zero Z3 calls.

## Interpretation and limits

The prior positive effect is not confined to its original 50-folio cohort. New cohorts, artificial layout and additional words retain it, while refitted nulls remove it approximately. This supports local ordering dependence beyond the tested within-word/position baseline, especially within transcription lines.

It does not identify why the dependence exists. EVA is a transcription convention rather than established glyph segmentation. Line proxies, the four position bins, source exclusions, original development selection and first-eligible-block sampling remain limitations. Folios can share scribes, sections or text production processes; bootstrap uncertainty is descriptive. A positive gain can arise from natural language, context-dependent encoding, local generation or other structure. The matched synthetic controls already show that a known ordering intervention can reproduce its scale.

Next priority: **compare matched synthetic boundary-conditioned encoding and local-generation mechanisms** using this frozen predictive statistic together with spelling/frequency checks. Start with known reversible encoding and known generated-text fixtures, and record whether both reproduce the effect. Its replicated magnitude alone cannot choose between them; avoid further internal calibration tuning or historical-language ranking on that basis.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.manuscript_character_replication --run
.venv/bin/python -m benchmarks.manuscript_character_replication_validation
.venv/bin/python -m benchmarks.manuscript_character_replication_assessment
.venv/bin/python -m pytest tests/integration/test_manuscript_character_replication.py -q
```

Three tests pass. Independent probability reconstruction verifies **66,624 context/position-model word scores**, all plan/result chains, aggregates, raw manuscript fields, folio exclusions, A/B separation, primary/additional word disjointness, null inventories and invariant baseline losses. Other stored gains are summarized from the frozen predictor rather than independently reconstructed here.

Artifacts: `experiments/results/manuscript-character-replication/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Prior modules/results remain intact.
