# Iteration 149: one repeated-siue sentence drives the learned boundary

The influential exemplar is concentrated in one source sentence. Three of the six siue occurrences lie in a single50-token Cicero sentence. Removing that sentence reverses the role-similarity coefficient and sharply reduces target accuracy; removing any of the other three siue-containing sentences changes no target decisions. This narrows the fragility to a concrete source context, rather than merely a training-type identity.

The design was frozen before feature computation: locate all six source occurrences, remove each unique containing sentence separately, recompute both scalar features for all13 training types, and refit the original class-balanced model without offsets or threshold changes. The six occurrences occupy four sentences, so four deletion models and one full reference were fitted. Concatenation creates a new seam at the removed sentence. Target features are the unchanged seven full-text caches from iteration144; models were frozen before predictions and predictions before evaluation. No new annotations, reserved material or sealed works were used.

| Source sentence ID | Source index | Removed tokens | Removed siue occurrences | Remaining siue count |
|---|---|---|---|---|
| 76252 | 590 | 50 | 3 | 3 |
| 79855 | 2094 | 16 | 1 | 5 |
| 79993 | 2123 | 5 | 1 | 5 |
| 79994 | 2124 | 13 | 1 | 5 |

| Text | Full correct/types | Remove sentence76252 | Remove any of the other three |
|---|---|---|---|
| Caesar | 12/15 | 10/15 | 12/15 |
| Jerome | 12/16 | 7/16 | 12/16 |
| Gellius | 12/15 | 4/15 | 12/15 |
| Livy | 10/14 | 5/14 | 10/14 |
| Apuleius | 6/13 | 6/13 | 6/13 |
| Curtius | 12/15 | 5/15 | 12/15 |
| Suetonius | 12/16 | 6/16 | 12/16 |

Removing76252 changes61 of104 supplied candidate decisions; unchanged Apuleius accuracy conceals six decision flips. All three other deletions leave decisions intact, although probabilities shift slightly. The deleted50 tokens are about0.16% of the31,884-token source stream. This is a large influence for one sentence, but removes half of the influential conjunction's occurrences, not just one occurrence.

The source context is a repeated coordination pattern: siue incommoda siue uitia siue iniurias. Existing annotations label all three siue tokens CCONJ and the alternating words NOUN; no relabeling was applied. This is a plausible structural exemplar of coordination, not evidence of a mislabeled sentence. Its influence nevertheless leaves generalization dependent on a single source example.

| Model | siue corrected overlap | siue role similarity | Role coefficient in original units |
|---|---|---|---|
| Full | .151515 | .706479 | 3.0891 |
| Remove76252 | .000000 | .012111 | −16.8284 |
| Remove79855 | .177778 | .747919 | 2.8405 |
| Remove79993 | .177778 | .811327 | 2.7553 |
| Remove79994 | .177778 | .800898 | 2.7693 |

The experiment does not isolate the three focal occurrences from the other47 tokens or the new deletion seam. It therefore cannot yet establish whether the repeated coordination motif itself, collateral changes to other training features, or both cause the boundary reversal. It does show that the full-model success is not robust to removal of this sentence. Preserve the grammatical milestone as conditional development evidence; do not claim robust general POS tagging, lexical recovery or a new confidence filter.

Next proposed diagnostic: replace each nonempty subset of the three focal siue occurrences with unique fresh opaque IDs, leaving every other source token and its position unchanged. All seven subsets would be predeclared. Recompute both features/refit all13 training types; compare with the full and whole-sentence deletion models. This separates disruption of the focal repeated pattern from wholesale removal of the sentence. The artificial IDs are a diagnostic perturbation, not inferred words or new training labels.

Independent verification reconstructed all occurrences and unique deletions, recomputed65 source feature pairs with dictionary role and combinatorial overlap implementations, retrained all five models, and checked520 probabilities and35 metric groups. Full target references match exactly;18 focused tests passed. Frozen artifacts: `experiments/results/grammar-restoration/iteration149/`.
