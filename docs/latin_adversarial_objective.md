# One adversarial objective-training round

Run: 2026-10-12. **No tested scorer passed the preservation, restoration and budget-growth gate.** Adversarial pair training did not make the existing structural proxies robust to fresh optimization. The stable model collapsed to a constant score; nonflat linear and quadratic alternatives still rewarded damaging dictionaries.

## Frozen protocol

Collect accepted mutations using the unchanged optimizer and the two earlier structural rankers. Use four fitting works and three calibration works, keeping every passage, trajectory and mutation from a work in one split. Reserve the earlier four test works and a previously unused author/work: Palladius’s Opus agriculturae from UD Latin PROIEL r2.17. Palladius is absent from adversarial fitting and calibration. The earlier four test authors have been inspected in prior experiments, so they are reused holdouts, not independent fresh-author confirmation.

Fixtures are the first sentence-preserving 250-word and 1,000-word blocks available from each work: 21 fixtures, including eight test fixtures. A 3,206-word Palladius prefix is prepared for mutation generation/dictionary lookup, but only its first 250-word and 1,000-word blocks are attacked. These overlapping blocks are correlated, not independent trials.

This remains an assisted near-truth audit: at most 24 oracle-selected types vary, all other assignments are correct and fixed, and true forms are in the candidate pool. Every assignment applies globally and preserves injectivity. Proposals remain 75% single replacements and 25% two-type swaps; only strict score increases are accepted. The grammar evaluator never filters proposals or enters candidate scoring. No optimizer modifications or long blind decryption run were performed.

Collection: 104 searches, seed 211, 500 proposal opportunities each. Logs retain all 3,391 accepted mutations, including full before/after dictionaries, passage feature vectors, score differences, grammatical counts and lost/gained relationship identifiers. Source sentences and cipher segments reconstruct each complete before/after passage. There are 457 mutations losing at least one checked edge.

Training: pairwise logistic loss with ridge regularization. Compare linear nonnegative, linear signed, and signed quadratic expansions of the eight earlier structural features, at five fixed penalties: 15 fitted models. Quadratic expansion has 44 features. Normalization uses fitting-original passages only. Gold syntax supplies labels; inference uses decoded-word proxy features only.

Use 986 fitting pairs and 701 calibration pairs. Examples include individual mutations, complete optimized endpoints, and original/grammatical-alternative candidates versus damaged endpoints. Prefer a candidate only when both gold-edge count and original-role-compatible token count dominate, with at least one strict improvement. Mixed changes are retained in raw logs but omitted from ranking labels. This does not force each optimizer step to preserve grammar. Fitting balances work, fixture, trajectory and example kind.

Calibration: fresh seed 503, 1,000 opportunities for every model. Select on valid-start structural stability, then corrupted-start repair, then worst valid degradation, then calibration pair accuracy. Selection freezes before test attacks. The selected nonnegative model has exactly zero weights.

Because that selection does nothing, freeze two supplemental nonflat alternatives exclusively from calibration: quadratic/ridge 0.001 with the best repair criterion, and linear/ridge 0.1 with best pair accuracy (79.9%). Their selection is saved separately; it does not replace the original selected model, and no test result chooses either alternative.

Fresh attacks: seeds 907/919, checkpoints at 100, 1,000 and 5,000 opportunities, four starts (truth, grammatical noun substitutions, sparse corruption and denser corruption). Compare the selected scorer, both nonflat alternatives and the previous signed structural ranker. Total: 256 test searches and 1,280,000 proposal opportunities; collisions/no-ops are skipped. Calibration adds 300 searches / 300,000 opportunities.

## Acceptance criteria

Predeclared before collection: at least 95% of valid-start archived solutions preserve checked edges and role compatibility; median recovery of at least 50% of initial damage on corrupted starts (taking the worse of edge and role recovery); at least 80% corrupted-start nonregression; at least 90% nonregression from budget 100 to 5,000; worst high-scoring valid-start degradation no greater than 1% of eligible constraints.

Under unchanged strict ascent, the current candidate is the highest-scoring archive entry. Evaluate those best entries at checkpoints. Also track the worst edge/role loss across every accepted candidate above the initial score. Temporary deterioration is not prohibited by the optimizer. Higher scoring is not itself accepted as grammatical success.

## Fresh-test outcome

| Scorer | Valid-start stability at 5,000 | Median repair | Worst high-scoring valid degradation | Runs nonworse from 100 to 5,000 |
|---|---:|---|---:|---:|
| adversarial | 100.0% | 0% (no repairs) | 0.0% | 100.0% |
| nonflat_best_pair_accuracy | 0.0% | negative (-1.67) | 55.6% | 35.9% |
| nonflat_best_repair | 0.0% | negative (-2.00) | 50.0% | 26.6% |
| previous_structural_signed | 0.0% | negative (-2.00) | 35.0% | 18.8% |

Negative repair means damage increased relative to the initial number of damaged relationships/tokens; it can be below −100% when initially few constraints were broken. It is not a classification error rate. Worst degradation is the maximum of lost-edge and lost-role-token fractions, not an average.

The selected constant scorer accepts zero mutations: it preserves valid starts and leaves corrupted starts unchanged. It fails restoration. All nonflat alternatives damage both initially correct and grammatical-alternative starts. The best-pair-accuracy linear model has 79.9% calibration pair accuracy, yet fresh attacks find candidates with 55.6% loss of checked valid-start constraints. The quadratic model reaches 50.0% worst degradation. Pair accuracy again fails to predict optimizer robustness.

Budget trajectories:

| Scorer | Budget | Valid stability | Median repair | Worst valid degradation |
|---|---:|---:|---:|---:|
| nonflat_best_pair_accuracy | 100 | 0.0% | -1.67 | 50.0% |
| nonflat_best_pair_accuracy | 1000 | 0.0% | -1.67 | 55.6% |
| nonflat_best_pair_accuracy | 5000 | 0.0% | -1.67 | 55.6% |
| nonflat_best_repair | 100 | 0.0% | -1.83 | 45.0% |
| nonflat_best_repair | 1000 | 0.0% | -2.00 | 50.0% |
| nonflat_best_repair | 5000 | 0.0% | -2.00 | 50.0% |

The quadratic model’s median repair worsens between 100 and 1,000, and worst degradation grows for both nonflat alternatives. Some other aggregate values plateau; that is not restoration. Only 26.6%/35.9% of quadratic/linear runs avoid any edge or role deterioration between the first and last checkpoint.

On previously unused Palladius, both nonflat alternatives preserve zero valid-start runs and repair negatively; worst valid degradation is 23.1%. Thus the failure is not confined to the previously inspected test authors. Palladius is later Latin and differs in genre from some fitting works, which limits how specifically the transfer failure can be attributed.

## Label audit and measurement limits

A post-hoc control audit found that the Augustus 250-word noun-substitution start retains every measured original-role inflection but fails one of 18 baseline gold-edge checks. Consequently, it should not be described as fully satisfying the measured grammar. Excluding its two seeds leaves 30 eligible valid-start runs per model; their preservation results remain 100% for the constant scorer and 0% for all nonflat scorers. The original collection/selection/report remain frozen; [audited eligibility results](../experiments/results/latin-adversarial-objective/control-eligibility-audit.json) record this correction.

Gold-edge checks cover ambiguity-relaxed adjective agreement, finite-verb/noun-subject number agreement and selected preposition case government. Original-role compatibility separately checks POS and role-related inflections while allowing different vocabulary. Baseline-filter to dictionary-analyzable original constraints. Each edge may use a different admissible reading; this overestimates consistent grammaticality. These metrics do not reconstruct dependency trees, validate all verb arguments, establish semantic equivalence or rule out every alternative parse. Labels are automatic, not expert-adjudicated universal grammaticality.

No new inference model was trained to identify relationships from decoded text. Linear/quadratic adversarial learning operates on coarse morphology-sequence, agreement, coverage and low-tail aggregate features. The result establishes failure of this representation/training round; it does not prove adversarial training or all objective architectures cannot work.

## What to do with this result

The experiment now has auditable optimizer-generated examples and a repeatable acceptance test. The next justified change is richer evidence about grammatical relationships in the scorer—for example, a sentence model trained to infer dependencies and roles from known-language text, with ambiguity handled explicitly. Test its objective against these adversarial dictionaries and newly generated attacks. The existing aggregate features and one-round reweighting do not justify a large search budget.

## Artifacts and validation

[Mutation logs](../experiments/results/latin-adversarial-objective/collection.json), [training pairs](../experiments/results/latin-adversarial-objective/pairs.json), [selection](../experiments/results/latin-adversarial-objective/selection.json), [nonflat selection](../experiments/results/latin-adversarial-objective/alternative-selection.json), [main attack report](../experiments/results/latin-adversarial-objective/report.json), [nonflat attack report](../experiments/results/latin-adversarial-objective/alternative-report.json), [examples](../experiments/results/latin-adversarial-objective/examples.md). Mutation logs are approximately 121 MB because they retain complete dictionaries.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_adversarial_objective build
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_adversarial_objective collect
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_adversarial_objective train
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_adversarial_objective test
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_adversarial_alternatives
```

Build refuses existing frozen data. Repeating test and alternatives fully replays and compares the saved attacks. Both replay checks passed. Independent audit verified all 3,391 mutation dictionary transitions, score changes and relationship loss/gain counts; recomputed before/after features and gold metrics for 104 sampled mutations; refit all 15 models identically; checked whole-work split separation and recomputed acceptance gates. Incremental/full score checks passed at attack checkpoints. Ten focused tests passed, including safeguards against hiding role damage behind agreement repair and against claiming a flat score repairs damage.

## Sources and licenses

Earlier texts: [UD Latin Perseus r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17), CC BY-NC-SA 2.5. Fresh work: [UD Latin PROIEL r2.17](https://github.com/UniversalDependencies/UD_Latin-PROIEL/tree/r2.17), CC BY-NC-SA 3.0. PROIEL includes Palladius’s Opus agriculturae; see the [official corpus description](https://universaldependencies.org/treebanks/la_proiel/). Original licenses and attribution READMEs are retained beside derived artifacts.
