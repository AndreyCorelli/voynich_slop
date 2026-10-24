# Larger-corpus, morphology-backed Latin decipherment

Status: implemented through the development objective gate, 2026-10-15.
See the [results report](../scalable_latin_corpus_morphology.md). The cleaned
5.94M-token corpus and all tested factor mixtures fail the promotion gate, so
full decoding/validation/sealed-test stages are intentionally stopped. Numerical
and public-only smoke tests pass; no improved recovery is claimed.

Subsequent objective investigation is recorded in the
[ordering-contrast report](../scalable_latin_shuffle_contrast.md): frequency bias
is isolated and the reference gate repaired, but three-seed validation does not
show a robust recovery improvement. Experimental code is retained; defaults
remain unchanged and sealed-test recovery is unrun. All 154 relevant tests pass.

## Objective and constraints

Improve recovery of frequent, useful Latin word mappings under the existing
synthetic injective whole-word substitution channel. Compare exact recovery,
lemma recovery and grammatical information separately. English's approximately
35% token accuracy is a research target, not a forecast or a directly matched
Latin baseline. The ultimate motivation remains a Voynich-to-Latin attempt;
success here would establish usefulness only for the tested channel.

Use generic Latin resources, not target topic, guessed translations, target
vocabulary, original sentence boundaries or manually selected anchor words.
Training annotations are allowed; evaluation annotations never enter inference.
Cipher symbols have no readable Latin morphology. All inflectional information
belongs to candidate plaintext forms, not to their opaque cipher spellings.

Preserve historical experiments and defaults. All new resources and runs use
versioned, exclusive output directories. Do not deploy a model on Voynich as
part of this milestone.

## Working hypotheses

1. The original 169,100 training tokens provide inadequate surface-word coverage.
2. Separate counts for inflected forms waste evidence about common lemmas and
   grammatical constructions.
3. Adjacent-word scoring alone may remain insufficient even after those fixes.

The first two hypotheses are this implementation's scope. Long-distance syntax,
neural decipherment training, and latent sentence segmentation are later stages,
not prerequisites quietly added to this project.

## Phase 0: freeze protocol and evaluation split

Create a design manifest before resource selection or model tuning:

- Keep the existing Caesar stream, old resources and saved outputs as historical
  comparisons. Caesar is repeatedly inspected development evidence, not blind.
- Select development, validation and sealed test works by author/work metadata,
  before recovery results. Prefer at least three development/validation authors
  and three distinct sealed-test authors with sufficiently long continuous prose.
  If available data cannot support that, report the smaller design explicitly.
- Use complete works or position-selected contiguous passages up to 20k–35k
  tokens. Do not concatenate unrelated excerpts to simulate a continuous work,
  repeat short texts, or select passages for dictionary coverage.
- Exclude all works by evaluation authors from training, including the annotated
  training pool and alternative editions/translations of those Latin works.
  Existing short calibration works are already inspected, not new sealed tests.
- Freeze spelling/tokenization, attached-enclitic policy and punctuation removal.
  Keep the current lowercase, diacritic removal, j/i and v/u normalization unless
  an independently documented source incompatibility requires a new protocol.
- Keep private truth, annotations and held-out raw text inaccessible to inference.
  Preparation/overlap auditing are separate evaluation-side operations.
- Record source commits, licenses, raw hashes, work/author IDs, parser versions,
  exclusions, duplicate groups and every train/development/test assignment.

No held-out plaintext is used to fit smoothing, weights, analysis probabilities,
vocabulary, retrieval budgets or confidence rules. Development truth can evaluate
and select predeclared variants; sealed test is opened once after selection.

## Phase 1: acquire and normalize a larger corpus

First inspect cached sources, then acquire pinned, attributable resources. Initial
candidates are CLTK's Latin Library collection and Perseus canonical Latin texts;
audit actual file-level terms and metadata before choosing them. Collection
membership or a software MIT license does not establish every text's license.
Do not promise 20M usable tokens until the cleaned source census exists.

Prefer continuous edited texts over OCR initially. Remove editorial matter,
translations, apparatus, headings, duplicated editions and quoted test material
where identifiable. Reject or quarantine unknown authors/work IDs rather than
silently assigning independence. Preserve genuine document boundaries; never
count a transition between unrelated works.

Deduplicate normalized documents and overlapping passages across collections;
detect near duplicates with shingles and verify suspicious matches. Run exact
12-token held-out overlap audits as an additional contamination screen, not a
proof of independence. Long matching passages trigger exclusion/review; report
short conventional phrase overlap rather than selectively deleting test phrases
to improve outcomes. Store all decisions in a reproducible manifest.

Build deterministic, source-balanced nested samples near 1M, 5M and 20M tokens,
subject to available clean data. Use whole works and report actual sizes; cap
individual author domination by a declared generic policy. Keep source strata
represented without tuning the mixture to Caesar or another target. Reuse the
same nested samples in surface and morphological models.

### Resource and performance acceptance

Run a 100k-token pilot, measure unique forms/edges, analyzer throughput, load time,
RSS and disk usage, then extrapolate to the real census. Three hours is an initial
planning envelope, not a hardcoded timeout or a promised completion time. Corpus
acquisition, morphology preparation, model fitting and decoding are separately
timed. Checkpoint long preparation steps and allow resumable larger builds.

Stream tokenization and aggregate sorted count shards on disk. The current
SparseBigram keeps Python edge dictionaries and creates large identity payloads;
profile these before scaling. If needed add an opt-in compact sorted-array/CSR
edge store, streaming identity hashing and bounded caches. Keep double-precision
scores and 64-bit counts. Do not assume O(E) Python objects will fit simply because
the training token count sounds modest.

Deliverable: corpus manifest, normalized work streams, nested sample manifests,
quality/exclusion report and resource-cost projection.

## Phase 2: shared vocabulary and morphology catalog

For the primary matched comparison, build one inventory from the entire pinned
default generated lexicon union all admitted training surface forms. Freeze it
before model fits, and share it across corpus sizes and model families. Thus
adding data changes learned evidence, not eligibility. Report its difference
from the original 2,557,237-form inventory; historical comparisons are not pure
fixed-inventory ablations. Do not add held-out forms or hard-prune rare forms.

Reuse `word_mapping/morphology.py` and pinned Whitaker commit
`92eb56f188ec9dadecca01ca34d3c9fd13d746da`. Preserve all compatible lemma, POS,
case/number/gender, verb-feature and enclitic analyses; normalize duplicate
analyses. Resource IDs are lemma identities, not reconstructed dictionary labels.

Avoid running the parser independently over millions of generated forms.
Extend independent enumeration to emit compact form-to-analysis links alongside
forms, verify them against the analyzer on a fixed sample, and lazily analyze/cache
training-only forms absent from generated output. If enumeration cannot faithfully
preserve analyzer semantics, retain a checkpointed batched analyzer path and
report its cost instead. Do not invent analyses to fill missing records.

Use a compact relational/array catalog, reverse lemma/feature indexes and explicit
unsupported-analysis paths. Generic unknown features back off; unrelated unknown
words must not share one fake lexical identity. Known PACK-table failures and
upstream filtering/pronoun limitations remain visible in reports. Never silently
reinterpret missing analysis as evidence of ungrammaticality.

Deliverable: versioned morphology catalog with ambiguity counts, throughput,
coverage on training, index sizes, hashes and resource limitations.

## Phase 3: normalized morphology-backed model

Start with a local factorized conditional model to retain exact sparse dictionary
updates. This first model shares evidence across inflections; it does not claim
to recover long-distance agreement or implement a complete Latin grammar.

For each surface form u, retain a normalized analysis distribution r(a|u), where
a contains lemma l and grammatical bundle g. Learn r from training data only.
For annotated training, map UD features and lemma strings to the pinned catalog
with an explicit tested crosswalk; unresolved mappings remain ambiguous or use
fallback. Treebanks have heterogeneous annotations, so do not simply equate tags.
Retain original analyses and record crosswalk failures. Never tag the cipher.

Fit analysis probabilities on annotated source examples where compatible, then
use bounded soft-count updates on unannotated training streams. Initialize
unresolved ambiguity with normalized weights, not duplicated token counts.
Stop iterations using held-out source-work likelihood, independently of test
recovery. Fractional counts per token must sum to one. No target adaptation in
this first experiment.

Construct two full-support conditional channels:

    P_lemma(v|u) = sum_a r(a|u) sum_l P(l|lemma(a)) P(v|l)
    P_grammar(v|u) = sum_a r(a|u) sum_g P(g|features(a)) P(v|g)

Emissions over surface forms and transitions over lemmas/bundles must each
normalize over their complete outcome spaces, with explicit EOS handling.
Smoothing/backoff provides support for unseen lemmas, bundles and unanalyzed
forms. Reserve unsupported mass explicitly, not one independently rewarded
unknown alternative per analysis. Ambiguous spellings cannot gain likelihood
merely by having more listed analyses. Generic full-support surface priors remain
available in all channels; no shortlist-local normalization is allowed.

Combine channels by an arithmetic probability mixture:

    P(v|u) = lambda_surface P_surface(v|u)
           + lambda_lemma P_lemma(v|u)
           + lambda_grammar P_grammar(v|u)

Weights are nonnegative and sum to one. Fit smoothing and a small predeclared
weight grid on independent development work, using likelihood plus recovery
diagnostics. Include the surface-only endpoint. Specify how lemma transitions,
grammatical bundles and emissions back off before fitting; if the above
factorization cannot be normalized efficiently, resolve it in tiny examples
before production code. BOS conditioning and EOS match the continuous-stream
protocol. Source sentences do not create privileged target boundary resets.

This construction intentionally integrates uncertainty locally. The same word
can receive different posterior analysis support beside different neighbors,
but there is no globally consistent latent grammatical analysis yet. A full
sequence latent-state model is a separately evaluated extension if this local
model passes gates but proves insufficient.

Deliverable: surface, lemma-only, grammar-only and combined model variants;
serialized parameters, data identities and independent exact-score reference.

## Phase 4: objective gates before full decipherment

First establish numerical correctness on tiny inventories: full conditional
normalization, positive support, exact marginalization, duplicated-analysis
invariance, feature crosswalk, unknown/no-unknown cases and serialization.

On independent development works compare a feasible nearly correct reference
with frequency keys, random injective keys, unobserved-form keys, 10/25/50-percent
corrupted references and token-shuffled streams. Missing true forms use explicit
distinct feasible proxies for diagnostics only; report their rate. Truth-based
keys never become search starts or candidates.

Require the reference to beat frequency/null controls and median corrupted-key
controls on at least two of three development works. Report every work and seed;
do not hide failures behind a pooled average. Record score trends across corruption
levels, particularly for frequent words. Token shuffling is a diagnostic, not an
assumption that every legitimate Latin order must outrank every shuffled sample.

If gates fail, stop decipherment for that variant and diagnose emissions,
frequency pressure, ambiguity, smoothing or mismatch. Gate failure rejects that
formulation, not Latin morphology generally. Passing gates establishes basic
discrimination, not recoverability or a guaranteed global optimum.

## Phase 5: sparse candidate retrieval and search

Keep the full injective surface dictionary and existing swaps/cycles/checkpoints.
Union existing surface proposals with lemma-neighbor and grammatical-bundle
proposals. Rank within lemma/bundle using fitted emissions and all occurrences
of a cipher type. A lemma match never forces every cipher type in that family to
the same surface word. Maintain positive full-inventory exploration probability.

Do not construct a cipher-types by million-forms matrix. Use sparse reverse
indexes and bounded caches. Exhaustive tiny tests compare retrieval with exact
scores. For larger catalogs, retrieval is explicitly approximate unless an exact
top-k bound is implemented; report recall on independent training-derived queries.
Do not reuse the old exact-retrieval claim for a new mixture without proof.

Exact local pair scores must update every affected occurrence, including displaced
owners. Checkpoints bind corpus, inventory, morphology catalog, model and search
configuration. Full rescoring independently validates saved keys and archive.

## Phase 6: controlled experiments and evaluation

Run the following on shared fixtures and the shared new inventory:

| Training size | Surface only | Surface + lemma | Surface + grammar | All channels |
|---|---|---|---|---|
| Original admitted source subset | yes | development ablation | development ablation | yes |
| Approximately 1M | yes | development ablation | development ablation | yes |
| Approximately 5M | yes | development ablation | development ablation | yes |
| Approximately 20M, if available | yes | selected scale | selected scale | yes |

Run gates and one smoke chain first. Promote only surviving variants. Use three
seeds and both random and frequency starts for primary selected comparisons;
report initialization separately. Start at the historical 4,000-proposal cap,
then give selected models matched configurable wall-time comparisons. Longer
model evaluation and wider retrieval make proposal-count equality alone unfair.
Do not exhaustively multiply all optional cells and seeds before screening.

Select corpus scale and mixture on development, verify on validation, then freeze
the complete method before sealed test. Caesar is a historical supplementary
comparison. An eventual unchanged-decoder English rerun is optional context,
not a prerequisite or a license to call unmatched percentages equivalent.

Primary outputs:

- Exact word-type precision at fixed top 10/20/50 lists, majority-only candidate
  pool size/correct count, and frequent-word precision versus token coverage.
- Whole-stream exact token accuracy and type accuracy with inventory ceilings.
- Lemma and grammatical-feature accuracy on independently annotated evaluation
  passages, separated from literal recovery. Do not count any shared possible
  analysis as gold grammatical recovery. Use contextual reference annotations;
  report feature-wise coverage, ambiguity, macro scores and frequent-class
  baselines. Separate exact-surface-induced grammatical correctness from
  grammatical information recovered when the surface is wrong.
- Fixed-position original/restored excerpts, alternative candidate mappings,
  seed variability, per-work results, runtime/RSS/disk and all failed variants.

Old confidence calibration is invalid after changing the model. Report raw
agreement without calling it a probability. Fit any new calibrator only after
freezing the decoder, on separate calibration works, and confirm independently.
Do not require 50 anchors if evidence supports only a smaller set. Semantic
recovery needs separate human evaluation; lemma overlap is not proof of meaning.

## Implementation sequence and reviewable deliverables

1. Add corpus manifests, exclusions, deduplication, normalized streams and pilot
   timing. Freeze held-out works before final training acquisition/build.
2. Build the enlarged fixed inventory and surface baselines; expose count/index
   memory limits before adding morphology. Preserve these as the data-only arm.
3. Add compact ambiguity-preserving morphology indexes and tested annotation
   crosswalk; save all unsupported cases and source-only priors.
4. Implement normalized lemma/grammar channels and mixture; verify tiny exact
   calculations, then run development objective gates.
5. Integrate sparse retrieval and exact delta scoring for survivors; smoke-test
   public-only inference, checkpoint continuation and full-score consistency.
6. Run screened corpus-size and channel ablations, freeze the selected model,
   evaluate sealed works, and publish original/restored passages and limitations.

Suggested new modules under `word_mapping/scalable/`: `latin_corpus.py`,
`morphology_index.py`, `factored_lm.py` and optional compact count storage.
Keep the existing public morphology annotator as the upstream adapter. Add
focused numerical and pipeline tests, not tests that merely copy implementation.
Use a new `benchmarks/scalable_latin_corpus_morphology.py` driver and versioned
`experiments/results/scalable-latin-corpus-morphology/v1/` artifacts.

The first implementation slice is phase 0–1 plus the 100k-token throughput pilot.
It ends with a concrete source census, held-out manifest, resource estimate and
executable corpus builder, not an expensive unreviewed training run. Continue
through subsequent slices when implementation is authorized; no recurring user
permission gate is implied by these technical checkpoints.

## Research/resource references

- Existing implementation and limitations: `../scalable_latin_caesar.md`,
  `../scalable_latin_classes_confidence.md`, `../latin_morphology_coverage.md`.
- CLTK Latin Library candidate collection:
  https://github.com/cltk/lat_text_latin_library
- Perseus canonical Latin candidate collection:
  https://github.com/PerseusDL/canonical-latinLit
- UD Latin documentation and annotation differences:
  https://universaldependencies.org/la/overview/introduction.html
- Latin treebank harmonization discussion:
  https://aclanthology.org/2023.udw-1.2/

These references motivate resource audits and feature crosswalks; they are not
evidence that the proposed decipherment model will attain English-level recovery.
