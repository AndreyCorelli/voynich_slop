# Iteration240: shuffled word order still produces abundant replacement graphs

The negative control defeats a simple validation rule: every one of995 within-sentence shuffled texts remains clusterable, and four authors have more replacement edges in **every** shuffle than in the real text. Frequencies, sentence contents and boundaries therefore suffice to generate substantial graph structure. Graph availability is not evidence of restored grammar. The small Jerome core's order-specificity remains untested until the full strict-core selection is applied to controls.

## Frozen control

For199 seeds24000–24198 per author, shuffle opaque word identities among lexical positions within each admitted sentence. Preserve every sentence's word multiset, total word frequencies, lexical positions, punctuation/nonlexical slots and sentence boundaries. Unchanged floor5/two-shared-frame graph reconstruction; if at least17 endpoints, run the same corrected embedding and fixed23500 initialization. Never relax eligibility. Freeze every graph/partition before profile evaluation.

Compare the original23500 **single partition** with shuffled single partitions, not the previously selected strict core against a weaker null procedure. Reference global POS profiles stay attached to word identities; shuffled graphs may introduce endpoints absent from the real graph, so profiles for those words are reconstructed only from the already cached annotations. No raw annotation, new reserve or Seneca gold is opened. These are synthetic order controls, not fresh authors or named POS predictions.

## Graph availability

| Author | Real edges | Shuffled edges min / mean / max | Real nodes | Shuffled nodes min / mean / max | Clusterable shuffles |
|---|---:|---|---:|---|---:|
| Aquinas |565|585 /679.91 /780|202|173 /192.56 /214|199/199|
| Caesar |51|34 /58.56 /89|60|29 /44.14 /61|199/199|
| Cicero |93|100 /142.08 /195|75|58 /71.91 /87|199/199|
| Jerome |300|563 /700.92 /886|209|193 /219.66 /249|199/199|
| Dante |76|84 /121.60 /178|76|48 /65.04 /81|199/199|

No shuffle produces an empty graph. Edge-count upper tails are1.000 Aquinas/Cicero/Jerome/Dante and.775 Caesar. Thus neither a nonempty graph, enough nodes for clustering, nor a larger edge count can certify linguistic recovery. Repetition opportunities and frequency collisions remain in the control; sentence bags still preserve lexical co-occurrence, so this is not an unconstrained random-token null.

## Single-partition oracle purity

| Author | Real type-macro purity | Shuffled type-macro mean / maximum | Real token-weighted purity | Shuffled token mean / maximum |
|---|---:|---|---:|---|
| Aquinas |39.86%|34.39 /38.89%|48.38%|42.83 /50.60%|
| Caesar |56.56%|48.52 /63.19%|66.58%|66.39 /79.54%|
| Cicero |51.18%|41.09 /50.44%|61.80%|55.80 /71.97%|
| Jerome |47.59%|32.85 /38.33%|43.36%|52.09 /59.05%|
| Dante |45.72%|38.88 /51.27%|65.47%|60.43 /73.39%|

Real type-macro purity remains higher than every sampled control in Aquinas/Cicero/Jerome, but not Caesar/Dante. Jerome's real token purity is below every shuffled run(minimum43.58%). Global single-partition scores therefore show mixed order dependence, not a universal validation. Coverage/node sets differ across shuffles, and oracle naming is optimistic; these ranges do not replace a matched full-extraction test. All profiles, majority/per-word ceilings and one-to-one results are retained.

## Consequence for the preserved core

The six Jerome words remain a genuinely reference-pure verb group, and239's held-out perturbation robustness remains true. But those facts do not yet establish that the **selection procedure** produces such an output unusually often on grammatical order rather than sentence bags/frequencies. Do not upgrade the core to an inferred verb label, exact nuclei, or a validated Voynich input until the full procedure's false-output behavior is checked. No memberships or earlier results are rewritten.

## Audit and next matched experiment

Independent995 shuffle/multiset/graph/partition replays,15 independently computed geometry samples,2000 oracle metric groups,40 assignment-dual certificates and48 hashes pass. Cached reference/dependency manifests are independently verified. Artifacts: `experiments/results/grammar-restoration/iteration240/`.

Next run the **complete** initialization-consensus and sentence-deletion-consensus selection on19 predeclared Jerome shuffled texts, seeds24000–24018 in numerical order, without choosing controls by their scores. Use the exact31 initialization seeds,31 selection-deletion seeds and joint-core rule from235–238. Primary reference statistic is largest fully POS-pure non-singleton core size, maximizing over all cores/classes in both real and shuffled outputs; the real size is6. Report zero outputs, coverage and all controls, with no inferred label or confirmatory claim. This tests the specific strongest finding using a matched selection pipeline; other authors are outside that targeted pilot, not silently declared validated.
