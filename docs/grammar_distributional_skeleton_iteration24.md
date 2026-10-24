# Iteration 24: corpus context classes and a reliable skeleton

The proposed context-profile representation does **not** establish better grammatical recovery. Its small Jerome gain is uncertain; it loses on Caesar, where the shuffled-context control performs better. No anonymous arm has enough tuning evidence to enable even the conservative 50% precision policy. The additional diagnostics point toward class alignment and information loss in the coarse prototypes, rather than a demonstrated benefit from richer context alone.

## Frozen experiment

We reuse iteration 23's 767 eligible source training sentences. All new tuning, test and background IDs are disjoint from prior grammar manifest/truth declarations and from the reserved 200 IDs. Reserved sentences are skipped before token annotation parsing.

| Split | Sentences | Tokens |
|---|---:|---:|
| Source training: Jerome/Palladius | 767 | 8,106 |
| New tuning: Jerome | 40 | 473 |
| New test: Jerome | 100 | 844 |
| New test: Caesar | 100 | 1,717 |
| Unlabeled tuning background | 200 | 1,579 |
| Unlabeled Jerome test background | 400 | 3,486 |
| Unlabeled Caesar test background | 400 | 7,751 |

Background records contain tokens and metadata only: no dependency edges or property labels are stored or used. All arms receive identical background text. Caesar is absent from supervised fitting and tuning. Freshness is relative to the audited declared grammar samples, not a claim about every historic read of the treebank.

The task remains iteration 23's direct labeled subject, object, nominal-modifier and coordination links within a 12-token candidate radius. Full reference edges, including those outside the radius, remain in evaluation denominators. No reference predicate positions, POS tags, heads or dictionary readings enter the anonymous arms. Sentence boundaries are supplied.

## Corpus context representation

For each anonymous word and encrypted two-character ending, count neighbors at offsets −2, −1, +1, +2. Context axes are anonymous neighboring word-frequency ranks, ending-frequency ranks, and sentence boundaries. These axes are key-invariant but depend on corpus frequency ordering; they do not assume aligned Latin spellings.

We fit eight word-profile and eight ending-profile centroids on **unlabeled source training text only**, using deterministic farthest-first k-means. At prediction time, profiles exclude all context observations from the sentence being predicted. Sparse word profiles back off to ending profiles; sparse ending profiles back off to the remaining corpus context distribution. Frequency/rank axes still use the complete unlabeled split. Thus the experiment is transductive and the leave-sentence-out guarantee concerns profile observations, not all corpus statistics.

The representation adds nearest-cluster identities, quantized distances to shared source centroids, evidence-support bins and endpoint cluster interactions to the original frequency-based feature arm. Four matched arms compare:

- the original anonymous frequency/rank features;
- additional ordered context profiles;
- profiles from independently shuffled sentences, with prototypes refitted without labels;
- ambiguous dictionary morphology as an explicit privileged ceiling.

Shuffling preserves sentences' word multisets, all word/ending unigram statistics and available background text while disrupting ordered context. It is a negative control, not a null model of every possible non-grammatical signal. The oracle dictionary channel remains separate; prototypes never read it.

## Conservative skeleton

Three classifiers per arm are fitted on fixed sentence-bootstrap samples. A proposed edge must have the same head and relation in all three; numeric ties abstain. A threshold and competing-edge margin then select a subset, with greedy rejection of cycle-forming edges and no forced completion. This is stability across bootstrap classifiers, not proof of support under every grammatical analysis.

All thresholds and margins are frozen on tuning data before test scoring. In addition to an F1 operating point, precision targets of 50%, 70% and 85% require at least 20 tuning predictions and a Wilson 95% lower precision bound meeting the target. A target with no eligible tuning policy emits no edges. Because thresholds are selected from a grid and test distributions can shift, these bounds are diagnostic selection rules, not formal test-precision guarantees.

All anonymous arms declined all three precision targets. The dictionary arm qualified only for the 50% policy. No thresholds were relaxed after test results were seen.

## Fresh results

The table reports the tuning-selected **F1 operating point**, not a high-precision skeleton and not a percentage of restored words.

| Arm | Jerome precision / recall / F1 | Caesar precision / recall / F1 |
|---|---|---|
| Frequency baseline | 14.8 / 11.2 / **12.7** | 8.8 / 6.7 / **7.6** |
| Ordered profiles | 26.0 / 9.7 / **14.1** | 10.3 / 4.1 / **5.8** |
| Shuffled profiles | 11.3 / 11.2 / **11.3** | 12.6 / 9.9 / **11.1** |
| Dictionary ceiling | 50.8 / 37.3 / **43.0** | 39.7 / 23.3 / **29.3** |

There are 268/563 reference test links. The ordered-profile change versus baseline is +1.4 F1 points on Jerome, with paired sentence-bootstrap interval [−2.7, +5.5], and −1.8 on Caesar [−4.3, +0.7]. Against shuffled profiles it is −5.3 points on Caesar [−8.4, −2.3]. These are conditional descriptive intervals with fixed models/profile statistics; they do not account for refitting, shared transductive context or adjacent-sentence dependence.

All outputs are acyclic by construction. That structural property does not imply correct syntax. Ordered profiles cover only 11.8%/13.0% of dependent tokens at the F1 point and emit **zero complete shared-head subject–object fragments**. The reference contains 25/46 such fragments. Baseline recovers 1/25 on Jerome and 0/46 on Caesar; the dictionary arm recovers 5/25 and 0/46. A fragment means an exact subject→head plus object→same-head pair, not an entire restored clause.

At the only enabled conservative dictionary policy, test precision is 77.8% on 45 Jerome predictions and 56.1% on 66 Caesar predictions, with recalls 13.1% and 6.6%. No arm was enabled for the 70% or 85% policies. Empty policies have undefined precision and zero coverage; they are not successes at perfect precision.

Extra background, ensembles and acyclicity make direct comparisons with iteration 23 inappropriate. The matched within-iteration baselines are the comparison of interest.

## Did the clusters recover grammatical classes?

A separate source-supervised readout maps each anonymous word/ending cluster pair to a source label by training majority, with a global fallback. Labels never enter centroid fitting or the relation feature extractor. Case and Number are scored only at annotated property-bearing positions; these are conditional probes, not detection of which tokens bear the property. Coarse POS has three classes: nominal, verbal, function/other.

| Ordered-profile source readout | Jerome balanced accuracy | Caesar balanced accuracy |
|---|---:|---:|
| Coarse POS | 49.3% | 34.4% |
| Case | 21.2% | 21.7% |
| Number | 50.0% | 50.0% |

Case class counts differ between tests (six/five labels), so balanced-majority baselines are 16.7%/20.0%; Number baseline is 50%. This is weak morphological recovery. Coarse POS information exists descriptively: cluster-pair mutual information accounts for about 20% of coarse POS label entropy within each test corpus, above shuffled-context and shuffled-label controls. However, the source label mapping does not transfer well to Caesar. There is also concentration: the largest Caesar cluster pair holds 62.2% of tokens. These descriptive associations do not establish a useful transferable label assignment; token-permutation controls ignore sentence dependence.

The original frequency classes have many more possible categories than the 64 prototype pairs. Raw information measures are consequently not capacity-matched and cannot alone rank representation quality.

## Alignment diagnostic, kept separate

After the main test, a privileged diagnostic fits **only the property readout** using the first 20 labeled target sentences, then scores the remaining 80. Source centroids and context profiles stay fixed. This is labeled target adaptation on an already inspected corpus, not an unsupervised result or an improvement to the relation/skeleton models.

| Representation | Jerome coarse POS: source → target readout | Caesar coarse POS: source → target readout |
|---|---:|---:|
| Frequency classes | 41.8 → **74.3%** | 42.4 → **74.6%** |
| Ordered profile classes | 49.1 → 51.1% | 34.3 → 51.9% |
| Shuffled profile classes | 33.3 → 34.5% | 33.3 → 33.3% |

Frequency-class Number balanced accuracy similarly rises 60.7→73.5% on Jerome and 42.8→77.4% on Caesar. The contextual prototype representation gains little in Number and does not gain in Case under this diagnostic.

This suggests two limitations: aligning anonymous class identities to grammatical labels is difficult, and the chosen eight-by-eight context compression loses information already present in simpler frequency classes. The labeled diagnostic does not provide those labels for an unknown cipher. It is evidence about what to investigate next, not a deployable solution.

## Conclusion and next direction

This implementation does not pass the proposed success criterion of a reliable grammatical skeleton. It also does not support a transferable gain from these context profiles over their matched frequency baseline. That challenges this particular rank-context/centroid representation; it does not falsify all distributional morphology methods.

The stronger next question is **anonymous-class alignment**, rather than adding more local rules or larger context vectors. A controlled next experiment could hide/relabel coarse grammatical classes in a source corpus, then test whether unlabeled class frequency and transition constraints can recover their alignment under new corpus distributions. Compare an oracle alignment, inferred alignment and a shuffled alignment before involving word-level parses. Keep class-information loss separate from alignment failure and preserve abstention in the final relation task. The current tests/background are now declared and inspected; future comparisons need a newly declared evaluation set. The reserved 200 remain untouched.

## Artifacts and verification

Artifacts: `experiments/results/grammar-restoration/iteration24/`. Frozen model/prototype/readout/calibration artifacts precede fresh test evaluation. Separate diagnostic artifacts contain class information and labeled target-readout adaptation; neither changes the main fitted models.

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_distributional_skeleton_iteration24_validate`. Verification checks source labels, fresh split/background/holdout disjointness, train-only centroid fits, bootstrap membership, tuning-only operating choices, and all 3,200 sentence/arm/policy outputs. It independently checks forests and subject–object fragments, repeats cipher-key invariance, and replays the auxiliary diagnostics. Tests cover whole-sentence profile exclusion, privileged-channel isolation, label blindness, shuffle controls, consensus disagreements/ties, conservative abstention and cycle rejection. The relevant combined suite passes **270 tests**. Prior artifacts remain unchanged.
