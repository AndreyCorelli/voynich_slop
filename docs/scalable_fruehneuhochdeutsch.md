# Frühneuhochdeutsch: resources and first English-algorithm pilot

**Follow-up completed:** see [long-text and excluded-author validation](scalable_fruehneuhochdeutsch_long.md). It includes the continuous 35,000-word test; the pending milestone described below is historical to this first pilot.

The first historical-German pilot is complete. On a 4,000-word excluded-author passage, the unchanged English bigram/search algorithm recovers **13.59% of tokens on average from random starts** and **13.06% from frequency starts**. A small frequent-word core is correct, but unanimous errors persist. This is not yet the planned continuous 35,000-word replication.

## Resources and independence

Downloaded **ReF v1.0.2**, pinned Zenodo record **5793616**. Its 143,463,482-byte archive matches the published MD5 `65673554d1edd6ea1299d8a185cfd48e`; SHA-256 and source/export metadata are retained locally. Archive `LICENSE` and `README.md` specify **CC BY-SA 4.0**, consistent with the project website. Repository API metadata instead says CC BY 4.0: that discrepancy is recorded, and the archive's BY-SA notice is retained with derived resources.

Citation: Wegera, Klaus-Peter; Solms, Hans-Joachim; Demske, Ulrike; Dipper, Stefanie (2021). *Referenzkorpus Frühneuhochdeutsch (1350–1650)*, Version 1.0. This experiment uses archive v1.0.2.

- [Pinned corpus release](https://zenodo.org/records/5793616)
- [Project access and licensing](https://www.linguistics.rub.de/ref/access/index.html)

The census admits 190 CorA-XML sources (ReF.RUB/MLU), with 3,113,482 retained surface tokens before held-out exclusions. ReF.UP TIGER representations are not added: they overlap sources and use a different representation.

Seven works/authors are reserved, selected from longest explicitly genre-P sources with identifiable authors before any recovery results:

| Role | Sources |
|---|---|
| Development | F137, Johannes Hartlieb; F332, Johann von Gelnhausen; F064, Rulmann Merswin |
| Validation, no recovery runs yet | F019, Guilelmus Durandus; F283, Nikolaus Wurm |
| Sealed for recovery | F001, Konrad Megenberg; F161, Otto von Passau |

Source-author name fragments exclude associated works. Unknown or inconsistent attribution remains a limitation. Each training segment is screened against every reserved work for shared exact 12-word windows; no additional segments were rejected for this overlap condition in this release. Exact duplicate training segments are removed (442 exclusions); one-token segments are omitted. This does not prove independence from spelling variants, paraphrases or unidentified related works.

Frozen training resources contain **2,956,502 tokens**, **30,292 segments**, **183 works**, **245,420 surface forms**, and **1,598,191 observed bigram edges**. The inventory contains admitted training forms only; there is no external historical dictionary yet. Held-out forms are never added to improve coverage.

## Historical spelling and continuity

The adapter uses **CorA `tok_anno` UTF surfaces and source word segmentation**, not lemma spellings or the ASCII layer. It lowercases, applies NFC, folds long s to s, and removes zero-width joiners. It preserves u/v, i/j, umlauts, combining superscripts and abbreviation marks. Exact accuracy therefore means accuracy under this declared surface contract, not facsimile-level transcription recovery.

Supported punctuation-only tokens are discarded. Unsupported/unclear lexical notation, digits and ambiguous bracket/asterisk/question notation create conservative barriers; numeric page jumps/backtracking also split excerpts. These decisions lose usable context in places. Unmarked excerpt joins may still escape detection. Titles and foreign-language spans remain; no topic/target language filtering is applied.

After these rules, the longest retained segment is **13,056 tokens**, and the longest explicitly genre-P prose segment is **8,484 tokens**. Even the largest raw CorA source has fewer than 35,000 annotation tokens. No excerpts were concatenated or repeated to manufacture the English target length. A genuinely long benchmark requires another suitable source or a separately justified representation revision.

## Pilot design

Target: first 4,000 tokens of the longest retained F137 segment, Hartlieb's *Buch aller verbotenen Künste*, manuscript dated 1465. Choosing this position by retained length favors an easy-to-parse stretch; it is not a random representative historical passage.

- 4,000 tokens, 1,060 cipher types, opaque injective whole-word substitution, seed 83.
- 849 types present in the independent inventory; 211 absent types account for 307 tokens.
- Inventory token recovery ceiling: **92.325%**. All inventory words are source-attested.
- No topic, title, author, vocabulary, sentence boundaries or source annotations enter search.
- Six chains: random/frequency starts × seeds 3/5/7; **4,000 proposals each**.
- Numerical search/retrieval settings copied from the saved English independent-work protocol: sparse bigram objective, mixed scheduler, default temperatures and candidate settings, 400-second per-chain budget and 10-second reserve. Only the proposal cap is reduced from the main English 8,000 to the predeclared pilot 4,000. Historical-language contracts differ as required.
- Private evaluation files are moved away from their normal path during each real inference bundle and restored afterward. Public confidence features are saved before truth evaluation; no fitted English/Latin confidence model is transferred.

English used a 35,000-word target, 298,475 training tokens, and an independently sourced/training-union inventory of 126,896 forms. Different lengths, corpus composition and dictionary policies prevent interpreting the percentage difference as a language-only effect.

## Results

| Initialization | Seed 3 | Seed 5 | Seed 7 | Mean | Source-score-selected |
|---|---:|---:|---:|---:|---:|
| Random | 13.225% | 15.125% | 12.425% | **13.592%** | 13.225% |
| Frequency | 12.525% | 13.000% | 13.650% | **13.058%** | 13.000% |

Frequency initialization starts at 9.75% before search. Its three chains share that initial dictionary; they are not independent initial guesses.

Under unanimous-three-run agreement and at least 100 public occurrences:

| Starts | Correct types / selected types | Correct token coverage | Mappings |
|---|---:|---:|---|
| Random | 1/1 | 5.15% | `vnd` correct, 206 occurrences |
| Frequency | 2/4 | 8.35% | `vnd` and `der` correct; `die → das` and `das → die` wrong |

Agreement-first top-50 type predictions contain 5 correct mappings for each initializer. Frequency-first top-50 contains 10 for random starts and 6 for frequency starts. These lists use one most-voted prediction per cipher type; they differ from historical reports that padded lists with alternative single-vote candidates. They are not calibrated 50-word dictionaries. A one-type correct anchor set does not establish general high precision.

Six chains completed all **24,000 proposals**. Search wall times sum to **202.17 seconds**, excluding acquisition, parsing, resource loading and evaluation. Peak shared-process RSS reached approximately **1.46 GB**; this is not an isolated decoder-only measurement. Every saved current/archive key and initial score passes the existing independent full-score evaluator.

Fixed-position original/restored excerpts are retained at offsets 0, 1000 and 2000 for each initializer. Grammatical and semantic recovery are **not measured**. Examples show occasional structural words amid mostly wrong lexical assignments, not recovered meaning.

## Objective diagnostic

After inference, feasible reference controls decode all covered words correctly and assign distinct observed proxy words to unavailable types. They are **92.325%-correct token references**, not full correct plaintext keys or solver outputs.

Both proxy schemes score below all six optimized wrong outputs:

- Rare observed proxies: **−32,252.48**.
- Common observed proxies: **−29,898.30**.
- Optimized outputs: **−25,626.24 to −23,152.49** (higher is better).

The rare-proxy reference beats all sampled corrupted/random controls, yet the searched wrong dictionaries beat it. This repeats a Latin warning: scoring simple controls well is insufficient. Proxy words affect contextual scores, and coverage/corpus mismatch remain confounded; the diagnostic does not isolate a single cause or prove the fully correct unavailable dictionary would be disfavored. An all-unobserved null control is unavailable in this training-only inventory.

## Implementation, validation and next milestone

New adapter: `src/voynich_smt/word_mapping/scalable/historical_german.py`.
Driver: `benchmarks/scalable_fruehneuhochdeutsch.py`.
Artifacts: `experiments/results/scalable-fruehneuhochdeutsch/v1/`.

Unicode support is an explicit optional inventory/fixture/model contract. English/Latin defaults remain unchanged; their frozen inventory and model identities still verify. The generic evaluator now labels historical-German limitations correctly. **163 relevant tests pass**, including genuine Unicode search/serialization/full-rescoring integration and tests for diplomatic-versus-lemma isolation, combining marks, gaps and excerpt page jumps.

Completed: source census, surface adapter, frozen splits, source-only baseline resources, verified pilot fixture, six matched pilot chains, anchors, excerpts and objective controls. Validation/sealed recovery has not started; no algorithm improvement or reliable-nucleus claim is made.

Next milestone: acquire an independent, genuinely continuous in-period prose source for the **35,000-token / 8,000-proposal English-method replication**. If that is unavailable, report a separately labeled shorter baseline rather than silently changing the target. An external historical lexicon is also a resource difference to resolve or explicitly retain in the comparison. Do not introduce spelling models or Latin scorer variants before establishing that baseline.

Reproduce in a fresh versioned directory (existing outputs are preserved):

```
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch census
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch build
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch pilot
.venv/bin/python -m benchmarks.scalable_fruehneuhochdeutsch diagnose
```

`pilot --budget-seconds N` overrides the per-chain search allowance. The archive acquisition URL/checksums are recorded in `data/raw/scalable-fruehneuhochdeutsch/download.json`; it is not downloaded implicitly by the benchmark driver. The current driver targets the version constant `ROOT`; choose a new version before an intentional rerun.
