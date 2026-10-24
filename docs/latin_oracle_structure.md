# Oracle grammatical relationships and roles in dictionary search

Run: 2026-10-12. **Supplying original token roles/inflections makes near-truth structural repair work in this assisted audit. Supplying relationships alone is insufficient for restoring the original roles.** No grammatical inference model or blind decoder is established.

## Protocol

Use the same eight held-out 250-word/1,000-word fixtures, four starts and two seeds as the adversarial attack: four previously inspected authors plus previously unused Palladius. At most 24 types vary; other assignments are correct and fixed. The candidate pool includes original forms and grammatical alternatives. This is a strong oracle diagnostic, not plaintext-independent decryption.

Leave the optimizer unchanged: strict ascent, 75% single replacements and 25% injective two-type swaps, global assignments applied to every occurrence. Score/evaluate at 100, 1,000 and 5,000 proposal opportunities. Exclude the previously identified Augustus control that does not initially satisfy every measured edge. Three objectives × 62 runs = 186 searches / 930,000 opportunities; collisions/no-ops are skipped.

Objectives have equal unit costs and no fitted weights:

- **Edges only:** negative count of failed supplied adjective agreement, noun-subject number agreement and preposition-government checks. The gold topology and relation types also supply the endpoint POS types used to select admissible dictionary readings.
- **Roles only:** negative count of occurrences lacking a dictionary reading matching their original POS and role-related case/number/gender or verb number/person. This supplies context-specific inflection answers in addition to POS; it is substantially stronger than knowing the language or merely knowing dependency heads.
- **Edges and roles:** sum of those two negative violation counts.

As before, evaluate only original dictionary-analyzable constraints. Edges are independently existential over readings, not a jointly consistent parse. The role oracle permits alternative vocabulary; it does not reward exact lemma identity. Of the 30 fully repaired combined-objective runs, 27 finish with vocabulary differing from the original dictionary. Gold information is deliberately inside these objectives. Evaluation reuses the supplied constraints, so this isolates search/constraint adequacy rather than independently validating linguistic correctness.

## Results

| Oracle | Budget | Median repair of initial damage | Corrupted runs with all checked structure restored |
|---|---:|---:|---:|
| edges_only | 100 | 0.0% | 2/32 |
| edges_only | 1000 | 0.0% | 3/32 |
| edges_only | 5000 | 0.0% | 3/32 |
| roles_only | 100 | 8.4% | 2/32 |
| roles_only | 1000 | 96.4% | 17/32 |
| roles_only | 5000 | 100.0% | 30/32 |
| edges_and_roles | 100 | 9.8% | 2/32 |
| edges_and_roles | 1000 | 96.4% | 17/32 |
| edges_and_roles | 5000 | 100.0% | 30/32 |

Repair takes the worse of restored gold-edge fraction and restored original-role-token fraction whenever initially damaged. Consequently, agreement improvement cannot conceal role damage.

**All 30 valid-start runs per objective remain unchanged and structurally stable.** Worst high-scoring valid-start damage is zero. This preservation is expected by construction: zero violations is the maximum score, and the unchanged optimizer rejects ties. It is not evidence that the oracle inferred grammaticality or explored equivalent vocabularies.

Role-only and combined objectives have 100% corrupted-start nonregression at all checkpoints. Their archived structural quality never deteriorates between budgets 100 and 5,000. Both restore every checked constraint in 30/32 corrupted runs at 5,000. On Palladius, both have 100% median repair and stable valid starts.

Edges-only leaves median original-role repair at zero and fully restores only 3/32 corrupted runs. Some relationships can agree under an incorrect role assignment. Its corrupted-start nonregression is 87.5%, and budget nonregression across all starts is 98.4%. Explicit relations alone therefore do not establish restoration of the original construction.

Two residual combined-objective runs retain 3/399 and 1/419 incompatible role occurrences, respectively: Sallust and Palladius 1,000-word high-corruption starts, seed 907. All their checked edges are satisfied. We have not exhausted their neighborhoods or established a local optimum; they remain unresolved within this search budget.

## Acceptance criterion and interpretation

The earlier adversarial gate required >=50% median repair at **every** checkpoint, including 100 proposals. The role/combined oracles miss that early-budget requirement, so they do not pass the full original gate. At 1,000 and 5,000 they satisfy its preservation, repair, nonregression and worst-degradation thresholds. Increasing the budget now improves repair without the systematic damage seen under learned proxies.

These are correlated runs of overlapping blocks from five works, and corruption is sparse. The figures are descriptive assisted-search outcomes, not generalization bounds or recovered dependency-tree accuracy.

**Finding:** context-specific grammatical role/inflection information is sufficient for substantial repair in these fixtures. The remaining engineering question is whether that information can be inferred from a proposed decoding with enough reliability. Knowing the language alone does not supply it.

The next step is a known-language token-role/morphology predictor trained on annotated Latin, evaluated without gold inference inputs and against fresh search attacks. Use predicted distributions rather than rigid uncertain labels; preserve valid alternative vocabulary. Start by measuring whether its sentence-level predictions approximate the oracle on the existing adversarial dictionaries. Do not interpret this oracle result as a working unknown-key decoder.

## Artifacts and verification

[Complete traces and dictionaries](../experiments/results/latin-oracle-structure/report.json), [original/corrupted/repaired excerpts](../experiments/results/latin-oracle-structure/examples.md), [manifest](../experiments/results/latin-oracle-structure/manifest.json), [replay](../experiments/results/latin-oracle-structure/validation.json).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_oracle_structure
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_oracle_structure --validate
```

Full deterministic replay reproduces all oracle attacks and the report. An independent audit recomputed every checkpoint score and grammatical metric and verified dictionary injectivity and nondecreasing objective scores; 27 fully repaired combined-objective dictionaries use alternative vocabulary. Nine focused tests passed, including preservation under alternative noun vocabulary, detection of agreement damage, and the distinction between agreement and original-role restoration.

Data/licenses: [UD Latin Perseus r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17), CC BY-NC-SA 2.5; [UD Latin PROIEL r2.17](https://github.com/UniversalDependencies/UD_Latin-PROIEL/tree/r2.17), CC BY-NC-SA 3.0. Attribution READMEs and licenses are retained beside derived outputs.
