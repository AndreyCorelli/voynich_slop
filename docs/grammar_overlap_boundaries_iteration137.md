# Iteration 137: Caesar class signal survives sentence-boundary removal and fails word-shuffle controls

**Preserve this strengthened result:** expanded Caesar remains **13/15 types correct (86.67%) with AUC 1.0** after removing all supplied sentence boundaries and under all three fixed sentence-order variants. All sixteen frequency-preserving word-order shuffles yield **7/15 correct**, with maximum AUC **0.6786**. The observed long-context signal therefore survives this segmentation challenge and is not reproduced by these unigram-preserving nulls.

This remains a one-author development success, not a general Latin classifier, blind function-word discovery, or lexical nucleus. Other contexts remain uneven, particularly original Jerome and short Caesar.

## Frozen transformations

Keep iteration 135's statistic, thirteen-type-trained models, scalar calibrations, and class cutoff unchanged. The primary is count-corrected left/right opaque-neighbor overlap; raw overlap and frequency remain reported controls. Features use only opaque ID equality and counts, with no supplied translations or POS tags.

For each of the five existing contexts (source, original/expanded Jerome, original/expanded Caesar), construct twenty sentence-free word streams:

- Original sentence order, concatenated into one stream.
- Three fixed SHA256 sentence orders (seeds 13700–13702), preserving each sentence's internal word order before concatenation.
- Sixteen global word-order permutations (seeds 13710–13725), each preserving exactly every word type's occurrence count.

The original sentence-preserved predictions from iteration 135 are references, not refitted arms. All one hundred transformations are frozen before statistics, and all predictions before metrics. Every present target type remains included. Original sentence-count support metadata is retained for reporting only; no sentence boundary enters new statistics or inference.

Sentence reordering alters artificial joins between segments while preserving within-segment structure; global word shuffling removes that structure. These are correlated development controls, not independent texts or formal significance guarantees. No transformation, model, or cutoff is selected from target performance. No PP inference, new annotations, reserve features, sealed lexical tests, defaults, or exact word recovery are introduced.

## Primary corrected-overlap results

| Context | Sentence-preserved correct | Concatenated correct | Concatenated AUC | Correct across three sentence orders | Shuffled AUC range | Null AUC at least concatenated |
|---|---:|---:|---:|---|---:|---:|
| Source | 9/16 | 9/16 | 0.6875 | 9/16 · 9/16 · 9/16 | 0.2344–0.7344 | 3/16 |
| Jerome original | 3/13 | 3/13 | 0.3500 | 3/13 · 3/13 · 3/13 | 0.3500–0.7000 | 16/16 |
| Jerome expanded | 10/16 | 10/16 | 0.6719 | 11/16 · 10/16 · 10/16 | 0.2500–0.7031 | 1/16 |
| Caesar original | 6/13 | 6/13 | 0.6190 | 6/13 · 6/13 · 6/13 | 0.2976–0.7976 | 6/16 |
| **Caesar expanded** | **13/15** | **13/15** | **1.0** | **13/15 · 13/15 · 13/15** | **0.0179–0.6786** | **0/16** |

For expanded Caesar, concatenated NLL is **0.4146**, versus shuffled mean **0.9015** and range **0.8748–0.9604**. All shuffled streams classify the fifteen candidate types as conjunctions, giving seven correct classifications. The concatenated model instead retains all eight correct preposition classifications and five of seven conjunctions; `atque` and `que` remain its two errors. Sentence-order variants retain AUC 1.0 with NLL approximately 0.415–0.416.

Raw-overlap and frequency controls are saved for all transformations, without choosing whichever model favors a context. Frequency is unchanged by the transformations, as expected; order-dependent changes in the primary cannot be explained by changed token counts. This does not establish that the statistic measures only grammatical structure: other systematic word-order properties can contribute.

The source and Jerome results do not justify extending the strong Caesar claim to all texts. Source and expanded Jerome beat most, but not all, word shuffles on AUC. Original Jerome is poor, and short Caesar's ranking overlaps the nulls substantially. Removing sentence boundaries does not repair those failures.

## Implication for Voynich research

Together with iteration 136's passage-mixture checks, expanded Caesar now provides an anchor-free, sentence-free grammatical-class signal that survives two relevant challenges. It is a plausible information source to investigate independently of the current lexical decoder, consistent with the high-level goal.

Word boundaries, repeated-type grouping, and membership in the function-word candidate catalogue remain supplied. The classifier distinguishes only prepositions from coordinating conjunctions among those candidates; it does not identify which arbitrary cipher words belong in that set. Perfect ranking of fifteen development types is not a general reliability guarantee or a discovered translation key.

Next replicate the frozen sentence-free method on two additional already inspected cached Latin works, such as Gellius and Livy, without reopening sealed works, adding grammatical annotations, or changing the model. Retain the full supplied candidate catalogue, report missing and normalization/segmentation differences, and use fixed count-preserving shuffles. This would move toward the desired multi-text evidence while testing the current cross-author limitation; it would still measure grammatical classes rather than shared exact lexical nuclei.

## Verification

Independent review verifies seventeen frozen input hashes, reconstructs all one hundred transformations, checks preserved word counts and candidate sets, recomputes 1,460 type/context statistics using integer-combination null probabilities, replays 4,380 class probabilities and nine hundred metric groups, and reconstructs all null summaries. There is no fitting or anchor/sentence-boundary feature use in new predictions, and reserve IDs remain excluded. Fifteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration137/`.
