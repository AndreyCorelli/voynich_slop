# Sentence-wide masked roles with morphology and dependency supervision

2026-10-12. **Implemented and tested. More context and supervised structure improve role prediction slightly, but the objective still fails under optimization.** This model cannot replace the successful role oracle.

## Model and separation of information

Use two 64-dimensional GRUs, reading a sentence forward and backward. Expected role at position i uses only forward state i−1 and backward state i+1. Its own spelling, suffix and dictionary morphology are therefore absent from its prediction. Each surrounding word supplies hashed lexical/suffix embeddings and an ambiguity-preserving union of dictionary morphological features. Unlike the earlier three-word window, every sentence position can influence a prediction.

The joint-role output predicts POS plus the oracle's role-related inflections: case/number/gender for nouns and adjectives; number/person for verbs. There are 113 training signatures. Two auxiliary heads learn the gold dependency relation and a nine-class head offset (root, left/right, distance ranges). This supplies dependency supervision, **not a full dependency parser or a recovered dependency tree**. Auxiliary outputs are not used as gold information at inference. The scorer uses only expected-role probabilities and proposed words' public dictionary readings.

Preserve old experiment files. New implementation is `src/voynich_smt/sentence_roles.py`, with a separate training/search benchmark and audit. Existing Torch and the pinned Whitaker dictionary were sufficient; no additional downloads were needed.

## Data, training and selection

Merge the local public UD partitions and enforce a new whole-author experiment split:

- **Train:** Caesar, Jerome, Phaedrus, Petronius and Propertius; 13,311 sentences / **145,616 tokens**. Jerome contributes 107,883 tokens, so this training distribution is heavily biblical.
- **Calibration:** Ovid, Vergil and Suetonius; 351 sentences / 4,652 tokens, including 3,102 content-word tokens.
- **Test:** the existing Cicero, Sallust, Tacitus, Augustus and Palladius fixtures. No test author contributes supervised training or calibration examples.

Training sentences have 3–96 non-punctuation alphabetic tokens. Deduplicate identical word/head/relation sequences and explicitly check that no exact test-sentence word sequence occurs in training/calibration. All dictionary features are obtained from Whitaker analyses, not selected using gold tags. Look up 6,895 additional surface forms. Dictionary resource files and public corpus inputs are hashed; lookup failures are recorded.

Train eight epochs with seed 2303, AdamW learning rate .002, batch size 32, dropout .2, role label smoothing .05 and auxiliary loss weights .2 each. Select checkpoint using calibration role negative log likelihood only, then choose temperature from .5/1/2/4 using the same calibration criterion. Epoch **4**, temperature **1**, was selected. Freeze weights and selection before test inference/attacks.

Readiness criteria for a long search were declared before test results: >=30% calibration complete-role accuracy and >=90% calibration original/valid-alternative preference over corruptions. These are exploratory engineering thresholds. The model fails the role criterion, so run only the bounded attack diagnostic rather than extending the budget.

## Inference and static ranking

On **unique test sentences**, 2,166 content tokens:

| Measurement | Result |
|---|---:|
| Complete expected-role signature accuracy | **10.99%** |
| Previous short-context model on exactly the same tokens | 8.77% |
| POS of highest-probability signature correct | 27.42% |
| Auxiliary dependency relation accuracy, all eligible tokens | 23.23% |
| Auxiliary head-offset-bin accuracy, all eligible tokens | 43.58% |

Do not compare 10.99% directly with the earlier report's 8.53%: that earlier figure double-counted overlapping fixture sentences. The aligned audit removes that difference.

Calibration complete-role accuracy is 9.61%, despite 100% coverage of its gold content-role classes. Static original > corrupted preference is 9/10 on calibration and **14/16 on test**. The noun-substitution grammatical controls score above corruptions in 10/10 and **16/16** respectively. The known Augustus control has one failing evaluation edge; its two static comparisons remain in this descriptive count, while its optimization starts are excluded.

These are repeated correlated passage comparisons, not generalization bounds. Better static discrimination again does not establish a robust optimization objective.

## Frozen-model fresh attacks

Use unchanged strict ascent: 25% injective type swaps, 75% single replacements, global dictionary assignments. Seeds **1601/1613**, budgets **100/1,000**, eight existing fixtures, four starts; exclude the known invalid Augustus control. **62 runs / 62,000 proposal opportunities.** Original forms are supplied in the candidate pools and most assignments are correctly fixed; at most 24 types vary. No gold role, edge or plaintext information enters scoring.

Score sums log probability mass compatible with each proposed word's dictionary readings. Unsupported words receive a constant probability floor rather than disappearing from the objective. The dictionary readings are independently compatible, not a globally consistent morphological parse.

| Structural outcome | 100 proposals | 1,000 proposals |
|---|---:|---:|
| Valid starts structurally stable | **0/30** | **0/30** |
| Corrupted starts avoiding both edge and role regression | 0/32 | 2/32 |
| Median minimum edge/role repair | −116.7% | **−133.3%** |
| Worst degradation among high-scoring valid-start candidates | 30% | **35%** |

**0/32 corrupted searches fully restore the checked structure.** Only 9/62 runs avoid further structural damage between 100 and 1,000 proposals. Palladius also fails: zero valid-start stability, zero corrupt nonregression and −203.3% median repair at 1,000.

Repair measures the worse of recovered original-role-compatible occurrences and independently satisfied gold agreement/government edges. Negative repair beyond −100% means additional damage exceeds the initially small damage. These checks are not full parse correctness or expert judgments of every candidate's grammaticality. They reuse the earlier evaluation definition; test authors/passages have been inspected in previous experiments.

## What this establishes

The sentence-wide model improves complete-role accuracy by about 2.2 percentage points on aligned tokens. It still leaves most expected roles unresolved and rewards dictionary changes that damage the measured structure. Adding morphology and these dependency auxiliary targets is **insufficient in this implementation**. It does not refute all sentence-wide or learned objectives; this is a small randomly initialized recurrent model, with a highly uneven corpus, no pretrained language encoder and no full dependency-tree scoring.

Hiding the target removes direct inflection lookup, but also removes evidence about which role it should occupy. Multiple roles can be plausible from the remaining sentence. The next research question should distinguish this uncertainty from model weakness: compare grammar-feature prediction conditional on dictionary-derived target POS, while withholding the target's case/number/gender, and use more balanced cross-author training. That would be a separate experiment, with no supplied gold POS. Do not increase this objective's search budget.

## Verification and artifacts

Ten focused tests pass, including exact target-invariance under spelling/morphology changes, influence beyond the earlier window, padding isolation, ambiguous-reading preservation and head-index remapping after punctuation removal. Frozen-model replay reproduces all attacks and report. Independent audit recomputes all **186 checkpoint** grammatical metrics, verifies dictionary injectivity, fixed assignments and nondecreasing objective scores, and aligns the earlier model's accuracy.

[Report](../experiments/results/latin-sentence-role/report.json), [precheck](../experiments/results/latin-sentence-role/precheck.json), [selection](../experiments/results/latin-sentence-role/selection.json), [manifest](../experiments/results/latin-sentence-role/manifest.json), [audit](../experiments/results/latin-sentence-role/audit.json), [replay](../experiments/results/latin-sentence-role/validation.json), [examples](../experiments/results/latin-sentence-role/examples.md).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_role build
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_role train
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_role test
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_role validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_role_audit
```

`build` refuses an existing dataset. Frozen inputs and implementation hashes are checked before test/replay. Replay validates frozen-model inference and searches; it does not rerun training. UD Latin PROIEL r2.17 is CC BY-NC-SA 3.0; UD Latin Perseus r2.17 is CC BY-NC-SA 2.5. Source attribution/license files are retained beside these artifacts.
