# Iteration 109: long-context source calibration enables substantially more restoration

**Preserve this positive conditional finding:** a separately source-calibrated long-context rule gives **46 correct / 3 wrong** primary Caesar repairs, versus 26 / 2 under the previous cutoff. **45 affected corruption cases recover the clean PP probability vector, versus 25 previously.** The additional exact hit affects zero scored tokens and is not credited as grammatical restoration. The short-context rule remains OFF.

This is a different policy hypothesis from iteration 108's shared rule. It does not pass that experiment's requirement for one operating point with useful coverage in both regimes, and it does not solve short-text restoration.

## Source-only selection and routing

Reuse exactly iteration 108's 11,910 gain/gap/stability settings and 603 cached source-calibration cases. Choose independently for the full 829-sentence regime and the eight 100-sentence blocks. Within each regime retain its existing guard: at least 90% exact-pair precision, at least ten full or twenty pooled sparse calls, zero clean/same-class false calls, and zero wrong calls with an unavailable true partner. Maximize correct repairs, then fewer wrong repairs, smaller gap, smaller stability cutoff and higher gain cutoff. Choose OFF if no rule qualifies in that regime.

Derive routing bands from the source input sizes before author replay: at most 100 sentences uses the short rule; at least 829 uses the long rule; intermediate sizes abstain. These bands are conservative observed calibration ranges, not an estimated minimum text length. Raw-prose segments and annotated source sentences are not identical units, and total size does not guarantee enough evidence for each word type.

The long regime has 4,643 qualifying settings. The selected rule requires gain at least **0.354845920096932**, rank stability at least **0.50**, and gap at least zero. It restores all 64 source-calibration errors with zero wrong recommendations; all three controls abstain. No sparse setting qualifies, so the short rule is OFF. Freeze both rules and routing before loading the corrected author inputs. No Caesar threshold selection, model fitting or new annotation occurs.

## Author pair results

Keep all three iteration-107 context views, sixteen candidate types, 195 supplied context anchors, all 64 cross-class swaps and three controls, including all eight errors whose `c` partner is unavailable after the generic initial-identity correction.

| Context | Previous fixed cutoff: correct / wrong | Conditional rule: correct / wrong / abstained errors |
|---|---:|---:|
| Original 100 | 6 / 14 | 0 / 0 / 64 |
| Civil-added, 1,674 segments | 28 / 1 | 49 / 3 / 12 |
| Primary expansion, 2,494 segments | 26 / 2 | 46 / 3 / 15 |

All clean/same-class controls abstain. Primary observed recommendation precision is 46 / 49 = **93.88%**, with recall 46 / 64 = **71.88%**. These are reused development results, not guaranteed precision. The primary expansion remains the predeclared main view; the Civil view is not selected post hoc.

One exact hit in each added view (`sine/uel`) affects no scored token. The affected-error grammatical restoration counts are therefore 45 in the primary view and 48 in Civil. The source-calibrated short rule's abstention removes both correct and wrong original-context recommendations; it does not improve those PP inputs beyond leaving them corrupted.

## Fixed-position grammatical outcome

Apply every recommendation blindly using global context assignments, then evaluate only the original 100 sentences / 1,514 token positions. Added prose never enters PP feature extraction or pooling. Keep the original iteration-85 model at 0.80 and augmented iteration-89 model at 0.71 and 0.80. No pair-correctness gate, threshold changes, reserve scoring, sealed lexical test or new annotations are used.

All affected exact repairs reproduce the full clean probability vectors. The clean original model's subset remains 72 correct / 4 wrong PP memberships at 94.74% precision and 45.28% recall. This is recovery of the same grammatical subset under more alternative corruptions; clean coverage and lexical nuclei do not increase.

Across the 62 affected alternative errors, the original PP model gives:

| Input / rule | Correct selections | Wrong selections | Precision | Recall |
|---|---:|---:|---:|---:|
| Corrupted, no repair | 3,969 | 571 | 87.42% | 40.26% |
| Previous primary cutoff | 4,110 | 434 | 90.45% | 41.69% |
| Conditional primary rule | 4,278 | 245 | 94.58% | 43.40% |
| Conditional Civil rule | 4,323 | 287 | 93.77% | 43.85% |
| Clean comparator repeated 62 times | 4,464 | 248 | 94.74% | 45.28% |

Primary repair versus corruption adds 414 correct memberships, loses 105, adds twenty false memberships and removes 346: net **+309 correct / −326 false** selections. Compared with the previous primary cutoff, it adds net 168 correct selections and removes 189 false selections. Gross losses remain visible even when a correct mapping restores the clean model. These totals repeatedly count the same positions under alternative mappings and are not unique restored words or independent observations.

## Remaining errors and availability shift

All three primary wrong actions select `uel` as a substitute partner: `a/et`, `a/que`, and `ad/et`. The newly active `a/que` failure is retained. The ten `uel` observations still come from only four segments, despite the large total context. A gain threshold appropriate to the complete long source sample does not make every rare candidate reliable.

All three Civil wrong actions occur when the true `c` partner is absent: `ab/c`, `de/c`, and `sine/c`, selecting `a/ab`, `a/de`, and `a/sine`. The last corruption affects zero original tokens, but the wrong action changes them and loses two true PP selections, as already observed in iteration 107. Full-bank results include it.

The complete long source sample supports all sixteen candidates, so its zero-unavailable-error guard contains no unavailable-partner error examples. The author tokenizer correctly separates initials from syntactic `c`, leaving that candidate absent. This availability shift is a concrete limitation of volume-only routing and a reason to stress-test it before adoption. All errors remain counted; no `c` blacklist or smaller successful error bank is substituted.

## Verification and next test

Independently check 23,820 per-regime source-setting decisions, reproduce the selected rules and routing, and replay all 201 blind author actions. Verify 907 input hashes, seventy prediction-cache payloads, six new PP model inferences and 1,809 independent confusion counts, along with hidden counts, gross transitions and clean-probability comparisons. Ninety-three affected exact restorations across the two overlapping added views are verified, not ninety-three independent successes. All 65 focused tests pass, including joint-gate and conditional-routing tests. Artifacts and the frozen tracker/design are in `experiments/results/grammar-restoration/iteration109/`.

Next stress the frozen long-context rule on source cases with **each candidate omitted from the repair pool in turn**, using all sixteen omissions rather than the inspected author word. Recompute rankings and stability from the cached pair columns, keep the original error bank, and explicitly count unsupported-partner errors and false substitute repairs. This is a candidate-availability diagnostic with context otherwise fixed, not literal deletion of words from the text. No new annotation or classifier predictions are needed. If that exposes the anticipated failure, evaluate source-calibrated reciprocal endpoint evidence as a separate proposed policy; do not tune it from the six author failures. Initial sentence-boundary handling and independent confirmation remain open.
