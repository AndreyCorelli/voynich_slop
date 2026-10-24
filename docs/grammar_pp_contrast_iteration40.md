# Iteration 40: can a score recognize a correct prepositional construction?

A source-trained structural score distinguishes many annotated preposition–noun constructions from small corruptions, but its apparent attachment success is mostly explained by easy local geometry. Its clearest failure is choosing accusative versus ablative after *in*. This is an oracle diagnostic, not grammatical restoration from ciphertext.

## Design and information boundary

Train on 457 contiguous prepositional constructions from the existing 767-sentence Jerome/Palladius source split. Evaluate on the previously inspected iteration26 query slices: 100 sentences each from Jerome and Caesar. Caesar is absent from the source authors, but its evaluation slice is reused development data, not a new untouched test. Neither iteration39's fresh queries nor the reserved 200 sentences are scored here. Reserved IDs are excluded before token annotation parsing.

Use UD `case` attachments with an ADP marker, a NOUN/PROPN/PRON head, and a known head case. The reference span contains marker, head, and direct `amod`, `det`, `nummod`, `flat`, or `compound` dependents. Keep only contiguous spans. This operational definition covers simple constructions; it is not a full NP subtree or a claim about the only valid linguistic boundary.

The scorer receives oracle POS, case/number/gender, plaintext preposition identity, sentence order, and candidate head/span. Reference dependencies are used only to extract examples and generate contrasts, never by the score. There is no candidate-retrieval or morphology-inference challenge here. The scorer is deliberately a transparent new diagnostic model, not the earlier HMM objective.

Freeze equal additive weights on four source-trained log-probability terms before target scoring: preposition-specific case government, marker–head distance, internal POS template with marker/head placeholders, and modifier agreement category. Add-half smoothing includes an unseen outcome bucket; government has a fixed eight-case inventory. The local control uses global case frequency plus distance. Five hundred ninety-five contrast pairs and all inputs/models are frozen before scoring. No weights or thresholds are tuned on target results.

Contrasts:

- **Attachment:** one alternate nominal head in the same sentence, within 12 tokens of the marker, with the same POS and case and within one log2 bin of source word frequency. Choose the nearest distance match. Its span is the marker–head hull, so this intervention also changes the boundary; it is not a clean attachment-only comparison.
- **Morphology:** change only the proposed head case to the alternative case nearest in source frequency. Token observations remain fixed. This is a frequency-matched single-feature intervention, not a guarantee that the alternative is ungrammatical.
- **Boundary:** add or remove one endpoint token, retaining marker and head. Several alternatives are possible; weight each reference construction equally in the family summary.

An alternative attachment or morphological interpretation can be linguistically valid. Scores are tested against the treebank interpretation, not against a complete inventory of grammatical possibilities. The gold-conditioned negative generator and privileged observations make this an upper-bound diagnostic.

## Results

Strict win percentages give no credit for ties. Boundary percentages average alternatives within each construction, then constructions. Parentheses show 95% sentence-cluster bootstrap intervals from 10,000 draws, conditional on the source model and generated contrasts.

| Contrast | Jerome constructions | Local wins | Structural wins | Caesar constructions | Local wins | Structural wins |
|---|---:|---:|---:|---:|---:|---:|
| Attachment | 18 | 100% | 100% (100–100) | 54 | 81.5% | 100% (100–100) |
| Head case | 57 | 56.1% | 77.2% (63.8–89.8) | 121 | 43.8% | 74.4% (65.5–82.3) |
| Boundary | 57 | 0% | 93.9% (89.8–97.3) | 121 | 0% | 94.1% (89.9–97.7) |

The local score ties every boundary comparison because its inputs do not change. This zero is expected and should not be read as a strong competing boundary model. Pair counts are 18/57/106 for Jerome attachment/case/boundary and 54/121/239 for Caesar.

On constructions having **all three contrast families**, the structural model strictly beats every supplied alternative for **7/18 Jerome (38.9%)** and **36/54 Caesar (66.7%)**. The local baseline gets zero because of boundary ties. These are complete supplied-set ranking results, not end-to-end construction accuracy: the correct candidate is supplied, only one alternate head is generated, and many constructions lack a matched head alternative.

## What actually drives the score?

Descriptive component removals were computed after the primary outcomes, without selecting a revised model:

- Distance alone wins all 18 Jerome attachment contrasts and 44/54 Caesar contrasts. Boundary alone wins all Jerome and 52/54 Caesar contrasts. Attachment success therefore provides weak evidence for nonlocal grammatical reasoning. A bootstrap interval of 100–100 does not remove the contrast-generation bias.
- Boundary-template probability exactly reproduces the structural boundary results. It recognizes these limited local span patterns; this is not demonstrated global attachment reasoning.
- Removing preposition-specific government drops case wins to 8.8% Jerome and 9.1% Caesar. Government contributes real information beyond global case frequency on this diagnostic.
- Removing modifier agreement changes neither headline case wins nor complete-set successes. This experiment does not establish a useful agreement contribution.
- Removing distance leaves complete-set successes unchanged. Removing government leaves 0/18 Jerome and 4/54 Caesar complete successes. Removing the boundary term leaves zero complete successes because boundary contrasts tie.

Of 595 pairs, 70 are nonwins, including ties. Case nonwins concentrate on *in* with reference accusative versus alternative ablative: **11 Jerome and 24 Caesar cases**. The preposition supports both cases, while the model only knows its aggregate source case distribution and local modifier compatibility. Some other nonwins involve rare or source-unseen prepositions; for an unseen preposition the government distribution is uniform rather than invented evidence.

## Next experiment

Do not expand the search space on the strength of the attachment score. First build harder attachment contrasts matched on distance and boundary/POS shape and report how often such contrasts exist. This may expose a much smaller testable subset.

For case, test whether **governing-predicate context** improves the *in* accusative/ablative contrast beyond the preposition-only model. Use source-only estimation, an explicit unseen-predicate fallback, and a shuffled-predicate control. Separate predictive evidence from gold predicate-link access: an oracle governing predicate would be a diagnostic upper bound, not a recovered relation. Avoid labeling either case intrinsically wrong when both readings are grammatical. Only if this adds discriminative information should it enter joint candidate construction decoding.

No relation recovery or ciphertext reconstruction is claimed. These reused query slices remain development data.

## Verification and artifacts

All 595 scores replay exactly; the source model reconstructs from source examples alone; all 72 alternate-head pairs retain case/POS matching; source and target IDs are disjoint; the 200 reserved sentences remain unscored. The scorer ignores reference heads/relations, verified by a mutation test. Other tests check case intervention, agreement propagation, and neutral government for unseen prepositions.

Code: `src/voynich_smt/pp_contrast.py`; run `python -m benchmarks.grammar_pp_contrast_iteration40`, then `python -m benchmarks.grammar_pp_contrast_iteration40_validate`. The runner refuses to overwrite artifacts. Data, model, declarations, stage freeze, scores, component removals, bootstrap summaries, and individual failures are in `experiments/results/grammar-restoration/iteration40/`. Previous artifacts and the shared todo are unchanged.
