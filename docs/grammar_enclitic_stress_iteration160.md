# Iteration 160: coarse frequency shortlist survives an enclitic-joining stress test

**Preserve the robustness result:** the frequency top10 signal does not depend on keeping the tested enclitic components separate. After fixed label-blind joins, its tie-robust correct-count ranges are Caesar10/10, Jerome8–9/10, Cicero9/10 and Palladius9–10/10 under both reference projections. This is a segmentation stress test, not verified reconstruction of original orthographic words.

The boundary audit covers all1,799 admitted sentences in the four existing datasets. Every sentence has zero multiword-token ranges, zero SpaceAfter=No metadata, and a text header matching the already split FORM sequence. For example, the cached text itself contains silvis que and ne c. Thus these files do not independently identify the original joins. No new POS annotations were read: labels come from the existing caches, while raw-file projection is limited to FORM and boundary metadata for admitted sentence IDs, excluding reserved material before projection.

The initial metadata preflight exposed an existing normalization difference: iteration40 lowercases/u-v/i-j normalizes, while iteration44 additionally uses the existing Latin tokenizer (e.g. cciↄↄ→cci). That failed attempt produced no features or predictions and is preserved in `iteration160-preflight-initial`. The normalization correction and amended design were frozen before features; the audit verifies both the archived and final inputs. The experiment's joins, models and metrics did not change.

The predeclared stress rule joins each que or ue to the preceding token within its sentence, and joins c only after literal ne to form nec. It never crosses sentence boundaries and leaves sentence-initial components untouched. Selection uses word forms, never POS or observed errors. All other words remain in order. There are351 joins:

| Dataset | que | ue | c after ne | Original tokens → joined |
|---|---|---|---|---|
| Caesar | 48 | 0 | 0 | 1,514 → 1,466 |
| Jerome | 0 | 0 | 2 | 913 → 911 |
| Cicero | 230 | 8 | 57 | 20,136 → 19,841 |
| Palladius | 2 | 0 | 4 | 737 → 731 |

All supported joined types (>=5 occurrences) remain eligible with no purity, source-vocabulary or candidate-class filter. Frozen iteration157 models are unchanged, including their training segmentation; raw count features are primary and no length-normalized arm is added here. Anonymous features are recomputed on original and joined streams. Word views/events were frozen before feature computation and predictions before reference projection/metrics.

Projected references use cached component POS only. The primary host policy retains the first component's POS; the deliberately generous alternative uses the first component in the seven-tag positive union, if one exists, otherwise the host POS. Type labels come from the resulting modal POS. Neither policy is a validated annotation of reconstructed orthographic words. Both are reported, without selecting a favorable policy.

| Dataset | Original frequency top10, any boundary tie | Joined host projection | Joined component projection |
|---|---|---|---|
| Caesar | 9/10 | 10/10 | 10/10 |
| Jerome | 8–9/10 | 8–9/10 | 8–9/10 |
| Cicero | 8/10 | 9/10 | 9/10 |
| Palladius | 9/10 | 9–10/10 | 9–10/10 |

The inherited lexical tie-break displays10/10 in joined Palladius, but anonymous tie resolution permits9/10, so the range is the relevant result. Every top5/10/20/50 boundary tie is retained in the artifacts. Different joined reference policies can change other models' results (e.g. Caesar combined9/10 host versus10/10 component), which is why both policies remain explicit. Structural-only performance remains inconsistent across authors; no favorable per-author model is promoted.

This challenges one concrete segmentation dependency and preserves a possible grammatical input: a frequency-led shortlist enriched for ADP/AUX/CCONJ/DET/PART/PRON/SCONJ. ADV remains outside the defined union. It does not establish exact orthographic reconstruction, original manuscript segmentation, generic POS tagging or Latin word identities. Authors/statuses and development reuse are unchanged: Caesar/Jerome are source-unseen author sets, Cicero/Palladius seen-author sentence checks.

Next proposed utility test: use the frozen coarse cue as a soft prior in a controlled lexical candidate-ranking comparison against source unigram frequency alone. Declare an oracle exact-vocabulary candidate condition if used, derive candidate POS knowledge only from the source lexicon, leave unknown candidate labels uninformative, and evaluate target labels only after all scores. Freeze prior strength/ranking and report true-candidate rank changes and coverage before claiming that grammatical enrichment helps a decoder. This tests whether the cue adds information beyond frequency, rather than merely documenting a known frequency effect; no exact-nucleus success is presumed.

Independent verification reconstructed every join and projected reference, checked all metadata and the preflight amendment, recomputed1,335 feature vectors with independent combinatorial/dictionary implementations, replayed4,005 probabilities and48 metric groups, and verified all four original author summaries. No fitting, new labels, reserved text projection or production model changes occurred. Artifacts and manifest: `experiments/results/grammar-restoration/iteration160/`.
