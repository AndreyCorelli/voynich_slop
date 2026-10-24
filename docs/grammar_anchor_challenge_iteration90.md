# Unrehearsed anchor-swap challenge — iteration 90

**Finding: the iteration89 improvement is specific to the rehearsed errors; it does not establish general robustness to wrong anchor classes.** Frozen augmentation still fails severely on unseen ADP/CCONJ swaps, sometimes more severely than the original model. Preserve the conditional clean-anchor PP findings and the known-error gain, but reject a broad robustness claim.

## Frozen challenge

Rank the common20 supplied anchors using source-fit token frequency, excluding the rehearsed in/et identities. The two highest remaining ADPs are ad/de and CCONJs que/sed. Before evaluation freeze all four cross-class swaps (ad/que, ad/sed, de/que, de/sed), same-class controls ad/de and que/sed, plus clean and rehearsed in/et controls. The cross-class mappings are absent from iteration89 training; ad was hidden in its dropout view, so these are unseen errors rather than wholly unseen identities.

Use both frozen195-anchor models (original85 and augmented89), identical public features and opaque equality IDs. Apply swaps consistently to all occurrences without merging types. Keep cutoffs0.80,0.71,0.70 unchanged. The0.71 cutoff is the selected iteration89 augmented policy; the original model did not qualify its robust calibration rule, and its result at0.71 is only an identical-cutoff control. No fitting, recalibration or target-driven pattern selection. Report every pattern on all source-test tokens and the cached100 Jerome/100 Caesar sentences. These datasets have been reused during development, not fresh independent confirmation.

## Results

| Dataset | Pattern | Affected anchor tokens | Original0.80 correct / wrong | Augmented0.80 correct / wrong | Augmented0.80 precision | Augmented0.71 correct / wrong | Augmented0.71 precision |
|---|---|---:|---:|---:|---:|---:|---:|
| source | correct | 0 | 357 / 33 | 173 / 17 | 91.05% | 307 / 42 | 87.97% |
| source | rehearsed_in_et | 460 | 252 / 186 | 159 / 16 | 90.86% | 307 / 42 | 87.97% |
| source | unseen_ad_que | 216 | 277 / 100 | 111 / 52 | 68.10% | 218 / 112 | 66.06% |
| source | unseen_ad_sed | 194 | 277 / 66 | 107 / 18 | 85.60% | 220 / 85 | 72.13% |
| source | unseen_de_que | 207 | 298 / 86 | 125 / 52 | 70.62% | 236 / 117 | 66.86% |
| source | unseen_de_sed | 185 | 300 / 47 | 120 / 19 | 86.33% | 237 / 80 | 74.76% |
| source | same_adp | 201 | 353 / 37 | 170 / 13 | 92.90% | 307 / 45 | 87.22% |
| source | same_conjunction | 200 | 357 / 34 | 172 / 17 | 91.01% | 306 / 42 | 87.93% |
| Jerome | correct | 0 | 40 / 1 | 15 / 0 | 100.00% | 29 / 2 | 93.55% |
| Jerome | rehearsed_in_et | 111 | 22 / 76 | 16 / 0 | 100.00% | 29 / 2 | 93.55% |
| Jerome | unseen_ad_que | 5 | 36 / 2 | 12 / 1 | 92.31% | 24 / 2 | 92.31% |
| Jerome | unseen_ad_sed | 9 | 36 / 2 | 13 / 1 | 92.86% | 24 / 4 | 85.71% |
| Jerome | unseen_de_que | 11 | 31 / 1 | 8 / 0 | 100.00% | 18 / 2 | 90.00% |
| Jerome | unseen_de_sed | 15 | 30 / 1 | 9 / 0 | 100.00% | 17 / 4 | 80.95% |
| Jerome | same_adp | 16 | 41 / 1 | 17 / 0 | 100.00% | 28 / 2 | 93.33% |
| Jerome | same_conjunction | 4 | 40 / 1 | 16 / 0 | 100.00% | 29 / 2 | 93.55% |
| Caesar | correct | 0 | 72 / 4 | 27 / 1 | 96.43% | 62 / 4 | 93.94% |
| Caesar | rehearsed_in_et | 63 | 37 / 12 | 26 / 1 | 96.30% | 62 / 4 | 93.94% |
| Caesar | unseen_ad_que | 71 | 65 / 33 | 16 / 18 | 47.06% | 44 / 35 | 55.70% |
| Caesar | unseen_ad_sed | 25 | 58 / 4 | 16 / 1 | 94.12% | 42 / 3 | 93.33% |
| Caesar | unseen_de_que | 57 | 76 / 25 | 23 / 22 | 51.11% | 57 / 34 | 62.64% |
| Caesar | unseen_de_sed | 11 | 66 / 4 | 22 / 1 | 95.65% | 56 / 2 | 96.55% |
| Caesar | same_adp | 32 | 69 / 5 | 25 / 1 | 96.15% | 60 / 4 | 93.75% |
| Caesar | same_conjunction | 50 | 70 / 4 | 23 / 1 | 95.83% | 60 / 4 | 93.75% |

At0.80, source clean augmented precision91.05% falls to68.10% (ad/que),85.60% (ad/sed),70.62% (de/que),86.33% (de/sed). The rehearsed in/et case retains90.86%. With Caesar, unseen que swaps are decisive counterexamples: ad/que16correct/18wrong (47.06%), de/que23/22 (51.11%), versus clean27/1 (96.43%) and rehearsed26/1 (96.30%). The corresponding original-model precisions are66.33% and75.25%, so the augmentation is worse on those two challenges.

The selected0.71 policy does not fix this: source unseen-swap precision ranges66.06%–74.76%; Caesar que swaps give55.70% and62.64%. Relative to clean predictions at the same cutoff, these Caesar swaps introduce33 and32 new false positives. Same-class source controls retain92.90% and91.01% at0.80, close to clean91.05%, supporting the distinction between identity errors within a class and errors that change the proposed class.

Jerome has only5–15 affected tokens in the new cross-class patterns, versus25–71 for Caesar and185–216 source. Its higher observed precisions do not rescue the general claim. Token frequency and contexts differ; these are fixed stress cases, not estimated rates of naturally occurring mapping errors.

## Controls and scope

Clean and rehearsed control probabilities reproduce iterations87/89 despite rekeying. Models, inventories and thresholds are unchanged. Evaluation artifacts preserve recall, hidden-token metrics, prediction transitions from the clean baseline, and frozen nearest-left F1 for every case. Nearest-left has a different operating point; no matched-precision advantage is established.

This is still conditional restoration of PP-governed membership, not exact governor links, Case, full grammatical structure, anchor discovery or lexical nuclei. Failure with wrong supplied mappings does not negate the clean-anchor findings. It shows that targeted augmentation has not solved the anchor-correctness requirement. No reserve, sealed lexical final test or new annotations were used.

## Decision and next check

Do not adopt iteration89 as a general anchor-error solution or keep adding individual swaps without an explicit generalization test. A more informative next diagnostic is an independent anchor-class audit: hide a candidate anchor type everywhere, infer its POS from the remaining context, pool evidence across occurrences, and compare that evidence with the proposed class. Freeze detection/abstention rules on source calibration and evaluate both correct-anchor false alarms and unrehearsed-swap detection before connecting the gate to PP inference. Source-modal anchor classes are known for source supervision; target reference classes must not enter detection features or decisions. This is proposed, not yet tested.

Validation: all48 model/dataset/pattern conditions replayed; patterns regenerated using only source-fit frequency; opaque equality IDs preserved; frozen thresholds and original/augmented control scores verified; 2,179 prior frozen-input hashes verified;87 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration90/.
