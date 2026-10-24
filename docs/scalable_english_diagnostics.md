# Why the first sparse-search results remain weak

Post-hoc diagnostics, 2026-10-14. This analyzes the existing 35,000-token EWT
engineering fixture and unchanged 2,000-proposal trajectories. It is not a new
validation set, a grammatical/semantic evaluation, or a tuned search result.
See [implementation status](scalable_english.md).

## 1. The frequency-score counterexample

The continuous bigram score can be written exactly as a sum of base-distribution
log probabilities plus the remaining contextual contribution. Both include
actual document endpoints; BOS's nonempty conditioning is in the contextual
remainder. This is an accounting identity, not two independently trained models.
Higher (less negative) scores are preferred.

| Key | Literal token accuracy | Base-frequency component | Context component | Full source score |
| --- | --- | --- | --- | --- |
| Frequency matching | 8.53% | -244,253 | -31,630 | -275,883 |
| Score-selected search seed 7 | 25.25% | -276,511 | -16,756 | -293,268 |
| True dictionary, diagnostic only | 100% | -254,507 | +115,247 | -139,261 |

Frequency matching's base advantage over seed 7 is approximately 32,258 log
units. Its context contribution is approximately 14,874 units worse, leaving
it preferred by 17,384 overall. Thus better common-word frequency fit outweighs
worse contextual fit in this comparison of two wrong keys. Observed-edge rates
are similar (25.59% frequency versus 25.31% seed 7), so counting seen bigrams
alone does not resolve the issue either.

The true key scores much better than both. This does NOT show that the source
model rejects the correct dictionary globally. Search/candidate discovery is
still far from that attractive region. The fixture also occurs in LM training,
which strongly favors this true-key diagnostic and prevents external-validity
claims. Do not fit a new objective weight from these values and call it validated.

## 2. Fixed decoding inspection

Before viewing passages, fix five corpus-wide quantile offsets (0, 7,000, 14,000,
21,000, 28,000), taking up to 40 words without crossing document endpoints.
Render the reference, frequency key and all three search winners. The generated
[inspection set](../experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2/inspection.md)
retains EWT attribution and links back to the local source/license record.

Assistant qualitative inspection: both the frequency baseline and all search
winners remain largely incoherent in these samples. Search recovers some useful
function-word frames, but most content substitutions do not preserve the
reference's entities or assertions. This is not independently adjudicated human
review and supplies no numerical grammatical/semantic acceptability claim.
Local plausibility, literal matches and semantic fidelity remain distinct.

Shared mappings reveal systematic function-word errors: in seed 7, original
`and` decodes as `to`, while original `to` decodes as `and`. The other two seeds
also map `to` to `and`. These confusions affect many contexts globally; the
25% token result is not evidence of recovered grammatical relationships.

## 3. Where the literal recovery comes from

For the score-selected seed 7:

| Cipher frequency | Types | Tokens | Correct types | Token recovery in band |
| --- | --- | --- | --- | --- |
| 1 | 3,166 | 3,166 | 0 | 0% |
| 2–4 | 1,976 | 5,143 | 1 | 0.039% |
| 5–19 | 882 | 7,496 | 1 | 0.160% |
| 20–99 | 173 | 6,586 | 12 | 10.46% |
| 100+ | 38 | 12,609 | 18 | 64.53% |

The 100+ band contributes 8,136 of the 8,839 correct token positions: about 92%
of all correct tokens. No singleton type is recovered in any restart. Word-type
accuracy is therefore a critical companion to the token headline.

## 4. Trajectory attribution without altering inference

Original checkpoints retain candidate caches but not complete historical offers.
A public-only observational replay now records every pool and actual move as
streamed gzip JSONL. No truth enters replay. The logger adds no random draws,
proposals or accept/reject decisions. Each seed reproduces the saved full joint
archive EXACTLY, and final dictionary/score checks pass. The roughly 94-second
replay is additional diagnostic work, not a longer search or fresh evidence.

Evaluation reads truth only after replay. An offered candidate counts for the
selected cipher type and for the implied other row of a possible swap. Actual
proposal and acceptance flags also include indirect swap effects. Initial
correctness, displacement and later reacquisition are tracked. Classification
is relative to the saved score-selected key; it is descriptive, not causal.

All 6,235 true word types are in this inventory. There are zero inventory-absence
failures in this in-training fixture; that is not a realistic unknown-inventory
coverage estimate.

| Final category | Seed 3 | Seed 5 | Seed 7 |
| --- | --- | --- | --- |
| Recovered | 18 | 20 | 32 |
| Correct word never offered | 6,113 | 6,116 | 6,094 |
| Offered, never active or actually proposed | 3 | 3 | 7 |
| Active at some point, never actually proposed | 98 | 93 | 98 |
| Correct assignment proposed but never accepted | 1 | 2 | 0 |
| Correct at some point, absent from final selected key | 2 | 1 | 4 |

For seed 7, 6,094/6,235 types (97.74%) never have a correct assignment offered
by the recorded pool/move mechanisms. Of these, 4,843 are never selected as the
primary update type; 1,251 ARE selected but still lack the right offer. Only
1,390 distinct primary types are visited at all. Some unvisited types can still
receive swap offers, so these sets are intentionally distinguished.

The 2,000-proposal run is shorter than even one guaranteed pass over 6,235 types.
This is both a scheduling-coverage limitation and a candidate-discovery
limitation. It is not justified to attribute every failure to pruning or to a
poor objective: most correct candidates never reach that decision point.
Conversely, more steps cannot be assumed to repair visited types whose contexts
continue to yield poor candidates.

## 5. A concrete score-improving literal regression

In seed 7, step 446 greedily swaps away the then-correct assignments for `and`
and `to`. The move improves the source score by 67.29184456 but makes 967 + 957
= 1,924 token positions incorrect (5.50 percentage points of this fixture).
Neither word is recovered in the final selected dictionary. Other greedy moves
later displace correct assignments for `before` and `you`.

This is a direct local objective/recovery counterexample, not merely a comparison
between separate wrong runs. It does not quantify grammatical damage or prove
that all correct-key neighborhoods are unstable. The move's acceptance is
correct under the implemented objective; the objective does not encode literal
correctness. Some displacement events in other seeds are later repaired, which
is why event totals need not equal final acquired-then-lost type counts.

## 6. What the diagnostics justify next

First test coverage-aware scheduling: a declared pass that visits every observed
type, followed by adaptive/frequency-weighted refinement. Compare at a fixed
proposal or wall-time budget and report coverage/support, not only score. The
current 2k-proposal pilot cannot establish long-run behavior.

For visited-but-starved types, compare broader context/proposal retrieval on
frozen development text, preserving full-inventory exploration and measuring
correct-offer recall. For the active-but-unselected set, inspect candidate rank,
move implications and scheduling before changing acceptance rules. Do not inject
truth-derived candidates into a headline run.

In parallel, independent modern-English source/lexicon selection and a calibrated
grammatical evaluation set remain necessary. Changing LM weights, increasing
neural strength or launching much longer search without those checks could
simply optimize a more fluent wrong key. No defaults change in this diagnostic.

## Artifacts and verification

- [Trace report](../experiments/results/scalable-english/search-ewt-diagnostics-v1/traces/trace-report.json)
- [Machine-readable analysis](../experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2/diagnostics.json)
- [Fixed inspection excerpts](../experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2/inspection.md)

The initial analysis directory is retained; analysis-v2 adds explicit displacement
events without changing counts or inference. Three compressed traces total
approximately 7.74 MB. All three replayed archives match; final keys, move counts,
frequency-band totals and recovered-category totals agree with original outputs.
A separate validator fully rescores each accepted displacement before/after,
checks net literal changes and reproduces the step-446 loss of 1,924 tokens;
its results are saved in analysis-v2/validation.json.
Ninety-six targeted tests pass, including observational RNG/decision invariance,
disjoint failure categories, indirect swap attribution and end-to-end artifact
analysis. There is no independent grammar or semantic score.

```sh
.venv/bin/python -m benchmarks.scalable_english_trace
.venv/bin/python -m benchmarks.scalable_english_diagnostics --output experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2
.venv/bin/python -m benchmarks.scalable_english_diagnostics_validate
```

Use fresh output paths for reruns; existing artifacts are protected. The source
fixture/LM/training overlap and limited proposal horizon remain explicit limits.

The proposed coverage-first follow-up is now complete; see
[the matched scheduling report](scalable_english_coverage.md). At 8,000 proposals
per seed, full visitation reduced candidate support and literal recovery
relative to the existing mixed schedule. Mixed remains the default.
