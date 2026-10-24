# Relative-ranking dictionary search: near-truth audit

Run: 2026-10-12. **The structural rankers fail the preservation test: strict score ascent damages checked grammatical structure from a correct dictionary in every tested run.** Some errors are repaired from more damaged starts, but no run restores all checked edges or all original-role inflections. Good curated-pair rankings did not make the score robust to search.

## Experiment

Ten fixtures from four earlier test works: first complete 250-word block per work, first 1,000-word block where available, and complete works (250–4,204 words). Each fixture encrypts distinct word forms into opaque identifiers, preserving repetitions and sentence order. Search receives ciphertext segments, candidate surfaces, current assignments and frozen scorers; gold token syntax is reserved for evaluation.

This is a deliberately assisted diagnostic, not blind decryption. Select at most 24 active types from the earlier known corruption/control source types, prioritizing their passage frequency. Other dictionary assignments stay correct and fixed. The candidate pool contains true active forms, earlier corrupt/control targets and 64 training-frequent content forms, excluding fixed forms. There are 9–24 active types and 67–105 candidates per fixture. The true answer is available, and most of the text is already supplied. Candidate choices have no target-specific POS or grammatical-role filters.

Start from (1) truth, (2) sparse corruption, (3) denser corruption, or (4) grammar-preserving noun substitutions. Only active types are changed at initialization. Apply every assignment globally and preserve injectivity. Compare frozen signed and nonnegative structural-only pair rankers with morphological-sequence likelihood alone. These structural arms were highlighted after earlier test inspection; no claim of fresh independent model selection is made.

Two seeds, 1,000 proposal opportunities per run: 240 runs and 240,000 opportunities. Proposals are 75% single replacements and 25% two-type swaps. Collisions, no-ops and same-type swaps are skipped, so these are not 240,000 distinct scored dictionaries. Accept only strict increases above 1e-10. Sentence features are cached; rescore all sentences containing a changed cipher type and update the token-weighted passage score transactionally. Check incremental scores against full passage recomputation at saved checkpoints and endpoints.

The eight structural features and their weights/scales/tail thresholds are frozen from earlier experiments. No neural scoring or new fitting occurs. Transitions are cached without changing likelihood computation.

## Results

| Objective | Start | Runs | Edges improve / same / worsen | All checked edges restored | Sum edge change |
|---|---|---:|---:|---:|---:|
| structural_features_signed | truth | 20 | 0 / 0 / 20 | 0 | -124 |
| structural_features_signed | corrupt_low | 20 | 0 / 1 / 19 | 0 | -88 |
| structural_features_signed | corrupt_high | 20 | 18 / 2 / 0 | 0 | +73 |
| structural_features_signed | control_high | 20 | 0 / 0 / 20 | 0 | -117 |
| structural_features_nonnegative | truth | 20 | 0 / 0 / 20 | 0 | -127 |
| structural_features_nonnegative | corrupt_low | 20 | 0 / 0 / 20 | 0 | -86 |
| structural_features_nonnegative | corrupt_high | 20 | 19 / 1 / 0 | 0 | +64 |
| structural_features_nonnegative | control_high | 20 | 0 / 0 / 20 | 0 | -127 |
| morphological_sequence | truth | 20 | 0 / 0 / 20 | 0 | -159 |
| morphological_sequence | corrupt_low | 20 | 0 / 1 / 19 | 0 | -117 |
| morphological_sequence | corrupt_high | 20 | 18 / 1 / 1 | 0 | +44 |
| morphological_sequence | control_high | 20 | 0 / 0 / 20 | 0 | -153 |

Sums combine correlated runs of overlapping fixtures; they describe observed changes, not independent sample sizes. Each objective has 20 truth-start runs. **All 60 truth-start runs lose gold edges while increasing the objective.** All 60 grammar-preserving-start runs also lose edges. No run restores all eligible edges.

The denser-corruption starts sometimes gain edge satisfaction: signed ranker improves 18/20 and nonnegative improves 19/20. However, total original-role-compatible token counts decrease even in those groups. Repairing some agreement while introducing other role errors does not restore the original construction.

Whole-work truth starts, signed ranker, seed 11:

| Work | Checked edges before → after | Role-compatible tokens before → after |
|---|---:|---:|
| phi0474.phi013.perseus-lat1.tb.xml | 82 → 72 | 551 → 524 |
| phi0631.phi001.perseus-lat1.tb.xml | 294 → 279 | 1627 → 1590 |
| phi1221.phi007.perseus-lat1.tb.xml | 54 → 48 | 243 → 227 |
| phi1351.phi005.perseus-lat1.tb.xml | 51 → 42 | 273 → 254 |

Overall exact-token recovery remains around 96%, because nearly all assignments were supplied and fixed. This is not 96% decryption success. The saved summary also reports recovery within active types only; exact identity is a diagnostic and not the grammatical success criterion.

## What the structural metrics actually establish

Evaluate dictionary readings against the original annotated dependencies: adjective–noun case/number/gender compatibility, a single noun subject’s agreement in number with its finite verb, and unambiguous preposition case government. Include only edges that the dictionary can satisfy in the original text. Each edge independently asks whether some pair of readings satisfies it; this can overestimate grammaticality because different edges may use inconsistent analyses.

Separately measure whether each dictionary-analyzable gold content occurrence retains an admissible reading matching its original POS and role-related case/number/gender or verb number/person. This permits alternative vocabulary with matching roles. It is not exact lexical recovery. Eligible original occurrences are baseline-filtered, so truth scores 100% by construction on the measured subset.

Neither metric infers a dependency tree. We do not evaluate full verb valency, idioms, semantic constraints, unmeasured subject types or all possible alternative parses. Gold heads/roles are available only to the evaluator. The strong conclusion is loss of the intended checked structure under strictly increasing proxy score, even in an assisted setting.

## Consequence

Do not spend a long search budget on these rankers as the sole objective. The search itself constructs adversarial examples that defeat the curated-pair results. Longer ascent can continue exploiting those weaknesses.

The saved wrong dictionaries are useful next training/evaluation material: compare structurally valid candidates with these actual score-improving failures. A stronger scorer needs explicit grammatical relationship inference, stronger role constraints, or adversarial training evaluated on new works and new optimizer-generated failures. Oracle role/dependency restrictions can diagnose how much such information would help, but cannot be presented as a plaintext-independent decoder.

## Artifacts and verification

[Complete run traces/dictionaries](../experiments/results/latin-relative-search/report.json), [summary](../experiments/results/latin-relative-search/summary.json), [original-versus-decoded excerpts](../experiments/results/latin-relative-search/examples.md), [protocol](../experiments/results/latin-relative-search/manifest.json), [validation](../experiments/results/latin-relative-search/validation.json).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_relative_search
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_relative_search --validate
```

Fifteen focused tests passed, covering transactional changes, global repeated-occurrence updates, injectivity, pair fitting and existing morphology models. Full deterministic search replay reproduced the report, with incremental/full scores checked during both runs.

Source text and annotations: [UD Latin Perseus r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17), CC BY-NC-SA 2.5. License and original attribution README are copied beside the derived artifacts.
