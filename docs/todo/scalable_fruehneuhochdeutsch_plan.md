# Frühneuhochdeutsch decipherment: implementation plan

Status: resource/pilot and long-text validation completed, 2026-10-15; see progress below. No Voynich inference has started.

Confirmed scope: repeat the algorithm and overall setup that worked for English, using Early New High German resources. The first deliverable is a direct baseline replication, not a new decipherment method. A reliable frequent-word nucleus is the primary goal; historical spelling modernization is not the requested task.

Reference: [independent-work English benchmark](../scalable_english_independent.md). Its main setup used a continuous 35,000-token target, an independently frozen inventory, sparse bigram scoring, the mixed scheduler, seeds 3/5/7, and paired random/frequency starts at 8,000 proposals per seed. Frequency-start mean recovery was 29.70%; source-score-selected recovery was 34.91%. Preserve the numerical search/retrieval settings from those saved protocols unless a language-independent compatibility issue requires a documented change.

## 1. Objective and constraints

Recover useful structural words and grammatical relationships from relatively long historical German passages, without supplying topic, target vocabulary, sentence boundaries, guessed translations, author, date or regional labels to inference. The language-period hypothesis itself is allowed. Date, region and genre metadata may organize training and evaluation splits, but cannot select a target-specific dictionary/model in the primary benchmark.

Start with injective whole-word substitution: each historical surface type has a unique opaque cipher type, with word order and word boundaries preserved. Cipher labels must reveal neither original word length nor spelling. This tests the same channel as the recent English/Latin experiments; it does not establish that Voynich uses it. Do not revive the older character/homophone SMT German experiments as if they were equivalent controls.

Success is measured first by precision and coverage of frequent-word mappings, then grammatical plausibility, with literal recovery reported separately. Do not promise English's approximately 35% token accuracy. Latin demonstrated strong author dependence and misleading scoring/consensus signals.

## 2. Resource selection and feasibility audit

Preferred primary resource: **Referenzkorpus Frühneuhochdeutsch (ReF)**. Its project covers 1350–1650 and provides lemma, POS and morphology annotations. The access page advertises downloads and CC BY-SA 4.0 licensing. Verify the exact release, export format, component coverage and release-specific terms when downloading; a web-search description is not an acquired, verified dataset. Direct retrieval of some project pages failed during planning.

Secondary possibilities:

| Resource | Intended role | Constraint |
|---|---|---|
| ReF | Primary historical corpus and evaluation annotations | Confirm actual token counts, complete-text availability, annotation layers and download access. |
| Bonner Frühneuhochdeutschkorpus (FnhdC) | Optional additional historical material or separate diagnostic | Its 40 sources are excerpts across four time slices, including 1650–1700. Terms restrict redistribution and specify scholarly/noncommercial use and attribution/publication obligations. Do not assume an open redistribution license. |
| Deutsches Textarchiv (DTA) | Optional later-language contrast or a date-filtered supplement | Broadly 1600–1900: most of it is not the intended period. Any supplement must have an explicit historical range and remain a separate ablation. |
| Existing cached German streams | Parser regression fixtures and small diagnostics | Audit regional parsing, edition, dates and source overlap. Prior solver compatibility is not evidence of linguistic recovery. |

First deliverable: source census with author/work/edition/witness identifiers, dates, regions, genres, raw/usable token counts, longest continuous streams, annotation availability, licenses, export hashes and duplicates. Preserve notices. Do not export restricted raw passages through reports or commit them as freely redistributable data.

Do not promise a million-word corpus or Voynich-length targets before this census. Prefer the largest diverse, reliable in-period corpus over indiscriminate volume. If only short excerpts are available, report an excerpt benchmark and explicitly defer the long-text milestone. Never concatenate unrelated excerpts into a supposedly continuous manuscript.

Sources checked during planning:

- [ReF project overview and annotation scope](https://www.linguistics.rub.de/comphist/projects/ref/)
- [ReF access and license](https://www.linguistics.rub.de/ref/access/index.html)
- [ReF corpus search, identifying the 1350–1650 scope](https://www.linguistics.rub.de/ref/access/search.html)
- [FnhdC composition, downloads and use terms](https://www.korpora.org/FnhdC/)
- [BBAW historical corpus overview, including DTA](https://clarin.bbaw.de/en/corpus/)

## 3. Text representation: preserve the actual challenge

Implement a historical-German adapter rather than reusing Latin's ASCII-only tokenizer and j/i, v/u rules.

Maintain aligned layers where the source provides them:

1. Original transcription, retaining provenance and editorial distinctions.
2. Declared surface tokens for the encrypted benchmark, with conservative Unicode handling.
3. Optional normalized-spelling, lemma, POS and morphological annotations, separately tagged as source annotations or private evaluation labels.

Inventory the actual script conventions before freezing normalization. Explicitly decide treatment of long s, combining marks, umlaut notation, capitalization, abbreviations, punctuation, hyphenated line breaks, editorial expansions and compounds. Avoid blanket diacritic removal or splitting compounds. Resolve TEI choices without duplicating both original and regularized readings. Preserve gaps as barriers rather than joining unrelated word sequences. Do not treat every printed line as a sentence or document.

The main track encrypts historical surface tokens. Different spellings remain distinct types unless a declared mechanical policy merges them. The decoder never sees the original spellings, so it cannot normalize cipher tokens by their letters.

A separately labeled normalized-before-encryption track may diagnose how much spelling variation hurts. It is an easier, different benchmark, not an improvement in restoration of the historical cipher.

In the main track, source-derived variant relationships can share statistical evidence across candidate plaintext spellings. Surface assignments remain injective; multiple historical spellings may project to the same normalized word or lemma for evaluation. Do not impose a one-to-one lemma dictionary, and do not use private target normalization to construct inference candidates.

## 4. Splits and fixture design

Freeze split manifests before search. Hold out authors and works, group related editions/manuscripts/translations, and audit exact and normalized near-duplicates across corpora. Shared biblical or formulaic passages need an explicit overlap report; different author labels alone do not establish independence.

Provisional allocation, subject to corpus size:

- Diverse training set spanning available regions, time slices and genres.
- Three development works, covering more than one regional/genre group.
- Two validation works for frozen method comparison and any confidence fitting/confirmation split.
- At least two sealed confirmation works, never opened for recovery until selection is frozen.

Record region/date/genre mismatch as an evaluation condition. Primary inference uses the pooled source model. A matched-region model is permitted only as a clearly labeled assisted diagnostic, not the headline result.

Prepare a 2,000–5,000-token pilot and contiguous long fixtures targeting roughly 20,000–40,000 tokens where genuine source continuity permits. Report real lengths. Use fresh substitution keys per fixture; several relabelings of one passage do not count as independent linguistic tests.

Public inputs contain only opaque token streams and allowed document barriers. Private evaluation contains plaintext, annotations, source identity and hidden boundaries. Make private fixture files unavailable during inference, as in the Latin experiments.

## 5. Dictionary and scalable baseline

Build a disk-indexed historical surface inventory from training and independently acquired generic resources. Do not add hidden target words to fix coverage. Start with observed training forms; expand through verified historical lexica or source-learned spelling/morphology rules only as a separately measured step. Avoid enumerating speculative forms merely to reach an arbitrary dictionary size.

Report inventory size, attested/unattested proportions, memory, candidate support and exact/normalized/lemma coverage ceilings. A missing surface form limits literal recovery but does not necessarily preclude its normalized equivalent. Candidate support must be audited separately from final assignments.

Reuse existing public/private fixtures, sparse bigram model, indexed retrieval, injective dictionary search, traces, checkpointing, independent full rescoring, consensus extraction and inspection reports. Begin with the original surface bigram objective and unchanged retrieval/search settings, not a bundle of Latin modifications that failed confirmation. English/Latin confidence calibrators must not be transferred as calibrated German probabilities.

Keep all language policy in adapters and metadata. Preserve existing English/Latin resource hashes and behavior with targeted regression checks.

## 6. Experiment ladder

### A. Resource/parser milestone

Acquire the selected release, validate extraction against representative source displays, freeze corpus/normalization/splits, and train the baseline. Produce coverage and vocabulary-growth curves before long search.

Tests should catch real hazards: duplicated TEI readings, lost diacritics, abbreviation expansion, gap joining, cross-document counts and accidental access to evaluation annotations.

### B. Baseline pilot

Run matched random and frequency initializations, three seeds per condition. A 4,000-proposal pilot is permitted as a preliminary resource check; the main replication uses the English benchmark's **8,000 proposals per seed**, seeds 3/5/7 and mixed scheduler, with the other numerical settings copied from its saved protocol. Record their different starting-key diversity. The earlier 200-iteration setting belongs to a different experiment configuration; do not substitute it for proposal counts here.

Before interpreting recovery, compare intact or feasible references, partial dictionary corruptions, frequency keys, null keys and actual optimized wrong outputs. Report both covered and unsupported-word behavior. A favorable intact-reference comparison alone does not validate the objective.

### C. Long, excluded-author baseline

If resource continuity and runtime permit, run at least two development long passages with identical settings, targeting the English setup's continuous 35,000-token length and 8,000 proposals per seed. Match algorithms and numerical settings rather than artificially making the historical inventory or corpus the same size as English. Record vocabulary/training-size differences as comparison limits. Audit frequent-word candidate availability and whether correct assignments are rejected, displaced or never offered. This determines whether to improve coverage, retrieval, scoring or search rather than guessing from total accuracy.

### D. Optional follow-up after completing the English-method replication

Candidate order:

1. **Source spelling-variant evidence sharing:** smooth across independently learned historical variants while retaining surface identity. Priority only if spelling fragmentation or coverage is demonstrably important.
2. **Short grammatical context:** trigram or source-trained POS/morphological factors, compared with the unchanged baseline. German annotation must support the proposed representation; Latin's failures are a warning against assuming a factor model will work.
3. **Hard-negative reconstruction scoring:** train across multiple authors on optimized wrong dictionaries versus partially correct dictionaries. Require partial-recovery ranking, not merely intact-text recognition. Keep scorer discrimination separate from actual decipherment results.
4. **Broader search/proposals:** only where traces demonstrate search/candidate barriers. More Latin iterations alone produced little benefit.

These are conditional branches, not an authorization to implement all of them in one batch. Freeze any selected variant before validation and sealed confirmation. If performance is negative, preserve the result rather than adding target-specific hints.

## 7. Evaluation and decisions

For every work, report:

- Exact surface token/type accuracy and normalized/lemma accuracy where independently annotated; expose ambiguity rather than selecting whichever lemma makes a guess correct.
- Correct/incorrect top-10, top-20 and top-50 frequent-word mappings, both frequency-first and consensus-first under frozen ranking rules.
- Precision and token coverage for selected anchors. Retain the existing unanimous-three-run/count-at-least-100 diagnostic, noting its length dependence and shared-initialization bias. Unanimity is not a probability.
- Structural-word categories, source-derived POS compatibility, and a fixed paragraph plus fixed-position excerpts. Broad POS agreement is weak evidence and must be compared with frequency-matched wrong controls; it does not establish meaning.
- Mean across seeds and source-score-selected recovery separately, all failed/time-limited chains, elapsed time, actual proposals, peak memory, inventory coverage and candidate-support traces.

A provisional useful-nucleus milestone is at least 20 distinct selected types with measured precision at least 80% on each of two excluded-author works, alongside token coverage and uncertainty. This is a benchmark target, not a calibration guarantee; repeated words and authors are dependent. A trustworthy 50-word claim requires evaluating all 50 rather than padding a tiny correct set. Freeze thresholds on development/calibration data, not final targets.

Promote a change only after matched validation shows useful anchor/coverage gains without a material precision regression and sealed works confirm the direction. A single favorable text or seed is insufficient. Failure to reach the milestone is still a valid completed benchmark, not a reason to keep tuning against sealed targets.

## 8. Implementation batches and compute

Proposed files:

- `src/voynich_smt/word_mapping/scalable/historical_german.py`: extraction/normalization adapter.
- `benchmarks/scalable_fruehneuhochdeutsch.py`: census, build, pilot, validation, confirmation and report stages.
- `experiments/results/scalable-fruehneuhochdeutsch/v1/`: exclusive versioned manifests, public/private fixtures, models and results.
- `docs/scalable_fruehneuhochdeutsch.md`: findings, excerpts where permitted, limitations and reproducible commands.

First implementation batch: resource census, adapter, split manifest and small verified fixture. Second: baseline resources and pilot. Third: long baseline and error audit. Only then select an improvement branch. Keep each batch independently reviewable and preserve all earlier outputs.

Runtime settings remain configurable. Budget roughly one to three hours for an initial experimental bundle if the measured pilot supports it; this is a planning envelope, not a hardcoded timeout or wall-time promise. Estimate costs after the census and pilot. Checkpoint per chain, use matched proposal caps where feasible, and explicitly label comparisons stopped by time limits. Do not start a multi-hour run as part of this planning task.

## 9. Open decisions

- Scope confirmed by the user: repeat the English algorithm and overall experimental setup. No algorithm-improvement branch is part of the initial implementation milestone.
- Default period scope follows ReF, 1350–1650. No specific region or genre is assumed; use a pooled primary model and describe diversity in the census.
- Long-stream availability, exact release/export format and admissible resource licenses remain facts to establish in the first implementation batch.

## First implementation completed

See [resource census and pilot report](../scalable_fruehneuhochdeutsch.md). ReF v1.0.2 is acquired/checksummed; the Unicode surface adapter, author/work splits, source-only model/inventory, six-chain 4,000-word pilot, anchor reports and objective diagnostics are complete. Mean literal recovery is 13.59% random / 13.06% frequency. All 163 relevant tests pass; English/Latin resource identities remain unchanged.

The corpus cannot supply a 35,000-word continuous target under the conservative adapter: the longest retained prose stretch is 8,484 words. The original long-text replication is therefore **pending an additional suitable source**, not completed by concatenating excerpts. Validation and sealed recovery remain unrun. The model also still favors optimized wrong dictionaries over proxy-completed near-correct controls. No algorithm variants are promoted from this pilot.

## Long-text validation completed

[The follow-up report](../scalable_fruehneuhochdeutsch_long.md) completes the full 8,484-word Hartlieb test, two other excluded-author ReF passages, a continuous 35,000-word Arndt prefix and a 31,260-word Abelin confirmation. Thirty chains complete 8,000 proposals each with the original English algorithm. Long-text random-start mean literal recovery is 14.07% and 13.01%; frequent unanimous cores contain three correct/one wrong type and two correct/two selected types respectively. A substantial reliable nucleus is not established.

Source-only overlap cleanup and unchanged dictionaries are recorded; target vocabulary is never added. A separate, explicitly post-hoc source-analysis lemma diagnostic credits some spelling/inflection variants, but does not establish grammar or meaning. All 167 relevant tests pass. F019, F283, F001 and F161 remain unrun for recovery. The missing-length test is completed; quality/confidence work remains before trusted Voynich restoration.
