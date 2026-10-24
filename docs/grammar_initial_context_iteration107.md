# Iteration 107: preserving initial identities restores the broad-bank benefit

**Preserve this positive conditional finding:** a generic initial-abbreviation rule improves primary expanded-context pair repair from **6 correct / 44 wrong to 26 correct / 2 wrong** on the full 64-error bank, with unchanged models and cutoffs. On the original scored text, **25 affected corruption cases reproduce the clean PP probability vector, versus five before the fix**. The stricter frozen gain-gap rule gives 15 correct / 0 wrong repairs. This remains failure-motivated development evidence with supplied anchors and synthetic errors, not blind lexical or nucleus recovery.

## Single preprocessing change

When an uppercase single-letter token is followed by a period in the admitted raw prose, retain the period in its normalized identity: `C.` becomes `c.`, `L.` becomes `l.`, and likewise for other initials. The rule never names `c` or consults annotations. The punctuated form does not match the source function-anchor inventory and becomes opaque, rather than masquerading as a syntactic component such as source `ne-c`.

Apply this only to added raw context. Keep the original 100 sentences, 1,514 token positions and global type IDs unchanged. Retain the previous raw segment boundaries, including breaks after abbreviation periods, to isolate identity/anchor matching from sentence segmentation. This is not yet a complete Latin sentence tokenizer. The primary context changes 134 initial tokens across ten normalized letters. Only 30 previously visible anchors become opaque: 27 `c` initials and three `a` initials. Other changed initials were already opaque.

Keep the same admitted Gallic V/VII and Civil I–III books, Gallic VI overlap exclusion, all 195 supplied anchors, sixteen-type candidate catalogue, all 64 cross-class errors and three controls per context. Freeze the resulting public inputs before scoring. Reuse the exact classifier, support gate, 256 sentence-bootstrap draws, original cutoff and secondary gain-gap rule. The latter was calibrated with eight candidates; its transfer to the full bank remains a secondary test. All three OFF policies stay OFF. No training, cutoff adjustment, new annotation, reserve or sealed lexical test access occurs.

## Full-bank pair results

| Fixed rule / context | Before identity fix: correct / wrong | After fix: correct / wrong / abstained errors |
|---|---:|---:|
| Original cutoff, original 100 | 6 / 14 | 6 / 14 / 44 |
| Original cutoff, Civil-added | 9 / 48 | 28 / 1 / 35 |
| Original cutoff, primary expansion | 6 / 44 | 26 / 2 / 36 |
| Gain-gap, original 100 | 3 / 7 | 3 / 7 / 54 |
| Gain-gap, Civil-added | 0 / 30 | 25 / 0 / 39 |
| Gain-gap, primary expansion | 0 / 29 | 15 / 0 / 49 |

All clean/same-class controls abstain. The unchanged original-context case files and bootstrap arrays are reused bit for bit as a control. No context view is selected using these outcomes.

All eight errors involving the now-absent syntactic `c` endpoint remain in the 64-error denominator and count as misses. In both added views, 56 true pairs remain supported and globally available. Their raw top rank is correct in all 56 Civil cases and 53 / 56 primary cases. This does not license dropping the unavailable cases or lowering the cutoff to claim those rankings as repairs.

Primary recommendation precision is 26 / 28 = 92.86%, with recall 26 / 64 = 40.63%; these are observed development proportions. One primary exact hit (`sine/uel`) affects zero scored tokens. Therefore the grammatical-restoration count is **25 affected exact repairs**, not 26. In the Civil view, 27 exact hits affect the query; a further exact hit is likewise zero-affected. The stricter rule's 15 primary and 25 Civil hits all affect scored positions.

The matched fifteen core errors also improve over iteration 106: primary results change from 0 correct / 15 wrong to 8 / 2, and Civil from 2 / 13 to 8 / 0. The earlier eight-candidate 9 / 0 result is still not a guarantee for the broader pool.

## Actual grammatical benefit

Every affected exact repair restores the full probability vector of both frozen PP models on the original 100 sentences. The clean original model at 0.80 gives 72 correct / 4 wrong memberships; the augmented model gives 62 / 4 at 0.71 and 27 / 1 at 0.80. These existing clean errors and omissions are preserved. This improves robustness to alternative corruptions, without expanding clean grammatical coverage or recovering additional lexical nuclei.

Across the 62 affected alternative errors, original-model outcomes are:

| Intervention | Correct PP selections | Wrong PP selections | Precision | Recall |
|---|---:|---:|---:|---:|
| Corrupted, no repair | 3,969 | 571 | 87.42% | 40.26% |
| Original-context repair | 4,048 | 546 | 88.11% | 41.06% |
| Previous primary expansion, colliding identities | 3,891 | 223 | 94.58% | 39.47% |
| Corrected primary expansion | 4,110 | 434 | 90.45% | 41.69% |
| Clean comparator repeated 62 times | 4,464 | 248 | 94.74% | 45.28% |

Corrected primary repair versus corruption adds 181 true selections, loses 40, adds seven false selections and removes 144: net **+141 correct and −137 false selections**. Compared with original-context repair, it gains 62 correct selections and removes 112 false selections. The earlier unsafe expansion's higher PP precision came with lost correct coverage; it was not evidence of correct mapping recovery.

Both augmented settings also improve over original-context repair: at 0.71, 3,489 / 585 becomes 3,544 / 466; at 0.80, 1,503 / 200 becomes 1,546 / 116. All totals repeat the same token positions under different synthetic mappings and are not unique restored words or independent observations.

## Remaining failures and context sensitivity

The two primary wrong actions are `a/et` and `ad/et`, both selecting `et/uel`. Their rank gaps are about 0.0792 and 0.0487, and bootstrap rank stabilities 0.6367 and 0.6094. The fixed gain-gap rule rejects both.

`uel` has only ten added-context occurrences in four segments: two in one Civil-I segment, two in one Civil-II segment, five in one Civil-III segment, and one in Gallic VII. In the wrong pair masks, the Gallic-VII occurrence has P(CCONJ) about 0.0452. Its influence is enough to change the competing type profile, despite the overall context containing more than 52,000 tokens. Total corpus length is not equivalent to reliable evidence for each candidate.

Report all five leave-one-book-out counterfactuals for both errors. Removing Gallic VII changes `ad/et` to an exact repair and `a/et` to abstention; removing the other books leaves the wrong selections. This is a post-result diagnostic, not a policy that selects the Civil view or discards Gallic VII.

The Civil view's sole wrong action is `sine/c`, whose true partner is unavailable. The injected error affects zero query tokens, but the wrong `a/sine` recommendation modifies the query and reduces correct PP selections from 72 to 70, with four false selections unchanged. This failure remains in full-bank results and is not hidden by the affected-error stratum. The gain-gap rule rejects it too.

## Verification and next proposal

Replay all 201 bootstrap cases, 1,005 blind case-policy actions, and 162 PP model inferences for 81 unique scored inputs. Recompute 154 clean pair profiles, 20,612 endpoint count checks, 5,604 unchanged original-prefix probability checks and 2,592 legacy point gains. Verify all 265 changed public tokens across the two added views and 270 unchanged base core scores; check 9,045 independent confusion counts, hidden counts, gross transitions and 4,320 aggregate fields. Verify 1,400 audit input hashes. All 61 focused tests pass. Decompose all three remaining added-context wrong actions from saved totals, including all ten book-deletion counterfactuals; no policy changes follow inspection.

Artifacts and frozen tracker/design: `experiments/results/grammar-restoration/iteration107/`. The helper is `src/voynich_smt/initial_abbreviation_context.py`. Existing experiments remain unchanged.

Next calibrate the previously untested **combined gain + runner-up gap + bootstrap rank-stability gate** using only the cached full sixteen-candidate source-calibration cases, with the same precision, coverage, clean-control and unavailable-partner guards. Earlier tests calibrated gain/gap and gain/stability separately. Freeze the combined policy before evaluating these corrected author inputs; do not pick thresholds from the three inspected failures. Retain OFF if no source-only policy qualifies. Sentence-boundary handling after initials and independent confirmation remain necessary before a general adoption claim.
