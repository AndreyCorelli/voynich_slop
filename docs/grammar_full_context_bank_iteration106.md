# Iteration 106: full-bank challenge fails; raw initials collide with syntactic components

**The added-context result does not survive the full candidate bank.** With all sixteen candidates and 64 cross-class swaps, the fixed original cutoff gives **6 correct / 44 wrong** repairs after primary expansion, versus 6 / 14 on the original sample. All 44 expanded wrong recommendations involve `c`. On the matched fifteen core errors, expansion changes the earlier eight-candidate result of 9 correct / 0 wrong to **0 correct / 15 wrong** when the extra competitors are available.

The eight-candidate conditional finding from iterations 104–105 remains recorded, but it is not a generally reliable repair method. This challenge exposes a concrete representation mismatch: the source inventory's `c` is mainly the separated conjunction component of `ne-c`; raw added prose instead contributes `C.` name abbreviations under the same normalized identity.

## Frozen challenge

Use the exact three iteration-104 public context views, unchanged original 100-sentence prefix, context-selection exclusions and tokenizer. Keep all 195 supplied context anchors, the source-defined sixteen candidate types, all 64 global ADP/CCONJ swaps and three clean/same-class controls: 201 cases. Keep the original classifier, count gate, original iteration-95 cutoff and all 256 sentence resamples. The iteration-103 gain-gap rule is a secondary transfer check: it was calibrated with eight candidates, not sixteen. Its three OFF companion policies stay OFF. No calibration, threshold selection, new annotation, reserve scoring or sealed lexical access occurs.

Three candidates are absent from the original query (`c`, `sine`, `uel`) but may occur in added context. Apply every recommendation using its context-level assignments, then pass only the original 100-sentence prefix to the unchanged PP models. Do not reject an action because an endpoint is absent from the query. Keep all errors in evaluation, separating the two swaps (`sine/c`, `sine/uel`) that affect zero scored tokens. This avoids counting their unchanged grammatical predictions as newly restored structure.

## Exact pair recovery

All entries below count the full 64-error bank; controls abstain under both active rules in every view.

| Fixed rule and context | Correct | Wrong | Abstained errors |
|---|---:|---:|---:|
| Original cutoff, original 100 | 6 | 14 | 44 |
| Original cutoff, plus Civil | 9 | 48 | 7 |
| Original cutoff, primary expansion | 6 | 44 | 14 |
| Gain-gap, original 100 | 3 | 7 | 54 |
| Gain-gap, plus Civil | 0 | 30 | 34 |
| Gain-gap, primary expansion | 0 | 29 | 35 |

The original sample supports only 24 true pairs; both added-context views support all 64. More occurrence support therefore does not rescue the pipeline. Raw correct top ranks are 10 / 64 originally, 9 / 64 with Civil, and 6 / 64 under primary expansion.

Of the primary cutoff's six exact hits, five affect the query: `sine/ac`, `sine/atque`, `sine/aut`, `sine/que`, and `sine/sed`. The sixth, `sine/uel`, affects no scored token. On the 62 affected errors, results are 5 correct / 44 wrong, with only five cases restoring clean PP probabilities. The gain-gap rule repairs none correctly. All original core-pair scores are unchanged by adding competitors; the loss is caused by their ranking against the expanded pool, not a changed score computation.

## Representation diagnostic

Inspect only previously cached source-fit annotations and the admitted raw books; do not change policy after inspection.

- Source fit contains 95 `c` tokens: 93 CCONJ and two PROPN. All 93 conjunction instances immediately follow `ne`, with contexts such as `ne c per ...` and `ne c facere ...`.
- Added raw prose contributes 27 standalone `c` tokens: seven in Civil I, seven in Civil II and thirteen in Civil III; none in admitted Gallic V/VII. All 27 are followed by a period in raw text and end a segment under the current period-splitting tokenizer. Examples include `C. Caesaris`, `C. Trebonius`, and `C. Triarius`.
- Normalization strips the abbreviation punctuation and case before matching the source anchor inventory, conflating these initials with the syntactic component. The source-modal CCONJ assignment consequently does not transfer to these occurrences. The binary classifier gives their mean P(CCONJ) approximately 0.30–0.31 under clean joint-mask views, creating a strong apparent class disagreement for a candidate that the pipeline wrongly treats as a conjunction anchor.
- All 44 primary-expanded wrong pairs involve `c`; 47 of 48 Civil wrong pairs do. All 29 primary-expanded gain-gap wrong pairs involve it too.

This evidence identifies a representation/anchor-applicability problem rather than sampling noise alone. Eleven primary-expanded wrong winners have bootstrap rank stability at least 0.90; Civil has wrong winners stable in every resample. Resampling can make a systematic mismatch confidently wrong. No `c` blacklist or target-selected rerun is adopted here.

## Grammatical effects: precision alone is misleading

On the 62 affected alternative corruptions, the original PP model at 0.80 gives:

| Input / intervention | Correct PP selections | Wrong PP selections | Precision | Recall |
|---|---:|---:|---:|---:|
| Corrupted, no repair | 3,969 | 571 | 87.42% | 40.26% |
| Original-context recommendations | 4,048 | 546 | 88.11% | 41.06% |
| Civil recommendations | 3,909 | 223 | 94.60% | 39.65% |
| Primary-expanded recommendations | 3,891 | 223 | 94.58% | 39.47% |
| Clean comparator, repeated 62 times | 4,464 | 248 | 94.74% | 45.28% |

Primary expansion versus corruption adds 23 correct memberships, loses 101, adds five false positives and removes 353: net **−78 correct selections and −348 false selections**. Precision rises by suppressing predictions while most anchor repairs are wrong. Relative to original-context repair, it loses 157 correct selections and removes 323 false selections. This is not evidence that the correct translation or clean grammatical structure was restored.

The augmented PP models show the same coverage boundary. At 0.71, original-context outcomes are 3,489 / 585 versus primary expansion 3,409 / 216; at 0.80, 1,503 / 200 versus 1,477 / 59. The clean/same-class controls and the two zero-affected errors are reported separately. Counts repeat the same 1,514 token positions under alternative synthetic mappings, not independent observations or unique restored tokens.

## Verification and next test

Replay all 201 bootstrap cases, recompute 170 clean pair profiles, verify 22,756 endpoint count arrays and 5,604 unchanged original-prefix probability profiles, and reproduce 2,592 legacy original-sample pair gains. Check 810 unchanged core-pair scores. Replay all 1,005 case-policy actions; independently recompute 244 PP model inferences for 122 unique scored inputs and 9,045 confusion-count checks, including hidden selections and gross transitions. Verify 867 input hashes and 3,600 aggregate count fields. All 59 focused tests pass, including tests for a repair endpoint absent from the query and zero-affected query handling.

Artifacts, frozen design and tracker snapshot, all wrong actions, input deltas, complete score arrays, representation examples and audits are in `experiments/results/grammar-restoration/iteration106/`.

Next test a generic preprocessing correction that preserves initial abbreviations as distinct surface tokens instead of merging them with syntactic components. Apply it uniformly to initials, not as a `c` exception; inspect compatibility with source token boundaries before matching function anchors. Retain the same books, original 100 sentences, fixed models/rules and complete 64-error bank. Count newly unavailable true partners as misses and report both all-error and compatible-endpoint strata. This is a failure-motivated development diagnostic requiring later confirmation, not permission to drop inconvenient errors or select a smaller successful pool.
