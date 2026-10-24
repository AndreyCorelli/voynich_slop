# Voynich Decipherment via Constrained Optimization

## Goal

Build an experimental system that searches for coherent Latin interpretations of the Voynich manuscript using globally consistent word mappings and statistical language models.

Exact plaintext recovery is not required initially. Semantic approximations (e.g., garlic → onion, lance → spear) are acceptable if the resulting text is coherent and the mapping remains consistent.

A promising interpretation should eventually enable reconstruction of the underlying cipher or encoding mechanism.

## Core Hypothesis

Correct word assignments reinforce one another through recurring collocations and grammatical patterns.

Even a small number of correct assignments may improve the objective function sufficiently to guide optimization through an otherwise enormous search space.

## Existing Project Sources and Reusable Resources

Start from the cached, provenance-tracked sources below rather than downloading
another copy. Paths are relative links from this document. Original downloads
have manifests; generated datasets retain normalization settings and hashes.
These resources exist locally, but **they are not already a lemmatized Latin
training corpus**. Preserve source boundaries and create a separate, versioned
lemmatization artifact for this experiment.

### Voynich Transcription and Metadata

- [Processed ZL EVA corpus](../../data/processed/zl-eva.json), with
  [original IVTFF transcription](../../data/raw/ZL3b-n.txt) and
  [source manifest](../../data/raw/ZL3b-n.txt.manifest.json).
- [Corpus ingestion and normalization guide](../corpus_milestone.md) describes
  acquisition, annotation handling, uncertain spaces, sampling and provenance.
- Reuse the [IVTFF parser](../../src/voynich_smt/data/voynich.py) and
  [Corpus loader/sampling API](../../src/voynich_smt/data/corpus.py). Records
  retain folio, locus, section (`$I`), Currier class (`page_variables['L']`),
  original word position and exclusion/uncertainty flags. Currier labels are not
  available for every page; do not infer missing labels from the text.
- [Atomic/grouped EVA sensitivity](../eva_tokenization.md),
  [A/B structural census](../currier_structural_constraints.md) and
  [section/line-position matching](../currier_section_position.md) provide
  counting and filtering baselines. Freeze a convention for training/evaluation;
  section overlap is uneven, and matched herbal results do not cover all B pages.

### Latin Texts for Language-Model Training

| Resource | Local source / extraction | Suggested use |
| --- | --- | --- |
| Caesar, *De bello Gallico* I–IV | [Corrected parser-v2 corpus](../../data/processed/caesar-latin-v2.json), [original text](../../data/raw/pg218.txt), [manifest](../../data/raw/pg218.txt.manifest.json) | Initial reproducible classical-Latin baseline; retain the version distinction from the earlier corpus |
| Aquinas, *De ente et essentia*; *Vita Caroli IV* | [Historical source cache](../../data/raw/historical-lengths/), [extraction functions](../../benchmarks/historical_word_lengths.py), [source/normalization report](../historical_word_lengths.md) | Medieval prose with historical spellings retained |
| Einhard, *Vita Karoli Magni*; *Gesta Francorum*; Bury, *Philobiblon*; Dante, *Monarchia* | [Expanded medieval-Latin source catalog and loader](../../benchmarks/expanded_medieval_latin.py), original files/manifests in the historical source cache | Cross-author/genre evaluation; do not treat all works as interchangeable prose |
| Existing extracted Latin/German streams | [Prepared source bundle](../../experiments/results/contraction-distribution-audit/prepared.json) | Reuse `sources[*].segments` and metadata; `None` entries are barriers, not words to remove and join across |
| Thematic Latin comparanda | [Extracted texts and counts](../../data/processed/historical-comparanda/), [word-frequency notes](../research/word_frequences.md), [audited thematic passages](../research/thematic_latin_passages.md) | Grosseteste and Manilius as genre sensitivities; the Emerald Tablet is too small for a primary language model |

The frequency notes link original providers and editions. Their counts preserve
word forms and inflection, with no lemmatization. The original **Turba** extraction
mixes Latin and English and is quarantined; do not use it as a Latin prior. The
English *Mirror of Alchemy* and Greek *Tetrabiblos* are separate comparanda.
Existing Latin pipelines differ in u/v and j/i handling: select and record one
policy, retain original surface forms, and keep lemmatizer failures/ambiguities
explicit. The downloaded texts are not abbreviation-faithful manuscript editions.

### Frequency, Context and Morphology Baselines

- [Latin unigram ranking](../latin_frequency_ranking.md) and its
  [implementation](../../benchmarks/latin_frequency_ranking.py) provide an existing
  smoothed frequency baseline and frozen source/evaluation separation.
- [Adjacent-word context ranking](../contraction_context_ranking.md) and its
  [implementation](../../benchmarks/contraction_context_ranking.py) show how to
  count context without crossing discarded-token barriers. These are surface-form
  scorers, not the proposed lemma bigram/trigram optimizer; they produced no
  added recovery benefit in their tested candidate pools.
- [Latin morphology/form-inventory report](../latin_form_inventory.md) documents
  the pinned morphological resource and canonical spelling assumptions. Generated
  forms are not attested prose or gold lemma annotations; a lemmatization pipeline
  still needs ambiguity handling and validation.
- [Historical frequency extractor](../../benchmarks/historical_word_frequencies.py)
  can reproduce the thematic counts, but its extracted text must be audited for
  boundaries before training n-grams. A top-word table is not a sequence corpus.

### Synthetic Fixtures, Controls and Prior Findings

- [Contraction recovery/coverage fixtures](../contraction_coverage_calibration.md)
  and [frozen-key holdout tests](../frozen_key_holdout.md) supply examples of
  truth/public-input separation and continuation evaluation. They test character
  codes, not this proposed word-to-lemma mapping; build dedicated word-substitution
  fixtures rather than treating existing SAT keys as successful lemma recovery.
- [Structured negative controls](../structured_negative_controls.md) preserve
  lengths, repetitions and selected local glyph structure. See their
  [implementation](../../benchmarks/structured_negative_controls.py). A structural
  corruption is not automatically a model-impossible negative.
- [Text-generation comparison](../text_generation_comparison.md),
  [synthetic discrimination](../currier_mechanism_discrimination.md) and
  [cross-source transfer audit](../currier_mechanism_transfer.md) provide additional
  controls and examples of held-out scoring. Same-source accuracy did not ensure
  source transfer or reliable rejection of unfamiliar mechanisms.
- Use [German historical comparanda](../historical_word_lengths.md) as a non-Latin
  control source, retaining edition/normalization metadata and the
  [regional parsing audit](../german_regional_audit.md). They are individual source
  witnesses, not exhaustive language models.
- Consult the [structural coverage map](../approach_coverage.md) before reusing an
  experiment: corpus availability, assisted recovery, plausible statistics and
  successful decipherment are different evidence levels.

For the MVP, reuse the Voynich loader, choose one attested Latin training text
and a different author for evaluation, create a versioned lemma stream, and
build dedicated deterministic word-cipher positives plus matched controls.
Hash the source, normalization, lemmatizer version, splits and generating mapping.
Split Latin passages before fitting the n-gram model or neural reranker, and
keep plaintext used for synthetic evaluation out of their training data.

## Mapping Constraints

Define a deterministic, many-to-one mapping:

    f: Voynich word → Latin lemma

Rules:

- Every Voynich word maps to exactly one Latin lemma globally.
- Different Voynich words may map to the same Latin lemma.
- Latin morphological variations are permitted, but lemma identity must remain fixed.
- Mapping rules must remain consistent across folios.
- Penalize excessive many-to-one collapsing.
- Initially assume Voynich word boundaries correspond to Latin word boundaries.
- Do not allow context-dependent reinterpretation of Voynich words.
- Do not insert, remove, or reorder words during scoring.

Unmapped vocabulary may be represented by an explicit unknown token during partial-dictionary optimization.

## Language Models

Use two levels of language scoring.

### 1. Fast Statistical Model (Primary Optimizer)

Train word-level bigram and trigram models on lemmatized Latin texts, preferably including medieval Latin.

Requirements:

- Estimate smoothed conditional word probabilities.
- Support efficient incremental scoring.
- Cache affected token positions for each Voynich word.
- Recalculate only affected n-grams after a dictionary mutation.
- Support millions of candidate mutations.

This is the primary fitness function during optimization.

### 2. Pretrained Neural Model (Reranking)

Investigate publicly available Latin transformers:

- Latin BERT: https://huggingface.co/latincy/latin-bert
- Cicero: https://huggingface.co/gmmeyer/cicero
- HPLT Latin GPT-BERT: https://huggingface.co/HPLT/hplt_gpt_bert_base_4_0_lat_Latn

Prefer models that can run locally on a MacBook.

Latin BERT is a masked language model; evaluate candidates using pseudo-log-likelihood.

Autoregressive models can use next-token log-likelihood directly.

Important considerations:

- Pretrained models generally expect inflected Latin, not lemma sequences.
- Test their ability to distinguish coherent from incoherent lemmatized Latin.
- Compare neural rankings against the statistical n-gram baseline.
- If necessary, fine-tune a small model on lemmatized Latin.
- Do not assume that a pretrained model's score is a reliable semantic-coherence measure.
- Normalize scores appropriately for sequence length.
- Use neural scoring only for promising candidates, not every mutation.

Initially, retain the top N distinct mappings (configurable, e.g., 100–1000) for neural reranking.

### Future: Morphology and Syntax

Introduce grammatical validation after establishing the baseline.

Given a fixed lemma sequence, determine whether plausible Latin inflections exist without changing lemma identities or word order.

Evaluate case agreement, verb agreement, preposition requirements, and other grammatical constraints.

Do not introduce arbitrary words to improve grammaticality.

## Optimization

Optimize the discrete Voynich-to-Latin dictionary rather than generating translations with an LLM.

Candidate algorithms:

1. Simulated annealing with multiple random restarts.
2. Parallel tempering.
3. Genetic algorithms with collocation-preserving crossover.
4. Hybrid search using joint bigram/trigram assignments.

Implement simulated annealing first.

Keep the optimizer interface extensible so alternative algorithms can be benchmarked under identical conditions.

### Objective Function

Use a configurable score:

    score =
        α * Latin_ngram_log_likelihood
      + β * morphological_plausibility
      + γ * neural_language_score
      - λ * mapping_complexity

For MVP:

    score =
        Latin_ngram_log_likelihood
      - λ * mapping_complexity

Mapping consistency is a hard constraint, not a scoring bonus.

Mapping complexity should discourage degenerate many-to-one solutions without prohibiting legitimate homophones or synonymous mappings.

Use corpus-level statistics and explicit regularization rather than arbitrary dictionary-size restrictions.

### Mutation Operators

Implement:

- Replace one Voynich word's assigned Latin lemma.
- Swap two assigned lemmas.
- Jointly modify mappings for frequent Voynich bigrams/trigrams.
- Reassign groups of words based on co-occurrence structure.

Track acceptance rates, score progression, and mapping stability.

## Search-Space Reduction

1. Begin with the 100–300 most frequent Voynich words.
2. Construct candidate Latin lemma sets using corpus frequencies.
3. Analyze Voynich and Latin word co-occurrence graphs.
4. Investigate approximate graph alignment for dictionary initialization.
5. Optimize frequent words first.
6. Progressively expand the mapped vocabulary.
7. Add morphology and neural scoring only after the statistical baseline works.

Frequency matching should be a soft prior, not a hard constraint.

## Validation

Fluent Latin alone is insufficient evidence of decipherment.

### Synthetic Cipher Recovery

- Collect authentic Latin texts, preferably medieval.
- Lemmatize them using a consistent preprocessing pipeline.
- Encrypt them using deterministic word substitutions.
- Test increasingly complex schemes, including homophones and morphological variants.
- Measure dictionary recovery accuracy, lemma accuracy, and semantic similarity.
- Evaluate recovery on held-out passages.

Synthetic tests must include both simple and difficult ciphers.

### Negative Controls

- Shuffle Voynich tokens while preserving unigram frequencies.
- Generate synthetic texts preserving selected bigram or positional statistics.
- Compare against non-Latin texts and other structured artificial corpora.
- Apply identical optimization budgets and scoring procedures.
- Compare distributions of best fitness scores across independent runs.

Avoid controls that are trivially distinguishable from Voynichese.

### Cross-Folio Generalization

- Split folios into training and held-out sets.
- Learn mappings only on training folios.
- Freeze the dictionary before testing.
- Measure held-out vocabulary coverage and language-model likelihood.
- Evaluate Currier A and B separately and across each other.
- Do not assign new meanings to unseen words during evaluation.

Ensure that the Latin language model and any neural reranker are trained independently of the held-out Voynich evaluation.

### Cipher Reconstruction

For promising mappings:

- Analyze relationships between Voynich spellings and assigned Latin lemmas.
- Investigate recurring prefixes, suffixes, and character patterns.
- Search for systematic substitution or abbreviation rules.
- Consider homophones, null symbols, and morphological encodings.
- Prefer compact, reproducible encoding mechanisms over arbitrary word dictionaries.

A compact encoding mechanism that predicts previously unseen correspondences would provide particularly strong evidence.

## Success Criteria

A promising candidate must:

1. Produce coherent Latin across multiple folios.
2. Preserve globally consistent lemma assignments.
3. Generalize to held-out text without refitting.
4. Significantly outperform matched negative controls.
5. Preferably reveal a compact, independently testable encoding mechanism.

Assess statistical significance across multiple seeds and identical computational budgets.

Synthetic cipher recovery must be demonstrated before interpreting Voynich optimization results as evidence of decipherment.

## Implementation Stack

- Python 3.12+
- NumPy / SciPy for numerical operations
- Numba for incremental scoring and mutation evaluation
- PyTorch / Hugging Face Transformers for neural reranking
- Latin morphological tools and lemmatized corpora
- SQLite or Parquet for experiment results
- pytest for automated tests

Prefer CPU-efficient statistical optimization. Use Apple Silicon acceleration for neural inference where supported.

Do not introduce Rust unless profiling demonstrates a substantial bottleneck that Numba cannot address.

## MVP Deliverables

1. Voynich transcription loader with folio and Currier A/B metadata.
2. Latin corpus loader and lemmatization pipeline.
3. Latin word-frequency, bigram, and trigram models.
4. Deterministic many-to-one mapping representation.
5. Incremental scoring implementation.
6. Simulated annealing optimizer with configurable mutations.
7. Synthetic cipher generator and recovery benchmarks.
8. Shuffled and statistically matched negative controls.
9. Cross-folio evaluation.
10. Experiment logging, checkpoints, reproducible seeds, and progress visualization.
11. Export of candidate mappings and reconstructed Latin lemma sequences.

### Phase 2

1. Benchmark pretrained Latin transformers on lemmatized Latin.
2. Integrate neural reranking of candidate mappings.
3. Compare neural reranking against n-gram-only rankings.
4. Introduce morphological plausibility scoring.
5. Experiment with parallel tempering and genetic algorithms.
6. Investigate co-occurrence graph alignment and collocation-aware search.

## Engineering Requirements

- Modular interfaces for optimizers, scorers, corpora, and mapping constraints.
- Reproducible experiments with configurable random seeds.
- Checkpointing and resumption of long-running optimization.
- Efficient batch experiments.
- Profiling of mutation throughput and scoring bottlenecks.
- Automated tests comparing incremental scores against full recomputation.
- Explicit separation between training, validation, and held-out evaluation data.

## Research Principle

**Optimize for globally consistent, generalizable linguistic structure—not merely fluent output.**

The decisive experiment is whether authentic Voynich text supports a coherent Latin interpretation substantially better than statistically matched controls, and whether the resulting mapping exposes an independently verifiable encoding mechanism.
