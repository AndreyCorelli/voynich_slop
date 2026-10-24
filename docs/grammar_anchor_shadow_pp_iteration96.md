# Blind pair repair: downstream PP shadow run — iteration 96

**Preserve this conditional grammatical result: applying all five frozen primary pair recommendations restores the original clean-input PP predictions in every selected case.** There is no reference-correctness gate. Clean/same-class controls remain unchanged. A less selective control also demonstrates damage from wrong repairs. This is successful repair of selected synthetic mapping errors, not an improvement over the clean PP model or evidence of general blind restoration.

## Frozen shadow integration

Use all six iteration95 pair arms, models and source-selected thresholds unchanged. Recompute a recommendation using only its cached candidate-pair scores and frozen threshold; never inspect the reference pair before applying it. For every recommended pair, swap the currently supplied public anchor names AND source-modal tags between its two opaque IDs, consistently at every occurrence. Keep IDs, token positions and private PP reference labels unchanged. An abstention makes no change.

Rerun both fixed PP models on every unique intervention: original85 at0.80 (primary downstream policy), augmented89 at0.71 (its selected policy) and0.80 (secondary diagnostic). No training, calibration, score interpolation or threshold selection. Preserve all24 scenarios across source and cached Jerome/Caesar, including clean inputs, same-class swaps, missed detections and inactive controls. All transforms and predictions are saved/frozen before their evaluation.

The clean-input PP predictions are an evaluation reference only; they never select an intervention. Original uncorrected scores replay iteration90. Source PP reference labels remain the same node-membership task as earlier experiments, not complete phrase spans, exact governor links or Case values.

## Primary paired-rule outcomes

| Dataset | Scenario | Repair applied | Original PP correct / wrong before | After | After precision | After recall |
|---|---|---|---:|---:|---:|---:|
| source | correct | no | 357 / 33 | 357 / 33 | 91.54% | 45.95% |
| source | rehearsed_in_et | no | 252 / 186 | 252 / 186 | 57.53% | 32.43% |
| source | unseen_ad_que | yes | 277 / 100 | 357 / 33 | 91.54% | 45.95% |
| source | unseen_ad_sed | yes | 277 / 66 | 357 / 33 | 91.54% | 45.95% |
| source | unseen_de_que | no | 298 / 86 | 298 / 86 | 77.60% | 38.35% |
| source | unseen_de_sed | yes | 300 / 47 | 357 / 33 | 91.54% | 45.95% |
| source | same_adp | no | 353 / 37 | 353 / 37 | 90.51% | 45.43% |
| source | same_conjunction | no | 357 / 34 | 357 / 34 | 91.30% | 45.95% |
| Jerome | correct | no | 40 / 1 | 40 / 1 | 97.56% | 60.61% |
| Jerome | rehearsed_in_et | yes | 22 / 76 | 40 / 1 | 97.56% | 60.61% |
| Jerome | unseen_ad_que | no | 36 / 2 | 36 / 2 | 94.74% | 54.55% |
| Jerome | unseen_ad_sed | no | 36 / 2 | 36 / 2 | 94.74% | 54.55% |
| Jerome | unseen_de_que | no | 31 / 1 | 31 / 1 | 96.88% | 46.97% |
| Jerome | unseen_de_sed | no | 30 / 1 | 30 / 1 | 96.77% | 45.45% |
| Jerome | same_adp | no | 41 / 1 | 41 / 1 | 97.62% | 62.12% |
| Jerome | same_conjunction | no | 40 / 1 | 40 / 1 | 97.56% | 60.61% |
| Caesar | correct | no | 72 / 4 | 72 / 4 | 94.74% | 45.28% |
| Caesar | rehearsed_in_et | yes | 37 / 12 | 72 / 4 | 94.74% | 45.28% |
| Caesar | unseen_ad_que | no | 65 / 33 | 65 / 33 | 66.33% | 40.88% |
| Caesar | unseen_ad_sed | no | 58 / 4 | 58 / 4 | 93.55% | 36.48% |
| Caesar | unseen_de_que | no | 76 / 25 | 76 / 25 | 75.25% | 47.80% |
| Caesar | unseen_de_sed | no | 66 / 4 | 66 / 4 | 94.29% | 41.51% |
| Caesar | same_adp | no | 69 / 5 | 69 / 5 | 93.24% | 43.40% |
| Caesar | same_conjunction | no | 70 / 4 | 70 / 4 | 94.59% | 44.03% |

All five selected repairs reproduce the full clean-input PP probability vectors, not just aggregate counts. They are source ad/que, ad/sed, de/sed, and in/et for Jerome/Caesar. Source clean357/33 corresponds to91.54% precision and45.95% recall; Jerome40/1 to97.56%/60.61%; Caesar72/4 to94.74%/45.28%. Hidden-content positions after those repairs are source267/31 (89.60% precision), Jerome35/1 (97.22%), Caesar67/4 (94.37%): the source hidden subset still misses90%.

Every primary abstention preserves its uncorrected predictions. This leaves substantial failures unresolved: source in/et remains252/186 (57.53% precision), source de/que298/86 (77.60%), Caesar ad/que65/33 (66.33%) andde/que76/25 (75.25%). Do not report only the five repaired cases as overall robustness. No primary clean/same-class control is modified.

## Token-level gains and losses

Even a correct repair can introduce baseline false positives or lose individual true assignments relative to the corrupted input. Returning to the clean model is not zero token-level damage. The following changes use the original PP0.80 policy.

| Selected primary case | New correct | Lost correct | Removed wrong | New wrong |
|---|---:|---:|---:|---:|
| source/unseen_ad_que | 84 | 4 | 77 | 10 |
| source/unseen_ad_sed | 86 | 6 | 43 | 10 |
| source/unseen_de_sed | 61 | 4 | 20 | 6 |
| Jerome/rehearsed_in_et | 18 | 0 | 75 | 0 |
| Caesar/rehearsed_in_et | 37 | 2 | 11 | 3 |

The net changes are favorable in each selected original-model case, but gross changes include losses and newly selected baseline errors. These are repeated, correlated perturbation probes, so summing them does not measure distinct restored tokens or independent restoration trials.

## Augmented model and unsafe control

| Selected primary case | Augmented0.71 before | After | Augmented0.80 before | After |
|---|---:|---:|---:|---:|
| source/unseen_ad_que | 218 / 112 | 307 / 42 | 111 / 52 | 173 / 17 |
| source/unseen_ad_sed | 220 / 85 | 307 / 42 | 107 / 18 | 173 / 17 |
| source/unseen_de_sed | 237 / 80 | 307 / 42 | 120 / 19 | 173 / 17 |
| Jerome/rehearsed_in_et | 29 / 2 | 29 / 2 | 16 / 0 | 15 / 0 |
| Caesar/rehearsed_in_et | 62 / 4 | 62 / 4 | 26 / 1 | 27 / 1 |

The already augmented0.71 model gains source coverage/precision after the three selected unseen-swap repairs, but the selected known in/et repairs leave Jerome/Caesar aggregate counts unchanged. The0.80 secondary can even lose a correct Jerome assignment (16/0→15/0) while returning to its clean baseline. This is why downstream value must be measured under each fixed policy.

The independent pair control applies every recommendation, including its two wrong pairs. In source in/et it swaps et/atque and changes original PP252/186→241/31: many false positives disappear, but eleven net correct assignments are lost and the clean mapping is not restored. On Jerome ad/que it wrongly swaps ad/de and changes36/2→31/1; augmented0.71 falls24/2→18/2. Better precision or fewer false positives cannot by itself certify a correct dictionary repair. Correct independent recommendations elsewhere reproduce clean inputs, as expected; no oracle gate filters out its mistakes. Prior/permutation pair arms abstain throughout.

Frozen nearest-left F1 is also evaluated after every intervention in the artifacts. Its threshold/operating point differs from the selective PP policies. The experiment does not establish a matched-coverage advantage over a correspondingly corrected proximity-only system.

## Scope and next check

The positive result combines blind pair identification with recovery of previously learned PP membership under a single injected bijective ADP/CCONJ swap. Once the correct pair is selected, restoration to clean PP predictions is the expected consequence of undoing that injection; it is not independent evidence that the PP scorer has improved. The learned contribution is selective pair identification without being told the corrupted pair. Supplied anchor inventory/other assignments remain a privilege. No new lexical nuclei, unanchored decipherment, multiple-error recovery or full grammatical parse is established.

Preserve the primary option and the unsafe-control counterexamples; do not adopt from five successful, correlated development cases. Next freeze a larger source-frequency-defined error bank: all remaining59 ADP×CCONJ pairs among these16 candidates, excluding the five previously used cross-class pairs. Keep classifier, pair threshold, support limits and PP policies fixed; report wrong repairs, abstentions, absent/unsupported endpoints and downstream token losses as well as gains. This would challenge the apparent precision before changing models or testing the reserve. Proposed, not run here.

Validation: all24 scenarios and six pair arms replayed; 68 unique model/intervention PP inferences replayed; blind public actions and IDs verified; uncorrected scores reproduce90; exact public repairs reproduce full clean probabilities; 2,643 prior frozen-input hashes verified;99 focused tests passed. Prior artifacts are unchanged. No new annotations, reserve or sealed-test scoring. Artifacts: experiments/results/grammar-restoration/iteration96/.
