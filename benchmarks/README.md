# Benchmarks

Run `uv run python benchmarks/recovery.py` from the repository root. Options:
`--seed`, `--timeout-ms`, and `--output`. The runner records deterministic
10/25/50-word known-plaintext recovery for all three implemented cipher families.
Results include machine details, versions, exact samples, bounds, solver runtime,
construction time, constraints, variables, statistics, and independent verification.
See `docs/milestone1.md` for the initial measurements and their limits.

Run `uv run python benchmarks/hidden_recovery.py` to test verbose homophones with
fully hidden plaintext on four- and 24-symbol alphabets, and known plaintext on
the 24-symbol alphabet. Defaults: seeds 7/17/1729, sizes 10/25/50, ten-second
solver timeout. Options also include `--profiles`, `--sizes`, `--seeds`,
`--representation`, `--artifact-dir`, and `--request` for truth-free replay.
Inputs and ground truth are separate; outputs are checkpointed after every run.
Exact-original matching is recorded only as a diagnostic, not the success criterion.

Run `uv run python benchmarks/staged_recovery.py` for the configuration-driven
staged comparison. It uses `experiments/configs/staged-recovery.json`: six stages,
three seeds, and sizes 5/10/25. The default representation is `finite`. Public inputs,
ground truth, and checkpointed results are stored separately. See
`docs/staged_recovery.md` for the algorithm, measurements, and reproduction commands.

Run `uv run python benchmarks/nulls_optimization.py` for bounded nulls and
complexity minimization: seeds 7/17/1729, sizes 5/10/25, and feasibility,
lexicographic, and weighted modes on identical ciphertexts. Public inputs and
truth are separate; results are checkpointed in
`experiments/results/nulls-optimization.json`. See
[nulls and optimization](../docs/nulls_optimization.md) for measurements and limits.

Run `uv run python benchmarks/corpus_comparison.py` after acquiring and normalizing
the initial corpora. It checkpoints a synthetic recovery gate, a five-word f1r
Voynich sample, and five controls under shared public language/cipher bounds. See
[the corpus pilot](../docs/corpus_milestone.md) for its narrow scope and matching rules.

Run `uv run python benchmarks/latin_frontier.py` for one-dimension vocabulary and
cipher relaxations with paired free/cyclic selection, three synthetic seeds, and
two matched shuffles. The alternate `latin-frontier-lexical.json` configuration
filters single-letter initials. Use `--stages` or `--resume` for checkpointed work.
See [the frontier report](../docs/latin_frontier.md).

Run `uv run python benchmarks/sample_scaling.py` to vary only contiguous sample
size (5/10/25/50 words) under the fixed full-vocabulary H2/L2 cyclic model. It
selects a clean span long enough for every nested prefix, records exact locations,
and checkpoints each check. See [sample scaling](../docs/sample_scaling.md).

Run `uv run python benchmarks/unsat_boundary.py` to narrow the saved SAT–UNSAT
prefix interval, search a contiguous conflicting suffix and compare four single
setting changes. Use `--resume --budgets-ms 10000` to reuse checkpointed attempts.
Run `uv run python benchmarks/observation_core.py` to remove glyph observations
while retaining word lengths and cyclic context. See
[UNSAT diagnostics](../docs/unsat_boundary.md) for interpretation and masked replay.

Run `uv run python benchmarks/l3_conflict.py` to validate length-three coding on
synthetic controls, test the saved 11-word conflict and, if it fits, test the
23-word prefix. Configuration fixes H2/cycles/vocabulary and varies only maximum
code length in the hypothesis. Flat/trie retries change only the solver formula.
Use `--resume` for checked checkpoint reuse. See
[length-three coding](../docs/l3_conflict.md) for the witness and remaining limits.

Run `uv run python benchmarks/guided_extension.py` to extend the verified suffix
key across the full original prefix. It permits cycle rotations, extracts
per-letter pin cores and releases mappings using certified cycle/vocabulary
obstacles. Inputs are guided wrappers, replayed with `--replay`; `--resume`
checks source/configuration/environment identity. See
[guided extension](../docs/guided_extension.md) for conditional UNSAT semantics.

Run `.venv/bin/python -m benchmarks.learned_search` to search alternative suffix
keys under checked full-context exclusions. Core proofs are independently replayed;
timeouts never create exclusions. See [learned search](../docs/learned_search.md).

Run `.venv/bin/python -m benchmarks.learned_prefix` to check all 23 words with
all mappings free and the 19 proved exclusions. Its 120-second solver budget
excludes proof validation and formula construction, which are included in wall time.

Run `.venv/bin/python -m benchmarks.cycle_performance` for paired history/Boolean
H2 cycle calibration, full-vocabulary synthetic controls and the unchanged
23-word manuscript retry. Replay wrappers with this runner's `--replay` option.

Run `.venv/bin/python -m benchmarks.dictionary_selection` to compare bounded
entry selectors with the saved trie seed-7 controls. Replay its public wrappers
with the cycle-performance runner. See [dictionary selection](../docs/dictionary_selection.md).

Run `.venv/bin/python -m benchmarks.synthetic_prefix` for full-vocabulary seed-7
prefix calibration, or add `--resume` for checked checkpoint reuse. It attempts
all configured lengths after timeouts. Replay wrappers with cycle-performance.
See [synthetic prefixes](../docs/synthetic_prefix.md).

Run `.venv/bin/python -m benchmarks.segmentation_diagnostic` for paired fresh
four-word hidden and oracle-boundary solves. Use this dedicated runner's
`--replay` for its wrappers. See [boundary diagnostic](../docs/segmentation_diagnostic.md).

The same diagnostic runner accepts `word-length-diagnostic.json` for a fresh
three-way comparison: lengths only, exact boundaries, fully hidden. Use the
explicit output/artifact paths in [word-length diagnostics](../docs/word_length_diagnostic.md).

Run `.venv/bin/python -m benchmarks.length_search` for truth-free public length
branching on the four- and eleven-word controls. Branch replay uses the explicit
length wrapper with the segmentation-diagnostic runner. See [length search](../docs/length_search.md).

The intermediate length calibration has a separate configuration and result;
see the intermediate-control commands in the length-search documentation.
Run `.venv/bin/python -m benchmarks.solver_engines` to compare `qffd` and ordinary
SMT on the first stalled six-word branch. Replay with its dedicated `--replay`.

The length-search runner accepts optional `orderings` in configuration. Run the
separate `length-search-diverse.json` configuration as shown in
[diverse ordering](../docs/length_orderings.md) to preserve earlier reports.

Run `.venv/bin/python -m benchmarks.observed_codes` to test explicit substring
domains on the same hidden synthetic prefixes. Replay uses its dedicated runner;
unused mappings retain the freedom required by the original model.

`corpus_sequence_selection.py` prepares or runs a fixed four-case pilot using
reference-only vocabulary/bigram counts, disjoint projected Caesar evaluation
text, fresh synthetic keys and paired shuffles. `--run` allows at most three
five-second fits per case, checkpoints completed cases and selects keys using
training scores before evaluating continuation. See
`docs/corpus_sequence_selection.md` for the recorded zero-hit result and
codeword-coverage limitation.

`coverage_sequence_selection.py --run` runs the separate fixed coverage-control
pilot, preserving the prior corpus score. Coverage-conditioned projected Latin,
engineered training choices, paired shuffles and bounded key enumeration are
specified in `docs/coverage_sequence_selection.md`. Completed cases are preserved.

`generating_key_ranking.py` performs the fixed truth-assisted capacity check on
saved covered positives, with no solver calls. It appends the generating key,
uses unchanged training scores, then evaluates the frozen selections. See
`docs/generating_key_ranking.md` for scope, results and validation.

`guided_model_calibration.py` prepares or runs the fixed Latin/Swabian ×
letter/mixed generation × positive/shuffle matrix, fitting both recovery models
with ordinary and language-guided proposals. `--case ID` runs one ciphertext's
four arms; `--run-all` runs/resumes the fixed matrix. Each arm allows at most
three attempts and five seconds total solver time. Full scope and recorded
results are in `docs/guided_model_calibration.md`.

`feasible_sequence_search.py` compares ordinary enumeration with training-score
improvement inside shared-key feasibility search on one saved covered positive.
Each arm gets at most three checks and five seconds total solver allocation.
See `docs/feasible_sequence_search.md` for the negative result and stopping rule.

`structured_negative_controls.py --run` prepares/runs the fixed pair-chunk and
bigram-preserving controls with paired positive replays. One ordinary fit per
case receives five seconds; completed cases are preserved. See
`docs/structured_negative_controls.md` for invariants, the unavailable
construction, recorded separation and scope limits.

`single_code_baseline.py --run` compares H1 versus H2 variable-length expansion
under unchanged per-case dictionaries/contraction profiles, with four new
one-code positives and paired structural controls. Existing matching H2 fits
are reused after identity verification; new fits get five seconds each.
See `docs/single_code_baseline.md` for the flexibility trade-off and repeat limits.

`novel_word_holdout.py --run` performs the fixed three-type-disjoint H1/H2
prediction comparison under full generating-code coverage. Eight engineered
vocabulary positives have two recovery arms each, with one five-second fit per
arm. See `docs/novel_word_holdout.md` for selection, novel-word results and limits.

`fresh_voynich_screen.py --run` runs/resumes the fixed two-folio full-vocabulary
screen. All H1 checks precede H2, with one five-second check per real/control arm.
Selection and novelty are frozen before fitting; unavailable controls and
UNKNOWN outcomes are preserved. See `docs/fresh_voynich_screen.md` for the
zero-SAT result, construction overhead and limits.

`full_vocabulary_h1.py --run` compares matched reduced/full Latin H1 dictionary
recovery on the saved novel-word positive, with a completed full Latin alphabet,
one five-second fit per arm and no repeated finished outcomes. See
`docs/full_vocabulary_h1.md` for the reduced SAT/full UNKNOWN result and limits.

`full_vocabulary_h1_known.py` runs the single fixed plaintext-revealed diagnostic
on the preserved full-vocabulary H1 positive. Only training plaintext is given;
key, code lengths, segmentation and continuation remain hidden. Existing protocol
prevents reruns. See `docs/full_vocabulary_h1_known.md` for the 0.04-second SAT,
3/3 novel predictions and the oracle-information limitation.

`full_vocabulary_h1_lengths.py` supplies only per-word plaintext token counts
to the unchanged full-vocabulary H1 request, keeping identities and segmentation
hidden. One five-second fit; recorded SAT and 3/3 novel predictions are
oracle-assisted. See `docs/full_vocabulary_h1_lengths.md` for the ambiguity limits.

`full_vocabulary_h1_public_lengths.py` freezes three public midpoint-ranked length
vectors and shares five seconds of solver budget across observed-domain branches.
Its preserved result is SAT with 3/3 novel predictions. No truth enters proposals;
the rule was developed retrospectively on a fixed-length synthetic fixture.
See `docs/full_vocabulary_h1_public_lengths.md` for validation and limitations.

`public_length_calibration.py` compares the frozen midpoint heuristic and ordinary
observed-domain recovery on six new-key full-vocabulary Latin positives. Preparation
freezes seeds, profiles and schedules before fitting; `--run` resumes checkpointed
arms, and `--validate` checks preserved results without solving. Four midpoint
fits are SAT versus none ordinary, with only 1/12 exact novel predictions among
SAT fits. See `docs/public_length_calibration.md`.

`public_length_known_plaintext.py` reveals only training words on the four
preserved successful midpoint cases. Keys, code lengths, segmentation and
continuation remain hidden; each fit keeps the five-second budget. All four
reach SAT in 0.03–0.04 seconds and predict 3/3 novel words. Runs checkpoint and
skip completed cases; `--validate` verifies artifacts without refitting.
See `docs/public_length_known_plaintext.md` for the oracle and selection limits.

`public_length_key_uniqueness.py` adds one negated conjunction of the five
generating held-out-letter mappings to each known-training-word case. All four
checks are UNSAT, so those mappings are forced within the bounded oracle model.
No held-out ciphertext constraints enter the solver. Runs checkpoint; `--validate`
checks saved artifacts without solving. See `docs/public_length_key_uniqueness.md`.

`public_length_known_lengths.py` supplies only the correct training token counts
on four preserved public-midpoint SAT cases, retaining full dictionary search
and five-second budgets. All are SAT; novel prediction counts remain 0, 0, 0, 1.
It checkpoints and skips completed fits; `--validate` checks saved witnesses,
lengths, training matches and predictions. See `docs/public_length_known_lengths.md`.

`training_diversity.py` freezes corpus-order additions on two existing keys,
reuses nine-type baselines, and fits 18/36-type inputs with only lengths revealed.
Three of four new fits are SAT with all training words correct and 3/3 novel
predictions; the fourth is UNKNOWN. Construction costs dominate wall time.
Use `--run` to resume or `--validate` to verify artifacts without solving.
See `docs/training_diversity.md`.

`training_diversity_hidden.py` prepares two matched hidden-length fits on the
36-type positives. Use `--run` locally (construction may take minutes), then
`--validate`. It freezes source/code/baseline hashes, passes only original public
requests to observed-domain recovery, and checkpoints each completed fit. Both
actual fits are validated UNKNOWN (`timeout`); measured solver checks took
8.51/9.55 seconds under configured five-second timeouts. See `docs/training_diversity_hidden.md`.

`training_diversity_midpoint.py` applies the frozen public midpoint schedule to
the two 36-type inputs with a shared five-second solver timeout per case.
`midpoint_grouped.py` removes unequal repeat assignments while preserving the
original admissible-vector ordering. `--run` checkpoints schedules and fits;
`--validate` regenerates public schedules and checks witnesses/predictions.
Both actual runs are validated UNKNOWN; only their first branch ran. The
length-two vector matches the successful oracle control. See
`docs/training_diversity_midpoint.md`.

`prefix_pruning.py` compares indexed candidate-graph construction against the
preserved original pairwise implementation on both 36-type requests, without
SMT. Exact graphs match; measured speedups are 835× and 667×. It checkpoints
completed comparisons. `experiments/results/prefix-pruning/validate.py` validates
hashes and regenerated graph digests without rerunning the slow reference.
See `docs/prefix_pruning.md`.

`training_diversity_indexed.py` records fresh ordinary hidden fits after the
output-equivalent dictionary optimization. Both cases remain UNKNOWN, while full
construction falls to 53.64/62.80 seconds. It hashes the dictionary implementation
and preserves old comparison records; `--validate` verifies saved artifacts.
See `docs/training_diversity_indexed.md`.

`recovery_construction_profile.py` profiles each preserved hidden input only up
to its first Z3 check, leaving the check unprofiled. It saves `.prof` files and
JSON summaries, then independently verifies results. Both profiles attribute
about 93% of construction to flat dictionary membership. Use `--validate` to
check saved files without repeating fits. See `docs/recovery_construction_profile.md`.

`dictionary_equality_reuse.py` records fresh timings after caching repeated
slot/value and word-length equalities within flat membership calls. The preserved
reference encoding matches the earlier profile hash. Construction falls to
22.93/26.72 seconds; both checks remain UNKNOWN. `--validate` checks saved artifacts.
See `docs/dictionary_equality_reuse.md`.

`flat_trie_comparison.py` checks matched requests differing only in dictionary
encoding, reuses verified saved flat records, and runs two trie arms. All four
records are UNKNOWN; trie construction is slower in these measurements.
`--validate` verifies cached provenance and artifacts without solving.
See `docs/flat_trie_comparison.md` for the stopping condition and limitations.

`small_varied_length_controls.py` freezes seeds 4301/4302 across three genuinely
varied generating-code profiles, with twelve-word vocabulary and known/hidden-word
arms under equal five-second solver timeouts. All twelve fits are SAT; known
predictions are 18/18, hidden predictions 17/18. `--validate` checks saved witnesses,
coverage and frozen scoring without solving. See `docs/small_varied_length_controls.md`.

`varied_length_vocabulary_ladder.py` freezes nested corpus-order 64/256-word
dictionaries under the unchanged 14-letter alphabet, and reuses six 12-word
hidden baselines. Only dictionary changes. All 64-word fits are SAT (17/18 exact
holdout); 256 words yields four SAT with 4/12 exact and two UNKNOWN. `--validate`
checks selection, request matching, witnesses and frozen scoring without solving.
See `docs/varied_length_vocabulary_ladder.md`.

`varied_length_shuffle_controls.py` freezes two typewise glyph shuffles for each
64-word positive, reusing six saved positive records. All twelve controls are
UNSAT with lengths, per-word multisets and equality partition preserved.
`--validate` regenerates inputs and checks artifacts; post-solve public domains
remain nonempty. See `docs/varied_length_shuffle_controls.md` for limits.

`shuffle_vocabulary_expansion.py` changes only dictionary size on the twelve
preserved shuffles, reusing old controls and matching 256-word positive rows.
One control is SAT, two UNSAT and nine UNKNOWN; the SAT key predicts zero fully
decoded/dictionary holdout words. `--validate` checks exact inputs, cached pairs,
SAT witness and frozen scores. See `docs/shuffle_vocabulary_expansion.md`.

`natural_passage_calibration.py` freezes contiguous Caesar/Swabian passages,
assisted 64-word dictionaries, length-two/varied keys and paired shuffles.
All eight positive known/hidden arms are SAT with correct training and 6/6 novel
predictions; four shuffled controls are UNSAT. `--validate` reconstructs sources,
selection and frozen scores without solving. See `docs/natural_passage_calibration.md`.

`natural_passage_replication.py` freezes the next two eligible nonoverlapping
24+6-word passages after each original Latin/Swabian block, using the same assisted
64-word protocol and seeds. Eight hidden positives predict every held-out word;
eight known-word positives succeed and eight shuffles are UNSAT. `--run` resumes
completed arms; `--validate` reconstructs inputs, witnesses and frozen scores.
See `docs/natural_passage_replication.md`.

`natural_vocabulary_expansion.py` changes only the dictionary from 64 to 256
words on all sixteen frozen natural replication cases, retaining original
entries and appending eligible corpus words in source order. Eight positives
remain exact; seven shuffles are UNSAT and one is UNKNOWN under five-second
budgets. `--run` checkpoints/resumes; `--validate` checks nesting, unchanged inputs,
baseline matching, witnesses and frozen scores. See
`docs/natural_vocabulary_expansion.md`.

`natural_training_vocabulary.py` rebuilds the same passages' 256-word dictionaries
from training words and corpus-order additions, without reserving held-out words.
Eight positives predict 48/48 words, including 22/22 excluded occurrences;
eight shuffles are UNSAT. `--run` resumes; `--validate` reconstructs dictionaries,
coverage, unchanged inputs, witnesses and frozen included/excluded scores.
See `docs/natural_training_vocabulary.md`.

`training_vocabulary_ablation.py` deletes the first one/two distinct true training
types in passage order, without refilling dictionaries. Eight real fixtures are
UNSAT after one deletion; two deletions give seven UNSAT and one UNKNOWN. Sixteen
shuffles are UNSAT. `--run` checkpoints; `--validate` checks exact deletions,
unchanged inputs and scoring. A separate `monotonicity.json` records the nested
UNSAT implication for the timeout. See `docs/training_vocabulary_ablation.md`.

`one_oov_calibration.py` permits one actual out-of-dictionary training occurrence
on the sixteen frozen one-deletion requests. An isolated experimental builder
relaxes dictionary pruning and symbol restrictions as well as membership.
Three positives recover/predict correctly and five time out; controls yield
three UNSAT/five UNKNOWN. `--run` resumes; `--validate` verifies OOV budgets,
witnesses and frozen scores. See `docs/one_oov_calibration.md`.

`oov_type_calibration.py` compares one unknown occurrence versus one unknown type
on six existing 64-word synthetic fixtures after deleting repeated `et`, and six
unchanged seed-4401 shuffles. Type positives are SAT (14/18 held-out exact);
occurrence positives and both shuffle arms are UNSAT. `--run` resumes and
`--validate` verifies matched cases, actual budgets, witnesses and frozen scores.
See `docs/oov_type_calibration.md` for the deterministic H1 restriction and limits.

`second_key_agreement.py` excludes first-key mappings used in training and makes
one additional five-second solve per SAT case. All six second keys are SAT;
9/18 held-out words agree, of which eight are correct. Prior UNSAT shuffles are
retained as ineligible. `--run` resumes; `--validate` verifies exclusions,
distinct witnesses, frozen predictions and agreement. See
`docs/second_key_agreement.md`.

`length_frequency_baseline.py` compares fixed length/frequency guesses with saved
natural-strict, natural-one-occurrence and synthetic-one-type results, using no
new solver runs. Paired SAT scores are 2/48 versus 48/48, 0/18 versus 18/18, and
6/18 versus 14/18. UNKNOWN cases and control compatibility stay separate.
`--run` scores frozen guesses; `--validate` reconstructs predictions and scores.
See `docs/length_frequency_baseline.md` for baseline assistance and limits.

`one_oov_timeout_pair.py` replays the first frozen timed-out one-OOV positive and
its shuffle with only the solver budget changed to 60 seconds. Positive SAT
predicts 6/6, shuffle UNSAT; solver times approximately 5.0/5.5 seconds.
`--run` resumes and `--validate` checks timeout-only changes and frozen scores.
See `docs/one_oov_timeout_pair.md`.

`one_oov_timeout_remaining.py` replays all four remaining frozen Swabian
positive/control pairs at 60 seconds, changing only timeout. Four positives
recover/predict correctly and four shuffles are UNSAT, without timeouts.
`--run` checkpoints/resumes; `--validate` verifies timeout-only changes, witnesses
and frozen scoring. See `docs/one_oov_timeout_remaining.md` for combined results.

`unseeded_vocabulary_calibration.py` freezes first-half corpus-order 256-word
dictionaries without training/heldout reservation, and new contiguous Latin and
Swabian blocks. Coverage excludes every generating explanation (17/24 and 10/24
missing training occurrences). Four encrypted fixtures are UNSAT; controls yield
three UNSAT/one UNKNOWN at 60 seconds. `--run` checkpoints and `--validate`
reconstructs dictionaries, coverage, passages, shuffles and scoring. See
`docs/unseeded_vocabulary_calibration.md`.

`independent_vocabulary_coverage.py` audits nested corpus-order/frequency prefix
vocabularies at 256/512/1,024/2,048/4,096 and full-prefix ceiling, preserving
unavailable sizes. Frozen passages and a midpoint-anchored nonoverlapping later
24-word grid reveal persistent coverage gaps. No solver runs. `--run` computes
coverage; `--validate` reconstructs ranking/provenance, grid and reports.
See `docs/independent_vocabulary_coverage.md`.

`external_vocabulary_coverage.py` builds frequency-ranked attested inventories
from cached other Latin works and German XML sources excluding the test sources.
External-only and external-plus-prefix ladders at 1,024/2,048/4,096/8,192/full
inventory are audited on unchanged passages/grid, with no solver or downloads.
Neither full combined inventory admits the frozen passage. `--run` computes
coverage; `--validate` reconstructs source provenance, rankings and coverage.
See `docs/external_vocabulary_coverage.md`.

`latin_morphology_coverage.py` audits pinned independent Whitaker morphology on
unchanged Latin targets/grid. Defaults and a frozen broader threshold setting are
compared with exact attested vocabulary and orthography-only lookup. Combined
coverage reaches 268/393 or 367/393 blocks with ≤1 missing. No Z3; `--run`
checkpoints query evidence, `--validate` regenerates analyses and coverage.
See `docs/latin_morphology_coverage.md` for resource/API and finite-dictionary limits.

`latin_form_inventory.py` independently enumerates filtered stems/endings, unique
forms and one built-in enclitic layer into sorted canonical i/u inventories.
Default/broader settings produce 2.55/6.33 million forms. `--run` checkpoints each
mode; `--validate` regenerates full sets and checks hashes, recognition agreement
and coverage. No solver runs. See `docs/latin_form_inventory.md` for spelling,
completeness and scale limitations.

`latin_inventory_calibration.py` freezes three-seed changed-anagram/uniform
spelling controls and audits exact inventory recognition, with separate type/token
weights. It also counts public length-compatible candidates on canonical
24-word fixtures, without true lengths or key pruning. No solver runs.
`--run` scores frozen controls; `--validate` reconstructs acceptance and scale.
See `docs/latin_inventory_calibration.md`.

`latin_compact_membership.py` streams complete sorted inventories into exact
suffix-sharing acyclic automata, then builds shared SMT transition/acceptance
arrays. Full-inventory count/inclusion and query/control lookup checks pass.
`--run` checkpoints modes; `--validate` checks compressed artifacts and exact
membership. No cipher fits. See `docs/latin_compact_membership.md`.

`latin_symbolic_membership.py` freezes six standalone full-inventory queries:
concrete, one hidden letter and five hidden letters per inventory. Fresh workers
have a 2-second solver budget and 15-second external wall limit. Both concrete
cases return verified SAT; all four symbolic cases remain unresolved. `--run`
checkpoints workers; `--validate` checks identities and SAT witnesses. No cipher
recovery. See `docs/latin_symbolic_membership.md`.

`latin_layered_membership.py` compares exact sparse length-layered transitions
against the unchanged six `latin_symbolic_membership` queries and budgets.
All six return verified SAT; symbolic five-letter search takes 0.42/1.25 seconds.
`--run` checkpoints fresh workers; `--validate` checks baseline/code identities
and witnesses. See `docs/latin_layered_membership.md`.

`latin_layered_lengths.py` freezes lengths 2,5,8,12 with fully hidden positive
queries and exact-inventory-confirmed impossible two-letter prefixes on both
inventories. It preserves 2-second solver/15-second worker budgets. `--run`
checkpoints cases; `--validate` rescans inventories for expectations and checks
SAT words. See `docs/latin_layered_lengths.md`.

`latin_layered_timeout.py` replays only the frozen default length-eight positive
with a 30-second solver/60-second external budget and durable phase checkpoints.
It returns verified SAT after 2.27 seconds solving. `--run` preserves checkpoints;
`--validate` checks identity, timings and witness. See `docs/latin_layered_timeout.md`.

`latin_layered_cipher.py` freezes one seed-4901 synthetic control: three hidden
training words, one novel code-covered holdout, public fixed-two-glyph boundaries
and lengths, shared injective key, complete default morphology inventory.
`--run` fits once and scores the frozen first key; `--validate` reconstructs the
explanation and holdout score. SAT verifies, but training exact=0/3 and holdout
exact=0/1. See `docs/latin_layered_cipher.md`.

`latin_layered_diversity.py` freezes twelve independently selected inventory
forms covering 21 letters, three novel code-covered holdouts and a global
atomic-code shuffle preserving lengths and code counts. It fits one shared
fixed-two-glyph key per arm with 30-second solver/60-second worker budgets.
`--run` checkpoints phases; `--validate` checks source selection, generating
explanation, shuffle invariants and recovered explanations/scores when SAT.
See `docs/latin_layered_diversity.md`.

`latin_pattern_filter.py` filters the complete inventory by exact observed-code
word equality signatures under injective fixed-boundary H1. The frozen positive
recovers 12/12 training and 3/3 holdout words; the original shuffle has an empty
pattern and is trivially UNSAT. `latin_pattern_ambiguity.py` excludes the first
observed key and returns UNSAT. `latin_pattern_shuffle.py` runs one new shuffle
preserving per-word equality and code counts; it returns UNSAT without empty
candidate patterns. Each supports `--run` and `--validate`, with frozen sources,
budgets and phase checkpoints. See `docs/latin_pattern_calibration_loop.md`.

`latin_pattern_replication.py` freezes three independent inventory-sample/key
fixtures, twelve diverse training words and three novel covered holdouts each,
with matched pattern/count-preserving shuffles. It reuses the unchanged exact-
pattern worker and 30-second solver/60-second worker budgets. `--run` checkpoints
six arms; `--validate` regenerates fixtures and verifies cipher explanations,
controls, candidate counts and held-out scores. All positives recover all words;
all controls are UNSAT. See `docs/latin_pattern_replication.md`.

`latin_pattern_natural.py` audits the existing frozen Caesar 24+6 passage against
both complete morphology inventories. Zero missing training words gates strict
fit admission; default fails coverage, broader is admitted. Seed-5401 fixed-two
synthetic encryption and seed-5402 exact-pattern/count-preserving shuffle use the
same budgets and first-key scoring. Positive recovers 24/24 train, 6/6 novel
holdout; shuffle is UNSAT. `--run` checkpoints two fits; `--validate` reconstructs
coverage, cipher inputs, candidate counts and explanations. See
`docs/latin_pattern_natural.md`.

`latin_pattern_natural_replication.py` selects three further structurally eligible
nonoverlapping 24+6 natural blocks before auditing both inventory policies.
`latin_pattern_natural_ambiguity.py` excludes first observed keys on admitted
positives. `latin_pattern_natural_context.py` adds exactly the preceding 24 raw
records to the diagnosed ambiguous fixture, retaining its original holdout.
Each supports `--run` and `--validate`, fixed budgets and durable phases.
See `docs/latin_pattern_natural_loop.md` for coverage exclusions, original versus
refined scores and the limits of adaptive holdout reuse.

`latin_pattern_natural_long.py` freezes three fresh nonoverlapping 48+6 natural
blocks after all previously tested material, then audits both inventory policies.
Broader admits all three; default admits none. Same fixed-boundary H1 model,
first-key scoring and budgets, new seed-5801..5803 keys and seed-5901..5903
pattern/count-preserving shuffles. `--run` checkpoints six arms; `--validate`
rebuilds coverage, generating/recovered explanations, controls and scores.
All positives recover every word; all shuffles are UNSAT. See
`docs/latin_pattern_natural_long.md`.

The H2 sequence uses `latin_h2_public.py` (sound weak-pattern filtering/global
capacity), `latin_h2_propagation.py` (support/capacity pruning),
`latin_h2_direct.py` (direct candidate relations), `latin_h2_boolean.py` (first
pair with Boolean key selectors), and `latin_h2_pool.py` (same pair with the
original 512-word sampling pool). Each supports `--run`/`--validate`, frozen
inputs, 30-second solver/60-second worker budgets and durable phases. All full-
inventory fits remain UNKNOWN; the sampling-pool diagnostic recovers all words
and rejects its matched shuffle. See `docs/latin_h2_public_loop.md`.

`latin_h2_ladder --run` freezes and runs seven nested dictionaries (512–32,768)
on the original H2 pool fixture with unchanged 30s solver/60s worker budgets.
`--validate` verifies all fourteen artifacts against each rung's own dictionary.
See [results and scope](../docs/latin_h2_ladder.md). Sizes through 8,192 recover
all training and novel holdout words; larger positives and controls are UNKNOWN.

The `latin_h2_matching`, `latin_h2_semijoin`, `latin_h2_semijoin_full` and
`latin_h2_semijoin_replication` modules support `--run` and `--validate` for the
[seven-iteration capacity/support loop](../docs/latin_h2_capacity_loop.md).
They preserve the frozen 30s solver/60s worker limits, first-key scoring and H2
model. Sound matching detects control contradictions; joint word support enables
exact 16,384-form recovery on three assisted independent synthetic fixtures.
The 32,768-form positive remains unresolved; previous frozen modules are unchanged.

`latin_h2_compressed --run/--validate` compares three exact automaton-membership
encodings after unchanged matching/semijoin pruning on frozen 16,384/32,768-form
inputs. `latin_h2_compressed_replication --run/--validate` uses a status/runtime
selection rule to replay seed 5102 without selecting by holdout scores.
`latin_h2_compressed_analysis` verifies distinct generating/fitted training
explanations without additional solver calls. See the
[seven-iteration results](../docs/latin_h2_compressed_loop.md): large Boolean
fits are SAT but recover only 2/3 holdouts; the smaller regression cases are exact.

`latin_h2_identifiability --run/--validate` freezes seven fresh synthetic cases
with nested training ciphertext, six novel holdouts/family and 32,768-form
inventories. Separate 30s solver/60s worker limits apply to first fits, matched
shuffles and observed-key exclusion checks. All first fits recover exactly;
all shuffles and key-exclusion searches are UNSAT. See the
[scope and duplication-layout limitation](../docs/latin_h2_identifiability_loop.md).
Earlier frozen benchmark implementations and their scores remain unchanged.

`latin_h2_layout --run/--validate` runs seven matched adjacent/two-pass comparisons
with unchanged H2 fitting, scores and budgets. Six validated adjacent cases are
reused; the final pair is a fresh full-alphabet 24-type fixture. Both layouts
recover exactly, but the seed-7102 twelve-type two-pass case admits another key;
18/24-type cases are unique. `latin_h2_layout_analysis` verifies alternative
continuation and richer-case rejections without additional fits. See
[results, adaptive/fresh distinction and limitations](../docs/latin_h2_layout_loop.md).

`latin_h2_choice --run/--validate` freezes seven cyclic/balanced-random choice
pairs using the complete 32,846-form default length-compatible dictionary.
All cyclic baselines are refitted; paired code counts, words, keys and held
cipher remain fixed. All random cases recover uniquely; one cyclic twelve-type
case retains the known alias. `latin_h2_choice_analysis` verifies dictionary
closure and the alias's failure on random word arrangements without new fits.
See [results and natural-text follow-up](../docs/latin_h2_choice_loop.md).

`latin_h2_natural` freezes seven natural Caesar 48+6 passages before fitting, retains dictionary/code coverage failures, and tests admitted cases with free H2, first-key scoring and separate observed-key exclusion. `latin_h2_natural_analysis` independently reconstructs selection and coverage audits. See [protocol and results](../docs/latin_h2_natural_loop.md).

`latin_h2_natural_context` compares all seven prior natural passages at 48/96 words with fixed original ciphertext and continuation holdouts. It reuses exact prior records, retains missing-form conditions and scores only seen-code holdouts with the first key. `latin_h2_natural_context_analysis` audits backward prefix phase, matched inputs, reuse provenance and ambiguity diagnostics. See [the context loop](../docs/latin_h2_natural_context_loop.md).

`latin_h2_natural_random` freezes seven fresh natural 48+6 pairs, comparing cyclic versus independent uniform random training selection with shared independent random holdouts. Full inventories and partial code coverage remain explicit; no balancing or result reuse. `latin_h2_natural_random_analysis` audits source selection and RNG streams and records first-key training errors. See [the natural random-choice loop](../docs/latin_h2_natural_random_loop.md).

`latin_h2_random_context` freezes 48/96-word comparisons for all seven prior random natural passages, preserves original ciphertext and holdouts, and adds an independently seeded random prefix. Exact earlier results are reused with provenance; missing forms and partial holdout coverage remain explicit. See [results and protocol](../docs/latin_h2_random_context_loop.md).

`manuscript_width_audit` checks full cached EVA word/window lengths under six width profiles and the existing grouping, with excluded-record and folio barriers. `manuscript_width_validation` independently verifies arithmetic and provenance. See [audit and next calibration gate](../docs/manuscript_width_audit.md).

`text_generation_comparison` runs seven frozen stages of copying/template, frequency-baseline and natural structural-control comparisons, with disjoint development/heldout folios and first-use heldout scoring at stage seven. `text_generation_assessment` validates results and the predeclared exact-word-multiset shuffle diagnostic. See [results and limitations](../docs/text_generation_comparison.md).

`context_prediction` runs seven stages of fixed-vocabulary, smoothed frequency/context prediction, selecting by leave-one-folio-out development gains and scoring fresh blocks on heldout folios only at stage seven. `context_prediction_validation` independently reconstructs probabilities and all scores; `context_prediction_assessment` verifies permutations and bootstrap diagnostics. See [results and limits](../docs/context_prediction.md).

`line_context_prediction` runs seven stages of positional frequency baselines and within/cross-line suffix controls on new heldout folios. `line_context_validation` independently reconstructs likelihoods, split provenance and position-preserving permutations; `line_context_assessment` records the fixed interpretation. See [the controlled prediction results](../docs/line_context_prediction.md).

`character_prediction --run` completes seven frozen stages of open-vocabulary spelling prediction with within-word character models, line-position controls and preceding-suffix context. `character_prediction_validation` independently reconstructs all probabilities, gains, split provenance and permutation diagnostics; `character_prediction_assessment` reports descriptive folio uncertainty and novelty/subgroup results. See [results and next calibration](../docs/character_prediction.md).

`character_calibration --run/--validate` runs seven matched stages using the frozen character predictor: Caesar prose, bijective substitution, deterministic/random-homophonic two-character expansion, refitted position-preserving surrogates, an explicit boundary-dependent positive control, and disjoint-prose replication. `character_calibration_assessment` audits reversible transformations and reports paired manuscript/surrogate contrasts. See [matching, results and limitations](../docs/character_calibration.md).

`weak_boundary_calibration --run` freezes twelve inventory/length-preserving controls across seven stages, with independent split streams and four boundary-matching attempt probabilities. `weak_boundary_validation` independently reconstructs context/baseline scores, verifies exact inventories and layout, and reports realized matching and dose response. See [results and calibration limits](../docs/weak_boundary_calibration.md).

`mapped_boundary_calibration --run` freezes a training-only position-adjusted ending/initial mapping and twelve inventory-preserving controls in seven stages. `mapped_boundary_validation` independently reconstructs mapping, context/baseline probabilities, inventories and dose response; `mapped_boundary_assessment` records descriptive stratum results and limits. See [calibration and next priority](../docs/mapped_boundary_calibration.md).

`multilingual_character --run` freezes seven stages and 25 cached historical-prose cases with matched word counts, refitted nulls, layout sensitivity and disjoint excerpts. `multilingual_character_validation` independently reconstructs context/baseline likelihoods and verifies splits/inventories; `multilingual_character_assessment` records source coverage and German short-form caveats. See [results, normalization and limits](../docs/multilingual_character.md).

`manuscript_character_replication --run` freezes seven stages on 116 previously unscored statistical folios with two cohorts, layout/gate diagnostics, three refitted nulls and disjoint additional blocks. `manuscript_character_replication_validation` independently reconstructs likelihoods and verifies raw fields, exclusions, splits and inventories; `manuscript_character_replication_assessment` reports descriptive folio uncertainty. See [replication and limits](../docs/manuscript_character_replication.md).

`boundary_mechanisms --run` runs seven frozen stages comparing known reversible boundary-marker encoding with local word generation, nulls, key/stream replication and structural metrics. `boundary_mechanisms_validation` independently decodes ciphertext, reconstructs predictor scores and verifies edit/repetition metrics; `boundary_mechanisms_assessment` records null and vocabulary confounds. See [fixtures, results and next gate](../docs/boundary_mechanisms.md).

`boundary_null_contrasts --run` freezes seven stages of weaker known mechanisms and three exact-inventory refitted shuffles per active fixture, plus contrasts for earlier mechanism-specific nulls. `boundary_null_contrasts_validation` independently reconstructs likelihoods, decoding, invariant baselines, paired contrasts and structure; `boundary_null_contrasts_assessment` records descriptive ranges and confounds. See [null calibration and next gate](../docs/boundary_null_contrasts.md).

`shared_inventory_mechanisms --run` freezes seven stages of exact shared-payload ordering comparisons under common encoding, with two sources, three keys/streams and 36 matched nulls. `shared_inventory_validation` independently verifies inventories, decoding, likelihoods, baseline invariance and paired structural contrasts; `shared_inventory_assessment` records source-order findings and public-inventory limitations. See [results and next independent feature test](../docs/shared_inventory_mechanisms.md).

`adjacent_order_replication --run` freezes seven stages of a constrained-frequency-adjusted repetition feature on independent excerpts and five ordering rules. `adjacent_order_validation` independently enumerates slot-pair expectations, verifies inventories/decoding and prior-excerpt disjointness; `adjacent_order_assessment` records hard-negative specificity and source caveats. See [feature, results and limits](../docs/adjacent_order_replication.md).

`python -m benchmarks.joint_order_constraints --run` runs the seven frozen joint-ordering stages; `python -m benchmarks.joint_order_validation` independently audits expectations and decoding. See [protocol and results](../docs/joint_order_constraints.md).

`python -m benchmarks.joint_predictor_calibration --run` performs bounded training-only generator calibration and four-source evaluation; `python -m benchmarks.joint_predictor_validation` independently reconstructs evaluation likelihoods. See [protocol](../docs/joint_predictor_calibration.md).

`python -m benchmarks.long_range_calibration --run` runs seven frozen synthetic longer-range stages; `python -m benchmarks.long_range_validation` reconstructs all event probabilities independently. See [design and results](../docs/long_range_calibration.md).

`python -m benchmarks.long_range_realistic --run` runs seven sparse/shared-state calibration stages; `python -m benchmarks.long_range_realistic_validation` reconstructs features and likelihoods independently. See [protocol and assessment](../docs/long_range_realistic.md).

`python -m benchmarks.long_range_pooled --run` performs the seven-stage bounded pooling comparison; `python -m benchmarks.long_range_pooled_validation` independently audits likelihoods and training-only selection. See [results and limits](../docs/long_range_pooled.md).

`python -m benchmarks.long_range_families --run` runs seven frozen mapped-copy/template/shared-state stages; `python -m benchmarks.long_range_families_validation` independently audits likelihoods, mappings and features. See [specificity failure and assessment](../docs/long_range_families.md).

`python -m benchmarks.contraction_distribution_audit --run` runs seven offline stages on the frozen seven-rule inventory, full word/window distributions and German letters-only references. `python -m benchmarks.contraction_distribution_validation` independently audits minima and quantile bounds. See [capacity results](../docs/contraction_distribution_audit.md).

`python -m benchmarks.broader_contraction_capacity --run` runs seven stages on independently documented broader contraction macros with explicit graphic-unit costs and separate nasal/one-unit envelopes. `python -m benchmarks.broader_contraction_validation` audits weighted minima and distributions. See [evidence, capacity and limits](../docs/broader_contraction_capacity.md).

`python -m benchmarks.contraction_hidden_calibration_run` resumes seven bounded contraction-aware natural Latin recovery stages, including an explicitly labeled oracle-boundary diagnosis. `python -m benchmarks.contraction_hidden_validation` independently checks complete paths, retained costs, witnesses and continuation decoding. See [results and limits](../docs/contraction_hidden_calibration.md).

`python -m benchmarks.contraction_coverage_calibration --run` resumes seven bounded coverage-controlled recovery, ownership-ambiguity and frozen frequency-ranking stages. `python -m benchmarks.contraction_coverage_validation` audits actual observation of both alternatives, valid contraction paths, owner grouping and novel plaintext predictions. See [results and limits](../docs/contraction_coverage_calibration.md).

`python -m benchmarks.contraction_context_ranking` resumes seven frozen word-context selection and separate grouping-audit stages on saved contraction keys. `python -m benchmarks.contraction_context_validation` independently reconstructs reference adjacency, scores and grouping invariance. See [results and limits](../docs/contraction_context_ranking.md).
