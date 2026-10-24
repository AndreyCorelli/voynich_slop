# Surface word-dictionary implementation

The first five stages of the [implementation plan](todo/nn_w2w_implementation_plan.md)
are implemented in `src/voynich_smt/word_mapping/`: corpus adapters, ambiguous
morphology catalogs, candidate initialization, smoothed surface n-grams,
transactional incremental scoring and multi-restart simulated annealing.
Dedicated word-cipher fixtures, three matched surrogate controls, frozen
dictionary scoring and evaluation metrics are also available.

This implementation is independent of the existing Z3 character-code solvers.
It searches a dictionary of authoritative Latin surface forms; grammatical
analyses do not change the output form in context. UNKNOWN assignments belong
to inactive ciphertext types and cannot be introduced by a mutation.

## Running the pipeline

From the repository root:

```sh
uv sync --locked --extra word-mapping --group dev
.venv/bin/python -m benchmarks.word_mapping_foundation --medieval
.venv/bin/python -m benchmarks.word_mapping_foundation --validate
.venv/bin/python -m benchmarks.word_mapping_recovery --steps 2000 --restarts 2 --active-types 100 --controls
.venv/bin/python -m benchmarks.word_mapping_recovery --steps 2000 --restarts 2 --active-types 100 --validate
```

The foundation defaults to a 2,000-word Caesar prefix, finishing the final
sentence, with contiguous complete-segment 70/15/15 train/development/test
splits. Those proportions describe segment counts, not exact token counts.
`--medieval` exports six cached medieval works for subsequent cross-source
experiments; it does not silently include their text in the Caesar baseline LM.
Use `--max-words` and a new `--out` directory for a larger foundation dataset.

The recovery runner supports `--kind one-to-one`, `homophonic`,
`frequency-distorting` and `lossy`, plus seeds, budgets, active vocabulary size
and `--collapse-weight`. Give independent experiments different output paths.
Use `--resume` to continue a checkpoint; validation arguments must match its
search configuration. Checkpoints reject changed code, model, candidates,
public-input identity, configuration or Python version.

Checkpoints preserve RNG state, restart/temperature progress, score caches,
dictionary state, mutation statistics and a diverse candidate archive. Default
archive capacity is 100; `SearchConfig` exposes capacity, minimum dictionary
distance and mutation weights. Atomic checkpoint writes preserve the prior
complete file if an interrupted write fails.

## Corpus and scoring contracts

- Raw Latin spelling and offsets survive in the corpus adapter. Scoring folds
  lowercase/j→i/v→u/diacritics explicitly; cached historical spelling cannot be
  reconstructed if an upstream extraction already discarded it.
- Caesar sentence/paragraph breaks are recovered conservatively from raw offsets.
  Historical flat streams retain source and exclusion barriers and explicitly
  record that sentence boundaries are unavailable.
- Voynich folio/locus, original positions, uncertainty and exclusion annotations,
  section and original Currier metadata survive. Missing Currier labels stay
  missing. Locus boundaries are layout boundaries; crossing them is configurable.
- None/UNKNOWN breaks a decoded run; a nonempty run receives two BOS contexts
  and one scored EOS. Latin vocabulary OOV is a separate predicted class.
- N-grams use an additive-smoothed unigram prior and bigram/trigram context
  backoff. The configured mixture combines conditional probabilities before
  taking logs. Default bigram/trigram mixture is 50/50.
- Reported per-token likelihood includes EOS in its numerator and covered word
  tokens in its denominator. Prediction-event count is separately available.
  Compare coverage and boundary policies alongside likelihood.
- Search maximizes summed log likelihood minus a configurable extra-assignment
  collapse penalty. Frequency priors enter initialization, not a hard frequency
  matching rule. Unrestricted replacements keep every frozen form reachable.
- Whitaker resource lexeme IDs identify lemma groups. Display headwords are
  deliberately unset because its roots are stems. All inflections/analyses are
  retained; unrecognized attested forms remain candidates. Unique entries using
  upstream ID zero receive separate identities rather than being merged.

`IncrementalScorer.propose` computes the union of affected n-gram windows without
changing state. `commit` applies an accepted proposal; ignoring it rejects the
proposal. Repeated occurrences, adjacent identical words and swaps do not double
count windows. This reference backend uses bounded log-probability caching.
Numba is installed, but no accelerated kernel is enabled yet.

## Artifacts and initial measurements

Local artifacts are under `experiments/results/word-mapping/` and follow the
repository's existing ignored-results convention. The verified run is in
`foundation/` and `recovery-validated/` (the latter uses the commands above with
`--out experiments/results/word-mapping/recovery-validated`).

The foundation exports 20,484 accepted Caesar tokens, 37,608 Voynich words,
and the six cached medieval streams. Its small training split contains 761
candidate forms, including 130 unrecognized by the default morphology mode.
Candidate coverage of its 383-token test plaintext is 50.65%. Annotation
failures do not remove forms or inflate that coverage.

The pilot optimizes 100 ciphertext types with two 2,000-mutation restarts,
retaining 100 candidate dictionaries. The original and three refitted controls
each receive 4,000 evaluations. Python reference search processes approximately
3,800 evaluations/second on this local sample, including archives and periodic
checkpoints; this is not a full-manuscript throughput measurement.

The original objective improves from -2,196.60 to -1,624.74, but exact plaintext
recovery is only 3/383 tokens (0.78%), with 54.83% active-token coverage. The
within-segment and position shuffles achieve higher best scores than the
original. This pilot therefore fails to establish recovery or control separation.
More fluent or higher-scoring passages are not a successful decipherment result.
Do not launch manuscript inference from this pilot.

The lossy fixture merges distinct plaintext forms into one ciphertext type and
reports its oracle deterministic-decoding accuracy ceiling. It is an explicit
out-of-model stress test. Homophonic fixtures instead preserve deterministic
decoding while permitting several ciphertext types per Latin form.

## Validation

```sh
.venv/bin/python -m pytest tests/unit/test_word_mapping_foundation.py tests/unit/test_word_mapping_search.py tests/integration/test_word_mapping_pipeline.py -q
```

All 38 new tests pass. They include hand-calculated probabilities, randomized
normalized distributions, 1,500 transactional mutation trials against full
recomputation, UNKNOWN/source barriers, truth isolation, morphology ambiguity,
control invariants, archive identity and exact checkpoint-resume equivalence.
An identifiable four-form instrument cipher recovers exactly; that test trains
on its instrument text and is not a held-out natural-prose calibration.

The existing broader suite requires this invocation because of duplicate test
filenames and an integration test's direct sibling import:

```sh
PYTHONPATH=src:tests/integration .venv/bin/python -m pytest --import-mode=importlib -q
```

The broader run, before the search tests were added, yielded 990 passes and
three failures caused by a stale `guided-model-calibration/prepared.json` identity.
Those three tests pass with a fresh isolated output directory; the existing
experiment artifact was preserved.

## Remaining gates

The [fully covered large-budget calibration](word_mapping_full_coverage.md)
adds whole-segment screening and deterministic parallel searches with all types active.
The [frequency and constraint refinement](word_mapping_objective_refinement.md)
adds an optional decoded-frequency prior and explicit one-to-one constraint.
The [larger-bundle and local-objective calibration](word_mapping_long_context.md)
uses disjoint Caesar books and exhaustively audits replacements and swaps around truth.
The [offline neural scorer probe](word_mapping_neural_probe.md) compares full-segment
Latin RoBERTa scores with short context on frozen n-gram counterexamples.

The [truth diagnostic and multi-seed ablation runner](word_mapping_ablation.md)
now implement development-only scorer/initialization/penalty and budget
comparisons. A preparation-only mode preserves a final-test split without
scoring it. These instruments do not by themselves pass the recovery gate.

Next implement milestone 6: larger training/candidate coverage audits,
fresh disjoint and cross-author recovery fixtures, independent seeds, calibrated
penalties/smoothing and a matched word-to-lemma optimizer baseline. Freeze
success thresholds on development cases before evaluating untouched fixtures.

The three existing controls are a starting set; non-Latin/repetition-generator
controls and independent fitted fitness distributions remain necessary. Full
folio/Currier split orchestration and manuscript campaigns remain behind the
recovery gate. A [bounded neural archive reranking experiment](word_mapping_neural_rerank.md)
is implemented and validated; its development recovery remains unchanged.
A [diverse restart pool experiment](word_mapping_diverse_rerank.md) adds fresh
frequency, random and lemma-aware starts; neural reranking still misses the
modest recovery improvements in those pools.
A [matched candidate-pool size test](word_mapping_pool_size.md) finds limited
neural ranking gains in one development bundle; average recovery remains near 2.3%.
A [controlled neighbor-quality diagnostic](word_mapping_context_rank.md) finds
that neural word proposals need substantially better context than current saved
decodings provide; n-gram top-1 ranking remains stronger in these controls.
An [experimental bootstrap decoder](word_mapping_bootstrap.md) now implements
uncertain candidate proposals, soft morphological agreement and coordinated
dictionary moves. Its paired calibration remains below the recovery gate.
A [training-phrase proposal experiment and exhaustive small-case audit](word_mapping_phrase.md)
now compare objective quality, optimizer success and a larger fixed-objective budget.
Parallel tempering, richer phrase proposals and cipher reconstruction remain phase 2.

A [controlled widening experiment](word_mapping_widening.md) tests nested inputs
up to 32,004 words with fixed and scaled budgets, training-only and oracle-complete
candidate pools, and a frozen development holdout. Larger inputs improve frequency
initialization, but optimization remains below that starting recovery and wrong
mappings still outscore truth with scaled budgets.

A [zero-corruption oracle diagnostic](word_mapping_zero_corruption.md) starts
from the exact dictionary. Both annealing and strict greedy ascent move away
from truth; the greedy control isolates objective misranking from downhill
exploration. Oracle keys are confined to this explicit diagnostic.

## Morphology-tolerant objective experiments

The [structural oracle](word_mapping_structural_oracle.md) allows compatible
content-word substitutions while protecting fixed grammatical forms. The
[large dictionary and independent scorer experiment](word_mapping_large_dictionary.md)
builds 100,000 annotated candidate forms and tests a key-independent morphological
sequence model. Compatible controls tie truth; broad corruptions score worse,
but locally broken swaps still provide objective counterexamples. No whole-Caesar
recovery claim follows from these checks.

The [function-anchor recovery test](word_mapping_anchor_recovery.md) now runs
actual structural searches with supplied function mappings and paired unanchored
controls. Content compatibility remains low, including when unknown candidates
are forbidden. Saved excerpts distinguish supplied anchors from predictions.

The [repeated-word neural cloze probe](word_mapping_repeated_cloze.md) ranks
100,000 forms using correct function anchors and pooled occurrences. It supplies
some useful proposals, but much of the gain concerns grammatical glue words;
lexical top-10 coverage remains low. Jointly injective partial proposals and
word-by-word excerpts are saved.

The [repeated-mask partial fine-tuning pilot and context curve](word_mapping_cloze_finetune.md)
finds lower masking loss without consistent retrieval gains. The original model
is retained; supplying half the content mappings helps it substantially, but
bootstrapping those mappings remains unresolved.

The [repeat-aware input experiment](word_mapping_repeat_identity.md) compares
anonymous type embeddings with matched collapsed masks and broken identities.
Repeat-enriched training is tested, but the small retrieval difference disappears
under fresh anonymous identifier permutations. It does not justify a longer search.

The [oracle-morphology and grammar-inference diagnostic](word_mapping_grammar_oracle.md)
finds that supplied analyses improve exact frequency-ranked lexical top-ten
recovery from 3/22 to 17/22. Local inferred grammar does not reproduce the gain;
explicit joint grammatical constraints remain a separate experiment.
