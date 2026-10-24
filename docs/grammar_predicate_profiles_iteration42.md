# Iteration 42: can construction profiles transfer to unseen predicates?

**This attempt does not transfer the useful predicate signal to verbs without source *in* labels.** Source-derived profiles increase coverage, but do not improve case decisions on newly covered examples; their probability ranking is also unhelpful. The positive familiar-lemma result from iteration41 remains, but these profiles do not solve its coverage bottleneck.

## Fixed experiment and information boundary

Keep iteration41's source 767 sentences and reused target examples: 17 Jerome and 41 Caesar *in* + accusative/ablative constructions. No source expansion, target-derived profile building, new target IDs, or reserve scoring. Caesar remains absent from source authors. This is development analysis under privileged annotations, not fresh confirmation or anonymous-ciphertext grammar restoration.

Build a profile for each source predicate lemma using its other constructions:

- Counts of direct dependent relation/POS and relation/case frames.
- Nominal argument lemmas.
- Other preposition/case frames.

Exclude **every direct dependent subtree containing an ADP *in***, including indirect occurrences. Thus *in* complement case and lexical identity cannot enter the profiles. Predicate identity itself is not a vector feature. Profiles use source dependency/POS/case annotations and plaintext lexical context; query lookup uses the oracle predicate lemma, never query-context profile extraction. The nearest-verb alternatives retain oracle verbal POS and lemmas.

There are 605 source verbal lemmas, 549 with nonempty profiles. Three hundred in-bearing child subtrees are excluded. Transform source profiles with log-TF/IDF and cosine normalization. The fixed primary transfer estimator takes five positive-similarity donor predicates, excluding the query lemma, and averages donor case rates with cosine weights. Donor rates use the same mass4 shrinkage to the global source baseline as iteration41. Each donor contributes a rate rather than raw frequency weight.

Missing profiles or positive-similarity donors return the global baseline. A **transfer-only** arm excludes the query lemma's case counts even when available. A **hybrid** arm uses the transfer probability as the mass4 prior for that lemma's own source case counts. Fix all settings before predictions; no target tuning. Controls are the iteration41 lexical-count model, preposition-only baseline, matched nearest-verb training, oracle-trained nearest-verb inference, and 100 profile-identity permutations within log2 source verb-frequency bins. Permutations preserve nonempty profile coverage and the profile multiset.

## Coverage

“Unseen-in” means the predicate has no source *in* case labels; it may appear in other source constructions. It does not mean absent from the source vocabulary.

| Author | Query examples | Seen-in | Unseen-in | Unseen-in with source profile | No source profile |
|---|---:|---:|---:|---:|---:|
| Jerome | 17 | 6 | 11 | **6** | 5 |
| Caesar | 41 | 11 | 30 | **16** | 14 |

The six newly covered Jerome examples contain only **two distinct lemmas**: five *introeo* examples and one *aio*. *Introeo* has just one source occurrence. The sixteen newly covered Caesar examples contain ten distinct lemmas; several have only one to four source occurrences. These are not 22 independent tests of new predicate identities.

## Primary results

| Author/cohort | Examples | Lexical-model accuracy | Hybrid accuracy | Lexical log loss | Hybrid log loss |
|---|---:|---:|---:|---:|---:|
| Jerome, all | 17 | 47.1% | 52.9% | 0.7371 | **0.8152** |
| Caesar, all | 41 | 58.5% | 58.5% | 0.7238 | 0.7183 |
| Jerome, newly covered unseen-in | 6 | 16.7% | **16.7%** | 1.0075 | **1.2668** |
| Caesar, newly covered unseen-in | 16 | 50.0% | **50.0%** | 0.7604 | **0.7779** |

Lower log loss is better. The small overall Jerome accuracy increase occurs among familiar *in* predicates; it is not new-predicate transfer. Overall transfer-only accuracy is just the preposition-only accuracy: 35.3% Jerome and 41.5% Caesar.

For newly covered examples, all primary transfer probabilities remain below 0.5, so every decision is still ablative. This is not solely a threshold problem: primary accusative-ranking AUC is **0.00 Jerome and 0.3594 Caesar**. Shuffled-profile means are 0.54 and 0.4941, with wide 95% ranges [0,1] and [0.1793,0.7664]. These tiny samples do not establish systematic inverse generalization, but they provide no positive transfer evidence.

The five *introeo* accusative examples all receive p(Acc)=0.2403 and select *recumbo* as the closest donor. In Caesar, several accusative examples receive lower probabilities than ablative examples. Aggregate dependency/argument similarity here does not preserve the distinction we wanted.

For newly covered Jerome examples, paired sentence-cluster bootstrap log-loss reduction versus the lexical baseline is [-0.2946,-0.1675]; for Caesar it is [-0.0582,+0.0170]. The bootstrap uses 10,000 sentence draws and fixed source models. It does not represent uncertainty over new lemma identities; Jerome has only two such identities.

The hybrid nearest-verb variants reach 58.8% overall Jerome and 56.1% Caesar accuracy. Their cohorts are defined by oracle predicate membership, so an oracle-unseen example can have a nearest verb with seen labels. Those figures are not evidence of transfer to genuinely unseen nearest-verb predicates. On Caesar they do not beat the previous lexical nearest-verb accuracy. The appropriate headline remains the oracle-defined unseen-in profile cohort, where there is no accuracy gain.

## Source leave-predicate-out check

Remove **all** source *in* labels for one predicate at a time and refit donor counts and the global baseline. Keep its non-*in* profile as a source-derived covariate. This is leave-lemma-out case-label prediction, not withholding every occurrence of that lemma from the source corpus.

Across 166 linked source examples and 100 held-out predicate lemmas:

| Metric | Refit baseline | Profile transfer |
|---|---:|---:|
| Token accuracy | 66.87% | 66.27% |
| Predicate-macro accuracy | 71.63% | 70.63% |
| Token log loss | 0.6498 | 0.6191 |
| Predicate-macro log loss | 0.6085 | 0.5996 |

There is a small source probability improvement but no classification improvement, and it does not carry over consistently to the reused target cohorts. Five source examples with no predicate lemma are excluded from this leave-predicate-out analysis.

## Challenge to the conservative estimator

After inspecting primary outcomes, freeze a **descriptive sensitivity grid**, not a revised primary model: k in {1,3,5}, donor smoothing mass in {0.5,1,4}. This checks whether averaging and shrinkage suppressed a useful signal. No grid winner is selected.

Across all nine settings, newly covered Jerome accuracy never exceeds 16.7%; Caesar never exceeds 50%. AUC stays 0 for Jerome and ranges from 0.1563 to 0.3906 for Caesar. The least-smoothed one-neighbor model drops accuracy to 0% Jerome and 18.75% Caesar. Weakening shrinkage therefore does not rescue these profiles.

These sensitivity results are post-primary development diagnostics, not independent confirmation.

## What to retain, and what to try next

Retain the iteration41 evidence that familiar predicate identity carries case information. Reject this particular attempt to extend that signal through sparse aggregate construction similarity; do not promote it into the grammatical objective.

Two limits now have concrete examples. First, five target *introeo* examples depend on a single source occurrence, so richer source support remains necessary. Second, the newly covered Caesar examples include *sum* with both cases (five ablative and two accusative): a lemma-level profile necessarily assigns all seven the same probability. More lemma counts alone cannot distinguish those token-level readings.

The next discriminating hypothesis is **occurrence-specific context**, rather than another aggregate lemma profile: does non-target context around a particular predicate separate its *in* readings? A diagnostic should exclude the PP's case/agreement morphology, compare within the same predicate where possible, and use source-only fitting plus sentence/context shuffles. First audit whether source data contains enough predicates with both cases; otherwise expand source support while excluding target IDs/authors and the reserved set. This is a proposed next experiment, not a result of this iteration.

## Verification and artifacts

349 regression tests pass. The validator reconstructs source profiles and both source models, checks source-only IDs and reserve exclusion, replays 6,512 probabilities including shuffle controls, leave-predicate-out and sensitivity predictions, and confirms that donor lists exclude the query lemma. Tests mutate the case and lexical identity of an *in* complement without changing profiles; they also cover indirect subtree exclusion, exact fallback, self-donor exclusion, transferable profiles, and normalized/order-invariant vectors.

Run `python -m benchmarks.grammar_predicate_profiles_iteration42`, then `python -m benchmarks.grammar_predicate_profiles_iteration42_sensitivity` and `python -m benchmarks.grammar_predicate_profiles_iteration42_validate`. The experiment and sensitivity runners refuse overwrite. Code is `src/voynich_smt/predicate_profiles.py`; artifacts are under `experiments/results/grammar-restoration/iteration42/`, including the staged declarations, source annotations/profiles, models, predictions, neighbor audit, controls, leave-predicate-out results, uncertainty summaries, and sensitivity outputs. Previous artifacts and the shared todo remain unchanged; reserved200 remain unscored.
