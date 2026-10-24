# Scalable continuous English decipherment

Status: foundations, dictionary transactions, retrieval and the first budgeted
optimizer are delivered, 2026-10-14. The first literal search measurements use
an in-training engineering fixture; independent benchmark, grammatical and
semantic recovery remain unestablished. Implementation follows the
[scalable English plan](todo/scalable_english_decipherment_plan.md), preserving
the [historical EM experiments](ravi_knight.md).

## Implemented contracts and numerical reference

New package: `src/voynich_smt/word_mapping/scalable/`.

- `config.py`: versioned English tokenization and numerical configuration.
- `data.py`: opaque integer cipher streams, deterministic injective generation,
  content identities, strict public schemas and separate private truth export.
- `inventory.py`: read-only SQLite surface IDs and bounded lookup cache. Building
  streams words into a disk sort/deduplication; IDs follow lexical order, not the
  cipher or evaluation vocabulary. Opening verifies contents against identity.
- `sparse_lm.py`: observed bigram counts, uint64 outcome counts and normalized
  absolute-discount interpolation with a full-support base. No V-by-V matrix.
- `corpora.py`: preparation-only EWT document grouping; source IDs and sentence
  ends are excluded from public cipher exports.

The initial SQLite inventory is disk-indexed, not a claim of optimal packed
storage. The sparse LM still uses Python edge dictionaries and full identity
hashing temporaries. A measured million-form backend is not delivered yet.

The LM base reserves configured total probability for inventory forms unattested
in training, distributing it uniformly among those forms. Observed forms and EOS
share the remaining mass by counts. If all forms are observed, all mass goes to
observed outcomes. Absolute discount is per observed edge; residual mass backs
off to the normalized base. Unseen predecessor contexts use the base directly.
EOS participates in the outcome distribution. BOS is conditioned on a nonempty
document when scoring, excluding an immediate EOS and matching the dense HMM's
nonempty-segment convention. Document endpoints are actual observable endpoints.

Every permitted surface ID has positive probability, including independently
supplied but unattested inventory words. A spelling absent from the inventory is
rejected, never silently merged with another spelling. Training cannot add words
to an existing inventory. Current default discount 0.5 and unattested mass 0.01
are reference settings, not tuned recovery choices.

Storage chunks retain continuous context. There is one start and one end event
per document; no sentence-boundary or chunk-based reset. The small dense adapter
has a type-count guard against accidental large allocations. It supplies matching
probabilities to the old HMM for numerical checks, not an equivalence claim
between HMM inference and future deterministic dictionary search.

## Modern source and engineering measurement

Pinned [UD English EWT r2.17](https://github.com/UniversalDependencies/UD_English-EWT/tree/r2.17)
train/development data and the original license are cached with URL/byte/hash
manifest under `data/raw/scalable-english/`. The project identifies the resource
as [CC BY-SA 4.0](https://universaldependencies.org/treebanks/en_ewt/index.html).
Attribution and caveats are recorded in its local README. This is a provisional
engineering source; the long, independent modern evaluation corpus remains open.

The build uses only normalized EWT training words for inventory selection. There
is no artificial padding, dev-based lexicon expansion or final benchmark claim.

| Quantity | Measured value |
| --- | --- |
| Training documents | 540 |
| Scoring tokens | 176,085 |
| Inventory forms | 15,574 |
| Stored observed edges, including endpoints | 97,406 |
| Inventory file | 495,616 bytes |
| Model file | 1,331,200 bytes |
| Build/save/load/diagnostic elapsed | Approximately 0.61 s |
| Peak process RSS in the build run | 107,298,816 bytes, macOS measurement |

The timing includes small-corpus build/save, model reload and development scoring;
it excludes raw download time. This is one development-machine measurement, not
a throughput guarantee or projection to one million words. Inventory build alone
was approximately 0.16 s and LM build/save approximately 0.29 s. Cache/backend
choices need separate larger-scale profiling.

The dev split contains 318 documents / 21,741 normalized tokens. Its 1,594 missing
tokens cause 243 complete documents to be excluded from full-stream scoring.
Only 75 documents / 1,432 tokens are scored. On that explicitly coverage-selected
subset, genuine loss is 6.30936 nats/event versus 7.62534 for seeded within-document
word shuffles. This is a source-model diagnostic, not a representative held-out
performance estimate. Do not discard the exclusions or imply all dev text was
scored. Missing forms were not added after inspection. Standard EWT splits are
not verified author-disjoint, and many source documents are short.

Artifacts: `experiments/results/scalable-english/foundations-ewt-v1/`, with frozen
protocol, inventory/model SQLite files and measured report. An independent
validator reconstructs edge/count statistics from raw text, checks hashes and
normalization identities, and recomputes admitted development/shuffle losses.

```sh
.venv/bin/python -m benchmarks.scalable_english_build
.venv/bin/python -m benchmarks.scalable_english_validate
```

The builder rejects an existing output directory; choose a new `--output` for
reruns. Resource source paths belong to preparation commands, not solver inputs.

## Continuous cipher fixture preparation

```sh
.venv/bin/python -m benchmarks.scalable_english_prepare --text /path/to/licensed-document.txt --output /tmp/continuous-fixture --max-tokens 35000
```

`public/cipher.json` contains only opaque documents, dense observed type IDs,
format/tokenization version and hash. `evaluation-only/` holds the key, normalized
plaintext, key seed, original-source identifiers/hashes and character offsets.
Document boundaries are observable; sentence boundaries/punctuation are absent
from the public contract. Key generation is independent of LM/inventory selection.

The scoring surface lowercases ASCII words, retains internal apostrophes and
normalizes curly apostrophes. Digits, hyphens and non-ASCII letters separate
scoring tokens. This policy is explicitly lossy. Character offsets refer to the
decoded source string, not raw UTF-8 byte positions. Full original spelling,
numbers and punctuation are not recovered by this contract. No claims of gold
UD annotation alignment are made. More robust normalization/alignment remains
an audited future change with a new version.

## Verification and milestone status

Fifty-six targeted tests pass across the new foundation and previous Ravi–Knight
reference/pipeline tests. New checks cover normalized probability mass with and
without unattested forms, positive unseen-context support, numeric discount
formula, exhaustive small-sequence dense/full-score parity, arbitrary rechunking,
real document boundaries, deterministic IDs, serialization, inventory corruption,
strict public schemas, key consistency and separate private metadata.

Integration tests prepare a continuous fixture, alter private truth and remove
the original source, then load identical public inputs. The numerical scorer
consumes inventory IDs and has no truth/provenance path. API separation is tested;
an OS-enforced isolated solver process is not yet delivered because search does
not exist. Existing private-directory readability is not presented as isolation.

M1 code foundations and modern engineering build are delivered. M0 final corpus/
lexicon selection, adjudication and author-disjoint benchmark lock remain open;
M1's representative independent source-quality gate is not claimed complete.
The next code increment is M2: complete injective dictionary state, replacement/
swap transactions and independently checked local scores. Full-inventory dynamic
retrieval follows in M3. Search and independent grammar/semantic validation remain
substantial work, not consequences of sparse storage alone.

## M2: complete dictionaries and transactional scoring

The second increment adds `scalable/state.py` and `scalable/incremental.py`.
The state stores one concrete inventory ID for every observed cipher type,
requires injectivity, and binds snapshots to public cipher/inventory identities.
It does not duplicate inventory strings. Seeded random initialization samples
without replacement; insufficient inventory size is an explicit failure.

Sparse candidate initialization uses iterative augmenting paths. It can reassign
earlier rows to find a complete matching instead of relying on greedy choices,
and it raises `CandidateConflict` when the supplied graph has no complete key.
Nonempty lists and V >= U do not guarantee a feasible matching. Candidate
expansion is the next layer's responsibility. Matching is feasibility, not a
maximum-weight or linguistically optimized assignment. No U-by-V array is built.

Local moves support replacements by unused forms, swaps of occupied forms,
assignment-or-swap routing and atomic multirow cycles. Proposals are immutable
and do not mutate assignments or scores. Discarding a proposal rejects it.
Commit checks scorer identity and generation; foreign or stale moves fail.
Reverse ownership changes atomically, and other dictionary chains remain
independent even when sharing an immutable event/occurrence index.

Equivalent cipher bigrams are aggregated with multiplicities, including one
start and one end event per original document. A proposal deduplicates affected
event IDs across changed types while retaining every event's full count. This
handles adjacent repeats, self-transitions, alternating types and overlapping
swaps without double counting. All occurrences of a type change together. There
are no inactive types, sentence resets, dropped events or UNKNOWN assignments.

The objective is the fixed sparse source-model log probability. There are no
channel, grammar, semantic or frequency penalty terms. An independent scorer
renders each document and calls the full LM scorer occurrence by occurrence;
periodic validation checks both total score drift and cached event terms.
This is deterministic dictionary scoring, not HMM marginals or posterior sampling.

### Verification

Sixty-nine targeted tests pass across both new layers and the historical
reference/pipelines. Dictionary-specific checks include:

- Exhaustive sparse-matching feasibility against all keys for all 512 candidate
  graphs on three types/three forms, including empty lists and conflicting lists.
- A 1,500-type augmenting-path case without recursive stack dependence.
- Exhaustive local deltas over tiny injective dictionaries with single-token
  documents, repeated words, alternation, adjacent repeats and multiple endpoints.
- Reachability of all small injective keys using replacements/swaps, including
  when the inventory has no unused forms.
- Cycles, collisions, no-ops, stale/foreign proposals and independent chains.
- One thousand randomly accepted/rejected moves checked against full rescoring.
- Public-artifact transaction replay, model binding and immutable index sharing.

### 35k-token engineering exercise

`benchmarks/scalable_english_moves.py` exercises 2,000 uniform proposals with
random 50% accept/reject decisions, validating against full scoring every 100
proposals. It does not optimize a key or compute recovery. Uniform proposals
often touch rare types; this timing does not represent expensive frequent-type
candidate ranking, retrieval, neural scoring or a full search sweep.

| Quantity | Observed value |
| --- | --- |
| Ciphertext tokens | 35,000 |
| Original EWT documents | 24 |
| Observed cipher types | 6,235 |
| Independent inventory forms | 15,574 |
| Aggregated scoring events | 24,443 |
| Scoring event occurrences, including endpoints | 35,024 |
| Proposed / accepted moves | 2,000 / 1,000 |
| Swap / replacement proposals | 815 / 1,185 |
| Full validation checks | 20, all passing |
| Index build + initial score | Approximately 0.038 s |
| Proposal evaluation total | Approximately 0.016 s |
| Full validations total | Approximately 0.480 s |
| Whole transaction exercise | Approximately 0.558 s |
| Peak process RSS | 88,031,232 bytes, macOS measurement |

Resource loading and fixture generation are outside the exercise timing, but
inside the process lifetime used for peak RSS. This is a single-machine
engineering measurement. The fixture's prose also occurs in LM training, and
35k tokens span 24 original documents rather than one long work. These facts
exclude using it as an independent decipherment benchmark or a recovery claim.
There is no million-form or topic-independent inference result yet.

Saved artifacts: `experiments/results/scalable-english/dictionary-moves-ewt-v2/`,
with public cipher stream, resource hashes, full counts/timings and final key.
The initial v1 attempt failed before the proposal loop due to a counter
initialization typo; its preparation artifact and failure note remain preserved.

`benchmarks/scalable_english_moves_validate.py` independently replays the seeded
assignment choices using simple ownership bookkeeping without incremental
scoring, verifies the final key/counters, and recomputes full initial/final scores.
The saved 2,000-proposal run passes validation. Timing is not a recovery measure.

```sh
.venv/bin/python -m benchmarks.scalable_english_moves --output experiments/results/scalable-english/dictionary-moves-ewt-v2
.venv/bin/python -m benchmarks.scalable_english_moves_validate
```

Existing output directories are protected; use a fresh path for a rerun. The
next increment is M3: bounded dynamic candidate retrieval, candidate refresh and
full-inventory exploration with measured support/recall. M0 final long-form
corpus selection and independent grammar/semantic adjudication remain open.

## M3: bounded dynamic candidate retrieval

`scalable/retrieval.py` now supplies a versioned-by-artifact retrieval
configuration, sparse context indexes, dynamic per-type lists and broad proposals.
This is the first retrieval backend, not an optimizing solver or a solution to
the candidate-discovery problem.

Single-context queries rank full-model probabilities: successors for a left
neighbor, and possible predecessors for a right neighbor. The indexes combine
observed adjacency with high-base-probability or high-backoff candidates instead
of constructing all context pairs. Predecessor ranking includes unseen contexts;
reversing an observed bigram list alone would miss them. Floating near-ties are
handled before final probability/ID tie-breaking. Tiny exhaustive and randomized
model checks agree with full-inventory rankings across several discount/prior
settings. BOS/EOS are handled explicitly and never proposed as surface forms.

Context results use a bounded LRU cache keyed by direction, actual neighbor ID
and requested count. The source model is fixed. A cache miss scans that context's
observed neighbors plus fallback candidates; this is not a guarantee of constant
query cost for high-degree contexts. Index construction remains O(E + V) storage
with temporary frequency sorting; million-form build time/memory is unmeasured.

A candidate refresh combines current assignment, seeded random forms, bounded
archives/retained candidates, a broad frequency band and up to eight sampled
occurrence contexts. Default active K=100, pool cap=400, 16 candidates per
single context and eight random refresh draws. Every offered candidate is ranked
using its full assign-or-swap score delta over all affected occurrences, even if
retrieval used sampled contexts. Occupied words cause swaps; they are not silently
removed. The current assignment survives ranking, preventing shortlist churn
from invalidating a complete key. No score is called a posterior probability.

Combined lists are heuristic: pool truncation, limited context samples and the
current dictionary can all omit good words. Score pruning is separately audited
from pool absence. A diagnostic callback exports the offered IDs without making
the entire pool permanent search state. Any dictionary generation change forces
row refresh and rescoring; unchanged LM context queries remain reusable. Refresh
must not mutate the dictionary, including through its audit callback.

Active entries and archive entries have separate global caps, each controlled
by `total_entries`, plus per-row caps. LRU eviction removes derived candidate
rows, not dictionary assignments. Archived words can be offered again. Per-query
cache and pool budgets are also explicit; Python object/provenance overhead is
additional to raw IDs. This storage does not duplicate the inventory per chain.

A proposal chooses full-inventory uniform exploration with default probability
0.1, otherwise a candidate from the current active list. Exploration bypasses
pool admission and score pruning: each inventory form has proposal probability
at least epsilon/V for the selected cipher type, including unattested forms and
occupied forms handled as swaps. This supplies reachability, not efficient rare-
word discovery or exact sampling. The current policy is heuristic; no MH/Gibbs
or calibrated posterior claim is made. Uniform exploration alone can require
many draws when V is large.

### Cold-start support diagnostic

The public 35,000-token engineering fixture has 6,235 cipher types and a 15,574-
form inventory. Select eight most frequent types plus 56 seeded uniformly drawn
remaining types, without plaintext access. Start from a random injective key;
retrieve candidates and reject all 1,000 subsequent proposals. Preparation and
evaluation retain truth separately; the inference function accepts only model,
public cipher, selected type IDs and config.

| Quantity | Observed value |
| --- | --- |
| Sampled types | 64, deliberately mixed frequent/uniform sample |
| True word offered in bounded pool | 9/64 (14.06%) |
| True word retained in active list | 9/64 (14.06%) |
| Frequent types with active truth | 8/8 |
| Other sampled types with active truth | 1/56 |
| True-neighbor context union, assisted diagnostic only | 56/64 (87.50%) |
| Active / archived candidate entries | 5,129 / 102 |
| Context cache entries | 256, at its configured cap |
| Broad exploration proposals / total | 106 / 1,000 |
| Index construction | Approximately 0.026 s |
| First 64 refreshes | Approximately 0.363 s |
| Whole diagnostic, including assisted evaluation | Approximately 0.596 s |
| Peak process RSS | 85,950,464 bytes, macOS measurement |

The active and pool hits coincide on this sample: current failures mainly arise
before final active-list ranking, not from pruning true words already offered.
This does not prove the same for other states or texts. Online context quality is
a bottleneck. The true-neighbor diagnostic supplies forbidden information only
to evaluation; it excludes trivially protected current assignments, but its
context union can be larger than K and is not an equivalent online condition or
a strict upper bound. The fixture also appears in LM training, making this an
optimistic engineering diagnostic. It does not establish domain transfer.

The sampled token-weighted hit rate is 97.33%, dominated by the eight frequent
types. It is explicitly NOT whole-text candidate coverage, decipherment accuracy,
or evidence that most word types are recoverable. Zero true words occurred among
the initial refresh random draws; broad random support is a safeguard rather than
a demonstrated bootstrap solution. No proposal is accepted in this diagnostic.

Artifacts: `experiments/results/scalable-english/retrieval-ewt-v2/`, with public
cipher, separate private truth, fixed configuration/seeds, offered pools, active
rows/source flags/deltas and 1,000 proposal records. v1 is retained as the earlier
audit before explicit offered-pool export. v2 adds that measurement without
changing the observed active recall. No historical outputs are overwritten.

The validator deterministically replays all 64 rows and 1,000 proposals, checks
caps and current-state preservation, independently recomputes full scores for
128 candidate moves, recomputes online support metrics, and reproduces the
explicitly assisted context diagnostic. The saved artifact passes validation.

Eighty-two targeted tests pass. Added checks cover exact context indexes against
exhaustive scoring, 30 seeded random sparse models with unseen forms, cache/entry/
archive caps, stale-row refresh, full-swap deltas, deterministic replay, archive
reintroduction and a deliberately starved shortlist whose excluded inventory
forms remain reachable via broad exploration. Integration tests reproduce the
full artifact/evaluation separation on a small fixture.

```sh
.venv/bin/python -m benchmarks.scalable_english_retrieval --output experiments/results/scalable-english/retrieval-ewt-v2
.venv/bin/python -m benchmarks.scalable_english_retrieval_validate
```

Use a fresh output directory for reruns. Next is M4's budgeted optimization loop,
with periodic refresh and joint key archives, then development recovery evaluation.
The low cold-start support is a recorded risk for that search. Do not infer that
longer optimization will repair it automatically. Final long-form corpus/lexicon
selection and independent grammatical/semantic evaluation remain open.

## M4: budgeted optimization, restarts and exact continuation

`scalable/search.py` implements heuristic annealed dictionary optimization. Each
step selects a cipher type from a mixture of uniform-type and token-frequency
sampling. Half of proposal choices exploit the best current active candidate;
the other half use the retrieval proposal policy, including broad exploration.
This preserves positive access to every type/form while concentrating some
computation on useful moves. There is no MH correction or posterior claim.

Initial reference schedule: exponential temperature 1 to 0.05 over a configurable
proposal count, 50% greedy proposal choice, 50% frequency-weighted type selection,
forced refresh every 100 proposals, full validation every 500 and checkpointing
every 1,000. Changed dictionary generations also trigger candidate refresh as
before. Nonnegative moves are accepted; negative moves use an annealed acceptance
rule. No-ops advance the proposal schedule but do not mutate the dictionary.
The defaults are engineering choices, not tuned recovery parameters.

The archive stores up to four complete distinct keys per restart, selected by
source score. Nearby trajectory keys need not be substantially diverse, and
archive weights are not calibrated. Across restarts, selection is by best archived
source score with seed ID as deterministic tie-break, never plaintext recovery.
Initial, current and archived scores/keys are retained separately.

Budget checks occur between transactions. Time and conservative peak-RSS limits
can stop a run; one expensive retrieval step may exceed the remaining wall time.
The CLI divides its budget and reserve evenly across restarts (default one hour
total search allocation). Library SearchConfig budgets are per chain. Source
resource loading and external evaluation are outside that search clock; reserves
provide an allowance, not a hard end-to-end deadline. Runtime memory checks use
the process high-water RSS and cannot prevent a transient allocation overshoot.
Progress events are emitted approximately every 30 seconds during active work.

Checkpoints include resource/config identities, assignments/reverse-owner-derived
state, numeric event cache, generation, annealing position, both RNG states,
ordered candidate rows/archives/context cache, counters and whole-key archives.
A checksum protects the serialized payload; atomic replacement preserves the
previous checkpoint if serialization fails. Load checks model/cipher binding,
entry caps, full score consistency and joint-key scores. Numerical caches are
preserved rather than rebuilt with a different floating summation history.

Proposal-limited continuation replays exactly in tests, including subsequent
choices, accept/reject decisions and cache state. Timing/stop positions can differ
by host. Use the same implementation/environment: format v1 is not a promise of
compatibility across future algorithm changes. Partial invocations retain the
original full temperature schedule. Resume preserves consumed time; it does not
silently replenish an exhausted budget. A mid-operation process failure resumes
from the last completed atomic checkpoint, not necessarily the last proposal.

### Separate inference and evaluation commands

`benchmarks/scalable_english_run.py` accepts resources and a public cipher path;
there is no truth argument. It stores a frozen protocol, per-seed checkpoint/
result files and a score-selected inference summary. Existing outputs require
explicit `--resume` with a matching protocol. `--steps` permits partial invocations
without redefining the annealing horizon.

`benchmarks/scalable_english_evaluate.py` is a separate command that loads private
truth after inference. It validates resource identities, restores checkpoints,
fully rescores initial/current/all archived keys and computes token/type exact
metrics plus a frequency baseline. Grammar and semantics are explicitly
`not_evaluated`. Integration tests remove the original text and truth file while
inference runs, then restore truth for evaluation. This is API separation, not a
new OS-level isolation guarantee.

### First bounded search result

Run three fixed seeds (3/5/7), 2,000 proposals per seed, 100 active candidates,
10,000 total active entries and four archived joint keys. Each original chain
was allowed 120 seconds with a five-second reserve; all finished by proposal
count. The equivalent current CLI bundle allocation is 360 seconds / 15 seconds
reserve. Actual summed chain time was 93.92 seconds.

Use the existing 35,000-token EWT engineering fixture, spanning 24 documents and
6,235 cipher types, against the 15,574-form inventory. The fixture text also
appears in LM training. This is an optimizing engineering/development diagnostic,
not independent modern-English or Voynich recovery evidence.

| Seed | Initial token accuracy | Score-selected token accuracy | Correct word types | Chain time |
| --- | --- | --- | --- | --- |
| 3 | 0% | 16.44% | 18/6,235 | 29.71 s |
| 5 | 0.0057% | 18.97% | 20/6,235 | 32.45 s |
| 7 | 0% | 25.25% | 32/6,235 | 31.76 s |
| Mean | — | 20.22% | — | — |

Frequency matching scores 8.53% token accuracy (6 correct types). Source-score
selection chooses seed 7, which is also the best literal run here; that is not a
generalized selection guarantee. Its type accuracy is only 0.513%, so frequent
words account for much of the token result. Only 2,000 proposals for 6,235 types
is an early search diagnostic, not a convergence claim.

The best source score improves from about -417k to -293k in seed 7. However,
frequency matching scores about -276k, BETTER than every search winner while
recovering substantially fewer literal tokens. This is a retained score/recovery
counterexample; neither additional optimization nor higher score guarantees
better structure, meaning or wording. Do not compare these percentages directly
with the old 487-token segmented EM benchmark as if inputs/models matched.

Accepted moves: 1,363 / 1,343 / 1,349; no-ops: 144 / 159 / 169. Each chain passes
five full score validations. Peak process RSS reaches 109,330,432 bytes in the
bundle. Candidate refreshes number 1,902 / 1,897 / 1,893; active entries remain
below the 10,000 cap. Costs include search/index/checkpoint operations during
chains; external model loading and final evaluation are separate.

Artifacts: `experiments/results/scalable-english/search-ewt-v1/`, containing the
protocol, copied public stream, per-seed checkpoint/result files, `inference.json`
and evaluation-only measurements in `evaluation.json`. All three restored chains,
all twelve archived keys and initial/current keys pass full-score validation.
No grammar or semantics result is inferred from the literal measurements.

Ninety-two targeted tests pass after this increment. Added checks cover exact
checkpoint continuation, time/memory stops, partial runs, payload tampering,
whole-key archive bounds, budget splitting and separate public-only inference/
private evaluation integration. Earlier numerical/retrieval regressions remain.

```sh
.venv/bin/python -m benchmarks.scalable_english_run --public experiments/results/scalable-english/retrieval-ewt-v2/public/cipher.json --output experiments/results/scalable-english/search-ewt-v1 --proposals 2000 --budget-seconds 360 --reserve-seconds 15
.venv/bin/python -m benchmarks.scalable_english_evaluate --run experiments/results/scalable-english/search-ewt-v1 --truth experiments/results/scalable-english/retrieval-ewt-v2/evaluation-only/truth.json
```

Use a new output path for a fresh run. For an interrupted/partial run, repeat the
same budget/schedule flags with `--resume`; `--steps` can intentionally pause at
a proposal boundary. Increasing the proposal horizon or replenishing an exhausted
budget is a new protocol, not an implicit resume.

Next priorities are independent source/inventory coverage and development
recovery calibration, not a success declaration from this in-training fixture.
Checkpoint infrastructure is available for larger controlled runs, but long-form
modern texts, million-form resources, representative grammar/semantic evaluation
and target-scale resource profiling remain undelivered.


The [post-hoc score and failure diagnostics](scalable_english_diagnostics.md)
now decompose the frequency-baseline counterexample, inspect fixed excerpts,
and replay all candidate offers without changing trajectories. They identify
limited type visitation, candidate starvation and explicit score-improving
literal regressions. No search defaults change; grammar/semantics remain unscored.

The [matched coverage-first experiment](scalable_english_coverage.md) is complete:
three paired seeds at 8,000 proposals each. Coverage-first visited every type
but reduced mean literal token recovery from 27.13% to 15.60%, and reduced
true-assignment offer coverage. Mixed remains the default; its score-selected
chain reached 41.74% literal token recovery on this training-overlapping fixture.
Coverage-first was substantially faster, leaving equal-time comparison open.
All six runs completed and passed trajectory/score validation; 103 relevant
tests pass. The report preserves protocols, per-seed results, limits and the
unimplemented option of interleaving a coverage quota with frequent-type refinement.

The [independent-work benchmark and initialization comparison](scalable_english_independent.md)
now uses one continuous 35k-token Wells prefix, an independently frozen
126,896-form inventory, and an EWT/Austen source model. It finds zero exact
shared 12-token windows with training; 340 missing types remain unrecoverable.
At 8k proposals on three paired seeds, frequency initialization raises mean
literal token recovery from 27.04% to 29.70% (two improved seeds, one worse);
source-score-selected recovery rises from 26.90% to 34.91%. Starting frequency
matching alone gives 9.39%. Random remains default; frequency is an explicit
restart option. Both bundles validate, 109 relevant tests pass, and
grammatical/semantic recovery remains unmeasured. Stable document summation
also fixes a precision failure exposed by one continuous long document.

The [five-strategy screen and second-work checks](scalable_english_strategies.md)
are complete. Pooled contexts, joint cycles and trigrams give small unstable
two-seed mean gains; corpus expansion does not raise recovery at this budget.
The trigram's new-work gain is only 35.32% to 35.77% at roughly four times the
cost. Frequent unanimous mappings from independent starts form a small correct
core on two texts, covering 19.11% and 9.62% of tokens. A gold-assisted feasible
reference also shows that current scoring can prefer poor restorations over
98–99%-literal-correct keys. No defaults change; objective calibration and soft
consensus-guided retrieval are next candidates. All 119 relevant tests pass.
