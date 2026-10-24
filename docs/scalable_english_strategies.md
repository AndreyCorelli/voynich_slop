# English strategy screen

The goal is improved dictionary restoration before attempting Voynich-to-Latin.
This increment tests the five proposed directions separately: repeated-context
retrieval, broader LM training, small joint moves, trigram scoring and restart
agreement diagnostics.

## Declared comparison

All search variants use frequency initialization, mixed scheduling, 4,000
proposals and seeds 3 and 5. Each chain has a 400-second budget and 10-second
reserve. After profiling, trigram receives an 800-second allowance to complete
the same horizon; other variants remain at 400 seconds. This amendment
preceded recovery evaluation. Output logs include complete public-only candidate/move traces.
All comparisons require completion of the same proposal horizon.

| Variant | Change | Control |
| --- | --- | --- |
| baseline | Original 298k-token bigram and sampled contexts | Reference |
| pooled | Aggregate all occurrences; fuse observed-context lists | baseline |
| joint | 10% bounded, targeted three-word cycle attempts | baseline |
| trigram | 50% interpolated absolute-discount trigram scoring | baseline |
| corpus_control | Original training, enlarged common inventory | Corpus reference |
| corpus_expanded | Five additional works, same enlarged inventory | corpus_control |

The baseline/pooled/joint/trigram inventory has 126,896 forms.
Both corpus variants use exactly the same 133,208 forms, independently derived
from CMUdict and the union of training sources. Thus adding vocabulary is
separated from adding training context in the corpus comparison.

Equal proposals are not equal computation: larger offered pools, extra cycle
candidates and higher-order event scoring can increase work. Runtime, offered
candidate evaluation counts and accepted moves by source are recorded.

This is development screening on the previously inspected 35k-token Wells
prefix. Two seeds and one work cannot establish universal gains. Any later
selection is development selection; a longer run on new seeds would not make
the reused work an independent benchmark. No grammar/semantic score is claimed.

## Repeated-context retrieval

The old retriever samples up to eight occurrences. The new option first
counts neighboring decoded words across every occurrence, then queries up to
eight distinct contexts in each direction. It fuses their bounded candidate
lists with count-weighted reciprocal-rank votes.

Successor evidence uses probability relative to the candidate's base frequency;
predecessor evidence requires an observed source edge. This avoids rewarding an
untrained predecessor solely for having a large backoff coefficient.
The new candidates receive bounded fresh pool capacity before stale retained
lists. Final ranking always uses complete-key deltas over every affected
occurrence, including any displaced owner. Random exploration and exact
injectivity remain available.

This first pooled variant uses immediate contexts across repeated occurrences.
Distance-two evidence is supplied to scoring by the separate trigram experiment;
a dedicated longer-distance retrieval index remains unimplemented.

## Joint moves

At 10% of primary proposal steps, inspect at most four occupied candidates for
the primary type and at most four for the next owner. Form a three-word cycle
and select the best of at most 16 such cycles. The usual annealed decision
accepts or rejects the whole move atomically. A failed cycle search is logged
as a no-op. This is a bounded heuristic proposal, not posterior sampling.

Tests include a case where a three-cycle improves the score while every
pairwise swap loses. Observational logging records the actual multiword move,
not an intermediate candidate-scoring call.

## Trigram scoring

The sparse trigram model uses absolute discounting backed off to the unchanged
bigram model, with a fixed 0.5 mixture weight. It is trained on the same original
documents and inventory. It keeps the original bigram candidate index, so this
comparison changes scoring rather than both scoring and retrieval.

Every cipher trigram event and its multiplicity contributes to the objective.
Incremental updates include all windows touching any changed type. Document
starts/ends are handled once; chunks never add boundaries. Probabilities remain
normalized over the full inventory. Counts, configuration and model identity
are stored in SQLite and bound to checkpoints. Original bigram models remain
loadable.

## Expanded training

Add five non-Wells works to EWT and Austen:

- [Frankenstein](https://www.gutenberg.org/ebooks/84), Mary Shelley.
- [Jane Eyre](https://www.gutenberg.org/ebooks/1260), Charlotte Bronte.
- [Moby Dick](https://www.gutenberg.org/ebooks/2701), Herman Melville.
- [Little Women](https://www.gutenberg.org/ebooks/514), Louisa May Alcott.
- [Great Expectations](https://www.gutenberg.org/ebooks/1400), Charles Dickens.

Pinned raw hashes, download URLs and original Gutenberg notices are cached under
`data/raw/scalable-english-expanded/`. Prose incipits and source boundaries are
recorded; chapters remain within a continuous work. These add authors and genres
but are still dominated by older fiction, not contemporary broad-domain English.

Training grows from 298,475 to 1,146,863 tokens and from 141,593 to 421,013
observed bigram edges. Target LM-attested token coverage rises from 90.51% to
96.61%. Both corpus variants have 244 missing target types / 481 tokens:
98.63% token inventory coverage. Both exact 12-token overlap audits find zero
matching windows against the full set of training documents.

## Restart agreement

Build agreement using one score-selected complete key per seed, without truth.
Inspect strict-majority mappings separately from those still inherited from
the initial key. Only afterward evaluate precision against gold words.

No mapping is frozen or promoted merely for agreeing. Shared initialization,
limited search and common model bias can all produce repeated errors.
Multiple near-identical archived keys from one chain do not count as independent
votes. These diagnostics will determine whether agreement is a useful signal
before it is used for retrieval or initialization.

## Interfaces and reproducibility

Existing defaults remain unchanged. New options:

- `RetrievalConfig(context_strategy='pooled')`, or CLI `--context-strategy pooled`.
- `SearchConfig(joint_probability=0.1)`, or CLI `--joint-probability 0.1`.
- Trigram SQLite resources load through the common model loader; no change to
  cipher inputs or source-only selection.
- Legacy checkpoints/protocols default to sampled retrieval and no joint moves.

Screen design: `experiments/results/scalable-english/strategy-screen-v1/design.json`.
Frozen resources: `experiments/results/scalable-english/strategy-resources-v1/`.
Runs and subsequent evaluation: `strategy-screen-v1/{variant}/`.

```sh
.venv/bin/python -m benchmarks.scalable_english_strategy_resources --base experiments/results/scalable-english/independent-resources-v1 --raw data/raw/scalable-english-expanded --output experiments/results/scalable-english/strategy-resources-v1
.venv/bin/python -m benchmarks.scalable_english_strategy_screen search
.venv/bin/python -m benchmarks.scalable_english_strategy_screen measure
.venv/bin/python -m benchmarks.scalable_english_strategy_screen compare
```

Output directories/files are exclusive. These commands use the fixed design;
use fresh paths in the Python APIs for another experiment. Corpus coverage
audits live beside the resources in `corpus_control-audit/` and
`corpus_expanded-audit/`.

The initial trigram attempt was interrupted for runtime profiling and preserved
in `trigram-slow-attempt/`. Its first 30 proposal decisions match the optimized
implementation exactly. The optimization caches lower-order probability pairs
(maximum 262,144 entries per model) and removes redundant decoding/validation
in the already-validated incremental scorer. Full-trigram memoization had very
few hits and was discarded. Probability arithmetic and model identities remain
unchanged. Runtime allowances differ for trigram, but completed proposal counts
and all search-policy parameters remain matched. The cache is a derived runtime
optimization and does not affect checkpoint numerical continuation.

Corpus choice is development work made with knowledge that the target is a
literary work. It adds no Wells text or target-derived forms, but is not a
blind test of source-corpus selection for an entirely unknown domain. Replication
on another held-out work/genre remains necessary.

Candidate evaluation counts refer to logged shortlist pools, not every source
probability operation. Joint-cycle trial alternatives are evaluated internally
and only the selected cycle is logged. Consequently its candidate-support
counts and failure labels describe recorded pools/selected moves; they cannot
certify that a true mapping never appeared in an unselected cycle trial.
Recovery, accepted move deltas and final keys are fully validated.

The larger-corpus comparison changes unigram frequencies and contextual counts
together. Because frequency initialization uses those unigram ranks, its initial
key also changes. Initial accuracy is reported separately. This comparison
measures the complete effect of changing training data, not contextual counts
with a fixed initial dictionary.

## Screening results

All twelve screening chains finished 4,000 proposals. Values below are literal
token accuracies; source-score-selected values use no truth for selection.

| Variant | Seed 3 | Seed 5 | Mean | Score-selected run | Mean time / chain |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 33.49% | 19.67% | 26.58% | 33.49% | 104 s |
| Pooled contexts | 27.62% | 31.15% | 29.39% | 27.62% | 119 s |
| Joint cycles | 29.83% | 29.23% | 29.53% | 29.23% | 128 s |
| Trigram | 28.75% | 31.16% | 29.95% | 28.75% | 444 s |
| Corpus control | 35.15% | 20.23% | 27.69% | 35.15% | 109 s |
| Expanded corpus | 22.82% | 30.49% | 26.65% | 30.49% | 127 s |

Paired mean changes: pooled +2.80 percentage points, joint +2.95, trigram +3.37,
expanded corpus -1.04 against its separate common-inventory control.
Every change hurts seed 3 and helps seed 5. The large seed variation and poor
source-score selection make these fragile averages. None establishes a reliable
practical improvement; all modified bundles select a less accurate key than
their control's selected key on this screen.

Pooling does not solve its intended candidate-support problem: mean true
assignments ever offered fall from 166 to 112.5 types, while average correct
types fall from 23.5 to 19.5 despite the token-accuracy gain. The attempted
evidence fusion is an experimental variant, not a recommended default.
Its mean logged pool evaluations rise from 529,412 to 607,628.

Joint moves raise mean correct types from 23.5 to 33 at about 23% extra time.
299 and 303 selected cycles are accepted across the two chains. This is the
cheapest of the tested search changes, but its selected decoding still loses
to the baseline selected decoding.

Trigrams raise mean correct types to 29 at about 4.25 times baseline runtime.
Offered true types remain almost unchanged (166.5 versus 166). The extra
context changes ranking/search outcomes; it does not supply broad new
candidate support.

More training raises initial literal accuracy from 9.39% to 13.46% and
LM-attested target token coverage from 90.51% to 96.61%, but the measured final
mean falls slightly. True offered types rise only from 171 to 176.5. This
does not establish that more data is unhelpful: the model, initialization,
objective bias, candidate bottleneck and local optima interact.

Completed screening search time totals 34.37 minutes, excluding the interrupted
trigram attempt, profiling, source construction and evaluation. The largest
recorded process high-water mark is about 325 MB. Several variants share a
driver process, so these are cumulative process peaks, not isolated per-model
memory measurements. No million-form trained graph was allocated.

## Second-work check

The largest positive screening mean selects trigram by the recorded rule.
The selection and comparison SHA-256 are written before downloading the new
target. The text is the first 35,000 scoring words of
[The Hound of the Baskervilles](https://www.gutenberg.org/ebooks/2852),
Arthur Conan Doyle, using the pinned prose incipit. Seed 7 and 4,000 proposals
are fixed. The source model and vocabulary remain unchanged.

There are 4,248 target types, including 149 missing inventory types / 248 tokens.
The inventory ceiling is 99.29% of tokens. LM-attested token coverage is 93.74%.
Both source audits find zero exact shared 12-token windows.

| New-work result | Baseline | Trigram |
| --- | ---: | ---: |
| Literal token accuracy | 35.32% | 35.77% |
| Correct types | 45 | 50 |
| Search time | 80 s | 313 s |

The +0.45 percentage-point gain is small at nearly four times the runtime.
This is one new work/seed, not a generalization estimate. Both checkpoints,
archives and logged displacement/final-key checks pass.

The first fixed original excerpt is:

> mr sherlock holmes who was usually very late in the mornings save upon those not infrequent occasions when he was up all night was seated at the breakfast table i stood upon the hearth rug and picked up the stick

Baseline:

> never i'll get who was pieces very married in the reflections prevented on lady not sanders michelle when she was out all day was freeze for the doc points i cannot on the listening organizations and guts out the name

Trigram:

> may since then who were severe very brought in the pushed program from many so ridiculous celebrity when i were out all ladies were freeze on the meryton plan was certainly from the training periods and proper out the while

These remain poor restorations. The literal gain does not establish better
grammar or recovered meaning. All five fixed excerpts are in each run's
analysis/inspection.md.

## Agreement: a small useful core, not a complete restoration

The two-seed screens expose a serious issue with shared initial keys:
hundreds of agreeing rare mappings are unchanged wrong initial assignments.
For example, the baseline screen has 1,459 agreeing types but only eight are
correct. Agreement cannot be treated as calibrated confidence.

Reusing the earlier matched three-seed, 8,000-proposal runs gives a more
informative comparison:

| Earlier Wells runs | Majority types | Correct majority types | Majority token precision |
| --- | ---: | ---: | ---: |
| Random starts | 159 | 18 | 75.30% |
| Frequency starts | 1,458 | 27 | 64.56% |

Unanimity across all three random starts narrows this to nine types, four
correct, covering 6,805 tokens at 98.30% token precision. The high token precision
comes from frequent words; type precision is only 44.44%. For frequency starts,
224 types are unanimous but only nine are correct; most are inherited priors.

Exploratory filtering to the existing 100+ frequency band yields four unanimous
random-start mappings, all correct: **the, and, of, a**, covering 6,689/35,000
tokens (19.11%). This is a post-hoc finding on Wells, not a confidence guarantee.

Before examining consensus on the second work, fix this rule: three random
starts, all must agree, cipher frequency at least 100. Run seeds 3/5/7 for
4,000 proposals on the new 35k-token Hound prefix. The rule yields four mappings,
all correct: **the, a, his, with**, covering 3,368/35,000 tokens (9.62%).
Unfiltered unanimity contains five types, four correct, at 99.76% token precision.

This replicates a small frequent-word core across two works. It does not
certify future mappings or all source domains. It supports testing agreement
as a soft retrieval/context cue, with inherited-prior agreements separated.
No hard freezing or consensus-guided search was performed in this increment.

Supplementary three-seed check artifacts:
historical-consensus-comparison-v3.json,
consensus-replication-design.json, and
replication/consensus-check.json. Earlier diagnostic versions remain preserved.

## Objective diagnostic: scoring prefers some poor restorations

A separate gold-assisted diagnostic constructs a feasible reference dictionary:
every in-inventory target word is correct; missing words use distinct unused
forms absent from LM training. Those untrained proxy forms have identical model
statistics. Two different proxy selections give the same score, and the
dictionary remains complete and injective.

This is evaluation-only, never an initializer, search input or solver result.
Its literal accuracy is exactly the inventory token ceiling: 98.23% on Wells
for the original model, 98.63% for the corpus variants, and 99.29% on Hound.
It is not an objective upper bound.

| Fixture / model | Reference score | Best search score | Reference minus search |
| --- | ---: | ---: | ---: |
| Wells / original bigram | -262,390 | -228,963 | -33,427 |
| Wells / trigram | -264,094 | -233,556 | -30,539 |
| Wells / expanded corpus | -235,216 | -229,805 | -5,411 |
| Hound / original bigram | -235,942 | -223,247 | -12,696 |
| Hound / trigram | -236,927 | -227,903 | -9,023 |

Higher scores are preferred. Every row ranks an already found poor restoration
above this near-correct reference. Compare differences within each model;
absolute scores across different models are not recovery measurements.

This is a concrete objective/recovery counterexample involving a mostly correct
key, extending the earlier counterexamples between two wrong keys. It does not
prove that every high-scoring key must be wrong or that the global optimum is
known. It does show that stronger optimization of the present objective need
not improve literal recovery.

Out-of-domain content words and untrained forms are heavily penalized by the
source frequency/backoff model. This is a plausible contributor; the diagnostic
does not isolate every contribution. Broader training substantially narrows this
reference gap, even though the short search screen does not improve mean recovery.
Both candidate discovery and objective calibration remain important.

Code: benchmarks/scalable_english_objective_reference.py.
Data: evaluation-only/objective-reference.json under the screen root.

## Decision

Retain the options and all results. Keep existing defaults.

- Pooled evidence retrieval needs redesign before promotion: it reduces the
  very candidate support it was intended to improve.
- Joint cycles remain a relatively inexpensive experimental search option.
- The tested trigram is costly for its small replicated literal gain.
- More training improves coverage and the reference-score gap, but is
  insufficient on its own at this search budget.
- The frequent unanimous core is the most useful clue signal found here,
  with small-sample limits and no hard confidence claim.

Before another large search, test how to calibrate source-frequency versus
context/grammar evidence and how to use soft consensus anchors in retrieval.
For Latin, shared lemma/morphological structure is still needed; these English
results do not validate a Voynich word-substitution hypothesis.

## Validation and additional reproduction

119 relevant tests pass. Coverage includes full probability normalization,
all local trigram assign/swap deltas on tiny exhaustive cases, atomic three-cycles,
a pairwise-local-optimum escape case, exact checkpoint continuation, observational
logging, missing-form evaluation, common-inventory source construction, public-only
consensus collection, inherited wrong agreement, and feasible-reference integrity.

Additional commands, after the declared screens:

    .venv/bin/python -m benchmarks.scalable_english_strategy_screen select-replication
    .venv/bin/python -m benchmarks.scalable_english_strategy_screen replicate --source data/raw/scalable-english-independent/2852.txt
    .venv/bin/python -m benchmarks.scalable_english_strategy_screen consensus-check
    .venv/bin/python -m pytest tests/unit/test_scalable_*.py tests/integration/test_scalable_*.py tests/unit/test_ravi_knight_*.py tests/integration/test_ravi_knight_*.py tests/integration/test_word_mapping_pipeline.py -q

The latter check uses consensus-replication-design.json; source hash and terms
are retained in the independent raw-data manifest. All run/output paths are
exclusive. comparison.json is the frozen development screen; follow-up results
live in replication/comparison.json and replication/consensus-check.json.

## Follow-up: weaker unigram frequency pressure

The [frequency-tempering screen](scalable_english_frequency_tempering.md) tested
75%, 50%, and 25% weights. The best development mean rose from 26.58% to 29.49%,
but its second-book recovery fell from 35.32% to 28.32%. No default was changed.
The near-correct reference ranking improved, showing that fixing one objective
comparison is insufficient to fix the search result. All 120 relevant tests pass.
