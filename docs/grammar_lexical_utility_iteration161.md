# Iteration 161: the coarse prior does not consistently improve lexical ranking

The measured coarse grammatical shortlist survives, but this particular soft-prior use does not establish useful lexical restoration. Caesar and Jerome lose true-word top5 coverage, while the main top1 gain occurs in seen-author Cicero. Do not adopt this candidate-ranking change or describe its few correct top-ranked guesses as reliable nuclei.

The frozen diagnostic supplied each text/view's exact plaintext vocabulary as an **oracle candidate dictionary**, including rare types, ensuring the correct word was available for every query without identifying its mapping to the scorer. This isolates ranking from retrieval. Original and joined views of all four datasets were reported. Queries are all supported types at or above the tenth-largest count; every boundary tie is included, giving10 or11 queries rather than a plaintext-selected top10.

The baseline matches query counts against source unigram rates with a fixed Poisson score n*log(rate)−Ntarget*rate (the candidate-independent factorial term is omitted). Rates use source-fit counts, additive.5 smoothing and denominator Nsource+.5*(Vsource+1). Candidate counts in the target plaintext are never scoring inputs. This is a source-frequency count matcher, not a contextual language model or whole-dictionary assignment optimizer.

The additional cue assigns q=.8 to these frequency-selected queries, frozen from the earlier source shortlist result, and adds a unit-weight class log likelihood ratio: log(1.6) for known positive source-lexicon candidates, log(.4) for known negative candidates, zero for unknown/ambiguous candidates. Candidate class labels use only the existing source-fit lexicon with>=80% modal POS purity and the same seven-tag union. No candidate is pruned. The source lexicon was frozen before target inputs, candidate vocabularies/query counts before scores, and all score arrays before mapping/reference evaluation. No target outcomes selected q or weight.

| Dataset/view | Query count | Midrank improved/tied/worsened | True word top1: baseline → prior | True word top5: baseline → prior |
|---|---|---|---|---|
| Caesar original | 10 | 4/4/2 | 0 → 0 | 3 → 2 |
| Caesar joined | 10 | 5/3/2 | 0 → 0 | 3 → 2 |
| Jerome original | 11 | 4/2/5 | 1 → 1 | 5 → 4 |
| Jerome joined | 11 | 3/3/5 | 1 → 1 | 5 → 4 |
| Cicero original | 10 | 1/9/0 | 3 → 4 | 8 → 8 |
| Cicero joined | 10 | 1/9/0 | 2 → 3 | 8 → 8 |
| Palladius original | 10 | 4/4/2 | 1 → 1 | 4 → 4 |
| Palladius joined | 11 | 5/4/2 | 1 → 2 | 4 → 4 |

Top1/top5 guaranteed and possible counts coincide in this experiment; true-candidate best/worst ranks are nevertheless retained for all ties. Candidates number486–6,130 per view. Views and repeated queries are correlated, not independent replications.

On original texts, mean reciprocal midrank changes Caesar.1401→.1350, Jerome.2579→.2266, Cicero.5005→.5505 and Palladius.2580→.2511. Reciprocal midrank is explicitly1/(mean tie rank), not expected reciprocal rank under random tie resolution. A modest average-rank improvement can coexist with damaged top5/reciprocal-rank performance, as Caesar demonstrates.

Source class knowledge covers7–9 queries per view; there are zero coarse-class mismatches among those known correct words. Thus the failure cannot simply be blamed on wrong source labels for the covered true candidates. The prior also favors many wrong candidates of the same broad class and cannot distinguish identities within it. Its query cue is derived from frequency, so it is not independent contextual evidence.

The newly correct top1 word is ad in Cicero (both views), plus in in joined Palladius. Caesar has no correct top1 query. These are evaluation-revealed hits in an oracle-vocabulary experiment without a validated confidence selector, not reliable recovered anchors shared across four texts. Exact nuclei remain unestablished. No full assignment, contextual objective, retrieval improvement or Voynich decipherment was tested.

Next proposed direction: revisit the very small supervised binary-class training inventory under an explicitly different validation question. The prior strict protocol excluded all16 common target function-word types from training, leaving only13 examples/three conjunctions; the broader source inventory contains those16 labels legitimately in source-fit annotations. A separate **author-transfer** experiment could train on all29 source function types (18 ADP/11 CCONJ) while keeping inference features anonymous and source/target IDs independently salted, then test the frozen models on existing author streams and perturbations. This deliberately relaxes lexical-type holdout and must not be compared as another strict held-type result. It asks whether the data shortage is artificial for the intended opaque-text application; no target-text annotations may enter fitting, no identity features or mappings may be supplied, and all choices must be frozen before running.

Independent verification reconstructed the source unigram/lexicon, exact candidate sets and all tie-inclusive query counts, replayed every score using a separate scalar Poisson calculation, and checked all ranks and summary fields. Source-fit/reserve separation was checked; no new annotations, sealed works, production model changes or fitting were involved. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration161/`.
