# Contextual role/analysis compatibility — iteration 70

The tested score fails its lexical diagnostic. On 1,273 content-token positions in the 100 previously declared iteration-23 Caesar sentences, it strictly prefers the original word in **13.67%** of pairs, versus **13.83%** with shuffled context and **13.35%** with the unconditional grammatical prior. Do not add it to dictionary search. No new nuclei or restoration percentage were measured.

| Evidence | Original wins | Wrong candidate wins | Ties |
|---|---:|---:|---:|
| Masked contextual role/analysis posterior | 174 | 966 | 133 |
| Shuffled context | 176 | 964 | 133 |
| Unconditional role/analysis prior | 170 | 970 | 133 |
| Supplied reference role | 162 | 892 | 219 |
| Supplied reference POS, Case and Number | 203 | 218 | 852 |
| Source word frequency | 27 | 1,246 | 0 |

## Experiment

Fit only on iteration-49 source fold-0 fit sentences (no Caesar). A fixed add-one naive Bayes model predicts joint dependency-role/POS/Case/Number labels from candidate-derived neighboring POS at offsets −2, −1, +1, +2. The center word and POS are masked. Each candidate receives the posterior mass compatible with at least one of its cached joint dictionary readings; analyses are never recombined. Missing dictionary readings give zero evidence. Missing feature values act as unspecified constraints. No gold labels enter the contextual posterior or candidate score.

This is an intentionally favorable local diagnostic: correct surrounding plaintext and sentence boundaries are supplied, and the original word is always an offered candidate. Each original is compared with the most source-frequent different cached word with a dictionary reading in the original's **reference coarse POS**. All reference content positions are evaluated, including objects, obliques and modifiers. The distractor pool is the union of two cached morphology resources, not an exhaustive Latin inventory. Repeated token positions are correlated; these percentages are descriptive development results, not independent significance tests.

**Design correction:** the frozen design mistakenly says no target grammar is used to choose the distractor. The implementation uses reference coarse POS for controlled candidate sampling and reference POS to select content positions. That privilege is confined to constructing the diagnostic pairs; it is not inferred grammar or blind retrieval. Preserve this correction alongside the original freeze. The first preflight failed before evaluation because dictionary analyses were passed incorrectly to the existing POS helper; the corrected run was frozen before scoring. No score weights or gates were tuned after evaluation.

The supplied-role arm conditions the source distribution on the reference dependency role. The supplied-morphology arm checks dictionary compatibility directly against reference POS/Case/Number. These are privileged information probes, not attainable exact-word recovery ceilings: grammatical compatibility cannot distinguish interchangeable words or candidates sharing those features. The gate required at least 65% strict original wins, ten percentage points above prior and five above shuffled context; it fails. Historical first-corruption tests and dictionary search were therefore not advanced under this score.

## What limits the score

The reference analysis is admitted for 1,015/1,273 originals. **219 originals have no cached reading**, and another **39 have readings that miss the reference profile**. Even where the original admits that profile, the distractor also admits it in **812 cases**. Thus the privileged morphology arm frequently cannot distinguish the words, while dictionary coverage asymmetry can actively punish the original.

There is also a concrete ambiguity bias: the frequent distractors are `non` (727 positions), `est` (394), `omnia` (126), `ad` (15), and `me` (11). A cached alternative analysis allows a word into a coarse-POS pool even when that is not its usual contextual reading. Summing compatible label mass rewards broad analysis sets without accounting for how plausible each analysis is **for that word**. This is a candidate-reading problem as well as a context-model problem; the near equality to shuffled context provides no evidence that the tested contextual model repairs it.

The next bounded check should compare **word-conditioned analysis probabilities** against the current any-reading union, holding these pairs fixed. First audit whether rare readings of the frequent distractors account for their victories; then test source-estimated POS/analysis weights, with an explicit fallback for unseen words. Retain coverage failures and same-profile ties. Only a gain beyond both source frequency and shuffled context would justify returning to the ten historical corruption tests. None of this establishes semantic correctness or exact nucleus recovery.

## Verification

The audit replays all 1,273 contextual and shuffled scores, reference-morphology checks and the saved evaluation; it verifies 1,472 prior manifest input hashes. Ten focused tests pass, including joint-analysis preservation, masked-center invariance, unknown handling, duplicate-reading invariance and posterior normalization. The 200-sentence grammar reserve and sealed lexical final test remain unscored; only previously declared target sentence annotations were parsed.

Artifacts: `experiments/results/grammar-restoration/iteration70/`; runner and audit: `benchmarks/grammar_role_compatibility_iteration70*.py`.
