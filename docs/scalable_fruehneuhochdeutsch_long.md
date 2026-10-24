# Frühneuhochdeutsch: long-text and excluded-author validation

The missing long-text test is now complete: the unchanged English algorithm was run on **35,000 continuous retained words from Arndt**, a **31,260-word confirmation from Abelin**, and the full retained stretches of three excluded ReF authors. No Voynich inference was performed.

The long texts reach about **13–14% mean literal recovery with random starts**, with only two or three correct unanimous frequent anchors. A substantial reliable nucleus has not emerged. Historical spelling does account for some apparent failures, but a separate lemma diagnostic also remains modest. These results support further model work before treating a Voynich output as trusted restoration.

## Frozen algorithm and experiment design

Retain the original English sparse bigram score, mixed search scheduler, full frozen inventory, candidate retrieval, temperatures and archive selection. Each text has random/frequency starts, seeds 3/5/7, and **8,000 proposals per chain**. All **30 chains / 240,000 proposals** complete; no timed-out or unfavorable chain is discarded. English/Latin defaults are unchanged.

The ReF trials use the original model/inventory exactly. Arndt requires a separately recorded overlap cleanup; Abelin's independently rebuilt model reproduces the parent identity. All dictionaries have the same **245,420 source-derived forms**. No target vocabulary, topic, author, regional label, sentence boundaries, translation hints or anchors enter inference. Public ciphertext exposes word boundaries/order under the same injective whole-word channel assumption as English/Latin.

Initial design: `experiments/results/scalable-fruehneuhochdeutsch/length-validation-v1/design.json`. The second long source was added through a separate `confirmation-selection.json`, after seeing the initial cohort but before any Abelin decipherment; the algorithm was frozen. The same three previously reserved ReF development authors were all retained. Validation/sealed sources **F019, F283, F001 and F161 remain unrun for recovery**.

## Long sources, continuity and resource limits

- [Johann Arndt, *Von wahrem Christenthumb*, volume 1 (1610)](https://www.deutschestextarchiv.de/book/show/arndt_christentum01_1610): DTA TEI, CC BY-SA 4.0. Our extracted main body has **69,008 tokens**, with 485 consecutive facsimile pages, scans 33–517, and no retained main-text gap. Freeze its first **35,000 tokens** before recovery; headings remain, with no topic/vocabulary filtering.
- [Johann Philipp Abelin, *Theatrum Europaeum* (1635)](https://www.deutschestextarchiv.de/book/show/abelinus_theatrum_1635): DTA/HAB TEI, **CC BY-SA 3.0 DE** per the item's header, distinct from the site's general footer. It is the first author in the downloaded DTA catalog with a numeric publication date 1600–1650. Our main-text extraction retains 1,032,182 tokens in 244 gap-separated segments; the longest is **31,260 tokens**. Use that entire segment, number 187, rather than joining gaps to reach 35,000. This is a near-length confirmation, not a second exact 35,000-word fixture.

Both new targets exclude marginal notes, page furniture and figures, select original TEI readings rather than modernizations, retain supplied transcription, and mechanically join marked line wraps. Lowercase/NFC/long-s folding match the declared historical surface policy; diacritics, abbreviation marks and u/v, i/j distinctions remain. Abelin's underlying edition has its own transcription conventions, including superscript-e rendered as umlauts. Therefore this is not a perfectly controlled comparison of orthography alone. Source notices, download URLs and hashes are retained in `data/raw/scalable-fruehneuhochdeutsch/long-source-audit/` and the experiment's `SOURCES.md`.

The full DTA main texts are screened against training for exact and mechanically folded 12-word overlaps. Folding removes combining marks and equates v/u and j/i **only for the overlap screen**, never for inference. For Arndt, remove two entire training segments, **13,396 tokens (0.45%)**, leaving **2,943,106 training tokens**. Abelin requires no removals and reproduces the **2,956,502-token parent model**. Author-name checks find neither named author in admitted training metadata. Unknown attribution and paraphrased overlap cannot be ruled out by these screens.

Inventory token coverage ceilings are **94.78% for Arndt** and **87.29% for Abelin**, versus 90.58–92.68% for the shorter works. Target-missing words remain missing. The dictionary still contains training forms only, unlike English's external-lexicon-plus-training inventory. The two DTA targets are late-period printed works; they do not establish performance on all earlier regions, manuscripts or transcription conventions.

## Literal results and frequent anchors

| Text | Words | Start | Mean literal | Score-selected literal | Correct / primary anchors | Correct anchor token coverage | Top 50 correct |
|---|---:|---|---:|---:|---:|---:|---:|
| Hartlieb | 8,484 | random | 12.26% | 19.15% | 1/1 | 4.76% | 2/50 |
| Hartlieb | 8,484 | frequency | 10.09% | 9.94% | 3/6 | 9.51% | 3/50 |
| Gelnhausen | 7,590 | random | 2.16% | 5.23% | 0/1 | 0.00% | 0/50 |
| Gelnhausen | 7,590 | frequency | 11.62% | 15.84% | 1/2 | 3.14% | 7/50 |
| Merswin | 6,447 | random | 1.72% | 2.81% | 0/1 | 0.00% | 1/50 |
| Merswin | 6,447 | frequency | 0.49% | 1.04% | 0/2 | 0.00% | 0/50 |
| Arndt | 35,000 | random | 14.07% | 14.13% | 3/4 | 4.45% | 9/50 |
| Arndt | 35,000 | frequency | 9.89% | 13.54% | 1/2 | 3.69% | 1/50 |
| Abelin | 31,260 | random | 13.01% | 16.99% | 2/2 | 5.19% | 8/50 |
| Abelin | 31,260 | frequency | 7.21% | 10.89% | 2/2 | 5.19% | 2/50 |

“Mean” averages all three source-score-selected restart keys. “Score-selected” chooses a restart by the source objective, never by plaintext accuracy. Top-50 uses one most-voted prediction per cipher type, ranked by agreement then public frequency; single-vote entries are not a trustworthy dictionary.

Primary anchors require agreement across all three runs and at least 100 public occurrences. This length-dependent rule admits only **5–11 types** in the short ReF passages, so those passages cannot establish a 20-type nucleus under it. The long works permit a meaningful larger-support check. Neither produces the provisional target of at least 20 selected types at 80% measured precision, let alone confirmation on two independent authors. Small 2/2 observations do not calibrate a probability of correctness.

On Arndt, random starts recover `vnd` (1,293 positions), `aber` (149), and `sein` (117), but unanimously decode `es` as `daz` (145). Frequency starts retain `vnd` and incorrectly map `dem` to `ein` (265). On Abelin, both initializers unanimously recover `vnd` (1,047) and `in` (574), giving **5.19% correct token coverage**. The shared frequency initializer is one starting dictionary, not three independent initial guesses.

The 4,000-word Hartlieb pilot versus this full 8,484-word test changes **length and proposal cap together**. Its 13.59% random / 13.06% frequency means become 12.26% / 10.09%; that is not a causal estimate of a length effect. Per-seed results remain in `summary.json`.

## Spelling, lemma identity and actual meaning

Exact surface recovery understates some useful historical-word matches. Merswin's `vn̄` is decoded as `vnd`: every corresponding reference lemma label is *und*. Literal matching marks that wrong even though it identifies the lexical word.

A **post-hoc descriptive diagnostic** fits one most-frequent `(lemmaId, lemma)` analysis for each predicted spelling using **admitted source annotations only**. Freeze that table before reference evaluation; never choose whichever analysis matches the hidden answer. Compare the selected analysis with private reference annotations, separately by raw ID and lemma label. No decoder, shortlist or parameter changes result.

Mean results on positions with reference lemma labels:

| Text | Starts | Literal, same positions | Lemma-label agreement |
|---|---|---:|---:|
| Hartlieb | Random | 13.50% | 17.77% |
| Hartlieb | Frequency | 11.11% | 13.05% |
| Gelnhausen | Random | 2.46% | 6.57% |
| Gelnhausen | Frequency | 13.26% | 19.54% |
| Merswin | Random | 1.94% | 11.81% |
| Merswin | Frequency | 0.55% | 9.20% |

Coverage is 7,704/8,484, 6,646/7,590 and 5,723/6,447 positions respectively. Many reference analyses are automatic; manual-only results and their much smaller coverage are retained. No aligned independent lemma reference is supplied for the DTA fixtures, so their lemma accuracy is **not claimed**.

Raw IDs have quality problems: Merswin's same lemma *und* appears under both `[GU05758]` and `[G0U5758]`. Raw-ID results remain available rather than silently correcting IDs from target answers. Label agreement avoids that typo but can conflate homographs and credit wrong inflections. **Neither metric establishes grammatical or semantic recovery.** Fixed original/restored passages are retained for human assessment.

## Scoring controls and interpretation

After inference, evaluation-only feasible references restore every available word and assign distinct proxy words to absent true types. They attain each fixture's inventory coverage ceiling, not 100% correctness. Under a rare-proxy scheme, all six optimized wrong dictionaries outscore the reference on every work. Common-proxy alternatives on the long works beat the three random-start outputs but still lose to the frequency-start outputs. Proxy choice therefore matters; these controls neither isolate the cause nor prove how an unavailable fully correct dictionary would score.

The repeated finding is that model score and stable agreement are insufficient evidence of correct recovery. Larger texts do expose a small structural core, but have not solved dictionary/scoring mismatch. The low shorter-author results and limited long-text nucleus also prevent treating the earlier English percentage as a general expectation for historical German.

The long-text testing gap is closed to a useful first approximation. The remaining problem is restoration quality and confidence, including source spelling variation, vocabulary coverage and an objective that favors plausible wrong assignments. No Voynich reading is asserted, and the assumed cipher structure remains unverified for that manuscript.

## Artifacts, verification and reproduction

Artifacts: `experiments/results/scalable-fruehneuhochdeutsch/length-validation-v1/`. Each run retains public input, checkpoints, traces, full-score evaluation, complete top-50 tables and fixed original/restored excerpts at offsets 0, 1000 and 2000. Private fixture paths are isolated per trial, unavailable at their normal location during inference, and restored afterward. `summary.json`, `objective-diagnostics.json`, `lexeme-diagnostics.json`, source/model manifests and `validation.json` record the comparison and checks.

Search times sum to **74.76 minutes** across concurrent runs, excluding source preparation and evaluation; this is not elapsed bundle time. Peak individual shared-process RSS is approximately **0.94 GB**, not combined system memory. ReF trials retain the English 400-second per-chain allowance; DTA trials use a configurable 1,200-second ceiling to allow fixed-cap completion. Every chain actually finishes below 400 seconds, so the higher ceiling does not censor or extend their proposal trajectories.

**167 relevant tests pass.** Tests cover original-vs-modernized readings, physical line wraps/page furniture, combining marks, illegible gaps and Unicode fixture/search/serialization integration. All saved initial/current/archive scores are independently validated; anchor metrics reproduce exactly; paired protocols differ only by initialization within each text. Existing English/Latin resource identities remain unchanged.

Drivers:

```
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_long prepare
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_long prepare-long
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_long prepare-confirmation
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_long trial --work F137 --initialization random
# Repeat trial for every work and initializer; DTA runs use --budget-seconds 1200.
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_long summarize
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_diagnostics
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch_lexemes
```

Preparation requires cached, hashed source archives/XML and refuses to overwrite resource directories. Select a fresh experiment version before intentional reruns. The lexeme diagnostic is supplementary; it does not select or alter any decipherment run.
