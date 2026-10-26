# Iteration 187 — entropy-only range abstention repairs the known shortlist sensitivity

**Preserve as an experimental repair:** the fixed two-entropy-coordinate range rule, followed by top10 refill, changes the two weak endpoint-omission lists from5/10 to9/10 applicable pairs. Across all53 omissions, applicability is8–9/10 rather than5–9/10, with no decrease in applicable-pair count. It rejects0–2 useful candidate pairs per omission, so coverage costs and known-target development exposure remain essential.

## Frozen diagnostic

Use unchanged184 rich/control models, probabilities, features and all53 source-endpoint omissions plus the original baseline. For each fit derive raw coordinate min/max from retained source examples only, with fixed absolute tolerance1e-12. Compare three prespecified policies: none; any of19 coordinates outside; either mean left-context entropy or absolute endpoint left-entropy difference outside. Freeze all accepted masks before labels; no model refitting or coordinate/threshold tuning.

Keep original global threshold/top10/top20 lists and intersect them with each mask (**trim**). Separately refill top10/top20 from accepted candidates using original probabilities and exact boundary ties. Trimming and refilling are different outputs; abstentions are never scored as correct. Report acceptance, all useful candidate pairs lost, non-case rejection, accepted-set probability metrics, list case consistency, joint yield and type diversity. Retain every fit and policy, including sparse/empty outcomes; primary is rich entropy-only refilled top10 across all omissions.

## Coverage cost across53 omissions

| Policy | Accepted of126 candidates | Useful case-comparable pairs rejected (of36) | Non-case pairs rejected |
|---|---:|---:|---:|
| None | 126 | 0 | 0 |
| Any of19 coordinates | 70–88 | 10–13 | 28–45 |
| Two left-entropy coordinates | 117–122 | 0–2 | 4–8 |

Entropy-only acceptance is92.86–96.83%, retaining at least34/36 useful pairs. All-coordinate acceptance is55.56–69.84%, losing27.78–36.11% of useful pairs. These are candidate-level evaluation costs, not restored-token coverage or named-case accuracy.

On the original unperturbed model, entropy ranges reject4 non-case candidates and0 useful ones; its original9/10 top10 remains unchanged. All-coordinate ranges reject10 useful pairs and reduce the refilled original list from9 to8 applicable pairs.

## Rich-model list results across53 omissions

| Policy/output | Selected list size | Applicable pairs | Mean applicability | Joint-yield range |
|---|---:|---:|---:|---:|
| No abstention, top10 | 10 | 5–9 | 88.30% | 39.58–78.47% |
| All coordinates, trimmed top10 | 2–5 | 2–5 | 99.62% | 50.00–100.00% |
| All coordinates, refilled top10 | 10 | 6–9 | 78.11% | 40.00–69.58% |
| Entropy only, trimmed top10 | 5–10 | 4–9 | 89.43% | 59.17–78.47% |
| **Entropy only, refilled top10** | **10** | **8–9** | **89.81%** | **69.58–78.47%** |

The near-perfect all-coordinate trimmed applicability is accompanied by very short lists and large useful-evidence loss. Its refilled list worsens applicable-pair count in49/53 omissions, improves2 and ties2. It is not adopted.

Entropy-refilled lists give9 applicable pairs in52 fits and8 in one. Applicable count improves by4 in each of the two known weak fits and is unchanged in the other51. Mean joint yield rises73.19%→74.47%; worst-case joint yield rises39.58%→69.58%. The53 omissions represent47 distinct correlated training masks, and both repaired fits remove the same negative pair21; this is one repaired training sensitivity, not53 independent improvements.

## Known weak omissions

| Output for `omit12` / `omit33` | Selected pairs | Applicable pairs | Joint yield |
|---|---:|---:|---:|
| No abstention | 10 | 5 | 39.58% |
| Entropy-only trim | 5 | 4 | 59.17% |
| **Entropy-only refill** | **10** | **9** | **73.47%** |
| All-coordinate refill | 10 | 6 | 40.00% |

The entropy mask in these fits rejects9 candidates, including2 useful pairs. The original5/10 list loses4 non-case pairs and1 useful pair; refill then admits additional useful evidence from below the original cutoff. The repaired9/10 does not imply every rejected pair was wrong. Full per-fit probabilities, coverage/calibration and rich/control threshold/top10/top20 outputs remain available.

Joint yield retains its previous diagnostic definition: covered-pair frame agreement summed over all selected pairs, assigning inapplicable pairs zero contribution. Neither it nor case applicability names cases, restores identities, or measures token accuracy. Accepted-set probability losses cannot be compared to full-population losses without their differing coverage.

## Interpretation and next challenge

A source-only geometry check can protect this particular anonymous-context applicability interface from a known extrapolation failure while preserving most candidate coverage. It is a plausible **optional abstention-and-refill candidate**, not a default confidence rule or a fresh validation success. Its two coordinates were motivated by analysis of known target errors, and the target is reused same-author Cicero data with extensive vocabulary overlap. No hyperparameters or thresholds were chosen during this run, but the hypothesis itself has development exposure.

Next freeze the same rule and test **all double-source-endpoint omissions**, without changing coordinates, models, scales or thresholds. Enumerate source endpoint pairs before labels, remove their incident labeled examples, keep every low-data/one-class outcome, and report both no-abstention and fixed entropy/all-coordinate controls with coverage costs. This challenges the repair under a perturbation family not used to motivate it; it still will not substitute for new-author or novel-vocabulary validation.

No named cases, general POS tags, syntactic links or lexical nuclei are obtained here. Preserve the repair as a potential robustness option for a later grammatical decoder, with the original positive applicability findings and their limits intact.

## Verification

Independent scalar range reconstruction checked54 mask views, all3 policies, every tie-aware trimmed/refilled list,1,620 selected metric groups, accepted probability calibration and all useful-evidence/coverage costs. All184 no-abstention classification/list baselines match exactly; every range and paired result passed. Input/mask/selection hashes passed. The broader test suite was not rerun for this reference-only rule diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_abstention_iteration187.py`; reviewer: `benchmarks/grammar_case_abstention_iteration187_review.py`. Frozen design, accepted masks, complete selections/summaries, ranges, paired changes, audit and verification manifest: `experiments/results/grammar-restoration/iteration187/`.
