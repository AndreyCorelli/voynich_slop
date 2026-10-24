# Frozen-core context-length replication on source test — iteration 100

**Partial replication: the long-context selective core result survives; the smooth short-sample curve does not.** With the unchanged eight-type core,700and770sentences each give10correct/0wrong/5abstentions on15injected class swaps. But200sentences give9correct/11wrong across the two blocks, worse than100sentences. Preserve the long-context result and the merger counterexample; do not claim that more text alone guarantees safe repair.

## Frozen test-side setup

Use the separately partitioned source-test770sentences, disjoint from fit/calibration. This partition was already explored in earlier development; it is not a fresh sealed test. Keep exactly the99core (a, ad, de, et, ex, in, que, sed),93classifier,95cutoff0.6174674057358475, support≥5occurrences/3sentences and tie-abstention rule. No recertification or target-side core selection. The full195 supplied function anchors remain available as context.

There are not800source-test sentences. Apply the same fixed cal98|SID hash ordering to the test IDs. Primary levels are4×100,2×200,and1×400, using the identical first400sentences. Add a700-sentence prefix and the full770as larger endpoints. The extra endpoints add contexts rather than preserving the400-sentence census; do not portray them as equal-census comparisons or independent replications.

All64ADP×CCONJswaps plus clean/ad-de/que-sed controls are evaluated in each of nine blocks (603scenarios). The three frozen arms mirror99: all64errors/all16candidate types; the same15coreerrors/all16; and15coreerrors/fixed8. Unsupported core endpoints count as misses rather than triggering core reselection. A predeclared secondary evaluation stratum uses core-error endpoints supported across every100-sentence block; it never changes the inference candidate pool. No training, calibration, author scoring, PP integration, new annotations, reserve or sealed-test scoring.

## Core result

| Sentences per block | Blocks | Error probes | Correct | Wrong | Abstain | Recommendation precision | Recovery coverage | True pair supported |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 4 | 60 | 28 | 10 | 22 | 73.68% | 46.67% | 48 |
| 200 | 2 | 30 | 9 | 11 | 10 | 45.00% | 30.00% | 30 |
| 400 | 1 | 15 | 7 | 4 | 4 | 63.64% | 46.67% | 15 |
| 700 | 1 | 15 | 10 | 0 | 5 | 100.00% | 66.67% | 15 |
| 770 | 1 | 15 | 10 | 0 | 5 | 100.00% | 66.67% | 15 |

The700/770core reaches66.67%error recovery with zero observed wrong recommendations, versus99's80%at800calibration sentences. All15true pairs rank uniquely first at700/770before the gain cutoff; five are rejected by the frozen threshold. These are small repeated synthetic probes, not a100%population-precision guarantee.

At100sentences, a is unsupported in two blocks and ex in the other two. Thus the source-calibration support intersection does not transfer perfectly:48/60core error probes have a supported true pair. At200andlarger everycoretype is supported, yet200still performs badly. True-partner support alone does not explain that failure.

## Availability-only secondary stratum

The public-count common endpoints across all four100blocks are ad, de, et, in, que, sed (threeADP,threeCCONJ,ninecrosspairs). This is an evaluation-only stratum: candidate inference still uses the frozen eight-type core with its unchanged support requirement. It is not a new six-type repair policy, and non-stratum errors are retained in the primary totals.

| Sentences | Correct / wrong on common-supported errors | Precision | Unique top-rank correct / error probes |
|---|---:|---:|---:|
| 100 | 21 / 4 | 84.00% | 27 / 36 |
| 200 | 5 / 8 | 38.46% | 8 / 18 |
| 400 | 5 / 2 | 71.43% | 6 / 9 |
| 700 | 6 / 0 | 100.00% | 9 / 9 |
| 770 | 6 / 0 | 100.00% | 9 / 9 |

Even with true-error endpoints always supported, the200-sentence result deteriorates. Candidate eligibility for the other two core types can still change with length; this secondary stratum does not hold every competing candidate's eligibility fixed.

## Candidate competition and controls

| Sentences | All64errors/all16: correct / wrong | Precision | Core15errors/all16: correct / wrong | Precision | Core15errors/fixed8: correct / wrong | Precision |
|---|---:|---:|---:|---:|---:|---:|
| 100 | 35 / 40 | 46.67% | 26 / 12 | 68.42% | 28 / 10 | 73.68% |
| 200 | 20 / 53 | 27.40% | 7 / 16 | 30.43% | 9 / 11 | 45.00% |
| 400 | 37 / 12 | 75.51% | 7 / 4 | 63.64% | 7 / 4 | 63.64% |
| 700 | 41 / 12 | 77.36% | 9 / 1 | 90.00% | 10 / 0 | 100.00% |
| 770 | 44 / 4 | 91.67% | 10 / 0 | 100.00% | 10 / 0 | 100.00% |

All clean/same-class controls abstain at every length and in every arm. This remains weaker than reliability after corruption. The full770all-candidate result reproduces every one of the62shared source cases from97; it does not erase those wrong-repair counterexamples.

## Concrete merger failure: ex

A post-score descriptive audit locates the200-sentence collapse:

| Block | Core correct | Core wrong | Core abstain | ex occurrences |
|---|---:|---:|---:|---:|
| 100-0 | 6 | 4 | 5 | 5 |
| 100-1 | 10 | 1 | 4 | 4 |
| 200-0 | 0 | 11 | 4 | 9 |
| 100-2 | 9 | 1 | 5 | 5 |
| 100-3 | 3 | 4 | 8 | 2 |
| 200-1 | 9 | 0 | 6 | 7 |
| 400-0 | 7 | 4 | 4 | 16 |
| 700-0 | 10 | 0 | 5 | 34 |
| 770-0 | 10 | 0 | 5 | 37 |

The first200block makes11wrong recommendations and zero correct; ALL11wrong recommendations select ex as the incorrect partner. Its two100-sentence halves make4and1wrong recommendations respectively. ex has5occurrences in the first half and4in the second, so it is ineligible in the second half but becomes eligible on the merged9occurrences. The other200block has7exoccurrences and9correct/0wrong recommendations. Thus occurrence count alone cannot explain or fix the problem; evidence composition, eligibility and competition interact.

Do not blacklist ex or raise a word-specific support cutoff from this diagnostic. The wrong-pair and occurrence summaries were added after scoring solely to identify a reproducible failure. No output, core membership or threshold was changed.

## Interpretation and next step

The long-context source result is worth preserving, but the earlier near-monotone100→200→400calibration trend is not a general law. A robust algorithm cannot assume that adding sentences monotonically improves pair selection. The fixed frequent core can provide selective class repair on long source text, still conditional on the supplied anchor inventory and single bijective-error setup; no new lexical nuclei or full grammatical restoration is established.

Next trace ex's class evidence across the two halves and their200-sentence merge, and separate newly eligible competitors from changes in pooled scores. Use outcome-independent candidate-eligibility counterfactuals for diagnosis and report all cases, without adopting an ex exception. This is a more concrete bottleneck check than immediately changing thresholds or adding more training.

A later author-context test is feasible: cached unannotated Caesar GallicV–VII and CivilI–III HTML files are present (data/raw/word-mapping-caesar/README.md). They could add contextual occurrences while scoring only the existing100annotated sentences, without querying new annotations. Any such test must apply the SAME simulated mapping to all added context, exclude overlaps and preserve the sealed lexical positions. Only file availability/provenance was checked here; no author text was scored.

Validation: all603probability scenarios and decisions replayed; frozen core/model/cutoff and fit/calibration disjointness verified; secondary stratum, per-block/error-partner counts and62prior shared cases verified; 7,805 prior frozen-input hashes verified;109 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration100/.
