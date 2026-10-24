# Plaintext-independent contextual role pilot

2026-10-12. **This learned baseline does not replace the successful role oracle.** Its objective rewards structural damage under fresh optimization attacks.

## Method

Train a masked-target multinomial logistic classifier on the locally pinned UD Latin PROIEL r2.17 training partition: Caesar's Commentarii belli Gallici, 1,229 usable sentences / 23,183 tokens. All five evaluation authors are excluded from supervised training. The earlier proxy language-model resources also used Caesar; this is not a new external corpus. Training labels are gold POS plus the oracle's relevant inflections: noun/adjective case, number, gender; verb number, person. Other POS classes have no inflection targets. There are 95 joint classes.

The target word's spelling and morphology never enter its own prediction. Features use three words on each side, their suffixes, boundaries and coarse sentence position. All targets share a linear classifier, trained for 15 epochs with fixed seed 1703, Adam learning rate .01, and features occurring at least three times. This deliberately inexpensive pilot uses existing Torch; no package/model download was required. It has no dependency inference, pretrained encoder or long-range context.

The objective sums log probability mass assigned to dictionary readings compatible with each proposed word. It scores every dictionary-analyzable position, without selecting positions using gold annotations. Proposed words can affect neighboring predictions, including other occurrences of the same global substitution type. No original plaintext, gold roles or dependency topology enter scoring. Dictionary ambiguity is marginalized by compatible-class mass, rather than resolved into a joint parse.

Use the existing eight 250/1,000-word test fixtures, four starts, fresh seeds 1201/1213, and unchanged strict-ascent global injective search. Exclude the previously identified Augustus invalid grammatical-control start. **62 searches / 62,000 proposal opportunities**, checkpoints at 100 and 1,000. Most assignments remain correctly fixed, with at most 24 variable types and original forms supplied in the candidate pool. These remain strongly assisted tests, not blind decoding. Passages were inspected in earlier experiments; blocks overlap.

An initial presence-only naive Bayes implementation displayed severe rare-class bias and was replaced before the recorded classifier experiment. The final pilot is exploratory, not an untouched preregistered model comparison. No search-result-driven hyperparameter grid was run.

## Results

- Complete role signature top-1 accuracy: **8.53%** on 2,627 noun/adjective/verb token occurrences. The POS of the top joint signature is correct in 34.94%. Training classes cover 99.81% of these gold labels, so unseen labels alone do not explain the failure.
- Original passages beat corrupted starts in **14/16** comparisons. Relative ranking on static examples therefore still fails to establish a useful optimization objective.
- **0/30 valid-start searches remain structurally stable.** Worst valid-start structural degradation reaches 30% at 100 proposals and **50% at 1,000**, measured against the existing eligible gold constraints.
- **0/32 corrupted-start searches fully restore the checked structure.** Only 1/32 avoids regression in both role and edge counts.
- Median repair, taking the worse of edge and role repair, is **−116.7% at 100** and **−200% at 1,000**. Negative values beyond −100% mean additional damaged constraints exceed the initially small damage; they are not classification error rates.
- Palladius also fails: zero valid-start stability, zero corrupted-start nonregression, median repair −290% at 1,000.

These measurements are dictionary-compatible original roles and independently checked agreement/government edges, not full parse correctness or expert grammaticality judgments. Sparse corruption and overlapping fixtures limit generalization.

## Interpretation and next experiment

The oracle established that supplied contextual roles can guide repair; this pilot shows that local lexical context does not infer them reliably enough. Low training loss (0.264 in the final epoch) together with poor cross-author role accuracy is consistent with memorization and weak transferable structural information. It does not establish that every contextual model will fail.

A stronger experiment should first validate grammatical inference before another large search: a sentence-wide, morphology-aware masked-target encoder, supervised on broader author-disjoint Latin and auxiliary dependency relationships. Keep the target's own surface hidden for expected-role prediction, retain ambiguity, and calibrate confidence on separate works. Compare role accuracy and preference for valid alternative vocabulary against genuine corruptions, then freeze it for fresh optimization attacks. A conventional tagger that simply identifies the proposed word's own inflection would not supply an independent anomaly test.

## Verification and artifacts

Six focused tests pass, including target masking and alternative-lexeme compatibility. Full deterministic replay retrains identical weights and reproduces every attack and report; every checkpoint also checks incremental scoring against full rescoring.

[Report](../experiments/results/latin-context-role/report.json), [manifest](../experiments/results/latin-context-role/manifest.json), [diagnostic](../experiments/results/latin-context-role/diagnostic.json), [replay](../experiments/results/latin-context-role/validation.json). Saved model weights and feature vocabulary are beside these files.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_context_role
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_context_role --validate
```

Data: UD Latin PROIEL r2.17, CC BY-NC-SA 3.0, and inherited Perseus fixtures, CC BY-NC-SA 2.5. Original attribution and license files are retained in the source and adjacent experiment artifacts.
