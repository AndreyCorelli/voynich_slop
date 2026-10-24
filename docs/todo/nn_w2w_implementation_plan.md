# Word-to-word implementation plan

Implementation of [nn_w2w_todo.md](nn_w2w_todo.md). This is a plan, not a claim
that recovery or manuscript validation has succeeded.

Implementation status: milestones 1–5 are delivered, along with initial
synthetic metrics and surrogate controls. See [implementation and validation](../word_mapping.md).
Milestone 6 calibration and the matched lemma comparison are next; the initial
natural-text pilot has not passed the recovery/control gates.
Development-only truth-score diagnostics and paired multi-seed ablations are
now available; see [their protocol](../word_mapping_ablation.md).
The [fully covered large-budget calibration](../word_mapping_full_coverage.md)
activates every observed type and audits whole-segment coverage exclusions.
The [disjoint-book and local-objective calibration](../word_mapping_long_context.md)
adds larger natural segment bundles and exhaustive oracle-neighborhood diagnostics;
the recovery gates remain unmet.

## Scope and repository findings

Build a separate statistical word-dictionary experiment within `voynich_smt`.
The existing Z3 character-code solvers solve a different problem and should not
be used as the optimization engine for this experiment.

Reusable components:

- `data/corpus.py`: versioned `Corpus`, identity hashes, JSON serialization.
- `data/voynich.py`: EVA records with folio, locus, original positions,
  uncertainty/exclusion flags and Currier metadata in `page_variables['L']`.
- `data/latin.py`: Caesar parser-v2 normalization and source character offsets.
- `benchmarks/expanded_medieval_latin.py` and historical source extractors:
  cached medieval texts, manifests and discarded-token barriers.
- `benchmarks/contraction_context_ranking.py`: surface bigram baseline, not an
  incremental optimizer or a sufficient new language model.
- `benchmarks/latin_morphology_coverage.py`: pinned Whitaker parser and analysis
  extraction; the form inventory is a membership resource, not training prose.

Neither this optimizer nor the proposed word-to-lemma optimizer currently
exists. A matched lemma baseline must therefore be implemented explicitly.
Current runtime dependencies contain only Z3; add scientific dependencies as
optional extras. Do not assume Numba supports the Python used by the local
environment: validate the selected interpreter before enabling acceleration.

## Fixed contracts

1. Dictionary entries are integer IDs of authoritative Latin surface forms.
   Several ciphertext types may share an entry. Lemma/feature metadata retain
   every analysis and never change the rendered form in context.
2. Preserve original spelling alongside a versioned scoring spelling. Initial
   scoring uses lowercase, j→i, v→u to match the pinned morphology resource;
   retain spelling-preserving experiments as separately identified sensitivities.
   Never reconstruct distinctions already lost in a cached normalized stream.
3. Source, sentence, exclusion and UNKNOWN boundaries break scoring contexts.
   Voynich locus boundaries are observable layout boundaries, not inferred
   sentences; make cross-locus scoring a frozen sensitivity configuration.
4. Primary candidates are forms attested in Latin LM training data. Include an
   optional, independently selected morphology-inventory expansion with a
   declared probability floor. Report candidate coverage and vocabulary size;
   do not add forms based on evaluation plaintext.
5. UNKNOWN is distinct from LM OOV. Fix the active ciphertext vocabulary for
   each search stage; inactive types are UNKNOWN barriers. Do not let annealing
   remove difficult tokens by assigning UNKNOWN. Report coverage at every stage.
6. Synthetic truth is stored separately from public optimizer inputs. Corpus
   splits, candidates, tuning and checkpoint identities exclude this truth.

## Proposed modules and artifacts

Create `src/voynich_smt/word_mapping/` with:

| Module | Responsibility |
| --- | --- |
| `corpora.py` | Ordered segmented word streams, source adapters, split manifests |
| `morphology.py` | Cached ambiguous analyses, stable lexeme IDs, form groups |
| `mapping.py` | Dictionary state, rendering, occurrence index, collapse counts |
| `ngram.py` | Train/save/load model, full score, incremental scoring backend |
| `candidates.py` | Training-only frequencies, lemma groups, ranked proposals |
| `mutations.py` | Replacement, swap, same-lemma and lemma-changing proposals |
| `annealing.py` | Restart schedules, transactional updates, candidate archive |
| `evaluation.py` | Recovery metrics, frozen dictionary holdouts, control summaries |
| `artifacts.py` | Config validation, identity hashes, checkpoint/resume, exports |

Use `benchmarks/word_mapping_recovery.py` and
`benchmarks/word_mapping_voynich.py` as thin orchestration scripts, following
the repository's benchmark/report convention. Unit and integration tests belong
under `tests/`. Store shared prepared streams in `data/processed/word-mapping/`
and runs in `experiments/results/word-mapping/<run-id>/`.

Start with versioned JSON manifests, JSONL events and compressed numeric model
arrays; SQLite/Parquet can wait until measurements justify them. Run artifacts
include source/config/model hashes, exact splits, seeds, dependency versions,
budget, timing, mutation statistics, candidate dictionaries and validation.

## Delivery sequence

### 1. Freeze corpora and evaluation protocol

- Define stream records with original word, normalized form, source/record IDs,
  offsets, segment IDs and boundary reasons; retain all Voynich metadata.
- Iterate ordered `Corpus.records` rather than using randomized `Corpus.sample`
  to produce context sequences: sampling can join unrelated eligible records.
- Recover sentence boundaries from cached raw text/offsets where reliable.
  Existing flat streams do not establish sentence boundaries. Use declared
  paragraph boundaries or re-extraction; mark unavailable boundaries explicitly.
- Inventory usable sources; exclude known mixed-language material. Reuse cached
  source files without network access or duplicate downloads.
- Freeze LM train/development/test work splits and synthetic recovery passages
  disjoint from LM training. Keep cross-author evaluation distinct from
  disjoint same-author passages; detect duplicate passages across caches.
- Freeze folio splits, Currier A/B/unknown-label cohorts and tokenization policy.

Acceptance: reproducible stream hashes; no contexts across exclusions/sources;
audited boundary examples and split overlap checks.

### 2. Build morphology and candidate catalogs

- Adapt the pinned parser into a reusable wrapper without importing benchmark
  preparation routines that select existing target passages.
- Cache all analyses for training vocabulary. Use stable resource lexeme IDs
  rather than guessed display lemmas; validate how roots become lemma labels.
- Record unrecognized forms explicitly; keep them eligible as attested forms.
- Group attested forms by every supported lemma. For ambiguous tokens, use a
  declared fractional-count policy for lemma-frequency proposals, retaining
  the complete ambiguity set in exports and evaluation.
- Start with frequency-ranked lemma/form proposals and multiple seeded random
  initializations. Graph alignment is a later initialization experiment.
- Give replacement proposals nonzero support over the complete frozen candidate
  vocabulary so shortlists and incorrect lemma assignments remain escapable.

Acceptance: `terrae`-style ambiguity survives serialization; morphology lookup
does not alter spelling; evaluation inputs never determine candidates.

### 3. Implement full scoring and dedicated synthetic fixtures

- Train sparse unigram, bigram and trigram counts on segmented actual prose.
- Use interpolated conditional probabilities with unigram additive smoothing
  and context backoff; tune smoothing/mixture weights only on Latin development
  passages. Mix probabilities before taking logarithms.
- Specify BOS/EOS events, valid windows and score denominator. Preserve a full
  reference scorer independently of the fast path.
- Define the initial collapse penalty as
  `sum_form max(0, assigned_ciphertext_types - 1)`, excluding UNKNOWN.
  Compare lambda=0 and development-calibrated nonzero values. This penalty
  discourages homophonic collapse as well as degeneracy; report that tradeoff.
- Optimize summed log likelihood minus the penalty; report likelihood per
  covered token and coverage separately. Track unigram-only and zero-penalty
  baselines to expose frequency-driven collapse.
- Generate seeded one-to-one substitutions and homophonic encodings where
  several ciphertext types decode to one form. Add frequency-distorting
  homophone allocations and morphology-related ciphertext labels.
- Treat an encoder that merges different plaintext forms into one ciphertext
  type as a lossy, out-of-model stress test. Calculate its best deterministic
  decoding accuracy ceiling; do not demand impossible exact recovery.

Acceptance: hand-calculated small-model probabilities, boundary/OOV behavior,
mapping invariants, truth separation and unambiguous fixture directions.

### 4. Add incremental scoring and profile it

- Index every occurrence of each ciphertext type and each prediction window.
  A changed word affects its own prediction and the next two predictions for
  trigrams, subject to segment boundaries.
- For multi-entry proposals take the union of affected window IDs, deduplicate,
  and update collapse counts for touched forms only.
- Make proposals transactional: evaluate delta, commit accepted assignments and
  caches, or roll back without modifying state.
- Test replacements, swaps, adjacent repeated types, boundaries and multi-entry
  updates against full recomputation over seeded randomized cases. Include long
  accepted/rejected mutation sequences to detect cache drift.
- Benchmark cold/warm model lookup, frequent/rare word mutations, wall time,
  memory and evaluations/second. Add NumPy/Numba only after reference correctness;
  retain a fallback backend and equivalent scores within declared tolerance.

Acceptance: incremental/full equivalence; measured projected cost for one million
mutations on a declared corpus/vocabulary/hardware profile. Do not promise a
throughput figure before measuring it.

### 5. Deliver reproducible annealing

- Implement seeded multi-restart annealing with a fixed temperature schedule,
  proposal mixture and mutation-evaluation budget. Accept improvements; accept
  worsening moves using a numerically stable log acceptance test.
- Include replace, swap, within-lemma and lemma-changing mutations. Keep joint
  collocation/group moves in phase 2.
- Optimize from unigram, lemma-aware and random initializations. Archive top
  distinct dictionaries (default 100, configurable up to 1000), with diversity
  measured over fixed ciphertext types so tiny variations do not fill the pool.
- Checkpoint current/best dictionaries, score caches or reconstruction inputs,
  RNG state, restart/temperature/proposal position, counters and archive. Write
  atomically; reject resume after model/config/split identity changes.
- Export every assignment's surface, lemma analyses, morphology, occurrence
  count and cross-restart stability. UNKNOWN and uncovered types remain explicit.

Acceptance: uninterrupted and checkpoint-resumed runs produce identical results
on the same backend/environment; reproducible seed behavior; no partial updates.

### 6. Calibrate recovery and implement the matched lemma comparison

- Build a lemma-mode adapter sharing streams, optimizer, splits, random seeds
  and budget accounting. Retain ambiguous ground-truth lemma sets rather than
  pretending a unique gold lemma exists.
- Evaluate increasing passage lengths and active vocabularies; test candidate
  coverage failures explicitly. Compare frequency/random baselines, n-gram
  orders, initialization, penalty and mutation ablations.
- Report type and token exact-form accuracy, ambiguity-aware lemma accuracy,
  feature accuracy only where uniquely supported, dictionary coverage, frozen
  continuation likelihood, timing and variability across independent seeds.
- For homologous many-to-one decodings, retain exact plaintext truth; for lossy
  encodings report the ceiling separately. Match both evaluations and wall-time
  budgets because surface and lemma mutation costs differ.
- Predeclare recovery thresholds and minimum baseline improvement using pilot
  development fixtures, then freeze them for fresh test fixtures. Publish failures
  and candidate exclusions, not only best runs.

Gate: demonstrate recovery above frozen frequency/random baselines on untouched
fixtures, including cross-source passages. If this fails, diagnose the objective
and search before expanding manuscript optimization.

### 7. Run manuscript controls and frozen-folio validation

- Progress active vocabulary through 100/200/300 training-selected types, warm
  starting archived dictionaries and initializing new entries without test data.
- Fit matched controls with the same search/hyperparameter/budget protocol:
  unigram-preserving shuffles, position-conditioned shuffles, selected
  bigram-preserving surrogates, non-Latin prose and repetition-matched generators.
  Validate each control's claimed preserved properties and report limitations.
- Select on development folios and freeze all dictionary assignments for unseen
  folios. Do not optimize inflections or metadata on evaluation pages.
- Report known-word coverage and eligible scoring windows alongside likelihood;
  UNKNOWN tokens split runs and cannot create artificial adjacency.
- Evaluate A, B and cross-class transfer separately; retain unlabeled pages as
  their own cohort. Compare fitness distributions over independent fitted runs,
  including effect sizes and folio-level uncertainty, rather than a single maximum.

Gate: synthetic recovery, matched controls and frozen holdouts must support the
result together. Fluent output alone does not justify decipherment claims.

### 8. Phase 2, after the gates

- Audit the named pretrained models at integration time for availability,
  architecture, tokenizer, license, local requirements and scoring API. This
  plan does not assume their current compatibility.
- Add optional neural inference dependencies and rerank identical archived
  passages using subword-aware PLL or autoregressive likelihood with declared
  length/window normalization. Preserve mappings and measure recovery uplift.
- Add ambiguity-aware morphology scoring; calibrate weights against correlated
  LM evidence. Then test joint mutations and parallel tempering before genetic
  algorithms or Rust acceleration.
- Investigate spelling/inflection correspondences only for candidates passing
  validation; test proposed encoding rules on unseen word correspondences.

## First implementation slice

Deliver milestones 1–3 as one reviewable foundation: frozen stream schema,
cached corpus adapters, morphology catalog, full n-gram scorer and dedicated
word-cipher fixtures with tests. Follow with incremental scoring and annealing
as separate changes. No neural model downloads or manuscript recovery campaign
are required to validate this first slice.

## Dependency setup

Install the optional CPU word-mapping dependencies and development tools with:

```sh
uv sync --locked --extra word-mapping --group dev
```

The initial installation was verified on Python 3.14.4 with NumPy 2.5.3,
SciPy 1.18.1, Numba 0.68.0 and llvmlite 0.50.0. Exact resolved versions and
distribution hashes are recorded in `uv.lock`. Import checks, a Numba nopython
JIT calculation against NumPy, SciPy probability arithmetic and the pinned
Whitaker parser lookup for `terrae` passed; `uv pip check` found no conflicts.

The morphology implementation and generated tables already exist under
`data/vendor/whitakers-words/`; reuse the pinned resource rather than installing
a different morphology package. No pretrained neural model is required for
this first slice. PyTorch, Transformers and model weights remain phase-2 setup.
