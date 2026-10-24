# Word-Substitution Decipherment: Ravi–Knight Reproduction and Grammar-Tolerant Extension

Planning companion: [detailed implementation plan](ravi_knight_implementation_plan.md).
Initial delivery: English reproduction plus a small Latin feasibility pilot;
one-to-one type mappings in the main synthetic benchmark, with relaxed mappings
compared separately. Target roughly one hour per configurable experimental run.

## 1. Objective

Implement and evaluate unsupervised word-level substitution decipherment, based on:

**Sujith Ravi and Kevin Knight (2011), *Deciphering Foreign Language*, ACL, Section 2.**  
https://aclanthology.org/P11-1002.pdf

The target problem:

- The plaintext language is known.
- Ciphertext word boundaries and word order are preserved.
- Sentence boundaries are unavailable to the decipherment system.
- Every distinct ciphertext word corresponds to one plaintext surface form, globally and consistently.
- The plaintext vocabulary is unknown.
- A large independent corpus of the target language is available.
- No parallel text, original vocabulary list, topic label, or known substitution pairs are supplied.

The primary research goal is **recovering valid grammatical structure**, even when the recovered words differ from the originals.

Exact plaintext recovery is a secondary metric.

Do not assume that a fluent-looking or high-probability decoding is grammatically valid.

## 2. Implementation principles

1. Reproduce the published algorithm before introducing experimental extensions.
2. Keep all experiments reproducible with fixed random seeds.
3. Prevent any leakage of plaintext vocabulary, original word frequencies, or true mappings into inference.
4. Separate language-model quality, search quality, and grammatical evaluation.
5. Support incremental development and profiling.
6. Preserve competing hypotheses instead of committing irreversibly to one mapping.
7. Never use the original plaintext or its grammatical annotations in decipherment. They are permitted only for evaluation.

## 3. Recommended stack

- Python 3.12+
- NumPy and SciPy for numerical computation
- KenLM for word n-gram probabilities
- Cython or Rust for performance-critical sampling if profiling justifies it
- pytest for tests
- Parquet for experiment results
- CLI configuration using YAML or TOML
- Optional Stanza or UDPipe for independent grammatical evaluation

Use integer word IDs internally.

Do not introduce distributed computation until a correct single-process implementation has been benchmarked.

## 4. Data preparation

Implement a pipeline accepting:

- A plaintext training corpus in the target language.
- A separate plaintext evaluation corpus.
- A deterministic word-substitution cipher generator.

The generator must produce:

- Ciphertext token sequence.
- True substitution dictionary, stored separately.
- Original plaintext.
- Original sentence boundaries, stored separately.
- Optional grammatical annotations, stored separately.

Support two input modes:

**Mode A: segmented**

Sentence boundaries are preserved, matching the published experimental setting.

**Mode B: continuous**

Sentence boundaries and punctuation are removed, leaving only word boundaries.

The decoder must never access the hidden boundaries in Mode B.

Create controlled corpora with different sizes and domain relationships.

## 5. Baseline: Iterative EM

Implement Section 2.1 of the paper.

Required functionality:

1. Rank plaintext and ciphertext word types by frequency.
2. Initialize restricted vocabularies using the most frequent types.
3. Collapse excluded types into UNKNOWN.
4. Train a word-substitution channel using EM.
5. Expand both vocabularies iteratively.
6. Carry forward confident mappings using the paper's thresholding procedure.
7. Retrain the expanded channel.
8. Decode with Viterbi using the trained channel and language model.

Implement the original confidence-freezing behavior for reproduction.

Also support an experimental mode in which assignments remain revisable.

Report mapping accuracy, runtime, memory consumption, and likelihood.

## 6. Bayesian decipherment

Implement Section 2.2.

The published method uses:

- A Chinese Restaurant Process formulation.
- A fixed statistical source-language model.
- A sparse Dirichlet prior for the substitution channel.
- Point-wise Gibbs sampling.
- Candidate selection from local word contexts.
- Annealing.
- Initialization from Iterative EM.

Use the paper's published configuration as the initial reproduction target:

- Bigram source-language model as the Bayesian base distribution.
- Source-model prior concentration approximately 10,000.
- Channel prior concentration 0.01.
- Candidate proposal size 100.
- 2,000 sampling iterations.
- Linear temperature schedule from 1 to 0.08.

Implement the necessary predictive probability equations from the cited Bayesian formulations.

Where the paper omits implementation details, document the chosen interpretation. Do not claim exact reproduction without verification.

### Sampling variants

Implement two variants:

**A. Token-level sampling**

Follow the paper's token-position sampling approach as closely as possible.

**B. Type-level sampling**

Every occurrence of a ciphertext type shares one plaintext assignment.

When updating a type, calculate the effect of changing all its occurrences.

Support efficient incremental n-gram score updates.

These variants must be compared experimentally.

### Candidate proposals

Implement:

- Context-based top-K candidate retrieval.
- Random fallback proposals.
- Frequency-based proposals.
- Occasional unrestricted exploration.
- Optional Metropolis–Hastings correction for asymmetric proposals.

Measure proposal recall using synthetic data.

A proposal mechanism that never offers the correct candidate cannot recover it, regardless of the quality of the scoring model.

## 7. Extension A: unknown sentence boundaries

Implement three experimental modes:

**A0 — Original segmentation**

Use known sentence boundaries in training and decipherment.

**A1 — Continuous language model**

Remove sentence boundaries from both language-model training and ciphertext.

Train and score continuous word streams.

Do not insert artificial boundaries during decoding.

**A2 — Latent sentence boundaries**

Treat boundaries as hidden variables.

Start with a simple boundary probability model and compare against A1.

Avoid introducing a complex grammar parser initially.

Measure:

- Exact word recovery.
- Grammatical structure recovery.
- Language-model perplexity on held-out genuine Latin.
- Effect of boundary removal on decipherment performance.

A2 is optional until A1 is operational.

## 8. Extension B: grammar-tolerant decipherment

The model must permit alternative words that preserve grammatical relationships.

For example, replacing one singular nominative noun with another may be acceptable when its syntactic role and agreement relationships remain valid.

However, grammatical interchangeability is contextual. Do not assume that words sharing POS and morphological features are universally interchangeable.

Implement three scoring configurations:

**B0 — Original**

Only the language model and substitution-channel objective.

**B1 — Morphology-aware**

Add soft evidence based on morphological analyses.

Preserve ambiguous surface forms.

**B2 — Structure-aware**

Add optional grammatical factors concerning:

- Adjective–noun agreement.
- Subject–verb agreement.
- Preposition government.
- Plausible local POS patterns.
- Dependency and argument-structure compatibility.

These are hypotheses to evaluate, not proven improvements.

Avoid hard grammatical pruning unless the rule is demonstrably necessary under the chosen grammar coverage.

All grammatical factors must be individually switchable.

### Critical requirement

Do not optimize exclusively for POS compatibility.

A decoding can have plausible morphological features while violating dependency relationships.

## 9. Candidate uncertainty

Maintain a sparse candidate distribution for each ciphertext type:

    cipher_word_id -> [(latin_word_id, weight), ...]

This is a derived or approximate representation of the search distribution.

Also preserve joint candidate samples or equivalent dependency information.

Do not assume independently selected highest-probability assignments form a valid dictionary.

Support:

- Top-K active candidates.
- Candidate diversity.
- Multiple independent chains.
- Reintroduction of previously discarded candidates.
- Confidence tracking across iterations.

Treat candidate weights as uncalibrated until calibration is measured.

## 10. Evaluation

### Exact decipherment metrics

- Token-level exact recovery.
- Type-level exact recovery.
- Recovery of frequent ciphertext types.
- Accuracy by frequency band.

### Grammatical metrics

Use hidden original annotations only for evaluation.

Measure:

- POS accuracy.
- Morphological feature accuracy.
- Dependency relationship recovery.
- Subject–verb agreement validity.
- Adjective–noun agreement validity.
- Preposition–case compatibility.
- Overall grammatical acceptability.

Report two distinct quantities:

**Original-structure recovery:** how closely the inferred relationships match the original.

**Independent grammatical validity:** whether the alternative decoded construction is grammatical, even if its parse differs from the original.

Do not automatically classify an alternative valid parse as a failure.

Automated grammar judgments are imperfect. Include a small manually reviewed or independently adjudicated test set.

### Anchor usefulness

Evaluate whether the inferred candidates for frequent ciphertext words help a downstream cipher-recovery task.

Compare downstream recovery with:

1. No grammatical anchors.
2. Random anchors.
3. Inferred grammatical anchors.
4. Oracle grammatical anchors.

The fourth is an upper-bound diagnostic, not a valid decipherment result.

## 11. Essential stress tests

### Test 1: Perfect-dictionary stability

Initialize the solver from the correct dictionary.

Check whether optimization damages grammatical relationships.

Track both objective score and grammatical validity.

### Test 2: Valid lexical alternatives

Initialize from an independently verified grammatical alternative.

Check whether the algorithm preserves or damages its structure.

### Test 3: Corrupted dictionaries

Introduce controlled agreement and dependency errors.

Check whether inference repairs them.

### Test 4: Domain mismatch

Train the language model on unrelated Latin texts.

Measure degradation relative to related-domain training.

### Test 5: No sentence boundaries

Compare identical encrypted corpora with and without segmentation.

### Test 6: Candidate starvation

Measure how often the correct or a grammatically equivalent candidate is absent from the proposal set.

### Test 7: Search convergence

Run multiple chains and compare their mappings, grammatical structures, and scores.

### Test 8: Adversarial optimization

Allow the search algorithm to exploit the grammar-aware score.

Check whether higher scores correspond to increased grammatical corruption.

This test is mandatory because previous experiments exhibited this failure.

## 12. Experiment matrix

Run the following stages in order:

**Stage 1: English reproduction**

Reproduce a small published-style word-substitution experiment with preserved sentence boundaries.

**Stage 2: English without boundaries**

Use identical data and remove segmentation.

**Stage 3: Latin baseline**

Use Latin training and test corpora, with exact word substitution.

**Stage 4: Latin without boundaries**

Remove punctuation and segmentation.

**Stage 5: Latin with grammatical alternatives**

Evaluate structural recovery separately from lexical recovery.

**Stage 6: Voynich-scale synthetic benchmark**

Use approximately 30,000–40,000 ciphertext tokens and a realistic number of unique word types.

Only after these stages should the system be applied to actual Voynich transcription.

## 13. Required deliverables

- Reproducible cipher generator.
- Corpus preprocessing pipeline.
- Word n-gram language-model adapter.
- Iterative EM implementation.
- Bayesian sampler.
- Type-consistent sampler variant.
- Candidate proposal indexes.
- Evaluation suite.
- Performance profiler.
- Experiment configuration files.
- Tests verifying the absence of oracle leakage.
- A report comparing the reproduction and all extensions.

## 14. Milestones and stopping conditions

**M1: Baseline correctness**

The cipher generator, language model, and small-vocabulary EM solver pass unit and integration tests.

**M2: Published-method reproduction**

The Bayesian method demonstrates meaningful recovery on a controlled English benchmark. Document any discrepancy with published results.

**M3: Boundary robustness**

Quantify the loss from removing sentence boundaries.

**M4: Latin feasibility**

Establish whether grammatical relationships can be recovered without supplying the original vocabulary or grammatical analyses.

**M5: Grammar-aware benefit**

Show that grammatical extensions improve independent grammatical validity or downstream anchor usefulness, without merely improving their own training objective.

**M6: Scaling**

Demonstrate feasible runtime and memory usage on Voynich-scale synthetic ciphertext.

Do not advance to a later milestone merely because the optimizer's score improved.

## 15. Non-goals for the initial implementation

Do not initially implement:

- Glyph-level substitutions.
- Homophonic encodings.
- Word contractions or expansions.
- Unknown plaintext language.
- Unknown word boundaries.
- Full semantic reconstruction.
- A complete Latin grammar in Z3.
- A large neural language model trained specifically to prefer candidate decodings.

These can be investigated after the core model is validated.

## 16. Final research question

Can a word-substitution decipherment algorithm, given a known language but unknown plaintext vocabulary and unknown sentence boundaries, recover enough genuine grammatical structure to produce useful candidate mappings for a subsequent cipher attack?

The experiment succeeds only if independently evaluated evidence supports that conclusion.
