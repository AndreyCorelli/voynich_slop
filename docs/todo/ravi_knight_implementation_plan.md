# Ravi–Knight implementation and research plan

Status: implementation started, 2026-10-14. The small-state HMM reference
and exact enumeration checks, restricted source training and fixed-vocabulary
channel EM with confidence freezing and vocabulary expansion are delivered.
The generated-English iterative diagnostic matches, but does not outperform,
frequency matching. No successful reproduction is
claimed. A work-disjoint natural-English pilot and artifact validator are also delivered;
its recovery gate remains unmet. See [implementation status](../ravi_knight.md). The initial scope and
budget reflect the user decisions below.

Companion specification: [ravi_knight_todo.md](ravi_knight_todo.md).
Primary reference: [Ravi and Knight (2011), Sections 2–2.3](https://aclanthology.org/P11-1002.pdf).

Next implementation scope: [scalable boundary-free English plan](scalable_english_decipherment_plan.md).
It prioritizes a sparse type-consistent extension while preserving this historical
reproduction plan and its unfinished milestones.

## 1. Interpretation and confirmed decisions

The project asks whether unsupervised word substitution can recover useful
Latin grammatical relationships without knowing the original vocabulary or
sentence boundaries. Exact lexical recovery calibrates the system, but is not
a substitute for independent grammatical evaluation.

User decisions, confirmed 2026-10-14:

1. First delivery: English reproduction plus a small Latin feasibility pilot.
   The later boundary, grammar and scaling program remains gated work.
2. Enforce a one-to-one dictionary in the main type-consistent synthetic
   benchmark; compare relaxed many-to-one mappings separately. Keep the published
   probabilistic token model unchanged. A function from cipher types to plaintext
   types is not, by itself, a one-to-one substitution.
3. Target approximately one hour for a complete experimental run. Make this a
   configurable orchestration budget, not a hardcoded algorithmic assumption.
   Estimate cost from short profiling runs, checkpoint gracefully, record partial
   results and permit explicit budget overrides. Reserve time for evaluation and
   artifact validation within the run budget.

Other defaults to revisit during dataset selection: training-attested surface
forms define the initial vocabulary; work/source-disjoint splits are preferred;
English replacement data support a method reproduction, not an exact published
benchmark claim; Latin manual review must have a named reviewer and rubric
before grammatical success is claimed.

## 2. Elaborations and corrections to the specification

### Published method versus extensions

Maintain distinct experiment identities for:

- Published-style iterative EM, including irreversible confidence freezing.
- Published-style token sampling, approximate restricted candidates and final
  channel extraction followed by Viterbi decoding.
- Corrected sampling with a full-support proposal and Metropolis–Hastings.
- Type-consistent inference with optional injectivity.
- Boundary removal, morphology and structural factors.

The original token sampler and Viterbi decoder need not produce a single
consistent dictionary. Report token consistency and mapping collisions rather
than silently projecting their output into the type-consistent model.

The paper fixes the statistical LM used as the source prior base; a finite
concentration CRP predictive model still responds to counts. A strictly fixed
LM likelihood is a separate ablation. The published parallel sampler is also
different from sequential updates. Start sequentially, label that deviation,
and do not equate its runtime with the published distributed measurements.

The paper's final Viterbi score uses the cube of the channel probability.
Capture that separately from the training likelihood. Its EM experimental
schedule begins with 100 types plus UNKNOWN, adds 50 types per expansion and
stops at 350 plus UNKNOWN; its Bayesian initialization uses the 101-by-101
channel decoding. A generic full-vocabulary EM expansion is an extension.

### Vocabulary coverage and grammatical alternatives

Unknown plaintext vocabulary means selection from independent resources, not
an unlimited ability to recover unseen forms. Report attested-vocabulary
coverage and its token/type ceilings after inference. Never repair a vocabulary
because evaluation reveals a missing word.

There is no general automatic oracle for a grammatically equivalent candidate.
Measure exact proposal recall separately from manually adjudicated grammatical
alternatives. Shared POS or morphology alone does not establish equivalence.

A deterministic substitution also constrains alternatives globally: a word
replacement must work at every occurrence of the cipher type. Under injectivity,
colliding lexical alternatives are invalid dictionary hypotheses even when
individual sentences are grammatical.

## 3. Repository integration and reuse audit

Existing components to inspect and adapt, rather than replace wholesale:

| Component | Intended reuse | Required audit |
| --- | --- | --- |
| `src/voynich_smt/word_mapping/fixtures.py` | Public/truth fixture separation and deterministic encryption | Public source metadata and encoder seed must not reveal source passage/key; continuous export must omit segment lengths |
| `word_mapping/corpora.py` | Corpus adapters and split provenance | Genuine sentences versus record/layout boundaries; source-disjoint splits |
| `word_mapping/ngram.py` | Small reference scorer and stable IDs | Existing smoothing is not automatically a published LM match; continuous scoring and UNKNOWN semantics |
| `word_mapping/incremental.py` | Occurrence indexes and score-update patterns | Overlapping affected n-grams, count terms and transaction rollback |
| `word_mapping/candidates.py` | Independent vocabulary/frequency infrastructure | No evaluation-derived vocabulary or oracle candidates |
| `word_mapping/morphology.py` | Ambiguous Latin analyses | Missing analyses remain unknown; do not collapse ambiguity |
| `word_mapping/evaluation.py` | Exact metrics and artifact conventions | Add token-model consistency and independent grammar outputs |
| `docs/word_mapping_zero_corruption.md` and `docs/word_mapping_structural_oracle.md` | Objective failure evidence and controls | Preserve original results; morphology compatibility is not grammatical validity |

Add a focused `src/voynich_smt/word_mapping/ravi_knight/` package after the audit.
Suggested modules: `config.py`, `data.py`, `lm.py`, `em.py`, `collapsed.py`,
`token_sampler.py`, `type_sampler.py`, `proposals.py`, `artifacts.py`.
Keep benchmark orchestration in `benchmarks/ravi_knight_*.py`. New shared grammar
evaluators may live outside this package if their contracts are general.

Scientific dependencies remain optional. Use the existing small LM for numerical
reference checks; assess KenLM installation and model-building compatibility
before making it the production backend. Log probability base and conversion
explicitly. Defer Rust/Cython and Parquet until profiling or analysis needs them.

## 4. Data and inference contracts

### Public inputs

Versioned integer token stream, observable boundary policy, independently built
LM and vocabulary, permitted morphology resources, immutable configuration and
search seed. Record content hashes and preprocessing versions.

Mode A0 includes genuine observed sentence boundaries. Mode A1 contains a
continuous stream per document with punctuation and sentence markers removed.
Document endpoints are observable if the protocol declares them. Storage chunks
must not reset LM context or reveal original sentences. Do not join unrelated
works just to create longer streams. Corpus exclusions need an explicit policy;
do not bridge removed material as if it were adjacent prose.

Distinguish punctuation removal from boundary removal with an additional
punctuation-free segmented control, so the main paired comparison changes only
segmentation. Preserve token alignment in evaluation-only artifacts.

### Private evaluation inputs

Plaintext, key, sentence boundaries, annotations, and plaintext-identifying
passage offsets live outside solver input directories. Public manifests may use
opaque source IDs; detailed provenance remains in the evaluator manifest when
it would identify the encrypted passage. Cipher-generation seeds are private
when they permit deterministic reconstruction of the mapping.

Use separate preparation, inference and evaluation entry points. Inference must
run with the private directory unavailable. Truth changes must leave the public
input and deterministic inference output unchanged. Evaluation joins artifacts
by content hash and never changes a completed hypothesis.

### Outputs

Store final token sequence, channel parameters where applicable, complete joint
dictionary hypotheses, sparse per-type candidate summaries, chain/checkpoint
identities, raw objectives and their components, coverage, timing, peak memory,
proposal statistics and inference deviations. Marginal top choices are not a
joint dictionary. Annealed chain frequencies are heuristic weights unless
calibration and stationary sampling justify a stronger interpretation.

## 5. Phase 0 — Freeze mathematical and experimental contracts

Tasks:

1. Produce a paper-to-code checklist with section/page references for each
   algorithm choice; mark reported, derived and unspecified details.
2. Resolve source and channel count definitions, concentration conventions,
   boundary events, initial states, annealing exponent, sweep semantics and
   final channel extraction. In particular distinguish total Dirichlet mass
   from a per-outcome pseudocount.
3. Read the Bayesian references cited by Section 2 before freezing equations.
   Derive a complete collapsed joint and conditionals; do not copy a one-edge
   predictive formula into a multi-edge update without count corrections.
4. Audit English dataset availability, licenses and split independence. If the
   original temporal-expression/Transtac data cannot be obtained, document the
   replacement and reserve “exact benchmark reproduction” for matching data.
5. Freeze pilot sizes, seeds, budgets, baselines and success thresholds before
   running the evaluation split.

Acceptance: a reviewable fidelity table, dataset manifest template and explicit
list of unresolved interpretations. No recovery claim depends on guessed details.

## 6. Phase 1 — Fixtures, LM adapter and numerical reference

Tasks:

1. Adapt one-to-one fixtures to segmented and continuous public artifacts.
2. Train independent unigram/bigram models; add a common conditional-probability
   interface and full sequence scorer with explicit BOS/EOS/UNKNOWN policies.
3. Implement log-space or scaled forward-backward and Viterbi for a tiny dense
   bigram HMM. Keep the reference implementation simple and independent of the
   accelerated backend.
4. Enumerate every latent sequence in a very small fixture and compare evidence,
   marginals, expected counts and Viterbi paths to exact enumeration.
5. Verify normalization, OOV accounting, serialization identity and private-input
   isolation. Score continuous input identically across arbitrary storage chunks.

Acceptance: exact checks within declared numerical tolerance, deterministic
fixtures, no hidden boundaries in A1, and a measured tiny-run time/memory baseline.

## 7. Phase 2 — Iterative EM

Tasks:

1. Rank source forms only from LM training counts, and cipher types only from
   ciphertext counts. Resolve ties deterministically.
2. Collapse excluded forms into UNKNOWN and rebuild the source model for each
   restricted vocabulary; UNKNOWN is a modeled symbol here, not an old search
   barrier that discards surrounding evidence.
3. Initialize normalized channel rows and run EM with recorded stopping rules.
4. Freeze rows satisfying the published threshold in the published direction
   P(cipher | plaintext). Do not add reciprocal exclusion constraints silently.
5. Expand using the reproduction schedule, preserving frozen rows; record active
   coverage and likelihood at each stage. Compare likelihood only within a fixed
   model/vocabulary stage.
6. Decode with Viterbi and the published channel exponent. Keep token output and
   any derived dictionary summary distinct.
7. Add revisable freezing only as a named ablation after the baseline works.

Acceptance: likelihood monotonicity for exact EM within a stage, expected-count
agreement with enumeration, stable frozen rows, and a reproducible English pilot
against frequency matching and unigram baselines.

## 8. Phase 3 — Bayesian token sampler

Tasks:

1. Implement the collapsed source and channel joint with count insertion/removal
   and a full recomputation scorer for tiny cases.
2. Remove the current assignment before computing its conditional. For neighboring
   source events sharing a count cell, use sequential predictive counts or the
   equivalent gamma-function joint ratio. Include endpoint events explicitly.
3. Start with full-vocabulary sampling on tiny inputs. Compare conditionals to
   enumerated joint probabilities; check count conservation after every update.
4. Implement the published context candidate approximation as a separate kernel,
   retaining current state and logging fallback behavior and candidate support.
5. Add a full-support mixture proposal with explicit forward/reverse probability
   and MH acceptance. Top-K restriction alone does not make an exact Gibbs update.
6. Reproduce reported initialization, prior settings, sweep count and temperature
   endpoints; document sweep indexing and temperature application.
7. Extract the channel from the designated final sample and perform Viterbi;
   compare best-scoring samples only in a separately labeled analysis.

Acceptance: exact tiny-state conditional checks and stationary-distribution
checks at temperature one for the corrected kernel; deterministic replay; English
recovery and runtime comparison with EM. The approximate kernel carries no claim
of exact posterior sampling.

## 9. Phase 4 — Type-consistent inference and candidate support

Tasks:

1. Define a target over dictionaries explicitly. A channel sparse prior is not
   automatically meaningful under a deterministic injective mapping; derive the
   restricted target or declare a separate dictionary prior.
2. Build occurrence indexes and update every occurrence of a type atomically.
   Deduplicate affected n-gram windows, but retain event multiplicities.
3. For injective dictionaries support replacement with an unused form and swaps
   between occupied forms. Ensure the move family can reach the permitted state
   space. Relaxed many-to-one mappings get a distinct configuration identity.
4. Compare full recomputation with incremental LM and count-score deltas for
   adjacent repeats, alternating types, endpoints, swaps and failed proposals.
5. Combine candidates from multiple occurrence contexts, frequency ranks and
   full-support random exploration. Bound/cache context indexes and measure their
   construction memory rather than precomputing all context pairs.
6. Archive complete hypotheses across chains, with sparse marginal summaries;
   preserve candidate reintroduction and checkpoint/resume state.

Acceptance: global mapping invariants and score-delta parity; fair comparisons
with token inference under equal wall time and reported update counts. Separate
proposal absence, vocabulary absence and poor ranking in diagnostics.

## 10. Phase 5 — English calibration and boundary ablation

Begin with tiny controlled text, then a frozen independent English pilot. Do not
infer large-vocabulary feasibility from a small synthetic grammar alone.

Run frequency matching, iterative EM, approximate token sampling, corrected token
sampling and type inference. Use at least three search seeds per pilot condition
as an initial variability diagnostic; choose final replication counts from cost
and observed variability before final evaluation. Report distributions, not only
the best chain. Separate cipher-key, corpus-selection and search randomness.

Pair A0 with punctuation-free segmented text and A1 on identical word sequences.
Measure exact recovery, dictionary consistency, vocabulary coverage, held-out LM
loss, proposal recall, memory, time and chain disagreement. Hidden sentence
annotations must not enter A1 inference. Defer A2 until A1 is interpretable.

Acceptance: improvement over declared simple baselines on independent English
fixtures, or a documented negative result identifying the blocked component.
Published scores are context, not pass thresholds for replacement datasets.
Failure leads to a focused diagnostic; it does not justify adding grammar factors.

## 11. Phase 6 — Latin feasibility and independent grammar evaluation

1. Freeze independent Latin LM, development and evaluation sources. Document
   normalization and resource overlap, including pretrained evaluators.
2. Run the validated B0 models first, segmented and continuous. Report candidate
   coverage and genuine-text LM quality before attributing failure to search.
3. On development data only, run perfect-start stability, controlled agreement/
   dependency corruption, verified lexical alternatives and domain mismatch.
   Oracle starts are diagnostics, never unsupervised recovery results.
4. Define original-structure metrics on aligned token positions. Report POS and
   morphology with ambiguity/missing-analysis accounting; dependency recovery
   needs a complete declared parsing/annotation procedure.
5. Define independent grammatical validity separately: analyze the decoded text
   without feeding original dependency edges or boundaries to inference. For A1,
   report evaluator-inferred segmentation; evaluation using gold segmentation is
   an explicitly assisted sensitivity, not the headline validity result.
6. Prepare a blinded manual sample of competing decodings and genuine/corrupted
   controls. Freeze adjudication criteria for agreement, government, argument
   structure and unresolved cases. Report uncertainty and reviewer agreement.

Acceptance: a defensible feasibility report, including negatives. Parser scores
alone cannot establish Latin grammatical validity. Lack of manual adjudication
leaves that claim pending rather than converting a proxy into ground truth.

## 12. Phase 7 — Grammar extensions and adversarial checks

Only after baseline calibration, add B1 ambiguous morphology evidence and then
individually switchable B2 factors. Specify where proposed dependency relations
come from, how ambiguity is marginalized/approximated and what each factor costs.
No original POS, dependency edges or boundaries enter these factors.

Select weights on development controls, then freeze them. Use a factorial subset
that isolates each factor before testing combinations. Run matched B0 searches
with equal budgets. Mandatory checks include perfect-start degradation, repair
of planted errors, alternative grammatical parses, and search deliberately
maximizing the grammar score to find linguistic failures.

Acceptance: independent validity or downstream anchor benefit improves over B0
with uncertainty reported. Improvement only in the optimized score fails this
gate. A failed factor is retained as a negative result and removed from the
preferred configuration.

## 13. Phase 8 — Anchors and scaling

First specify the downstream solver interface: whole-word substitutions here do
not directly define a glyph key. Export scored joint hypotheses or soft anchor
constraints with provenance, rather than treating marginal candidates as facts.

Compare no anchors, random anchors matched for frequency/quantity/confidence,
inferred anchors and oracle anchors on fresh synthetic ciphers of the intended
downstream family. Measure recovery, false-anchor damage and budget required.
Keep the oracle condition explicitly diagnostic.

Profile 1k, 5k, 10k and 30–40k-token fixtures with independently chosen vocabulary
sizes and frequency spectra. Report candidate-index construction, EM lattice
memory, scoring throughput and full-run cost. Optimize measured bottlenecks only.
Large token counts with tiny repeated vocabulary do not establish realistic scale.
Actual Voynich application remains gated on synthetic validity and applicability
of the word-substitution assumptions.

## 14. Artifacts, checks and reporting

Each run contains resolved configuration, source/model/code hashes, environment,
separate random seeds, boundary/vocabulary policies, fidelity deviations, events,
checkpoints, final joint hypotheses and evaluator output. Keep private truth out
of public run bundles. Record timeout and failure states explicitly.

Use JSON manifests and JSONL progress initially; use numeric arrays for counts
and optional Parquet for aggregate result tables. Benchmark validators recompute
scores and metrics independently from stored outputs. Resume must preserve RNG,
counts, temperature and update position, not just the best dictionary.

Required checks target consequential invariants: exact small-state inference,
channel direction, count conservation, repeated-event conditionals, incremental
score parity, injectivity, full-support proposal accounting, boundary isolation,
truth isolation and deterministic resume. No large experiment should be needed
to discover a numerical or leakage bug.

The final report separates model quality, candidate support, search effectiveness,
grammatical validity and downstream utility. Report unattainable vocabulary
coverage, inconsistent token decodings and unresolved judgments explicitly.

## 15. Immediate implementation work package

With the initial scope confirmed:

1. Finish the reuse and paper-fidelity audit, including cited Bayesian equations.
2. Choose and freeze a legal, independent English pilot corpus and splits.
3. Define public/truth schemas, segmented/continuous policies and configuration.
4. Implement only the tiny reference LM/HMM and enumeration checks first.
5. Deliver iterative EM and an English baseline report before integrating a sampler.

These steps are the next concrete implementation scope; later phases remain
conditional on their stated gates. This draft does not yet assign calendar dates
or claim that experimental thresholds and manual-review capacity are settled.

## Scale constraint reaffirmed, 2026-10-14

The user specifies an eventual Latin inventory of roughly 20,000 lemmas and
800,000 surface forms. Treat these as design-scale targets, not measured counts
for the current resources. Surface forms remain the decipherment assignments;
lemma indexing may organize retrieval but must preserve ambiguous analyses and
must not substitute lemma frequency for surface-form probability silently.

The current dense HMM is a small-vocabulary numerical reference. A dense source
transition matrix over 800,000 forms has 640 billion entries (about 5.12 TB for
float64 values alone), before Python overhead or channel storage. Do not attempt
that allocation as the next vocabulary-size experiment.

The scalable backend needs sparse observed n-gram counts with backoff, on-demand
LM scoring, per-cipher-type sparse active candidates, retrieval across the full
independent inventory, and periodic full-support exploration. Candidate budgets
must be distinct from inventory size. Track index memory/build time, active
candidate counts, retrieval recall and candidate reintroduction. Unsupported
inventory forms need an explicit independent LM backoff policy, not evaluation-
derived additions. Validate restricted-support inference against the dense
reference on small cases and label approximations. A future sparse EM/beam
implementation is not automatically exact full-vocabulary forward-backward.

Immediate authorized sequence: compare frequency-informed initialization with
random starts at 200 updates, then compare freezing on/off under frequency
initialization. Keep the existing tiny natural-English vocabulary schedule fixed
for these controlled diagnostics; its purpose is isolating effects, not solving
the final inventory scale. Larger dense vocabulary alone is not the scale plan.


Initialization/freezing diagnostics are complete on the reused natural-English
pilot: random/freeze 15.88%, random/no-freeze 6.64%, frequency/freeze 7.87%,
frequency/no-freeze 14.51% mean token recovery across seeds 3/5/7. Keep random
initialization, freezing and the 200-update cap as current defaults. Effects
interact; no-freeze is fresh retraining, not warm-start revision. See the
[completed comparison](../ravi_knight.md) and stored factorial summary. The
recovery gate is still unmet; sparse full-inventory inference remains future work.

Restart-selection and revisable carryover diagnostics are now implemented and
reported. Likelihood selects the worst recovery in the random/fresh-no-freeze
condition; it is not a validated recovery selector. Revisable random carryover
with a 5% fresh mixture reaches 10.88% mean recovery, above fresh no-freeze
(6.64%) but below irreversible freezing (15.88%). Keep defaults unchanged.
These remain reused-development-fixture findings, not independent validation.

Remaining inexpensive diagnostics completed: expanding ciphertext from 487 to
960 tokens with fixed source and active cipher vocabularies improves recovery
on the common original prefix from 15.88% to 22.18% mean (19.17% over all 960).
A predeclared 0.01/0.1/1.0 smoothing sweep yields 15.88%/15.88%/15.95% mean
recovery, an immaterial difference; retain smoothing 0.1. All 27 new stages
validate and 42 targeted tests pass. Keep these as development evidence. Next
substantial work is sparse candidate support and type-consistent inference for
the full Latin inventory target, rather than further dense-pilot tuning.
