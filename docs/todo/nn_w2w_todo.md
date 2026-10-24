# Voynich Decipherment via Constrained Optimization — Word-to-Word Variant

Implementation status and commands: [surface word mapping](../word_mapping.md).
The corpus/scoring/search foundation is implemented; the initial natural-text
pilot has not passed the recovery and control gates. Broader synthetic
calibration, matched lemma comparisons and full cross-folio campaigns remain.
An [experimental bootstrap refinement](../word_mapping_bootstrap.md) adds
uncertain candidates, soft agreement and coordinated moves; its calibrated
recovery remains low, so it is not promoted to the default search.

A [phrase proposal and exact optimization audit](../word_mapping_phrase.md) compares
training-attested pair moves and larger search budgets with a fixed objective.

A [controlled widening calibration](../word_mapping_widening.md) now reaches
32,004 words; frequency initialization improves, but the optimizer does not build
on that advantage.

A [zero-corruption baseline](../word_mapping_zero_corruption.md) now starts
perfectly and confirms that strict score ascent alone moves away from truth.

## Goal

Build an experimental system that searches for coherent Latin interpretations of the Voynich manuscript using globally consistent word-to-word mappings.

Unlike the word-to-lemma experiment, this variant maps Voynich words directly to inflected Latin word forms, preserving grammatical information.

Exact plaintext recovery is not required initially. Semantic approximations (garlic → onion, lance → spear) are acceptable if the resulting text is coherent and the mapping remains consistent.

A promising interpretation should eventually enable reconstruction of the underlying cipher or encoding mechanism.

## Core Hypothesis

Correct word assignments reinforce one another through recurring collocations, Latin inflectional patterns, and grammatical agreement.

Surface-form mapping offers stronger linguistic constraints than lemma-only mapping, at the cost of a larger search space.

The experiment should determine whether these additional constraints improve decipherment accuracy enough to justify the increased optimization difficulty.

## Existing Project Sources and Reusable Resources

Reuse existing project resources rather than downloading duplicate corpora.

All paths are relative to this document, assuming it is placed alongside the original word-to-lemma TODO.

### Voynich Transcription and Metadata

- [Processed ZL EVA corpus](../../data/processed/zl-eva.json)
- [Original IVTFF transcription](../../data/raw/ZL3b-n.txt)
- [Source manifest](../../data/raw/ZL3b-n.txt.manifest.json)
- [Corpus ingestion guide](../corpus_milestone.md)
- [IVTFF parser](../../src/voynich_smt/data/voynich.py)
- [Corpus loader and sampling API](../../src/voynich_smt/data/corpus.py)

Preserve folio, locus, section, Currier class, original word position, uncertainty flags, and exclusion flags.

Do not infer missing Currier labels.

Reuse structural baselines:

- [EVA tokenization sensitivity](../eva_tokenization.md)
- [Currier A/B structural census](../currier_structural_constraints.md)
- [Section and line-position matching](../currier_section_position.md)

Freeze transcription, filtering, and tokenization conventions for reproducible experiments.

### Latin Training Corpora

| Resource | Local source | Purpose |
|---|---|---|
| Caesar, *De bello Gallico* I–IV | `../../data/processed/caesar-latin-v2.json` | Classical Latin baseline |
| Aquinas, *De ente et essentia* | `../../data/raw/historical-lengths/` | Medieval Latin |
| *Vita Caroli IV* | Same historical source cache | Medieval Latin |
| Einhard, *Vita Karoli Magni* | `../../benchmarks/expanded_medieval_latin.py` | Historical prose |
| *Gesta Francorum*, *Philobiblon*, Dante's *Monarchia* | Same expanded medieval loader | Cross-author evaluation |
| Prepared Latin/German streams | `../../experiments/results/contraction-distribution-audit/prepared.json` | Reusable normalized sequences |
| Thematic Latin comparanda | `../../data/processed/historical-comparanda/` | Genre sensitivity |

Important:

- Preserve original Latin surface forms.
- Do not lemmatize the primary training sequence.
- Build a separate lemma annotation layer for candidate generation and evaluation.
- Keep source boundaries and discarded-token barriers.
- Preserve historical spelling differences where possible.
- Standardize and record u/v and i/j normalization.
- Quarantine mixed-language or contaminated sources.
- Do not treat morphological form inventories as attested prose.

### Existing Statistical and Morphological Resources

- [Latin unigram ranking](../latin_frequency_ranking.md)
- [Unigram implementation](../../benchmarks/latin_frequency_ranking.py)
- [Adjacent-word context ranking](../contraction_context_ranking.md)
- [Context ranking implementation](../../benchmarks/contraction_context_ranking.py)
- [Latin form inventory](../latin_form_inventory.md)
- [Historical word-frequency extractor](../../benchmarks/historical_word_frequencies.py)

The existing context-ranking experiments did not improve recovery in their tested candidate pools. Treat this as a baseline to improve upon, not evidence that collocation optimization cannot work.

Reuse the pinned Latin morphological resource described in `latin_form_inventory.md`.

Build a mapping:

    Latin surface form → possible lemmas + morphological features

Ambiguous analyses must be retained rather than arbitrarily resolved.

### Synthetic Fixtures and Controls

Reuse experimental infrastructure and methodological lessons from:

- [Contraction recovery fixtures](../contraction_coverage_calibration.md)
- [Frozen-key holdout](../frozen_key_holdout.md)
- [Structured negative controls](../structured_negative_controls.md)
- [Negative-control implementation](../../benchmarks/structured_negative_controls.py)
- [Text-generation comparison](../text_generation_comparison.md)
- [Synthetic discrimination](../currier_mechanism_discrimination.md)
- [Cross-source transfer](../currier_mechanism_transfer.md)
- [Structural coverage map](../approach_coverage.md)

Existing character-cipher fixtures are not substitutes for dedicated word-to-word recovery benchmarks.

Preserve source provenance, normalization settings, hashes, random seeds, and train/test boundaries.

## Mapping Constraints

Define:

    f: Voynich word → Latin surface form

Rules:

- Every Voynich word maps to exactly one Latin surface form globally.
- Different Voynich words may map to the same Latin surface form.
- Different Voynich words may map to different inflections of the same lemma.
- Each mapped Latin surface form retains its lemma and possible morphological analyses.
- Mapping consistency is a hard constraint.
- No context-dependent changes of surface form.
- No insertion, deletion, or reordering of words.
- Initially assume one Voynich word corresponds to one Latin word.
- Penalize excessive many-to-one collapsing without prohibiting it.

Example:

    V1 → terra   → lemma: terra
    V2 → terram  → lemma: terra
    V3 → terrae  → lemma: terra
    V4 → est     → lemma: esse
    V5 → sunt    → lemma: esse

The mapping is deterministic at the surface-form level, not merely the lemma level.

Unknown Voynich words may receive an explicit UNKNOWN assignment during partial-dictionary optimization.

## Hierarchical Mapping Representation

Represent each assignment internally as:

    Voynich word
        → Latin surface form
        → possible Latin lemmas
        → possible morphological features

The surface form is authoritative.

Lemma and morphological information are supporting metadata, not permission to change the output according to context.

For ambiguous Latin forms, retain all valid analyses.

Example:

    V1 → terrae

Possible analyses include:

    terra, genitive singular
    terra, dative singular
    terra, nominative plural

The scorer may use grammatical context to evaluate these analyses, but the output must remain `terrae`.

## Language Models

### 1. Surface-Form N-Gram Model — Primary Optimizer

Train word-level unigram, bigram, and trigram models on actual Latin surface-form sequences.

Prefer medieval Latin while retaining classical Latin as a baseline.

Requirements:

- Smoothed conditional probabilities.
- Efficient incremental scoring.
- Cached occurrence positions for each Voynich word.
- Local recomputation after mapping mutations.
- Explicit sentence and source boundaries.
- Configurable vocabulary cutoffs.
- Robust treatment of rare Latin inflections.
- Millions of mutation evaluations per experiment.

Example:

    in terra est

should score differently from:

    in terram est

Unlike lemma-only scoring, the model can exploit Latin case, number, person, and tense patterns.

Use a configurable mixture of bigram and trigram likelihoods.

Avoid allowing unigram frequency alone to dominate the objective.

### 2. Pretrained Latin Transformer — Neural Reranking

Investigate:

- Latin BERT:
  https://huggingface.co/latincy/latin-bert
- Cicero:
  https://huggingface.co/gmmeyer/cicero
- HPLT Latin GPT-BERT:
  https://huggingface.co/HPLT/hplt_gpt_bert_base_4_0_lat_Latn

Verify model availability, architecture, tokenizer, licensing, and scoring support before integration.

Prefer locally executable models.

Because this experiment produces actual Latin surface forms, pretrained models can evaluate candidates without converting them into lemmatized text.

Scoring:

- Masked models: pseudo-log-likelihood.
- Autoregressive models: next-token log-likelihood.
- Normalize scores appropriately.
- Use the same candidate passages for fair comparisons.
- Measure whether neural reranking improves synthetic recovery accuracy.

Retain the top N distinct candidate mappings, configurable between approximately 100 and 1000.

Neural reranking must not silently alter mappings or regenerate Latin passages.

### 3. Morphological and Syntactic Scoring

Surface-form mapping allows direct grammatical evaluation.

Potential signals:

- Case agreement.
- Noun/adjective gender and number agreement.
- Subject/verb agreement.
- Preposition case requirements.
- Verb argument structure.
- Plausible inflection sequences.

Initially implement morphology as an optional scorer.

Do not require a full Latin parser for the MVP.

Do not assume every grammatical sentence can be identified through local agreement rules.

Morphological ambiguity must be handled explicitly.

## Optimization

Use discrete dictionary optimization.

Candidate algorithms:

1. Simulated annealing with multiple restarts.
2. Parallel tempering.
3. Genetic algorithms with collocation-preserving crossover.
4. Hybrid collocation-aware optimization.

Implement simulated annealing first.

### Two-Stage Search

#### Stage 1 — Lemma-Aware Initialization

Reduce the search space by proposing candidate Latin lemmas using:

- Latin lemma frequencies.
- Voynich word frequencies.
- Co-occurrence patterns.
- Latin lemma collocations.
- Approximate graph alignment.

This stage produces candidate lemma assignments or ranked candidate sets.

It does not need to finalize the mapping.

#### Stage 2 — Surface-Form Optimization

Expand candidate lemmas into their attested inflected forms.

Optimize the actual Voynich-to-Latin-surface-form dictionary.

For example:

    V1 → terra

Candidate refinements:

    terra
    terram
    terrae
    terrarum
    terris

The surface-form optimizer uses actual Latin n-gram probabilities.

Allow mutations to change both lemma and surface form.

Do not permanently lock lemma assignments from Stage 1; incorrect lemma initialization must remain recoverable.

Maintain multiple diverse initial mappings to avoid prematurely discarding correct candidates.

### Objective Function

For MVP:

    score =
        Latin_surface_ngram_log_likelihood
      - λ * mapping_complexity

Optional extensions:

    score =
        α * surface_ngram_likelihood
      + β * morphological_plausibility
      + γ * neural_language_score
      + δ * lemma_structure_prior
      - λ * mapping_complexity

Mapping consistency is always enforced as a hard constraint.

Avoid double-counting closely correlated language-model and grammatical signals without calibration.

### Mutation Operators

Implement:

- Replace one Latin surface form.
- Swap surface forms between two Voynich words.
- Change inflection while retaining the lemma.
- Change lemma and choose a corresponding surface form.
- Jointly replace assignments for frequent Voynich bigrams/trigrams.
- Reassign groups based on co-occurrence structure.

For example:

    V1 → terram

may mutate to:

    V1 → terra

without changing the lemma.

Or:

    V1 → aqua

changing the lemma entirely.

Use a mixture of local and larger mutations.

Track acceptance rates, mapping stability, and mutation-specific score improvements.

### Incremental Evaluation

Precompute token positions and affected n-gram windows.

Changing one Voynich word's assignment must only trigger recomputation of affected n-grams.

Test incremental scoring against full recomputation.

Profile mutation throughput.

## Search-Space Reduction

1. Start with the 100–300 most frequent Voynich words.
2. Build a frequency-ranked Latin lemma vocabulary.
3. Expand lemmas into attested surface forms.
4. Use Latin morphological inventories to group related candidates.
5. Initialize using lemma-level co-occurrence statistics.
6. Optimize surface-form assignments.
7. Progressively expand the Voynich vocabulary.
8. Preserve multiple diverse candidate dictionaries.

Use frequency as a soft prior rather than a hard matching rule.

Do not prohibit rare Latin forms, but avoid allocating excessive search effort to them initially.

## Validation

### Synthetic Word-Cipher Recovery

Generate deterministic word-level substitutions from authentic Latin surface-form sequences.

Include:

- One-to-one word substitution.
- Many-to-one word substitution.
- Homophonic encodings.
- Morphologically related ciphertext variants.
- Frequency-distorting substitutions.

Preserve the original plaintext for evaluation only.

Measure:

- Exact surface-form recovery accuracy.
- Lemma recovery accuracy.
- Token-weighted accuracy.
- Morphological-feature accuracy where unambiguous.
- Held-out language likelihood.
- Semantic similarity as a secondary measure.

Exact word accuracy and lemma accuracy must be reported separately.

Semantic similarity is not sufficient evidence of recovery.

### Negative Controls

- Shuffle Voynich tokens while preserving unigram frequencies.
- Generate controls preserving selected bigram and positional properties.
- Include structured non-Latin text.
- Include artificial text with Voynich-like repetition patterns.
- Apply identical optimization budgets.

Compare best fitness distributions over multiple independent runs.

Avoid trivially distinguishable controls.

### Cross-Folio Generalization

- Train on selected folios.
- Freeze the complete surface-form dictionary.
- Evaluate unseen folios without reoptimization.
- Report known-word coverage.
- Report language-model likelihood on covered text.
- Preserve UNKNOWN boundaries rather than joining unrelated known words.
- Test Currier A and B separately and across each other.

Do not allow the scorer to choose different inflections for the same Voynich word on held-out pages.

### Cipher Reconstruction

For promising mappings:

- Compare Voynich spelling patterns with Latin surface forms.
- Examine whether similar Voynich words correspond to inflections of one Latin lemma.
- Search for prefix/suffix correspondences.
- Investigate substitutions, abbreviations, nulls, and homophones.
- Attempt to derive a compact encoding mechanism.
- Test whether that mechanism predicts previously unseen word correspondences.

A consistent surface-form mapping provides additional opportunities to recover morphological encoding rules.

## Comparative Experiment

The word-to-word and word-to-lemma approaches should share:

- Voynich corpus splits.
- Latin source splits.
- Synthetic plaintext passages.
- Random seeds where applicable.
- Negative controls.
- Computational budgets.
- Evaluation metrics.

Compare:

| Metric | Word-to-Lemma | Word-to-Word |
|---|---|---|
| Lemma recovery | Primary | Secondary |
| Surface-form recovery | Not directly applicable | Primary |
| Grammatical coherence | Limited | Directly measurable |
| Search complexity | Lower | Higher |
| Neural-model compatibility | Requires adaptation | Direct |
| Morphological evidence | Indirect | Direct |

Determine whether surface-form constraints improve recovery enough to compensate for the larger search space.

## Success Criteria

A promising candidate must:

1. Produce coherent Latin across multiple folios.
2. Maintain globally consistent surface-form mappings.
3. Generalize to unseen folios without refitting.
4. Significantly outperform matched negative controls.
5. Demonstrate recovery capability on synthetic ciphers.
6. Preferably expose a compact, independently testable encoding mechanism.

Do not treat fluent Latin alone as decipherment.

## Implementation Stack

- Python 3.12+
- NumPy / SciPy
- Numba for high-throughput scoring
- PyTorch / Hugging Face Transformers
- Existing Latin morphological resources
- SQLite or Parquet for experiment records
- pytest for testing

Prefer CPU-efficient optimization and local neural inference.

Use Rust only if profiling demonstrates a substantial bottleneck.

## MVP Deliverables

- [x] Reuse the existing Voynich transcription and metadata loaders.
- [x] Build a versioned Latin surface-form corpus.
- [x] Build Latin surface-form unigram/bigram/trigram models.
- [x] Create surface-form-to-lemma and morphology lookup tables (resource lemma IDs; display headwords remain unset).
- [x] Implement deterministic many-to-one word mapping.
- [x] Implement incremental n-gram scoring.
- [x] Implement simulated annealing with configurable mutations.
- [x] Add lemma-aware candidate initialization.
- [x] Add inflection-preserving and lemma-changing mutations.
- [x] Implement synthetic word-cipher recovery benchmarks (initial fixture families and development pilot).
- [ ] Implement negative controls (three word surrogates implemented; non-Latin and repetition-generator families remain).
- [ ] Implement cross-folio validation.
- [x] Export dictionaries with surface forms, lemmas, and morphology.
- [x] Add reproducible checkpoints and experiment logging.
- [ ] Benchmark against the word-to-lemma approach.

## Phase 2

- [ ] Benchmark pretrained Latin transformers on surface-form sequences.
- [ ] Integrate neural reranking.
- [ ] Add morphological agreement scoring.
- [ ] Experiment with parallel tempering.
- [ ] Experiment with genetic algorithms.
- [ ] Implement collocation-aware joint mutations.
- [ ] Investigate Voynich spelling similarity versus Latin inflectional relationships.
- [ ] Attempt systematic cipher reconstruction from promising mappings.

## Engineering Requirements

- Keep scorers, optimizers, corpora, and mappings modular.
- Reuse existing project infrastructure.
- Avoid duplicating source corpora.
- Record normalization and model versions.
- Preserve training/evaluation isolation.
- Support reproducible random seeds.
- Support checkpoint/resume.
- Test incremental scores against full recomputation.
- Benchmark runtime and recovery accuracy.
- Preserve all candidate mappings needed for independent validation.

## Research Principle

**Optimize globally consistent Latin surface-form mappings, using lemma structure to reduce search complexity without discarding grammatical evidence.**

The central question is whether the additional constraints supplied by Latin inflection improve genuine recovery and cross-folio generalization, rather than merely increasing apparent fluency or optimization cost.

## Morphology-tolerant calibration

See [large dictionary and independent scorer results](../word_mapping_large_dictionary.md).
A 100,000-form inventory and an independent morphological sequence scorer are
implemented. Compatible controls tie truth and broad corruptions score worse;
local counterexamples, search integration, and a whole-work benchmark with
external training remain before a whole-Caesar recovery attempt.

The [function-anchor recovery experiment](../word_mapping_anchor_recovery.md)
adds 24 actual searches and full proposal replay. Correct function mappings alone
do not enable recovery under the current sequence objective; unknown-state
exploitation and relational grammatical scoring remain unresolved.

The [repeated cloze experiment](../word_mapping_repeated_cloze.md) tests neural
proposals over 100,000 forms, all target occurrences, incomplete-context controls
and a joint injective assignment. Partial proposal quality improves, but lexical
recovery remains insufficient for a whole-work search.

The [repeated-mask fine-tuning and context curve](../word_mapping_cloze_finetune.md)
pilot is implemented. Held-out masking loss improves, but lexical retrieval does
not improve consistently: function-only top-10 goes from 3/22 to 4/22 while
top-1 drops to zero, and 50%-content top-10 falls from 12/22 to 7/22.
The original model is retained; this does not justify a longer tuned-model search.

The [repeat-identity pilot](../word_mapping_repeat_identity.md) adds randomized
anonymous hidden-type embeddings, matched collapsed-mask training, repetition-
enriched examples and broken-identity/permutation controls. Lexical top-10 ties
at 0% and 50% supplied content; the 25% one-type advantage disappears under fresh
identifier permutations. Direct candidate-ranking training remains a separate,
unimplemented experiment.

The [oracle grammar diagnostic](../word_mapping_grammar_oracle.md) measures exact
identity to avoid circular compatibility success. Full-analysis intersection
narrows median candidate pools to 565.5 and raises frequency top-ten from 3/22 to
17/22. Full and coarse local grammar predictors, trained on disjoint text, do not
recover that gain. Global agreement/role inference remains unimplemented.
