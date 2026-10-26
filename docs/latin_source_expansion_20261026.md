# Latin source expansion — 2026-10-26

Collected four additional POS/morphology-annotated Universal Dependencies treebanks, pinned to **r2.17** to match the existing PROIEL/Perseus baseline. Downloads add **773,380 integer token rows in39,387 sentences**; all six local treebanks total **1,008,167 rows**. This is a collection/provenance milestone, not a new restoration result: no new model, anonymous graph, feature projection or evaluation has run on these sources.

## What was added

| Treebank | Main material | Integer token rows | Sentence-level admission |
|---|---|---:|---|
| ITTB | Aquinas, *Summa contra gentiles* I–IV; mixed-author concordances | 450,517 | Aquinas375,028 development; mixed75,489 quarantined |
| UDante | Dante's Latin works and related/disputed works | 55,553 | Secure/attributed43,495 reserved; mixed/disputed12,058 quarantined |
| CIRCSE | Seneca's three tragedies; Tacitus, *Germania* | 24,899 | Seneca19,225 reserved; Tacitus5,674 development |
| LLCT | Late Latin legal charters, multiple/anonymous scribes | 242,411 | Supplemental development genre; not one named author |

Counts are **syntactic integer-ID rows, including punctuation and split clitics**, not normalized model-word counts; they need not equal README counts from another release or tokenizer. Tacitus is still a short source, so this collection does not imply four equally long texts. The main identifiable author groups are Aquinas, Dante, Seneca and Tacitus; mixed authorship and charters are not inflated into named independent authors.

Prior answer clarification: the recent model experiments used one author (Cicero), with older related experiments involving at least nine authors. The local annotated-data availability inventory is broader: **13 named author/translation groups were already cached** across PROIEL/Perseus, now16 main named groups after adding Aquinas, Dante and Seneca; Tacitus was already available in a shorter/different work. Availability does not mean those authors trained or validated the current applicability model.

## Fixed data roles

The complete new sentence registry partitions into:

| Role | Sentences | Integer token rows |
|---|---:|---:|
| Development: Aquinas SCG + Tacitus Germania | 23,986 | 380,702 |
| Supplemental development: anonymous/multiple-scribe charters | 9,023 | 242,411 |
| Reserved evaluation: Seneca + secure/attributed Dante | 2,698 | 62,720 |
| Quarantined: mixed/disputed/uncertain | 3,680 | 87,547 |

Roles use author/work headers and documented source boundaries, not case/POS outcomes. Upstream `train/dev/test` filenames do **not** determine these roles: all Seneca annotations and designated Dante annotations remain reserved, including upstream training files. No reserved token labels, FORM/text features, POS/case distributions, predictions or metrics were inspected or projected; only row shape, token IDs, sentence IDs and attribution headers were inventoried. Acquisition necessarily downloads the complete annotated bytes, but does not decode them into evaluation labels.

ITTB train13520–16809 contains the mixed-author *forma* concordances and is quarantined. UDante's eclogues include Giovanni del Virgilio, *Questio* has disputed attribution and letterXIII is disputed; these are quarantined instead of silently counted as Dante. Secure *Monarchia* and *De vulgari eloquentia*, plus the other attributed letters, are reserved. Authorship uncertainty remains visible for the letters.

Reserved means **new-annotation/current-model evaluation embargo**, not globally unseen plaintext. Aquinas, Dante and Tacitus appear in older project experiments/raw resources; no claim is made that a broad historical Latin-library crawl never contained Seneca. Current applicability models trained only on Cicero. Existing200-sentence grammar reservations and sealed Ammianus/Quintilian raw works remain unchanged and unprojected.

## Version and licensing provenance

Every upstream file is pinned to an immutable commit, checked against GitHub's blob SHA-1 and independently hashed with SHA-256. Exact source URLs, sizes, tags and commits are recorded, with original README/license files preserved next to the raw data.

| Treebank | r2.17 commit | License declarations |
|---|---|---|
| ITTB | `9d01db4e4d9b194ab1421a0a6fd4fa5b052c640f` | CC BY-NC-SA3.0 |
| UDante | `06fbba3dcab84c0b577bc61e3696e3238141360d` | **Conflict:** README/UD metadata say CC BY-NC-SA3.0; pinned LICENSE.txt says CC BY-SA4.0 |
| CIRCSE | `13745972cb788304702f47afa8cf8d4619229408` | CC BY-SA4.0 |
| LLCT | `df63d06c5a7788b457f50bf37526146e9225c27d` | CC BY-SA4.0 |

The UDante discrepancy is preserved in `license-reconciliation.json`; the collector's initial expected-license field is metadata, not a resolution of that conflict. Both declarations remain available, no relicensing claim is made, and UDante remains reserved with the unresolved flag. Do not infer broader redistribution rights from the more permissive declaration alone. No upstream contact or publication was performed.

Official descriptions/provenance: [ITTB](https://universaldependencies.org/treebanks/la_ittb/), [UDante](https://universaldependencies.org/treebanks/la_udante/), [CIRCSE](https://universaldependencies.org/treebanks/la_circse/), [LLCT](https://universaldependencies.org/treebanks/la_llct/). Release-specific details are in the pinned READMEs rather than current master; current CIRCSE includes additional material not present in this snapshot.

## Legacy metadata issue discovered

The new inventory uses corrected Perseus identifiers: `phi1221.phi007` is Augustus' *Res Gestae*, and `phi0972.phi001` is Petronius' *Satyricon*, as confirmed by the [Perseus Augustus catalog](https://catalog.perseus.tufts.edu/catalog/urn:cts:latinLit:phi1221.phi007) and [Petronius catalog](https://catalog.perseus.tufts.edu/catalog/urn:cts:latinLit:phi0972.phi001).

An older registry in `benchmarks/scalable_latin_caesar.py` labels the former Petronius, and `benchmarks/grammar_structure_iteration3.py` labels the latter Gellius. Frozen historical code/results were not rewritten during collection. Their author-level provenance needs a separate impact audit before reuse; this does not by itself invalidate current Cicero-only applicability fits or independently sourced raw Gellius texts. The corrected inventory does not silently repair prior experimental claims.

## Reproducible handoff

Raw additions: `data/latin-grammar-benchmark/{ittb,udante,circse,llct}-r2.17/` (20 upstream files, including12 CoNLL-U files and8 README/license files). The collection manifest directory is `experiments/datasets/latin-grammar-expansion/v1/`:

- `catalog-freeze.json`, `inventory-design.json`: frozen acquisition/role policies.
- `downloads.json`, per-treebank provenance: exact commit/URL/byte/hash records.
- `sentence-registry.json`, `work-inventory.json`, `file-inventory.json`, `totals.json`: structural metadata and counts.
- `development-sentences.json`, `supplemental_development-sentences.json`, `reserved_evaluation-sentences.json`, `quarantine-sentences.json`: explicit file/sentence allowlists.
- `license-reconciliation.json`, `audit.json`, `verification-manifest.json`: metadata caveat, independent validation and integrity.

Future training must use role allowlists rather than globbing upstream `*-train.conllu` files. Existing PROIEL/Perseus are inventory-only here: their original author/sentence reservations take precedence over any new development plan. No runtime loader or old experiment silently changes its inputs.

Before the first new model run, freeze author/work-balanced training budgets, normalization/MWT/enclitic handling, cross-treebank annotation interpretation and label-blind duplicate checks. Exact normalized text overlap across collections has **not** been tested: reserved FORM streams remain unprojected until a dedicated frozen admission/evaluation protocol permits that check. Do not declare a clean independent transfer split merely from these metadata roles. Keep reserved labels out of model/threshold selection and do not move a reserve author into training after seeing a result.

## Verification

Independent byte/structural/header replay verified20 downloaded upstream files and4 license files,17 CoNLL-U files including the two existing treebanks, all39,387 new sentence-role records, disjoint author roles, quarantines and totals. All Git blob/SHA-256 checks passed, the UDante conflict was explicitly flagged, and the old grammar reserve metadata matches its iteration166 frozen hash. No token label fields/text comments were analyzed and no models/predictions ran. The broader test suite was not rerun for this data acquisition; dedicated independent audit passed.

Code: `benchmarks/collect_latin_grammar_expansion.py`, `benchmarks/inventory_latin_grammar_expansion.py`, `benchmarks/review_latin_grammar_expansion.py`.
