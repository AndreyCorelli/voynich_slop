# Known-language encrypted-text tests: experiment track

Updated: 2026-10-13.

## Scope and success criterion

Encrypt an existing text in a known language using a known transformation scheme, hide the key, and recover a globally consistent decoding whose sentences have the original grammatical structure. The original text is available for evaluation and explicitly labelled oracle controls, not as a normal decoder input.

Tests so far use Latin texts by Julius Caesar and synthetic word substitutions, primarily one-to-one mappings; early tests also included homophonic mappings. This is not a Caesar letter-shift cipher. Word order, repetitions and segment boundaries are preserved by the fixtures. Restoring sentence structure therefore means recovering grammatical roles and relationships, not merely restoring token order.

Exact original vocabulary is a useful diagnostic, but the intended outcome permits alternative content words where the sentence's construction remains correct. Matching POS or inflection alone is insufficient: subjects, objects, modifiers, agreement and verb–argument relationships must fit together. **No experiment has yet demonstrated that outcome.**

Resources include Whitaker-style morphological analyses, statistical word/analysis models and an offline Latin RoBERTa. Later training uses 39,346 words from Gallic V–VII and Civil III, disjoint from the development books. Development passages range from 503 to 32,004 words. A reserved final test remains unscored; repeated development experiments are exploratory, not independent confirmations of generalization.

## Search and objective experiments

| What we tried | Observed result |
|---|---|
| Word bigram/trigram objectives, simulated annealing, restarts, collapse penalties | A 16.8-million-mutation calibration found wrong dictionaries scoring above truth in every longer run. |
| Decoded-frequency penalties and injective mappings | Another 6 million mutations gave limited gains; objective misranking persisted. |
| Longer context and disjoint-book training | Recovery remained around 4%; local changes could improve the score while moving away from truth. |
| Latin neural scoring, reranking, diverse archives and candidate-pool changes | The neural scorer preferred truth in 74% of selected near-truth counterexamples, but not the rest. Gains from reranking were small or inconsistent. N-gram top-1 beat neural top-1 in every tested partial-context condition. |
| Morphological agreement, uncertain candidates and coordinated moves | Combined recovery was 2.34% versus 2.31% baseline. Consensus and agreement did not reliably identify correct mappings. |
| Training-attested phrase proposals and fivefold search budgets | Across 6.48 million mutations, all 18 longer-run scores improved while average recovery fell in every arm; baseline 2.31% → 1.72%, phrase proposals 1.79% → 1.10%. |
| Wider passages and an oracle vocabulary containing all target words | At 32,004 words, 13.38 million mutations reached 6.74% token recovery, below the frequency initializer's 6.94%. Only 9–11 of 8,220 type assignments were correct. |
| Perfect dictionary, zero-corruption start | Starting at 100% exact recovery, strict score ascent fell to 82.80% and annealing to 69.58% at the largest width. Having the answers available did not make the objective prefer retaining them. |
| Exhaustive optimization of small restricted cases | Annealing found an optimum in 34/36 runs; truth was below the optimum in all 18 five-token cases. This is an objective audit, not evidence that a small-vocabulary decoder generalizes. |

The budgets above belong to separate documented experiments and should not be added without checking their protocols. Details: [earlier attempts](docs/word_mapping_attempts_summary.md), [phrase/exact audits](docs/word_mapping_phrase.md), [widening](docs/word_mapping_widening.md), [perfect-start test](docs/word_mapping_zero_corruption.md).

## Morphology and assisted recovery

| What we tried | Observed result |
|---|---|
| Plaintext-derived morphology-tolerant oracle | An injective mapping changed 41.14% of tokens in the 32,004-word passage with zero strict-profile error. This demonstrates allowable substitutions under the metric, not restored sentence dependencies or meaning. |
| Larger annotated dictionary | Generated 1,412,284 surfaces and selected 100,000 without development-based selection. Selected coverage was 86.78% of development tokens and 61.96% of types. A larger inventory alone did not establish recovery. |
| Plaintext-independent latent morphological sequence scorer | Compatible-profile substitutions tied truth; broad broken controls scored worse. Nevertheless, 10/100 locally incompatible swaps outscored truth at the largest width. |
| Structural search with correct function-word mappings supplied | Twenty-four searches evaluated 240,000 proposals. Full anchors did not unlock content recovery. Even forbidding unknown/function candidates yielded only 2.6–4.8% strict-compatible known-content tokens. In five of six ordinary fully anchored runs, wrong dictionaries outscored truth. |
| Neural cloze retrieval pooled across occurrences, plus injective joint assignment | With function anchors, compatible top-ten retrieval was 9/28 known-content types versus frequency's 7/28. Excluding copulas/glue left both at 3/22 lexical types. Joint assignment recovered only 2/22 compatible lexical types. |
| Repeated-mask partial fine-tuning, 200 updates | Validation loss improved, but retrieval did not improve consistently. Lexical compatible top-ten went 3/22 → 4/22 with function-only context; with 50% correct content supplied it fell 12/22 → 7/22. |
| Repeat-aware anonymous embeddings, matched collapsed controls, 400 updates | After enriching training for repetition, both arms reached 4/22 lexical compatible top-ten at 0% content and 11/22 at 50%. A 25% advantage of 8/22 versus 7/22 disappeared under fresh identifier permutations. Breaking identity also matched the controls. |

These are different evaluations: token accuracy, type accuracy, compatible retrieval and top-ten membership are not interchangeable. Supplied mappings are answers given to the system and must not be counted as recovered words. Morphological compatibility checks analysis sets, not sentence composition.

Details: [tolerant oracle](docs/word_mapping_structural_oracle.md), [dictionary/scorer](docs/word_mapping_large_dictionary.md), [anchor searches](docs/word_mapping_anchor_recovery.md), [cloze](docs/word_mapping_repeated_cloze.md), [fine-tuning](docs/word_mapping_cloze_finetune.md), [repeat identity](docs/word_mapping_repeat_identity.md).

## Latest diagnostic: supply grammar, then infer it

The same 22 lexical development types were ranked over the large dictionary. Correct function mappings were supplied throughout. Exact identity, rather than oracle-filtered compatibility, was the primary measure.

| Supplied target information | Median candidate pool | Neural exact top-ten | Frequency exact top-ten |
|---|---:|---:|---:|
| No target grammar | 96,823 | 3/22 | 3/22 |
| POS alternatives | 7,247 | 4/22 | 3/22 |
| POS/case/number alternatives | 1,970 | 5/22 | 9/22 |
| Any shared full morphological analysis | 565.5 | 8/22 | 17/22 |
| Identical complete ambiguity profile | 48.5 | 14/22 | 20/22 |

The last row is an especially strong oracle: the entire ambiguity profile can fingerprint a word. Its expected random top-ten recovery is already 8.41/22, and strict morphological compatibility is 22/22 by construction. The full-analysis intersection row is less restrictive; random ordering would recover only an expected 0.83/22 originals there. Neither oracle supplies a context-disambiguated parse or proves that the selected words form the corresponding sentence. Top-ten membership is a shortlist, not a decoded assignment.

Two local grammar predictors were then trained from scratch on disjoint text: 628 full-analysis states and 43 joint POS/case/number states. They used visible function-word context and hidden-target repetition, without unknown spelling, length or lemma. Training used 20,416 examples, 1,000 updates and checkpoint selection on 2,534 training-book validation examples. Labels were ambiguous dictionary analyses, not annotated token syntax.

On the 22 lexical types, the full predictor proposed an admissible analysis for only 2/22 types; the coarse predictor reached 3/22 versus its context-free prior's 4/22. With fixed weight one, inferred full grammar produced neural exact top-ten 4/22 and frequency 3/22. A context-free grammar prior also produced neural 4/22. Coarse inference did not improve exact recovery. Stronger weighting and hard inferred filters generally worsened it.

**Finding:** correct morphology helps constrain lexical candidates. The tested local predictors do not reproduce that benefit, and no sentence-level grammatical reconstruction was established. Details: [grammar diagnostic](docs/word_mapping_grammar_oracle.md).

## What the evidence establishes—and what remains open

The objective is a demonstrated bottleneck: in several controls, improving its score worsens recovery, even from the true dictionary. The optimizer may also fail; some searches remain below the truth's score. Neither result alone establishes that the transformation is unidentifiable or that every structural decoder must fail.

We have not isolated whether the remaining difficulty is inadequate scoring, insufficient joint structural inference, or ambiguity between multiple valid decodings. Morphological profiles and local transition scores do not resolve that question. Small restricted successes, lower training loss, plausible words and shortlist gains cannot substitute for restored sentence structure on unseen passages.

Explicit dependency/argument-structure reconstruction, joint grammatical-role inference and a discriminator trained directly on correct versus plausible wrong dictionaries remain unimplemented proposals. A next experiment should distinguish scoring validity from search performance at realistic scale, freeze settings before evaluating new passages, and assess structural restoration separately from exact vocabulary.

Saved artifacts include dictionaries, scores, manifests, selected models and replay checks. The latest focused suite passed 95 tests; oracle filters and full/coarse predictor outputs replayed identically. Repeat-identity verification used complete ranking regeneration with sampled neural replay. These checks verify execution, not decryption success. The [experiment index](docs/word_mapping.md) links the detailed protocols and evidence.

## Sentence grammaticality discriminator (2026-10-12)

Tested nine existing proxies individually and in calibrated nonnegative/signed weighted combinations on 1,125 cases from 300 annotated Latin sentences. Whole works were separated for fitting, calibration and evaluation; weights and thresholds were frozen before scoring 437 test cases. Corruptions alter subject agreement, adjective agreement or governed case; valid controls change content nouns or local adjective order. Gold dependencies create labels but are unavailable to scorers.

The combinations reached only 57.7% / 57.6% balanced grammaticality accuracy, accepting about three quarters of corruptions. Original-versus-corruption ranking reached 81.4% / 80.1%, below neural scoring alone at 86.3%. Ranking a small deterioration within a sentence does not establish a grammaticality threshold across sentences. Neither combination passed the frozen reliability gate. Labels concern the intended annotated parse and have not been adjudicated by Latin experts.

This isolates a scoring limitation without running dictionary search; it does not rule out every combination or structural model. Details, confidence intervals, weights, examples and replay: [sentence proxy benchmark](docs/latin_sentence_proxy_combination.md).

## Passage accumulation audit (2026-10-12)

Expanded the sentence diagnostic to 24,404 words in 11 annotated works, using global injective substitutions and grammatical noun substitutions matched for changed-token count. Fit/calibration/test remain work-disjoint within the run; this reuses earlier diagnostic authors and is exploratory. Evaluated 250-word blocks, 1,000-word blocks and whole works with token-weighted proxy means, low-score rates and transferred sentence acceptance rates.

Neural original-versus-corruption ranking was perfect on the observed 34/10/8 pairs at those lengths, but its classification threshold accepted every test passage. Weighted combinations remained weak: nonnegative balanced accuracy 51.9%/50.0%/50.0%; signed 55.2%/60.0%/56.2%. Neither demonstrated consistent improvement with length or passed the reliability gate. Morphological sequence score preferred grammar-preserving vocabulary controls to matched damaging mappings in 8/8 whole-work comparisons, versus neural 7/8 and combinations 6/8. This is promising relative evidence from only four test works, not reliable structural decoding. Only one test work exceeds 3,000 words.

All passage aggregates and 59 sampled sentence feature vectors replayed; full downstream replay reproduced the report. Focused tests: 14 passed. [Passage anomaly report](docs/latin_passage_proxy_audit.md).

## Relative structural ranking (2026-10-12)

Trained pairwise logistic rankings on frozen passage-feature differences, giving equal fitting mass to work/width/comparison kind. Included original-versus-corruption and grammatical noun substitution-versus-corruption. Compared signed/nonnegative weights with all 19 features and with eight morphology-only features; selection used calibration only.

The selected all-feature signed model preferred grammatical controls in 26/29 short-passage pairs, compared with neural 21/29. Predeclared structural-only arms reached 28/29; structural-only signed ranked both whole-work kinds correctly in 8/8 pairs each, but reached only 9/10 for each kind at 1,000 words. No arm passed the per-length/per-work reliability gate. The better structural arm is an exploratory finding, not a retroactive replacement for the calibration-selected model.

These reuse earlier works/mutations: 149 fitting, 73 calibration and 99 correlated test comparisons. No fresh-author reliability or successful ciphertext recovery was established. Full fit/selection/evaluation replay passed; 12 focused tests passed. [Relative-ranking report](docs/latin_relative_ranking.md).

## Put relative ranking into dictionary search (2026-10-12)

Ran an assisted near-truth search audit on ten 250-word/1,000-word/whole-work fixtures. At most 24 types were active; all other assignments were correct and fixed. The oracle candidate pool contained the answers. Compared frozen signed/nonnegative structural rankers and morphological-sequence scoring, with four starts, two seeds and 1,000 proposal opportunities: 240 runs / 240,000 opportunities (collisions/no-ops skipped). Only strict score increases were accepted.

All 60 truth-start runs and all 60 grammar-preserving-start runs lost checked gold grammatical edges. No run restored all eligible edges. Denser-error starts often repaired some edges while reducing original-role-compatible tokens. Curated pair-ranking gains did not survive optimizer-generated dictionary changes. Around 96% overall exact-token recovery mostly reflects supplied fixed assignments and is not recovery success.

Metrics evaluate original annotated agreement/government and role-inflection compatibility, permitting alternate vocabulary. They are ambiguity-relaxed checks, not inferred complete parses. Full search replay and incremental/full-score checks passed; 15 focused tests passed. [Search audit, dictionaries and excerpts](docs/latin_relative_search.md).

## Adversarial objective training and fresh attacks (2026-10-12)

Collected 3,391 accepted mutations from 104 searches on separate fitting/calibration works, retaining dictionaries, score changes and lost/gained relationships. Trained 15 linear/quadratic pairwise objectives on 986 fitting pairs; 701 calibration pairs and fresh calibration attacks selected settings. Whole works and all their trajectories stayed together.

The stability-selected nonnegative scorer collapsed to zero weights: no damage but no repairs. Two calibration-selected nonflat alternatives failed fresh attacks, including newly reserved Palladius. At 5,000 opportunities, both preserved zero valid-start runs; worst high-scoring degradation was 50.0%/55.6%. Higher budgets did not establish restoration. Four objectives underwent 256 test searches / 1.28 million proposal opportunities. No acceptance gate passed. One Augustus control failed an initial edge check; excluding it leaves the same conclusions on 30 eligible valid-start runs per objective.

All mutation transitions/scores and relationship counts were audited; 104 sampled raw-feature/label pairs and all 15 fitted models replayed; fresh attacks replayed fully. Ten focused tests passed. This is one adversarial training round over existing coarse proxies, not evidence that every adversarial scorer must fail. [Protocol, examples and results](docs/latin_adversarial_objective.md).

## Oracle relationships versus original roles (2026-10-12)

Ran 186 unchanged-optimizer searches on the assisted held-out fixtures, excluding the previously invalid control. Supplied (a) agreement/government relationships, (b) original context-specific POS/role inflections, or (c) both; equal unit violation costs. Gold information is deliberately inside these oracle objectives.

All valid starts remained stable by construction. At 5,000 proposals, role-only and combined objectives restored every checked edge/role constraint in 30/32 corrupted runs; median repair rose from about 10% at 100 to 96.4% at 1,000 and 100% at 5,000. Neither systematically worsened structural quality with budget. Edges-only fully restored 3/32, with zero median original-role repair. The full earlier gate still fails its 100-proposal repair requirement; later checkpoints satisfy its thresholds.

This establishes assisted repair when role/inflection answers are supplied, not plaintext-independent grammatical inference or a recovered parse. Next diagnostic: learn token-role/morphological distributions from known-language annotations and measure how closely they approximate this oracle on adversarial dictionaries. Full replay and nine focused tests passed. [Oracle structural audit](docs/latin_oracle_structure.md).

## 2026-10-12: Plaintext-independent masked contextual roles

Implemented [contextual role pilot](docs/latin_context_role.md), replacing oracle roles with a fixed short-context multinomial logistic classifier. Train-only PROIEL Caesar: 23,183 tokens, 95 role/inflection signatures, all evaluation authors excluded. Hide each target's own surface; score probability mass on compatible dictionary readings. Existing assisted fixtures, fresh seeds, 62 searches / 62,000 opportunities.

Complete-role accuracy 8.53%; original > corrupted on 14/16 static comparisons, yet 0/30 valid starts stable, 0/32 corrupted starts fully repaired, worst valid degradation 50% at 1,000 proposals. Median minimum edge/role repair −200%; Palladius also fails. This baseline does not replace the oracle; local context and memorization do not provide robust expected grammatical roles. Six focused tests and full deterministic training/search replay passed. Next stronger model should use sentence-wide context, morphology and auxiliary dependencies, with author-disjoint validation before another long search.

## 2026-10-12: Sentence-wide role model with morphology/dependency supervision

Implemented [sentence-wide role experiment](docs/latin_sentence_role.md): forward/backward GRUs with shifted states exclude the target's spelling and morphology, while using sentence-wide surrounding lexical/dictionary context. Auxiliary gold dependency-relation and head-offset targets are used only during training; no full dependency parser is established. Train on five authors, 145,616 tokens; calibrate on three other authors; exclude all five test authors. Calibration-only selection chooses epoch 4, temperature 1.

On aligned unique test tokens, complete-role accuracy rises from the old model's 8.77% to 10.99%. Static original-over-corrupt preference is 14/16; grammatical controls beat corruptions in 16/16 (including the known imperfect Augustus control in this descriptive count). Calibration role accuracy 9.61% fails the predeclared 30% long-search readiness threshold.

Frozen-model bounded fresh attacks: 62 runs / 62,000 opportunities, new seeds 1601/1613. At 1,000 proposals, 0/30 valid starts remain stable, 0/32 corrupted starts fully restore measured structure, only 2/32 corrupted runs avoid regression, median minimum edge/role repair −133.3%, worst valid degradation 35%. Only 9/62 runs avoid further damage from 100 to 1,000. Added context and auxiliary supervision are insufficient for this small, biblically dominated recurrent model. Do not extend this objective's search budget.

Ten focused tests pass. Frozen-model full search replay passes; independent audit validates 186 checkpoints and aligned prior-model accuracy. No claim of training replay or full grammatical parse recovery. A separate useful diagnostic is expected inflection conditioned on dictionary-derived target POS while withholding target case/number/gender, rather than hiding every target clue or supplying gold POS.

## 2026-10-12: Exact joint dictionary/readings/parses on synthetic clauses

Conducted the [small joint-inference identifiability experiment](docs/latin_joint_identifiability.md), rather than another learned-objective search. The solver jointly chooses a globally injective surface dictionary, one context-specific reading per occurrence and coherent sentence roles/heads under an explicit finite synthetic grammar. Every type has the same full candidate inventory; original assignments/trees are evaluation-only.

Positive control: six clauses, 8 cipher types / 15 occurrences, 10 candidate surfaces. Independent dictionaries admit 1,728 structures; the shared dictionary admits exactly **one intended structure**, with **144 valid dictionaries**. Wrong-structure feasibility is UNSAT, so this is genuine finite-problem structural identifiability, not exact vocabulary recovery. Restrictive inventory and fixed complete valency are part of that result.

Widening with two nominative/accusative-ambiguous neuter nouns leaves **seven** global structures. A consistent `bellum`/`donum` mapping permits reversed subject/object roles while repeated `bellum` takes nominative elsewhere. With 29 surfaces, first-six-clause ambiguity decreases 9 → 7 as more contexts are added, then remains seven through 12 clauses. Full-passage rich enumeration hits the 2,000-structure cap; those counts are lower bounds. Allowing noun attachment leaves three parses even with the true dictionary supplied.

28 shared/independent problems took about 103 seconds. Six focused tests and full count/SAT/UNSAT replay passed; saved witnesses receive independent concrete checks. This establishes a joint-inference mechanism in a hand-designed positive control and exposes nonidentifiability in widened controls. It does not establish unrestricted Latin recovery, semantic correctness or reliability on random unseen synthetic passages.

## 2026-10-12: Joint inference under grammar undercoverage

Conducted [grammar-coverage controls](docs/latin_joint_coverage.md): generate covered clauses plus omitted subjects, genitive modifiers and coordinated subjects; compare the original narrow grammar with a broader fragment containing those constructions. Both jointly infer global dictionary assignments, per-occurrence readings and parses, with identical unfiltered candidate inventories. Forty hand-constructed problems use lean 15-word and richer 31-word inventories.

Among 16 narrow-grammar mismatch cases, five are UNSAT, ten admit multiple wrong structures and **one admits exactly one wrong structure**. The last case contains six coherent genitive constructions: the solver silently remaps them to subject/object/transitive-verb clauses. All 30 role/head variables are logically forced, but six disagree with the intended construction. Therefore, uniqueness and reporting only forced relationships do not establish grammar adequacy.

The broader grammar admits every original dictionary/tree, but 19/20 cases remain ambiguous. One genitive clause plus six covered contexts has a uniquely original structure in the lean broader grammar. Merely repeating an identical unsupported clause adds no evidence. Adding coverage also reduces certainty on genuinely covered input: lean six-clause alternatives rise 1 → 4; richer alternatives 9 → 194. One richer case hits the 512-structure cap; that count is a lower bound.

Twelve focused tests (six new/six previous) and full count/SAT/UNSAT replay passed. Separate witness checks and direct SAT queries audit forced relationships. Joint inference is an ambiguity/inconsistency mechanism; it has no demonstrated universal detector for missing grammar rules. All results remain conditional on finite, hand-constructed grammar and candidate assumptions, not unrestricted Latin recovery.

## 2026-10-13: Downstream compact-key discovery and held-out prediction

Changed the primary criterion from grammatical restoration to whether uncertain language evidence helps discover a compact key that predicts unseen text. Implemented [compact cipher benchmark](docs/latin_compact_cipher.md): known general letter-substitution family, canonical 24-letter alphabet, preserved boundaries, hidden permutation. A frozen 10-byte key—not the language model or a word dictionary—decodes a disjoint held-out passage. No exceptions or correct function-word anchors are supplied to ordinary arms.

Train on the earlier five fit authors; calibrate on three other authors, freeze evidence weights before evaluating five target authors. Fifteen independent keys / 24 paired fixtures use approximately 100/1,000 discovery words and 300 disjoint held-out words. Compare character baseline, independent 100,000-form pattern candidates, ciphertext-only inferred POS, and explicitly answer-supplied POS/role oracles. Existing authors/passages are reused, so this is exploratory rather than an untouched final test.

Baseline held-out accuracy is **99.9286% letters / 99.5956% words**, with 16/24 exact held-out passages. Long discovery reaches 99.9738% letters. Complete 24-letter identity matches only 1/24 baseline keys: rare/unobserved symbols remain unresolved, despite strong text prediction. Auxiliary-word prediction is 100% and function-word prediction 99.9149% on repeated test tokens, without supplied anchors. Standalone prediction bundles and 100-word original/predicted excerpts are saved.

Inferred POS is 42.16% correct on paired discovery tokens, but calibration chooses weight zero. Candidate/oracle POS arms slightly worsen final prediction; full-role oracle ties baseline average. Exploratory fixed-weight early budgets give oracle-role 97.64% versus baseline 97.01% held-out letters at 1,000 proposals/restart, heterogeneous across fixtures (three wins/two losses/19 ties, median gain zero). No reliable speedup from inferred structure is established. Candidate sets have median 175 forms but retain only 75.26% of correct discovery-word occurrences; exports preserve an escape option.

Six focused tests, full frozen test replay and budget replay pass. Independent checks audit 360 frozen predictions and verify real 10-byte key codes; ciphertext-only candidate/POS exports read no truth. This establishes downstream predictive success for one easy compact family, not unknown-family discovery, arbitrary word substitution or useful joint grammatical inference. A harder predeclared compact family/regime with oracle preflight should precede further expensive grammar training.
