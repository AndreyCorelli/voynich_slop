# Iteration 150: a single middle occurrence controls the learned boundary

Replacing only the middle siue in the influential coordination pattern largely reproduces the whole-sentence deletion failure. The other31,883 source tokens and all positions remain unchanged. The model's positive full-text result therefore depends on one opaque equality link, not merely on the overall presence of a useful sentence.

The frozen diagnostic tested every nonempty subset of the three focal positions in source sentence76252: token35,37,39 (zero-based). Each selected occurrence was replaced by its own distinct fresh opaque ID, excluded from supervised training. This intentionally breaks equality links and reduces siue's occurrence count without deleting a token or creating a seam. All13 training types and labels were retained, both scalar features were recomputed, and the unchanged class-balanced two-feature model was refitted. Models were frozen before target predictions and predictions before evaluation. No new annotations, reserved material or sealed works were used.

The local source pattern is siue incommoda siue uitia siue iniurias. The subset labels below correspond to first/middle/last occurrences, not a search over arbitrary source words.

| Text | Full | First | Middle | Last | First+middle | First+last | Middle+last | All three | Sentence deleted |
|---|---|---|---|---|---|---|---|---|---|
| Caesar (/15) | 12 | 12 | 10 | 12 | 10 | 10 | 10 | 10 | 10 |
| Jerome (/16) | 12 | 12 | 8 | 11 | 8 | 7 | 8 | 7 | 7 |
| Gellius (/15) | 12 | 12 | 4 | 11 | 4 | 4 | 4 | 4 | 4 |
| Livy (/14) | 10 | 10 | 5 | 10 | 5 | 5 | 5 | 5 | 5 |
| Apuleius (/13) | 6 | 7 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| Curtius (/15) | 12 | 12 | 5 | 12 | 5 | 5 | 5 | 5 | 5 |
| Suetonius (/16) | 12 | 12 | 6 | 12 | 6 | 6 | 6 | 6 | 6 |

Each value is the number of correctly classified supplied candidate types. All subsets are reported without selecting a replacement model. Accuracy alone understates changes: middle-only replacement flips62/104 candidate decisions, including six in Apuleius despite unchanged6/13 accuracy. Replacing all three reproduces every target hard decision of the whole-sentence deletion model, although probabilities are not identical.

| Source perturbation | Remaining siue count | Corrected overlap | Role similarity | Role coefficient (original units) |
|---|---|---|---|---|
| Full | 6 | .151515 | .706479 | 3.0891 |
| First only | 5 | .088889 | .525417 | 4.0009 |
| Middle only | 5 | .000000 | .004914 | −17.8721 |
| Last only | 5 | .088889 | .369019 | 4.2944 |
| All three | 3 | .000000 | .012069 | −16.7529 |

The three single-occurrence perturbations have identical siue counts, yet radically different feature and transfer effects. Pure count loss cannot explain that contrast. Breaking the middle identity disrupts both repeated links around the two alternating nouns; breaking either outer identity retains one. Replacing both outer occurrences also causes collapse. This implicates the repeated local motif, while the current experiment does not isolate changes to siue's features from collateral changes to other training types' features.

The motif is plausible grammatical coordination, so its influence is not evidence of a wrong annotation. However, the source estimator and fitted boundary are too dependent on this single motif to call the current result robust. Retain the demonstrated full-model71–80% type accuracy in six texts as conditional development evidence; it is not reliable arbitrary POS tagging, lexical recovery, or a confidence guarantee.

Next proposed diagnostic: feature attribution before another model change. For the middle-only perturbation, fit one hybrid using only the changed siue feature vector and all other original training vectors, and the complementary hybrid using the original siue vector with the other changed vectors. This separates the influential exemplar's estimate from changes elsewhere in the graph. Predeclare both hybrids, keep the same fitting and full/perturbed references, and report every text without favorable model selection. Hybrids are diagnostic interventions, not realizable input streams or proposed production features.

Verification independently reconstructed all seven subset substitutions, checked unchanged token length and all nonselected IDs, recomputed104 source feature pairs by combinatorial overlap and dictionary roles, retrained eight models, replayed936 target probabilities and63 metric groups, and matched both historical references on all seven texts. The focused suite passed18 tests. Frozen artifacts and manifest: `experiments/results/grammar-restoration/iteration150/`.
