# Ravi–Knight decipherment implementation

Status: third implementation increment, 2026-10-14. Reference inference,
restricted-vocabulary source training and fixed-vocabulary channel EM are
implemented, including vocabulary expansion and confidence freezing. Bayesian
sampling is not implemented.
The generated-English diagnostic below is not a published reproduction.

Research scope and delivery gates are in the
[implementation plan](todo/ravi_knight_implementation_plan.md).

## Delivered foundation

`src/voynich_smt/word_mapping/ravi_knight/reference.py` supplies an immutable,
validated dense bigram HMM, a full joint scorer, log-space forward-backward,
posterior state probabilities, expected BOS/EOS/transition/channel counts, and
Viterbi decoding. Plaintext states and ciphertext observations use integer IDs.
Channel rows have direction P(cipher | plaintext). All scores use natural logs.

The model describes a nonempty observed segment: BOS chooses the first state;
each state chooses another state or EOS. Every transition row together with its
EOS probability sums to one. The model permits zero probabilities and rejects
impossible observed sequences when a conditional posterior would be undefined.
It does not require a global almost-sure termination check; callers constructing
trained language models must separately ensure appropriate termination behavior.

Viterbi defaults to the ordinary channel exponent of one. An explicit exponent
of three supports the paper's final decoding convention. That stretched score
is not normalized evidence and is not used by forward-backward.

The backend deliberately uses Python dense loops and has no new dependencies.
It is a small-state correctness reference, not a production implementation for
large vocabularies. The source and channel parameters are supplied explicitly;
there is no automatic vocabulary selection, training or access to plaintext truth.

## Validation

Run:

```sh
.venv/bin/python -m pytest tests/unit/test_ravi_knight_reference.py -q
```

Twelve checks pass. Exhaustive enumeration independently verifies evidence,
state marginals, all expected counts, full joint scoring and both Viterbi
objectives. Additional cases cover a one-token segment, repeated observations,
zero-probability paths, deterministic ties, probability underflow, malformed
observations, invalid normalization and ownership of mutable constructor inputs.
These checks establish numerical correctness for this foundation; they do not
establish decipherment performance.

## Integration findings and next increment

The existing word-mapping framework remains in place. Its n-gram scorer and
incremental dictionary search are useful comparison implementations, but are
not substitutes for the reference HMM or collapsed Bayesian model.

Before corpus preparation:

- Audit `word_mapping/fixtures.py` public `source` and `encoder` metadata. Public
  artifacts must exclude key-generation seeds or passage locators that allow
  reconstruction of truth. Existing experiment formats remain unchanged.
- Define continuous public streams with no hidden sentence lengths. Separate
  document endpoints from arbitrary serialization chunks.
- Keep the EM UNKNOWN symbol distinct from the existing search's inactive-type
  barriers and from LM OOV.

The next increment should add confidence freezing and vocabulary expansion.
Dataset provenance and the paper-fidelity table must be settled before a
published-style English benchmark is reported.

One hour is a configurable experimental orchestration target, not a constant
inside inference kernels. This increment runs only small correctness checks.

## Fixed-vocabulary EM increment

`ravi_knight/lm.py` trains an additive-smoothed source bigram model from supplied
independent training segments. Vocabulary ranking uses only training counts with
lexical tie breaks. ID zero is reserved for UNKNOWN; excluded words are collapsed
before counting transitions. BOS, EOS and UNKNOWN receive explicit probability
mass. Smoothing is a per-outcome pseudocount, not a total prior concentration.
This smoothing is a reference choice, not an asserted match to the paper's LM.

`ravi_knight/em.py` initializes seeded normalized channels, sums exact posterior
channel counts across segments and performs maximum-likelihood channel updates.
Source parameters remain fixed. Unoccupied rows retain their previous values.
There are no channel pseudocounts, freezing constraints or vocabulary expansions
yet. The likelihood history includes the initial model and every completed update.
Stopping uses configurable iteration count and absolute likelihood improvement.

Run the diagnostic:

```sh
.venv/bin/python -m benchmarks.ravi_knight_em --output experiments/results/ravi-knight/fixed-em-generated-english.json
```

Independent random streams generate 300 training sentences and 60 encrypted
sentences (300 tokens) from the same small English sentence family. Six actual
surface types plus UNKNOWN form the source vocabulary. All observed ciphertext
is used for unsupervised fitting and evaluated afterward. Generated sentences
can overlap between samples; this is not a source-disjoint natural-text test.
The learner receives only numerical source parameters and ciphertext, not the
key or evaluation plaintext. The benchmark records public inputs, their hash,
channels, decoded IDs, search seeds and likelihood trajectories.

Observed results with the preselected seeds and 60 EM updates:

| Method | Seed | Exact token recovery |
| --- | --- | --- |
| Frequency rank matching | — | 100% |
| Fixed-vocabulary EM + stretched Viterbi | 3 | 80% |
| Fixed-vocabulary EM + stretched Viterbi | 5 | 76.67% |
| Fixed-vocabulary EM + stretched Viterbi | 7 | 40% |

All three EM runs hit the iteration cap; none met the convergence tolerance.
The complete diagnostic took approximately 0.84 seconds on the development
machine. These are retained development results, not evidence of an advantage
over frequency matching. Symmetric lexical roles, local optima and a very small
generator make this an integration instrument rather than a meaningful English
reproduction. No hyperparameters or seeds were selected to improve these results.

Twenty-four targeted tests pass across the reference, source training, EM,
generated pipeline and existing word-mapping integration. New checks compare a
full EM update against enumerated counts, verify likelihood monotonicity and
source immutability, test zero-occupancy rows, and independently enumerate the
probability of a generated segment from the recorded fitted channel.

Before scaling, freeze a more discriminating independent English dataset and
compare frequency initialization with random initialization as a named ablation.
The current result does not satisfy the English recovery gate.

## Iterative expansion and confidence freezing

`ravi_knight/iterative.py` adds independent frequency-ranked source/cipher
vocabularies, configurable increasing vocabulary sizes (default 100, 150, 200,
250, 300, 350), stage-specific source LM rebuilding, collapsed UNKNOWN tokens,
and irreversible confident source-row assignments. Saturated vocabularies stop
expansion early. Every stage records its own model, likelihood history, active
coverage and incoming frozen word pairs; decoding uses that stage's vocabulary.

Pairs above the strict probability threshold of 0.5 carry by word identity.
A frozen row is set to a point mass before the stage's initial likelihood is
computed and remains fixed through its EM updates. Other source rows can still
map to the same cipher word. There is no injective projection of the published
probabilistic channel. UNKNOWN rows and UNKNOWN destinations never freeze:
the aggregate changes meaning on expansion. That edge-case policy and fresh
seeded initialization of unfrozen rows are documented implementation choices,
not verified details of the original authors' code.

A no-freezing condition is available, but it independently reinitializes every
stage. It is not the planned warm-start, revisable-mapping extension.

Run the paired diagnostic:

```sh
.venv/bin/python -m benchmarks.ravi_knight_iterative --output experiments/results/ravi-knight/iterative-generated-english.json
```

On the reused generated-English development fixture, stages activate 2, 4 and
6 types with up to 60 EM updates per stage. Final token recovery is:

| Search seed | Confidence freezing | Fresh retraining without freezing |
| --- | --- | --- |
| 3 | 100% | 80% |
| 5 | 100% | 60% |
| 7 | 100% | 51.33% |

The freezing runs carry two and then four frozen rows into the later stages.
The complete six-run diagnostic takes approximately 2.85 seconds. Frequency
matching also scores 100% on this fixture. These results exercise incremental
vocabulary learning, but neither demonstrate an advantage over the simple
baseline nor validate natural-text performance. No likelihood comparison across
stages is meaningful because both observations and the source model change.

Thirty-two targeted tests pass, including prior inference/EM/pipeline checks,
fixed-row invariance, allowed channel collisions, strict threshold behavior,
UNKNOWN exclusion, identity-based carryover, coverage growth, deterministic
replay, saturation and schedule validation.

Next: select an independent natural-English corpus with explicit licensing and
work-disjoint splits, and finish the paper-fidelity table before reporting a
reproduction experiment. Add frequency initialization as a declared comparison;
retain these generated diagnostics unchanged. Bayesian sampling remains gated
on the mathematical-contract audit, not on this fixture's perfect score.

## Work-disjoint natural-English pilot

The fourth increment adds a versioned Gutenberg extractor, hashed raw-source
manifest, frozen pre-inference protocol, separate public/truth artifacts and a
natural-text benchmark. See [paper-fidelity audit](ravi_knight_fidelity.md) for
reported settings versus implemented choices. Catalogs identify
[Pride and Prejudice](https://www.gutenberg.org/ebooks/1342) and
[Alice’s Adventures in Wonderland](https://www.gutenberg.org/ebooks/11) as public
domain in the USA; complete downloaded notices are retained in the raw files.

The LM trains on 122,276 extracted Austen tokens; decipherment uses a contiguous
487-token Alice prefix (209 types), with no coverage-based passage selection.
Training/evaluation authors and works differ. Paragraph/punctuation segmentation
is heuristic, with known abbreviation and heading limitations; it is not gold
sentence segmentation. Apostrophes are preserved and other punctuation removed.
This fixture is now development data and must not become a fresh validation set.

The predeclared small pilot uses 10/20/30 active types, 20 EM updates per stage,
smoothing 0.1, seeds 3/5/7 and final channel exponent 3. Its source vocabulary
covers only 40.45% of plaintext tokens at the last stage; active cipher types
cover 50.92% of ciphertext. Missing vocabulary therefore limits recovery, but
does not explain all errors within available vocabulary.

| Method | Seed | Whole-stream token recovery | Inconsistent cipher types |
| --- | --- | --- | --- |
| Frequency matching | — | 11.91% | 0 |
| Iterative EM | 3 | 2.67% | 13 |
| Iterative EM | 5 | 15.81% | 14 |
| Iterative EM | 7 | 8.62% | 14 |

All stages reach the iteration cap. Total runtime is approximately 11.24 seconds.
One seed beats frequency matching; the three-seed mean does not. This does not
pass the recovery gate, and is not a published-result reproduction. Inconsistent
token predictions are preserved rather than projected into a dictionary.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english
.venv/bin/python -m benchmarks.ravi_knight_english_validate experiments/results/ravi-knight/natural-english-v1
```

Use a fresh `--output` directory for reruns; existing protocols are protected
against accidental overwrite. CLI flags expose sizes, updates, token limit and
`--budget-seconds` (default one hour). The budget is currently cooperative between
chains: an in-flight chain can overrun it. Completed chains are saved, but exact
within-chain resume and a hard wall-clock deadline are not implemented.

The independent artifact validator recomputes all nine saved stage decodings,
likelihoods, token metrics, consistency counts, coverage ceilings and frozen-row
constraints. Thirty-three targeted tests pass, including extraction anchors,
frontmatter/footer removal, apostrophes and whole-segment prefix selection.

Next diagnostic: profile the paper's 100–350 vocabulary schedule, then compare
frequency initialization with random starts under declared budgets. Choose the
configuration on development data before reserving another untouched passage.
Do not tune against this prefix and report its improvement as fresh validation.

## Tenfold iteration-cap comparison

At the user's request, reran the unchanged natural-English protocol with 200
rather than 20 updates per stage. Public input hashes, source models, vocabulary
sizes, seeds and all other protocol settings match. Original artifacts remain
untouched. New output: `experiments/results/ravi-knight/natural-english-v1-200-iterations/`.

| Search seed | 20-update cap | 200-update cap | Change |
| --- | --- | --- | --- |
| 3 | 2.67% | 19.10% | +16.43 percentage points |
| 5 | 15.81% | 19.10% | +3.29 percentage points |
| 7 | 8.62% | 9.45% | +0.82 percentage points |
| Mean | 9.03% | 15.88% | +6.84 percentage points |

Runtime increased from 11.24 to 104.25 seconds (9.27 times). Frequency matching
remains 11.91%; the 200-update mean exceeds it, but seed 7 still falls below it.
All nine stages reach 200 updates without satisfying convergence tolerance.
The unchanged candidate-vocabulary token ceiling is 40.45%.

This supports insufficient iterations as one contributor to the original weak
result. It does not establish a general improvement on independent text or
resolve the vocabulary/search/model limitations. In particular, seed 7's first
stage has better likelihood but lower exact recovery after longer training.

Longer earlier stages freeze more mappings: final stages enter with 17/17/18
frozen rows instead of 5/9/6. Their final likelihoods are actually lower than in
the short schedules. This does not violate EM monotonicity: each run is monotone
within a stage, but changed frozen constraints yield different feasible channel
families between schedules. The comparison is the total effect of increasing
all stage caps, not a controlled continuation of the identical final-stage fit.
Inconsistent final cipher types decrease from 13/14/14 to 12/12/10, but remain.

All nine new stages pass independent artifact validation. The comparison script
checks matching inputs/protocols and saves stage-level metrics, likelihoods,
updates, frozen counts, consistency and runtime in `comparison.json`.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --iterations 200 --output experiments/results/ravi-knight/natural-english-v1-200-iterations
.venv/bin/python -m benchmarks.ravi_knight_english_validate experiments/results/ravi-knight/natural-english-v1-200-iterations
.venv/bin/python -m benchmarks.ravi_knight_english_compare experiments/results/ravi-knight/natural-english-v1 experiments/results/ravi-knight/natural-english-v1-200-iterations --output experiments/results/ravi-knight/natural-english-v1-200-iterations/comparison.json
```

## Final iteration-cap test: 1,000

Reran the same public input and protocol with a 1,000-update cap per stage.
Only the iteration cap changes. Results are saved under
`experiments/results/ravi-knight/natural-english-v1-1000-iterations/`, including
`comparison-vs-200.json`. All nine stages pass artifact validation.

| Seed | 20 cap | 200 cap | 1,000 cap |
| --- | --- | --- | --- |
| 3 | 2.67% | 19.10% | 19.10% |
| 5 | 15.81% | 19.10% | 19.10% |
| 7 | 8.62% | 9.45% | 9.45% |
| Mean | 9.03% | 15.88% | 15.88% |

Runtime: 362.24 seconds (6.04 minutes), compared with 104.25 seconds for the
200 cap and 11.24 seconds for the 20 cap. The 1,000-cap run takes 3.47 times
as long as the 200-cap run, with zero recovery improvement in any of the nine
stage comparisons. Likelihoods improve slightly without changing those recovery
scores. Final inconsistency counts remain 12/12/10 and vocabulary ceiling 40.45%.

Actual updates by stage (10/20/30 types):

- Seed 3: 593 / 1,000 / 610.
- Seed 5: 548 / 1,000 / 616.
- Seed 7: 811 / 302 / 736.

Seven of nine stages satisfy the convergence tolerance, including all final
stages. The two middle-stage fits that hit 1,000 updates gain only approximately
0.0049 and 0.0044 log-likelihood units over their 200-update values. Frozen pair
counts and consistency counts are unchanged at all matched stages.

This completes the requested iteration-cap series. Additional iterations alone
are not supported as the next improvement for this fixture. Vocabulary coverage,
initialization, early frozen mistakes, limited context and source-model quality
remain separate hypotheses to investigate; this run does not identify which is
dominant. No inference code changed for this experiment.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --iterations 1000 --output experiments/results/ravi-knight/natural-english-v1-1000-iterations
.venv/bin/python -m benchmarks.ravi_knight_english_validate experiments/results/ravi-knight/natural-english-v1-1000-iterations
.venv/bin/python -m benchmarks.ravi_knight_english_compare experiments/results/ravi-knight/natural-english-v1-200-iterations experiments/results/ravi-knight/natural-english-v1-1000-iterations --output experiments/results/ravi-knight/natural-english-v1-1000-iterations/comparison-vs-200.json
```


## Current default and inexpensive next experiments

Decision, 2026-10-14: use 200 updates per stage as the natural-English pilot
default (`benchmarks/ravi_knight_english.py`, API and CLI). Keep the convergence
tolerance and configurable override. This is a development choice supported by
the 20/200/1,000 series, not a universal convergence guarantee. Other reference
solvers and historical protocols retain their own defaults/settings.

Revisit 100 versus 200 when ciphertext length, vocabulary size, initialization,
or LM changes. Compare recovery, likelihood and wall time, keeping other factors
fixed. Do not infer that more tokens require proportionally more EM updates;
each update already gets more expensive, and convergence can change either way.
Use development data for this choice and freeze it before fresh validation.

Prioritized hypotheses, not demonstrated improvements:

1. Frequency-informed initialization with a positive probability floor. The
   baseline already supplies information that random initialization ignores.
   Compare the same three seeds against random starts; apply frozen rows after
   initialization. Preserve the channel direction and row normalization.
2. Relax confidence freezing in a paired run. Compare current freezing with the
   existing no-freezing/fresh-retraining mode, keeping initialization and budget
   fixed. A true warm-start revisable extension is additional work, not already
   implemented. Diagnose whether confidently wrong early assignments cause harm.
3. Expand the vocabulary modestly, e.g. 20/40/60 versus 10/20/30, using independent
   training ranks. Report the raised candidate ceiling and actual recovery;
   vocabulary coverage is not recovery, and dense cost grows quadratically.
4. Small source-smoothing sweep on development data. Select using independent
   genuine-text predictive loss as well as recovery diagnostics; better LM loss
   does not guarantee better decipherment. Avoid combinatorial tuning with other
   changes until individual effects are understood.
5. More ciphertext as a separate scale experiment, with a nested contiguous
   prefix and a fixed vocabulary for the first comparison. Report accuracy on
   both the common original prefix and the full larger input, so a changed word
   mix does not masquerade as an inference improvement.

After these, consider higher-order LMs, type-consistent inference and Bayesian
sampling. Their implementation and compute costs are larger than the first
controlled changes above. No further experiment is claimed by this decision.

## Frequency initialization, then freezing ablation

Implemented and evaluated the two requested changes in sequence, holding the
487-token work-disjoint fixture, 10/20/30 vocabulary schedule, 200-update cap,
source smoothing, source models and seeds fixed. These remain development
experiments, not fresh validation. Default initialization remains random and
freezing remains enabled; the new options do not silently replace the baseline.

Frequency-informed initialization uses a predeclared 50/50 mixture of the
existing seeded positive random row and a point mass at the equal-frequency-rank
cipher type. Source ranks come only from LM training; cipher ranks come only
from ciphertext. UNKNOWN and unmatched source ranks retain the random row.
Every destination retains positive probability. This is a heuristic initializer,
not a known key or a guaranteed improvement. Frozen rows override it at the
start of each later stage. No mixing weights were tuned after observing results.

| Seed | Random + freeze | Frequency + freeze | Frequency + no freeze |
| --- | --- | --- | --- |
| 3 | 19.10% | 9.45% | 16.22% |
| 5 | 19.10% | 4.93% | 14.58% |
| 7 | 9.45% | 9.24% | 12.73% |
| Mean | 15.88% | 7.87% | 14.51% |
| Runtime | 104.25 s | 105.87 s | 105.89 s |

Frequency matching without EM is unchanged at 11.91%. The candidate ceiling
remains 40.45%. All new runs hit 200 updates at every stage.

Experiment 1: frequency initialization loses 8.01 percentage points in mean
recovery compared with random initialization under freezing. It is not adopted.
This rejects this particular rank-based mixture as an immediate improvement on
this fixture; it does not reject all frequency-informed proposal mechanisms.

Experiment 2: removing freezing improves the frequency-initialized mean by
6.64 percentage points, with gains in every seed. First-stage models and outputs
are exactly identical for each matched seed, confirming that the change starts
only when carryover would occur. No-freeze final likelihoods are also higher.
Final inconsistent-type counts are 15/12/16 without freezing versus 11/19/10
with it: improved token accuracy does not ensure a globally consistent key.

The no-freeze mode reinitializes each expanded stage, so this is an ablation of
irreversible carryover, not a warm-start repair algorithm. Its final stage does
not use earlier learned rows. The results support harmful early freezing under
frequency initialization, but do not establish a general freezing policy.
The missing random-initialization/no-freeze condition would be needed to assess
that interaction before changing defaults. Its mean here is not measured.

Outputs:

- `experiments/results/ravi-knight/natural-english-v1-frequency-200/`
- `experiments/results/ravi-knight/natural-english-v1-frequency-no-freeze-200/`

Both include protocols, public inputs, separate evaluation-only truth, all
stage channels/decodings/likelihood histories, and paired comparison JSON.
All eighteen new stages pass independent artifact validation. Thirty-six
targeted tests pass, including full-support rank initialization, unmatched and
UNKNOWN handling, seed replay, first-stage parity, frozen-row invariants and
one-factor-only comparison guards. Legacy protocol files receive explicit
random/freeze defaults only in the comparison reader, without modifying them.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --initialization frequency --output experiments/results/ravi-knight/natural-english-v1-frequency-200
.venv/bin/python -m benchmarks.ravi_knight_english --initialization frequency --no-freeze --output experiments/results/ravi-knight/natural-english-v1-frequency-no-freeze-200
```

## Final inventory scale

The user reaffirms a design target of roughly 20,000 Latin lemmas / 800,000
surface forms. Dense HMM inference remains a small-state reference only: an
800,000-square float64 source matrix alone would consume 5.12 TB. Increasing
the pilot's dense vocabulary is not the architecture for that target.

The production path must separate the full independently sourced inventory from
sparse active candidates, use sparse/backoff LM storage and on-demand scoring,
and retrieve/reintroduce candidates across the inventory. Lemma organization
must preserve surface assignments and morphological ambiguity. Independently
measure candidate support, memory and throughput; do not assume a high-scoring
small candidate list generalizes to the full inventory. See the scale constraint
in the [implementation plan](todo/ravi_knight_implementation_plan.md).

## Completed initialization × freezing comparison

Completed the missing random-initialization/no-freezing condition with the same
200-update cap, seeds and public input. No inference code changed. Output is
`experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200/`.

| Seed | Random + freeze | Random, no freeze | Frequency + freeze | Frequency, no freeze |
| --- | --- | --- | --- | --- |
| 3 | 19.10% | 9.03% | 9.45% | 16.22% |
| 5 | 19.10% | 8.83% | 4.93% | 14.58% |
| 7 | 9.45% | 2.05% | 9.24% | 12.73% |
| Mean | 15.88% | 6.64% | 7.87% | 14.51% |

Random/no-freeze takes 105.11 seconds and all nine stages hit the 200-update
cap. Its mean falls 9.24 percentage points below random/freeze, with losses in
every seed. By contrast, removing freezing under frequency initialization gains
6.64 points. The difference between these freezing effects is 15.88 points on
this fixture. These are descriptive paired results across three search seeds,
not independent-corpus evidence or a statistical generalization.

The effect of initialization reverses too: frequency initialization hurts under
freezing but helps without it. Thus neither “frequency initialization is worse”
nor “freezing is harmful” is a general conclusion. Random initialization with
freezing remains the best observed mean, and the default stays unchanged.
Frequency-only matching remains 11.91% and the candidate ceiling remains 40.45%.

The no-freeze implementation discards learned rows on every expansion, so it
also removes information transfer between stages. These results do not show
that warm-start revisable carryover would fail. That remains a distinct possible
extension. The completed comparison does not alter the full-inventory sparse
architecture requirement or establish natural-English recovery success.

All nine new stages pass artifact validation. First-stage models are exactly
identical between random/freeze and random/no-freeze for each seed, and every
no-freeze stage has zero frozen pairs. Stored paired comparisons check both
random freezing on/off and random/frequency under no-freeze. A descriptive
four-condition summary is saved as `factorial-summary.json` in the new output
directory. Previous artifacts and defaults are preserved.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --no-freeze --output experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200
.venv/bin/python -m benchmarks.ravi_knight_english_validate experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200
.venv/bin/python -m benchmarks.ravi_knight_english_compare experiments/results/ravi-knight/natural-english-v1-200-iterations experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200 --vary freeze --output experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200/comparison-vs-freeze.json
```

## Restart selection by likelihood

Analyzed the four existing 200-update configurations without new inference.
`benchmarks/ravi_knight_restart_selection.py` chooses the restart with maximum
final training log evidence, breaking ties by lowest seed ID. Accuracy is only
consulted after selection; an oracle-best recovery figure is a labeled diagnostic.
Only restarts with identical source models and final vocabularies are compared.

| Configuration | Mean restart recovery | Likelihood-selected seed | Selected recovery |
| --- | --- | --- | --- |
| Random + freeze | 15.88% | 3 | 19.10% |
| Frequency + freeze | 7.87% | 7 | 9.24% |
| Random, fresh no-freeze | 6.64% | 7 | 2.05% |
| Frequency, fresh no-freeze | 14.51% | 5 | 14.58% |

The selector picks a best-recovery restart only in the first configuration. In
random/no-freeze it chooses the worst recovery. Thus training evidence cannot
be treated as a dependable exact-recovery selector. It also differs from the
cubed-channel Viterbi score. This is a descriptive result on reused development
text and three seeds, not a calibration study. Sparse priors or grammar factors
must face the same score-versus-recovery checks rather than assume this issue
is solved by more search.

The saved analysis is `experiments/results/ravi-knight/restart-selection-development.json`.
A unit check changes evaluation accuracy while verifying selection stays fixed,
and checks deterministic tie breaking. This analysis does not change defaults.

## Revisable probability carryover

Implemented explicit `--warm-start` (implies no freezing) without changing the
baseline. At expansion, learned rows for previously active real source words
carry by identity. Existing real cipher columns retain their probability; the
old UNKNOWN probability splits among newly active cipher types and remaining
UNKNOWN in proportion to observed ciphertext counts. New source rows and the
UNKNOWN source row initialize afresh. A predeclared 5% mixture with the positive
fresh initializer reopens zero entries, allowing all carried assignments to
change. This is a reference initialization policy, not a new channel prior or
a guarantee of monotonic likelihood across vocabulary changes.

The 5% setting was selected before the experiment and not swept. Configuration
records `warm_start` and `exploration`; the comparison reader supplies historical
defaults without rewriting old artifacts. Warm-start with frozen rows is rejected
to keep the revisable experiment distinct. The transfer is dense only because
the solver is a correctness reference; it is not the 800,000-form architecture.

| Seed | Random + freeze | Random, fresh no-freeze | Random, revisable carryover |
| --- | --- | --- | --- |
| 3 | 19.10% | 9.03% | 12.53% |
| 5 | 19.10% | 8.83% | 12.53% |
| 7 | 9.45% | 2.05% | 7.60% |
| Mean | 15.88% | 6.64% | 10.88% |

At the unchanged 200 cap, carryover improves all seeds relative to fresh
no-freeze, gaining 4.24 mean percentage points, but loses to freezing in all
seeds (5.00 mean points lower). Frequency-only matching is 11.91%. Runtime is
103.79 seconds; all nine stages hit the cap. Candidate token coverage is still
40.45%, and final inconsistent-type counts are 15/15/15.

Within this configuration, likelihood selects seed 5 (12.53%), tying the best
recovery. However, the carryover final likelihoods exceed those of the freezing
baseline while its recovery is lower. Together with the earlier restart
counterexample, this is evidence against equating higher objective with better
recovery. It does not establish the cause or justify tuning on the same text.

All nine saved stages pass artifact validation. The first-stage models and
outputs exactly match the existing random/freeze condition, all carried rows
remain revisable, and the full run has no frozen pairs. Thirty-nine targeted
tests pass, including independent numeric UNKNOWN-splitting checks, identity
transfer with deliberately reordered IDs, positivity/normalization, deterministic
replay, first-stage parity and truth-independent restart selection.

Artifacts are in `experiments/results/ravi-knight/natural-english-v1-random-warm-200/`,
including `comparison-vs-fresh.json` and `restart-selection.json`.
Defaults remain random initialization, irreversible freezing and 200 updates in
the natural-English pilot. Both experiments are development diagnostics only.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --warm-start --output experiments/results/ravi-knight/natural-english-v1-random-warm-200
.venv/bin/python -m benchmarks.ravi_knight_english_validate experiments/results/ravi-knight/natural-english-v1-random-warm-200
.venv/bin/python -m benchmarks.ravi_knight_english_compare experiments/results/ravi-knight/natural-english-v1-random-no-freeze-200 experiments/results/ravi-knight/natural-english-v1-random-warm-200 --vary warm_start --output experiments/results/ravi-knight/natural-english-v1-random-warm-200/comparison-vs-fresh.json
```

## More ciphertext with fixed active vocabularies

A predeclared 1,000-token limit admits 960 complete-segment tokens, versus the
original 487. Preserve the original cipher identities and frequency-ranked
active cipher lists at every stage, as well as the source vocabularies/models,
200-update cap, random initialization and freezing. Newly observed inactive
cipher types remain UNKNOWN. Thus extra observations, not a larger active search
vocabulary, change the experiment. Plaintext/key access is fixture preparation
and evaluation only; inference receives public cipher order and training data.

| Seed | Original 487-token run | Same 487 tokens after longer fitting | Full 960 tokens |
| --- | --- | --- | --- |
| 3 | 19.10% | 22.18% | 19.17% |
| 5 | 19.10% | 22.18% | 19.17% |
| 7 | 9.45% | 22.18% | 19.17% |
| Mean | 15.88% | 22.18% | 19.17% |

The matched-prefix gain is 6.30 percentage points, with gains in every seed.
Runtime is 208.00 seconds versus 104.25 seconds. The final source vocabulary
ceiling is 36.98% on the longer text (40.45% on the original prefix). The fixed
frequency baseline scores 10.31% over all 960 tokens and retains its original
11.91% on the prefix. All nine stages hit the cap and final inconsistent-type
counts are 16 for each seed. Equal accuracy across seeds is not evidence of
identical dictionaries or calibrated confidence.

All nine new stages pass artifact validation, including independently recomputed
prefix metrics. `benchmarks/ravi_knight_length_compare.py` verifies nested public
ciphertext, unchanged training, matching protocols except length/reference
metadata, and identical source models/active cipher vocabularies at every stage.
This is an extended development prefix, not untouched validation. More text is
supported as useful on this fixture, but neither Latin-scale feasibility nor
natural-language recovery success follows.

Successful output: `experiments/results/ravi-knight/natural-english-v1-long-1000-v2/`.
The initial `long-1000` preparation failed on the frequency baseline's missing
fallback for newly inactive cipher types; no inference ran. That preparation
artifact is preserved with a failure note. The fallback is now UNKNOWN.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --tokens 1000 --reference-run experiments/results/ravi-knight/natural-english-v1-200-iterations --output experiments/results/ravi-knight/natural-english-v1-long-1000-v2
.venv/bin/python -m benchmarks.ravi_knight_length_compare experiments/results/ravi-knight/natural-english-v1-200-iterations experiments/results/ravi-knight/natural-english-v1-long-1000-v2 --output experiments/results/ravi-knight/natural-english-v1-long-1000-v2/comparison-vs-short.json
```

## Bounded source-smoothing sweep

Predeclared values 0.01, 0.1 and 1.0 in
`experiments/results/ravi-knight/smoothing-development-protocol.json` before
running new conditions. Reuse the 0.1 baseline and run only 0.01/1.0 on the
original 487-token fixture with unchanged sizes, seeds, initialization, freezing
and 200 cap. Do not combine this change with the length experiment.

| Per-outcome smoothing | Seed 3 | Seed 5 | Seed 7 | Mean recovery | Genuine-text nats/event |
| --- | --- | --- | --- | --- | --- |
| 0.01 | 19.10% | 19.10% | 9.45% | 15.88% | 1.79948 |
| 0.1 (baseline) | 19.10% | 19.10% | 9.45% | 15.88% | 1.79411 |
| 1.0 | 19.30% | 19.30% | 9.24% | 15.95% | 1.79028 |

The mean change at 1.0 is only +0.068 percentage points: one additional correct
token in each of two seeds, and one fewer in the third. This does not justify
promoting the setting or continuing a broad smoothing search. Default remains
0.1. New conditions take approximately 108.49 and 108.28 seconds (run concurrently);
all stages hit the iteration cap. All eighteen new stages pass validation.

The independent genuine-text diagnostic skips the whole-segment prefix fitting
2,000 Alice tokens, then scores the next whole-segment prefix fitting 2,000
tokens, never supplied to inference. There are 2,108 prediction events including
BOS/EOS, with 1,256 tokens mapped to UNKNOWN under the fixed source vocabulary.
Thus loss is for the collapsed vocabulary, not full-surface-word perplexity or
an independent Latin evaluator. Smoothing 1.0 has slightly better predictive
loss but essentially no recovery advantage. This passage is now development
material, not untouched validation.

New run artifacts:

- `experiments/results/ravi-knight/natural-english-v1-smoothing-001/`
- `experiments/results/ravi-knight/natural-english-v1-smoothing-1/`
- `experiments/results/ravi-knight/smoothing-development-summary.json`

`benchmarks/ravi_knight_smoothing_summary.py` recomputes genuine-text losses
from saved source models, including for the original baseline. Paired
comparisons require the same public inputs and source vocabulary/counts while
permitting the declared smoothing-dependent source probabilities.

Forty-two targeted tests pass after both experiments. New coverage includes
fixed cipher order despite changing frequencies, nested cipher identity
preservation, inactive-word fallback, common-prefix metric recomputation and
source loss including UNKNOWN and endpoints. All twenty-seven new fitted stages
(nine length, eighteen smoothing) pass artifact validation.

```sh
.venv/bin/python -m benchmarks.ravi_knight_english --smoothing 0.01 --output experiments/results/ravi-knight/natural-english-v1-smoothing-001
.venv/bin/python -m benchmarks.ravi_knight_english --smoothing 1.0 --output experiments/results/ravi-knight/natural-english-v1-smoothing-1
.venv/bin/python -m benchmarks.ravi_knight_smoothing_summary experiments/results/ravi-knight/natural-english-v1-smoothing-001/result.json experiments/results/ravi-knight/natural-english-v1-200-iterations/result.json experiments/results/ravi-knight/natural-english-v1-smoothing-1/result.json --output experiments/results/ravi-knight/smoothing-development-summary.json
```

These complete the requested remaining inexpensive diagnostics. Extra text helps
on this fixture; smoothing tuning does not materially help. Keep the short pilot
as a historical regression diagnostic, rather than silently replacing its data.
The next substantial work should address sparse full-inventory candidate support
and type-consistent inference, with independent validation after development
choices are fixed. Do not infer Latin-scale success from these small results.


The next subproject is specified in the [scalable boundary-free English implementation plan](todo/scalable_english_decipherment_plan.md): known English, unknown topic/vocabulary/sentences, roughly 35k tokens and a large independent inventory, with grammar/semantics evaluated separately from literal accuracy.
