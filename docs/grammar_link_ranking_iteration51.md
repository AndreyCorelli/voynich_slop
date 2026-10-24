# Iteration 51: surviving-link audit and one boundary cue

The broad morphology candidates retain 324/326 reference links, but only 30 are unique. A source-selected penalty for intervening subordinating conjunctions modestly improves attachment when one endpoint is supplied. It does not improve unanchored reference recovery and adds two unique wrong outcomes. Keep it as diagnostic evidence, not a default ranking or pruning rule.

## Opportunity and competitor audit

The frozen iteration-50 `proper_unseen` configuration has mean 12.63 remaining links, median seven and maximum 127. There are 326 reference constructions across 304 distinct sentences. In 145 construction evaluations, more than one annotated finite subject–predicate link survives. A global single-link chooser therefore cannot recover the full grammatical structure: its maximum unique selected-reference count is 302/326 given current coverage, even with an oracle chooser. That ceiling concerns this evaluation task, not parsing generally.

The 3,794 competitors, counting each construction evaluation separately, comprise:

| Diagnostic category | Count |
|---|---:|
| Other annotated finite `nsubj` link | 199 |
| Subject's nearest finite ancestor differs from candidate predicate | 2,973 |
| Same finite ancestor, but not an annotated subject link | 622 |

Finite-ancestor categories use gold dependencies and morphology **only for this audit**, and are proxies rather than independently established clause boundaries. Other annotated links are legitimate alternatives, not scoring errors. An unannotated link is an annotation contrast, not proof of linguistic impossibility.

Among competitors that are not annotated subject links, the reference crosses fewer intervening verbal tokens in 2,248 comparisons and more in 386; fewer SCONJ tokens in 1,484 and more in 100; fewer CCONJ tokens in 1,550 and more in 205. These descriptive comparisons are highly dependent and length-confounded. They motivate testing cues against distance rather than claiming those cues alone solve attachment. Source tokens contain no punctuation, so no punctuation-derived clause boundaries are available.

## Ranking design

All morphology candidates remain unchanged. The baseline score is negative token distance. The experimental score subtracts a nonnegative weight times one observable cue: count of intervening VERB/AUX, SCONJ or CCONJ tokens. VERB/AUX here means supplied POS, not oracle finiteness.

For each unchanged outer split, choose one cue on fit sentences, then its weight on disjoint calibration sentences. Fixed weights are 0, 0.5, 1, 2, 4, 8 and 16; ties prefer the baseline and smaller weights. Selection maximizes average fractional top-ranked valid-link recovery across known-subject and known-predicate tasks. Any annotated finite `nsubj` link counts as valid. Test labels never choose the cue or weight.

Fit/calibration ranking uses POS-only nominal/pronoun–verbal pairs and eligible source annotations: the full eligible pool has 1,513 constructions, of which only each fold's fit/calibration sentence subsets are used for selection. It does not use candidate predictions whose training might contain the current outer test set. This introduces a training/evaluation candidate-distribution difference, which limits conclusions about more elaborate learned ranking. At inference the score uses only token positions and supplied POS; words, lemmas, morphology and dependency edges cannot influence it.

All five fits choose SCONJ crossing count. Calibration selects weight eight in folds 0–2 and sixteen in folds 3–4. The latter reaches the predeclared grid boundary; no weights were added after evaluation. Selection and evaluation reuse development source data; they are not independent confirmation.

## Results

“Unique correct” requires the chosen reference pair to be the sole top-scoring pair. “Unique other valid” identifies a sole top pair that is another annotated subject link. “Unique wrong” means a sole top pair absent from the annotated finite-subject links. Ties are retained explicitly, never broken by token index.

| Task / score | Unique correct | Unique other valid | Unique wrong | Ties | Empty |
|---|---:|---:|---:|---:|---:|
| No supplied anchor / distance | 89 | 21 | 102 | 114 | 0 |
| No supplied anchor / selected cue | 89 | 22 | 104 | 111 | 0 |
| Known subject / distance | 250 | 0 | 58 | 16 | 2 |
| Known subject / selected cue | 254 | 0 | 57 | 13 | 2 |
| Known predicate / distance | 186 | 0 | 117 | 23 | 0 |
| Known predicate / selected cue | 191 | 0 | 115 | 20 | 0 |

Each row contains 326 construction evaluations. With the subject supplied, the experimental score adds four unique correct outcomes and removes none, but introduces one unique wrong outcome while removing two. With the predicate supplied it adds five unique correct outcomes and removes none, while introducing two unique wrong outcomes and removing four. Thus even the improved aggregate anchored counts include individual regressions.

Unanchored reference inclusion among the tied-or-unique winners stays at 146/326. No reference gains or losses occur; two ties become uniquely wrong. On the 270 originally ambiguous constructions, unanchored unique correct stays at 53 and unique wrong rises 85→87. Anchored unique correct changes 194→198 with the subject supplied and 150→155 with the predicate supplied.

Deduplicating the unanchored task to 304 sentences gives unique valid links 102→103, unique wrong links 98→100, ties 104→101, and any valid link among the winners unchanged at 175. The one extra valid winner is a previously tied alternative, not an additional uniquely recovered selected reference. Anchored gains occur in both authors, but the effects are small; no statistical reliability is claimed.

Ranking's unique-wrong counts are new consequences of taking score maxima. The underlying broad candidate sets still have zero observed unique wrong links. These are different outputs, so increased forced-choice recovery must not be presented as cost-free structural restoration.

## Decision and next proposal

Do not use this cue to prune candidates or as the general ranker. It provides weak evidence that observable boundary context helps an already anchored attachment task; it fails to solve the unanchored problem.

The next proposal is **multi-link attachment**, scored per potential subject rather than choosing one link for the entire sentence. Include an explicit “not a finite subject” alternative, since many plausible nominal candidates are objects or obliques. Compare a distance baseline against source-trained local eligibility/attachment evidence, and report edge precision/recall plus abstention. Other annotated sentence links must remain positives. This directly tests whether choosing subject eligibility and attachment together addresses the dominant ambiguity; it is not yet implemented or validated.

## Artifacts and validation

Implementation: `src/voynich_smt/link_ranking.py`; benchmark and independent replay modules: `benchmarks/grammar_link_ranking_iteration51.py` and `benchmarks/grammar_link_ranking_iteration51_audit.py`. Artifacts, selected models and pre-evaluation proposal snapshot are under `experiments/results/grammar-restoration/iteration51/`. Existing output directories are rejected.

The benchmark verifies iteration 50's frozen inputs and reproduces reference survival for all 326 constructions. Mutation of gold morphology, dependency edges, words and lemmas leaves all score features unchanged. Independent validation reselects all five models on disjoint partitions and replays all 1,956 task rankings. Four new tests check inference invariance, explicit ties/empty sets, multiple valid annotations and conservative selection; 35 relevant tests pass. The 200-sentence reserve remains unscored and no prior target queries were scored.
