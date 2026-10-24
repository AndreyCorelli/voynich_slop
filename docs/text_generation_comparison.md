# Seven-stage comparison of text generators

This branch asks whether simple copying and template generators reproduce selected manuscript statistics better than a frequency baseline and natural-text controls. It does not fit an encoder or interpret SAT as a language explanation. All runs use cached data, with zero solver calls or new downloads.

## Sampling and measurements

Clean atomic EVA records form nonoverlapping 64-word blocks; excluded records and folio boundaries interrupt blocks. SHA256(folio) modulo four assigns bucket zero to heldout and the others to development. Fixed seed sampling selects 16 development blocks from 12 folios and 12 heldout blocks from nine disjoint folios. Sixteen independently selected uninterrupted Caesar blocks supply natural controls, reused across development/heldout comparisons; they are not fresh natural-text replications at every stage. j/i and v/u are canonicalized for those controls.

The six frozen metrics are mean word length, unique-word fraction, adjacent exact repetition, exact repetition excess within eight positions relative to all pairs, global one-edit word-family pair fraction, and local one-edit excess relative to all pairs. A one-edit relation excludes identical words and permits one insertion, deletion or substitution. These measurements omit many potentially important manuscript properties: line positions, section/Currier labels, long-distance recurrence, character transition grammar, and semantics.

Model distance is the mean absolute metric difference from each target block, divided by the development metric standard deviation with a floor of 0.01. Length-free distance is a predefined sensitivity using the other five metrics. These distances are descriptive, not likelihoods, Bayes factors or p-values. Metric weights and scaling affect ranking.

All synthetic generators learn their word, character and component pools from development only. They generate 64 words under three fixed seeds per target block, without conditioning on target block lengths or word frequencies. Seeds reuse the same underlying blocks; they are not independent manuscript observations.

## Models and the seven iterations

1. Freeze and test measurements: injective glyph relabeling and word permutation preserve the appropriate global metrics; local metrics distinguish ordering.
2. Compare independent characters, independent whole words, and natural H1/H2 controls. Development whole-word sampling wins this stage.
3. Add local copying at fixed probabilities 0.20, 0.50 and 0.80 from the previous eight words. Even 0.20 worsens the whole-word baseline; higher rates severely overproduce repetition.
4. Add a single-character substitution to 25% of copying events. Mutation improves on corresponding copying rates, but still does not beat independent words.
5. Add prefix/stem/suffix templates: split development words of length at least three into first unit, middle and last unit, and independently recombine components. A second variant reuses the preceding stem with probability 0.5. Neither beats the word baseline. This is an arbitrary simple template family, not a reconstructed historical mechanism.
6. Freeze the development winner across all ten generators, with lexical tie breaking: **word-iid**. The length-free sensitivity also selects word-iid. Natural controls are comparators, not candidates for the trained-generator selection.
7. Evaluate all frozen models on heldout folios. Word-iid remains best; no heldout outcome changes selection. A separately planned within-block shuffle diagnostic checks ordering while holding every heldout word and its count fixed. That shuffle is an oracle-conditioned diagnostic, not a deployable generator.

All probability grids and templates were specified before development results. Later iterations assess the next predeclared family rather than retuning parameters to rescue an outcome. Each stage has its own saved plan, preceding-result digest, test output and assessment. Heldout statistics are evaluated only at stage seven.

## Heldout outcome

Lower distance is better under these six metrics.

| Model | All-metric distance | Length-free distance |
|---|---:|---:|
| Independent development words | **0.892** | **0.822** |
| Copy + mutation, p=0.20 | 1.449 | 1.442 |
| Independent development characters | 1.454 | 1.450 |
| Independent templates | 1.465 | 1.296 |
| Caesar H1 structural control | 1.524 | 1.055 |
| Copying, p=0.20 | 1.695 | 1.772 |
| Caesar H2 structural control | 1.784 | 1.367 |
| Locally persistent templates | 1.932 | 1.855 |
| Copy + mutation, p=0.50 | 3.331 | 3.622 |
| Copying, p=0.50 | 4.409 | 4.938 |
| Copy + mutation, p=0.80 | 7.682 | 8.531 |
| Copying, p=0.80 | 9.950 | 11.405 |

The target adjacent repeat rate averages 0.00794. Independent words give 0.00705, while p=0.20 copying gives 0.04056. Global one-edit family density is 0.0304 in the target, 0.0218 under word sampling and 0.0075 under independent templates: the baseline wins overall but does not reproduce every metric.

The oracle shuffle diagnostic gives target versus shuffled adjacent repeat rates 0.00794 versus 0.01279. Mean local exact-repeat excess is about 0.00075 in both; local one-edit excess is -0.00167 versus -0.00173. There is little average positive local enrichment in this selected sample under these measurements. No inferential confidence or absence-of-syntax conclusion follows from twelve blocks or point averages. Opposing block effects can cancel.

## What this does and does not establish

**The tested copying/template families do not improve on a frequency baseline.** That is the useful negative result. Their poor performance is not evidence against all text-generation mechanisms.

Word-iid learns manuscript development vocabulary and frequencies, whereas Caesar controls do not. Its advantage therefore cannot be read as fair evidence that nonlanguage generation is more likely than encryption. It captures some manuscript-specific lexical structure by construction, although it never sees heldout words during training. The heldout ranking is a baseline comparison, not a causal mechanism ranking.

The H1 control uses the invariance of these metrics under injective, one-unit relabeling of Latin letters. H2 independently splits each letter into two disjoint opaque labels. The latter may have a larger output alphabet than manuscript EVA and is not a width/alphabet-feasible manuscript cipher; it isolates homophonic splitting structurally. Neither control covers contraction, transposition, variable-width encoding, other languages or alternative boundary conventions. The preserved cipher hypothesis is not rejected.

Next priority: **out-of-folio predictive comparison of an order-aware word model against the frozen frequency baseline**, with fixed smoothing, explicit unseen-word handling and log scoring. This asks whether preceding context predicts heldout words, rather than whether additional hand-designed generators match six summaries. Freeze the protocol before fitting and aggregate by folio; do not interpret token counts as independent trials. No further copying grid is justified by this batch.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.text_generation_comparison --run
.venv/bin/python -m benchmarks.text_generation_assessment
.venv/bin/python -m pytest tests/integration/test_text_generation_comparison.py -q
```

Saved artifacts: `experiments/results/text-generation-comparison/`, including frozen source/split data, seven plans and results, development selection, heldout summary and the conditional-order plan/result. Five tests pass, including an independent dynamic-programming check of one-edit distance. Validation checks disjoint folios, code/source provenance, every stage's digest chain, unchanged selection, all saved generator metrics and the exact-multiset shuffle diagnostic. No prior cipher artifacts are altered.
