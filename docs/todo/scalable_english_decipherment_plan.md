# Scalable boundary-free English decipherment: implementation plan

Status: implementation started, 2026-10-14. Continuous fixtures, disk-indexed
inventory and a normalized sparse bigram reference are delivered with a modern
engineering build. M2 injective dictionary state, sparse feasibility matching
and transactional local scoring are also delivered, including a validated
35k-token engineering exercise. See [implementation status](../scalable_english.md).
M3 bounded context/frequency retrieval, refresh, archives and broad exploration
are delivered with a cold-state support diagnostic (9/64 active hits; assisted
true-neighbor context union 56/64). Candidate discovery remains a bottleneck.
The first M4 optimizer/checkpoint implementation is delivered. Three 2,000-
proposal engineering restarts reach 16.44%/18.97%/25.25% literal token accuracy
on a 35k-token in-training fixture; type recovery remains below 1%. Final-scale
profiling, independent benchmark and grammatical/semantic validation are not
delivered. These measurements do not establish the research goal. Final modern
corpus/lexicon selection remains open; this is not a claim of reproduction.

Historical baseline: [Ravi–Knight plan](ravi_knight_implementation_plan.md),
[implemented experiments](../ravi_knight.md), and
[paper-fidelity audit](../ravi_knight_fidelity.md).

## 1. Goal and fixed assumptions

Recover useful structure from a modern-English word-substitution ciphertext of
approximately 30,000–40,000 tokens, with a large independently selected surface
inventory, eventually testing around one million forms when a defensible
resource supports that size. English is known to the solver: the user explicitly
clarified that language identification is not required.

Assume preserved word order and observable word boundaries. Each distinct cipher
type has one globally consistent plaintext surface assignment, and the main
synthetic benchmark uses an injective dictionary. Cipher IDs are opaque: their
spelling, length and internal character patterns supply no plaintext clues.
Sentence boundaries, punctuation, topic labels, original vocabulary and key are
not supplied. A complete document's endpoints may be observed and declared.
Unknown word boundaries, homophones and unknown language are outside this stage.

Research priorities, in order:

1. Grammatical structure recovery and independently assessed grammatical validity.
2. Semantic content recovery, with room for lexical alternatives and uncertainty.
3. Literal surface-word recovery.

The levels are separate evaluation axes, not a rigid inference pipeline. Grammar
alone does not establish meaning, and fluent paraphrase alone does not establish
a valid shared substitution dictionary. Every claimed alternative must work
across all occurrences and respect injectivity in the main condition.

## 2. Lessons retained and changes in scope

The existing dense, segmented English development fixture achieved about 20%
exact token accuracy under selected conditions. That is not a prediction for
this problem. It has not established grammatical or semantic recovery.

Retain as historical settings: random initialization, confidence freezing, 200
updates per EM stage and smoothing 0.1. The 200/1,000 comparison plateaued on that
fixture. More text improved common-prefix recovery; smoothing, initialization
and carryover tuning did not establish a better preferred baseline. Likelihood
sometimes selected the worst recovery restart.

Do not transfer those hyperparameters blindly: the new dictionary optimizer is
not EM, and one dictionary sweep is not an EM update. Use configurable wall-time,
proposal and sweep limits, and measure convergence/stability rather than setting
200 as a universal iteration count. Preserve historical artifact identities.

This plan prioritizes a scalable dictionary-search extension. It does not depend
on finishing the original token-level Bayesian reproduction first. Keep that
reproduction track separate; its undelivered milestones remain undelivered.

## 3. Computational architecture

Let N be ciphertext tokens, U cipher types, V inventory forms, K typical active
candidates per type, and E stored observed LM n-grams.

| Component | Intended storage/work | Forbidden default |
| --- | --- | --- |
| Inventory and metadata | O(V), stable IDs, compact arrays and string table | Python objects duplicating all metadata in each chain |
| Source LM | O(E + V), observed counts plus normalized backoff | V-by-V matrix |
| Cipher occurrences and scoring events | O(N), shared immutable index | Rebuilding all events for each proposal |
| Active candidate lists | O(U K), explicit per-type and total caps | U-by-V channel |
| Joint dictionary and reverse ownership | O(U) per chain | Independent per-token plaintext assignments |
| Context retrieval | Bounded adjacency indexes, on-demand lists and bounded cache | All pairs of left/right contexts |

For illustration, U=5,000 and K=100 means 500,000 candidate entries, around
4 MB for uint32 IDs plus float32 weights alone. Indexes, string tables, LM,
search events, joint states and temporary retrieval allocations are additional.
V=1,000,000 would make a dense float64 source bigram matrix about 8 TB.
Neither calculation is a measured complete-system memory footprint.

A fixed-order local sweep evaluating K proposals against all affected occurrences
has a rough O(N K) scoring shape, multiplied by n-gram order and move overlap.
Retrieval, candidate unions, swaps and higher-order scoring add cost; benchmark
them independently. Sparse storage does not prove fast discovery or recovery.

Initial engineering targets: approximately one hour for a complete pilot run,
including its evaluation/validation allowance, and a configurable 8 GiB search
process memory ceiling. These are profiling targets, not guarantees or new
hardware requirements. Record actual host capabilities before scale tests.
Inventory/LM construction is a separate, resumable offline job whose total cost
and disk usage must also be reported. Do not hide it outside performance claims.

## 4. Data, independence and access contracts

Create three roles with separate manifests and entry points:

- Preparation: licensed raw sources, normalization, cipher generation, private
  provenance, annotations and boundary alignment.
- Inference: immutable inventory/LM, opaque cipher document, allowed public
  document endpoints, source-independent config and search seed only.
- Evaluation: completed hypothesis hashes plus private plaintext/key/annotations.

Private artifacts include passage titles/locators when identifying the text,
key-generation seed, punctuation, sentence lengths and boundaries. Synthetic
ciphertext filenames are opaque. Inference must not receive a path to original
prose, a corpus lookup facility, truth annotations, or evaluation-derived lexical
additions. Broad source corpus provenance is distinct from revealing which work
was encrypted. Shared inventories are fixed before evaluation selection.

Store one continuous token stream per observed document. Strip punctuation,
case and sentence markers using one pinned English tokenization policy; retain
apostrophes inside words if declared. Report accuracy relative to this scoring
surface, not restoration of lost punctuation or capitalization. Select complete
contiguous word spans without supplying their original sentence boundaries.

Build source models on equally continuous training documents. Training/storage
chunks preserve cross-chunk context; document endpoints are the only baseline
resets. If raw preprocessing excludes material, split at an explicitly public
missing-content barrier rather than joining nonadjacent prose silently.

Choose modern prose from independently sourced authors/works and multiple
unrelated domains, with recorded rights, normalization and contamination checks.
Existing Austen/Alice data are historical regression/development only, not the
new modern benchmark. No topic-specific source selection based on the target.
No source retrieval or text-completion lookup during inference.

Use work/author-disjoint LM training, development and locked evaluation sets.
Freeze three independent development documents and three independent evaluation
documents as an initial design target, subject to source availability and pilot
cost. Search seeds are not independent texts. If pretrained evaluators or LMs
are added, report possible training overlap; novel licensed/private benchmark
text may be needed for strong memorization controls.

## 5. Inventory and LM probability contracts

Inventory selection:

- Preserve exact surface IDs independently of lemma/feature IDs. Build a compact
  normalized string table, source frequencies and optional ambiguous analyses.
- Publish measured inventory size and resource composition. Do not manufacture
  a million random strings or inflate with normalization duplicates to meet a
  headline count. Distinguish attested prose forms, external lexicon forms,
  names/variants and generated morphological forms.
- An inventory can exceed LM training attestation. Assign unattested but permitted
  forms a declared positive prior mass; do not map all of them to one OOV state.
- Freeze lexical inclusion before evaluating truth coverage. Report token/type
  inventory ceilings afterward; missing forms remain failures or unresolved.

First sparse source model: a normalized interpolated, discounted bigram model
with a separately specified full-support unigram base over the inventory. Reserve
configurable total mass for unattested forms, allocating it independently of the
cipher truth. Define empty-history behavior, EOS/document endpoints and all
normalizers explicitly. Do not use the same unnormalized floor for every unseen
word: its total mass changes with V. Document discount selection using training/
development source text only. Add trigram scoring only after bigram validation.

Expose conditional probability, full stream score, bounded successor/predecessor
retrieval and training-frequency lookup. Word IDs must not depend on which cipher
is being solved. Use natural logs internally. Bounded retrieval ranks proposals;
it does not redefine the LM's probability support. Never normalize only over the
current candidate shortlist and call it the full-vocabulary likelihood.

## 6. Candidate retrieval and uncertainty

Keep a candidate catalog per cipher type with ID, retrieval-source flags, cached
proposal scores and last-visited generation. Proposed starting K=100, configurable
per type and globally. Keep current assignments and joint archive references
outside eviction. Evaluate memory and recall before treating K as suitable.

Combine weak proposal sources without irreversible grammatical pruning:

1. Broad frequency bands, not equal-rank commitments.
2. Bounded plaintext predecessor/successor lists under tentative neighboring words.
3. Aggregated compatibility across multiple occurrences; initial retrieval may
   sample contexts, but final proposed-move scoring includes every occurrence.
4. Optional morphology/POS groups retaining ambiguity, added after the baseline.
5. Independently weighted full-inventory random proposals with nonzero support.

Bootstrap before reliable neighbors exist using broad frequencies, multiple
random dictionaries and structural ciphertext statistics. No claim that cipher
context vectors can be compared directly with unaligned English embeddings.
Approximate-nearest-neighbor retrieval needs a justified shared representation;
it is not the first implementation dependency.

Retrieval must be reversible: refresh uncertain types, reintroduce archived forms,
and periodically probe outside shortlists. Give recurring, influential types
more initial effort, while preserving distinct rare cipher identities. Never
prune a type because it makes the score difficult. Log proposal support and
candidate churn independently of acceptance and objective improvement.

A shortlist is not a joint key. Preserve several complete dictionary hypotheses
and derive candidate summaries afterward. Candidate weights and annealed chain
frequencies remain uncalibrated. Evaluate abstention and confidence separately.

## 7. Type-consistent search objective and moves

First target: maximize a fixed continuous source-LM score over injective complete
dictionaries. Start without extra grammar, semantic or frequency penalties. This
is heuristic dictionary optimization, not the published collapsed CRP sampler.
A deterministic injective word substitution does not require a dense stochastic
channel. Any later dictionary prior has a named, independently derived term.

Every observed cipher type receives a distinct concrete inventory form in each
complete search state. If V < U, reject the fixture as infeasible for this model.
Incomplete or low-confidence output is an evaluation/reporting choice, not a way
to delete scoring events or replace many types with a freely optimized UNKNOWN.

Initialization uses seeded sparse candidate matching with collision detection;
when no injective assignment exists within current lists, expand/retrieve rather
than silently allowing collisions. Candidate-set conflicts can prevent a perfect
matching despite sufficient inventory size. Bound matching work and log failure.
Full-inventory fallback provides unused forms without allocating U-by-V edges.

Support replacements by unused forms, swaps of occupied forms and later bounded
cycles. Maintain reverse ownership so a useful occupied proposal is considered
as a swap, not simply discarded. Uniform/full-support replacements and swaps
must permit traversal of the valid dictionary space beyond current shortlists.

Use transactional incremental n-gram scoring: change all occurrences atomically,
deduplicate affected event IDs while preserving repeated event multiplicities,
and handle adjacent repeats, self-neighbors, alternating types, document ends
and overlapping swap windows correctly. Rejected moves leave state unchanged.
Keep an independent full scorer and periodically check drift.

Begin with seeded annealed local search plus several restarts and a joint archive.
Record schedule, accepted/rejected proposals and per-move scores. Do not describe
it as posterior sampling. A later MH kernel must specify forward/reverse proposal
probabilities, support and target before claiming stationary sampling.

## 8. Evaluation is a first-class deliverable

Keep these outputs separate, always with whole-text coverage denominators:

| Axis | Main quantities | Required limitation/control |
| --- | --- | --- |
| Literal | Token/type exact recovery, frequency bands, rare forms | Inventory ceiling, retrieval recall and candidate ceiling separate |
| Original structure | POS/features and aligned dependency/role recovery | Hidden annotations evaluation-only; valid alternative parses can differ |
| Independent grammar | Agreement/government/argument errors and adjudicated acceptability | Parser output/confidence is not grammatical truth |
| Semantics | Blinded proposition/role fidelity, contradictions and entity-role preservation | Grammar and embedding similarity do not establish meaning |
| Consistency | Shared-type agreement, injectivity, unresolved output | One fluent rendering must satisfy every occurrence |
| Resources | Build/search/evaluation time, RSS, disk, proposal throughput | Include failed/timed-out runs and preprocessing cost |

Build a small fixed adjudication set before optimizing grammar or semantic
factors: genuine text, lexical alternatives verified across shared occurrences,
controlled syntax/meaning corruption and objective-exploiting search winners.
Freeze rubric and reviewer procedure. Semantic judgments should allow literal
word changes but distinguish changing an actor, relation, polarity, quantity or
entity. An automated semantic similarity metric is a diagnostic only.

Boundary-free evaluation has two tracks. Original hidden boundaries may align
reference parses or define assisted diagnostics, but the independent validity
track must use evaluator-inferred segmentation from the decoded stream. Report
segmentation errors and uncertainty. Gold sentences must not reach inference or
silently improve headline grammaticality judgments. An evaluator may use generic
English pretrained resources, declared separately from inference resources.

Report joint key hypotheses, not an independently assembled marginal maximum.
Evaluate likelihood-based restart selection, score-versus-recovery disagreements,
perfect-start damage and search exploitation. The existing counterexamples are
mandatory regression cases. Do not choose headline runs using plaintext accuracy.

If qualified adjudication is unavailable, deliver engineering/literal results and
label grammatical and semantic success unresolved. Do not substitute POS scores
for the user's primary research goal.

## 9. Proposed code organization and reuse boundaries

Create `src/voynich_smt/word_mapping/scalable/` for the new backend, leaving the
historical `ravi_knight/` package and old experiments intact.

| Module | Responsibility |
| --- | --- |
| `config.py` | Versioned corpus, model, retrieval, search and budget contracts |
| `data.py` | Public continuous integer streams and private evaluation schemas |
| `inventory.py` | Stable surface IDs, compact counts, optional ambiguous metadata |
| `sparse_lm.py` | Normalized sparse/backoff probabilities and full reference score |
| `retrieval.py` | Bounded context/frequency indexes, exploration and refresh |
| `state.py` | Joint injective dictionary, ownership and occurrence indexes |
| `incremental.py` | Transactional local deltas with independent drift checks |
| `search.py` | Budgeted annealing, restarts, candidate and joint archives |
| `artifacts.py` | Hashes, checkpoints, RNG/schedule state and immutable exports |
| `evaluation.py` | Literal/retrieval metrics and separate structure/semantic adapters |

Use `benchmarks/scalable_english_prepare.py`, `scalable_english_run.py`,
`scalable_english_evaluate.py` and `scalable_english_validate.py` as thin entry
points. Solver loading consumes public directories only; it does not call fixture
preparation or evaluator code in process. Exact access restrictions depend on the
host; test API isolation and run with private truth unavailable where supported.

Reuse corpus hashes, normalization and artifact conventions where compatible.
Audit `word_mapping/incremental.py` for transaction patterns: its inactive-type
barriers and synthetic EOS resets are incompatible with the new stream policy.
Audit `mapping.py` occurrence indexing and injectivity checks; avoid duplicating
entire form strings per state. Existing candidate catalogs assume training
attestation and cannot silently stand in for the new full inventory.

Dense HMM forward-backward is an oracle only for matching probabilistic models.
For deterministic injective dictionary search, enumerate complete dictionaries
on tiny fixtures and compare that objective directly; HMM marginals solve a
different problem. Dense dictionary full scoring and sparse LM scoring must use
identical probabilities when compared numerically.

Use the existing optional NumPy/SciPy dependency group for packed arrays if needed.
No new mandatory neural dependency, GPU service, distributed framework or Rust
backend initially. Profile Python object overhead before choosing acceleration.
JSON manifests/JSONL events plus packed numeric arrays suffice; schema version
changes are explicit. Resource build commands cache by content/config hash.

## 10. Delivery sequence and acceptance gates

### M0 — Freeze the benchmark and evaluation specification

Deliver corpus/resource selection record, supported cipher assumptions, token
policy, public/private schemas, metric/adjudication rubric and predeclared pilot
config. Record available hardware and source rights. Lock evaluation identities
before tuning; prohibit coverage-based passage selection. Verify that English
knowledge is the only supplied language/topic information.

Gate: complete source manifests and reviewable inference inputs; unresolved
reviewer/resource availability is documented. No long inference run yet.

### M1 — Continuous fixtures and normalized sparse source scoring

Implement inventory IDs, one-document continuous streams and sparse bigram
training/scoring, including positive support for unattested inventory forms.
Preserve source offsets and boundaries privately. Add full-support probability
checks, tiny-vocabulary dense equivalence and chunk-invariance tests.

Gate: numerical normalization/equivalence, deterministic build/load and no private
boundary/source-locator leakage in exported inference data. LM loss on independent
genuine English and shuffled controls is reported, not used as proof of recovery.

### M2 — Injective dictionary state and exact local updates

Implement complete dictionary state, sparse initialization, replacement/swap
moves, event indexes, rollback and independent full scoring. Enumerate all small
injective keys to check objective scores and valid move reachability.

Gate: zero mapping inconsistencies/collisions; score-delta parity for overlap,
endpoints and repeated words; infeasible candidate matching handled explicitly.

### M3 — Dynamic retrieval without oracle help

Implement frequency/context candidate unions, bounded caches, refresh and broad
exploration. Test candidate recall against exhaustive retrieval on small models;
measure real online recall using actual uncertain contexts separately from
oracle-context diagnostics. Cache refresh must not retain stale context scores.

Gate: every proposal is a valid inventory form; discarded forms can return;
retrieval never inspects truth. Report inventory absence, retrieval absence and
poor objective ranking as distinct causes. A deliberately starved candidate test
must expose the failure and recover support after refresh.

### M4 — Budgeted search and engineering scale

Implement annealing/restarts/joint archives and exact checkpoint/resume, including
RNGs, candidate state, event cache identity, proposal position and remaining
budget. Emit progress at least once per minute. Stop at a consistent transaction
boundary; reserve time for exporting and evaluation. Interrupted partial chains
are labeled and never treated as converged.

Run engineering ladders independently varying N (1k/5k/10k/35k) and measured V
(10k/100k/up to 1m supported forms), with initial K=100 and configured memory cap.
Start with smaller paired rungs rather than a full Cartesian grid. Report U,
frequency spectrum, source coverage, throughput and peak RSS. Do not use repeated
copies of a short passage as evidence of long-text identifiability.

Gate: projected and then measured target-size run fits declared hardware budget,
or produces an explicit bottleneck report. Engineering success alone does not
permit a recovery claim. If retrieval dominates, improve indexes before more
search; if scoring dominates, profile acceleration with reference parity intact.

### M5 — Development recovery and boundary calibration

Start with exact word-substitution fixtures, then the frozen independent modern
English development documents. Compare random/frequency baselines and the sparse
type solver. Keep dense EM only on sizes it can handle, as a labeled historical
comparison with different dictionary constraints.

Pair punctuation-free segmented and continuous modes on identical words; retain
same inventory, key, random streams and budgets. Compare nested training-text
lengths on their common prefix and on all observed tokens. This is transductive
inference; any held-out predictive-key diagnostic is labeled separately and
reports unseen types rather than treating them as decoded errors.

Gate: reproducible development result tables including grammar/semantic unknowns
where applicable. Freeze practical candidate budgets and schedules before final
evaluation. Repeated objective gains without independent gains trigger a stop
and diagnosis, not indefinite tuning.

### M6 — Structure and semantics validation

Run predeclared genuine/corrupted/lexical-alternative and perfect-start controls.
Add independent parsing/segmentation adapters and blinded review. Before adding
an inference grammar factor, show the evaluator distinguishes these controls;
then freeze factor weights on development only. Keep initial source-LM-only
configuration available as an ablation. Semantic factors are optional later work.

Gate: no primary grammatical/semantic claim based exclusively on training score,
POS compatibility, parser confidence or embedding similarity. If controls fail,
report that axis unevaluable rather than marking recovery successful.

### M7 — Locked Voynich-length modern-English evaluation

Use approximately 35k continuous tokens per locked document, at least three
independent documents and three search seeds if measured budgets permit. If the
budget forces fewer replications, amend and freeze the protocol before revealing
results. Broad inventory and resource inclusion must not depend on each text.

Predeclare headline primary grammar measures and secondary semantic/literal
measures after M6 calibrates their reliability, with effect thresholds tied to
adjudication uncertainty. Do not invent a universal numerical success percentage
before knowing whether the metric detects controlled errors. Report paired
document-level differences and uncertainty; search-seed dispersion is not a
substitute for independent-document uncertainty.

Gate: claim useful grammatical recovery only if independent evidence improves on
predeclared controls/baselines across documents without score-exploitation failure.
Claim semantic or literal recovery separately. Any negative result and resource
failure remains a valid deliverable. No automatic claim about real Voynich text.

### M8 — Latin transfer and optional advanced methods

After English engineering and evaluation calibration, adapt the inventory to
roughly 20k lemmas / 800k forms with ambiguous morphology and comparable
resource/coverage accounting. Do not assume English success transfers to Latin.
Later options: sparse/beam EM, corrected slice/MH sampling, trigram or neural
reranking, latent sentences and open-vocabulary spelling proposals. Each is a
named ablation with independent tests and measured cost. Generative spelling
proposals do not extract letters from opaque cipher IDs.

## 11. Required verification and failure diagnostics

- Probability mass, unseen-form support, source-score serialization and dense
  parity where the mathematical objective matches.
- Cipher/type consistency, injectivity, candidate matching conflicts and all
  scoring events retained irrespective of confidence.
- Incremental/full-score agreement, accepted/rejected transactions, repeated-event
  multiplicities, swaps, cache invalidation and checkpoint replay.
- No original boundaries in inference; rechunking never changes scores or keys.
- Public outputs invariant to evaluator-only truth edits; inference succeeds with
  truth paths inaccessible. Source corpus exclusions do not invent adjacency.
- Full-inventory exploration/reintroduction, measured online candidate recall,
  missing-inventory ceilings and increasing K as a diagnostic rather than a
  guaranteed improvement.
- Perfect-start degradation and adversarial high-score/low-validity examples;
  archived joint alternatives, never a fabricated marginal key.
- Phase-level timing, peak memory, bounded caches, missing evaluator states and
  graceful budget exhaustion without losing completed artifacts.

## 12. Immediate implementation scope

First increment is M0/M1 only: versioned config/data schemas, licensed modern
corpus selection, continuous fixture export, compact inventory, a normalized
sparse bigram reference, and tests for full support, dense parity, chunk invariance
and truth separation. Deliver a measured build/score report before search code.
Then implement M2 state and local scoring, followed by M3 retrieval. No million-
word search or neural dependency is necessary to validate the first increment.

Open implementation choices resolved through small profiling/audit tasks:
which modern broad-domain corpus and independent lexicon are available with
suitable rights; actual attested inventory counts; source storage backend;
workstation memory; qualified grammatical/semantic adjudication capacity.
Proceed on code contracts and tiny numerical tests while those are investigated.
Do not ask for permission merely to choose reversible implementation details,
and do not claim a final evaluation is feasible before these dependencies exist.

## 13. Research basis and limits

- [Ravi and Knight (2011)](https://aclanthology.org/P11-1002.pdf): historical
  word-substitution baseline; deterministic type search is a distinct extension.
- [Nuhn and Ney (2014), EM Decipherment for Large Vocabularies](https://aclanthology.org/P14-2123.pdf):
  candidate preselection/beam approximations motivate avoiding exhaustive EM;
  their evaluated scale does not certify million-form performance here.
- [Dou and Knight (2012), Large Scale Decipherment for Out-of-Domain Machine Translation](https://aclanthology.org/D12-1025.pdf):
  efficient sampling and cached proposals are relevant alternatives. Its
  large-corpus success used far more ciphertext and parallel resources than our
  benchmark; published accuracy must not be imported as an expectation.
- [Sennrich et al. (2016), Neural Machine Translation of Rare Words with Subword Units](https://aclanthology.org/P16-1162/):
  supports an optional open-vocabulary representation, not a solution to opaque
  word-key discovery.

This plan separates tractability, candidate discovery, search quality, structure,
meaning and exact wording. Each requires its own evidence.


Post-hoc diagnostics are delivered in [the diagnostic report](../scalable_english_diagnostics.md).
The frequency baseline wins on base-frequency fit despite worse context fit.
All three 2k-step trajectories replay exactly with observational logs. In seed 7,
only 1,390/6,235 types are selected, 6,094 correct assignments are never offered,
and a greedy step displaces correct and/to mappings while improving the score.
Next controlled search change: coverage-aware scheduling, with independent modern
corpus and grammatical evaluation preparation still necessary. No defaults change.

Coverage-first scheduling has now been implemented and tested in a matched
three-seed, 8,000-proposal comparison; see [the experiment report](../scalable_english_coverage.md).
It guarantees a first visit to every type if the horizon/budget permits, but
performed worse here: mean literal recovery 15.60% versus 27.13% for mixed,
with fewer true assignments offered despite complete visitation. Keep mixed
as default. Exact resume, live diagnostic traces and comparison checks are
delivered. Interleaved coverage quotas and equal-time comparisons remain
unimplemented candidates; corpus independence, broad inventory coverage and
grammatical/semantic evaluation remain outstanding.

Independent-work and initialization follow-up is delivered in
[the benchmark report](../scalable_english_independent.md): one continuous
35k-token Wells prefix, frozen 126,896-form CMU/training inventory, EWT/Austen
LM, no target vocabulary additions, zero exact 12-token training overlaps.
Frequency starts modestly improve mean recovery (27.04% to 29.70%) across
three paired 8k-proposal runs, with one regression. Both initializers remain
available; no universal default promotion. Long-document stable summation,
missing-form-aware evaluation and matched initializer comparison are implemented.
Broader corpus replication, stronger candidate discovery, learned coverage for
dictionary-only forms, grammar/semantics assessment and Latin morphology remain
open. This is independent older literary English, not a final broad-domain
contemporary benchmark.

The [five-strategy experiment](../scalable_english_strategies.md) delivers
pooled repeated-context retrieval, bounded three-word cycles, sparse interpolated
trigrams, a 1.15m-token training comparison with a common inventory, and
public-only restart-agreement diagnostics. Screening gains are small and unstable;
a second 35k-token work gives only +0.45 pp for the costlier trigram.
A fixed frequent-unanimity rule finds four correct mappings on each of two texts,
but broader confidence is unproven. Gold-assisted feasible-reference checks expose
objective/recovery misalignment. Keep defaults; investigate calibrated scoring
and soft anchors before more search scale. Grammar/meaning metrics, Latin
morphology and Voynich assumptions remain open. 119 relevant tests pass.
