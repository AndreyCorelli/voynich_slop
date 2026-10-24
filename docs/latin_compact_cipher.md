# Compact cipher discovery judged by frozen-key prediction

2026-10-13. **The baseline discovers compact letter-substitution hypotheses that predict held-out Latin at 99.93% letter / 99.60% word accuracy. Our inferred POS evidence provides no demonstrated additional benefit in this first family.** This tests downstream cipher prediction, not whether a proposed decoding looks grammatical.

## Acceptance target and scope

Hide a global bijective letter-substitution key. Discover a hypothesis using one passage, freeze it, and decode different sentences under the same key without changing parameters or adding dictionary exceptions. Word/sentence boundaries remain visible; spelling is canonical lowercase j→i/v→u. The permitted family and its 24-character alphabet are supplied, but the key and original text are withheld from ordinary search.

This is a **general letter permutation**, not the earlier arbitrary word-substitution model. Its entire predictive hypothesis is one 24-letter permutation with no exceptions. There are 24! keys, about 79.04 bits of key information. Each selected key is actually serialized as a **10-byte enumerative code**; a standalone standard-library predictor decodes new ciphertext using that code and the fixed family specification. It needs no learned model, dictionary, POS or grammatical annotations after discovery.

Only this family is tested for hidden-key discovery. A calibration-only Caesar-style rotation sanity check enumerates all 24 shifts of the same canonical alphabet and recovers the generating shift on all three calibration works. We have not tested compact polyalphabetic extensions, unknown-family selection, missing boundaries or arbitrary word substitution in this benchmark.

## Data and separation

Character language model and POS training use the earlier author-disjoint fit corpus: 145,616 annotated tokens from Caesar, Jerome, Phaedrus, Petronius and Propertius. Train the character model from words only; POS labels supervise the auxiliary extractor. All five target authors are excluded from those training sources.

Calibration uses Ovid, Vergil and Suetonius: first approximately 100/300 words for discovery and a disjoint final approximately 300-word passage for prediction. Two independent keys per author give 12 calibration fixtures across overlapping widths. POS checkpoint selection uses these calibration authors' annotations; evidence weights use calibration held-out decryption accuracy.

Test uses Cicero, Sallust, Tacitus, Augustus and Palladius, with **15 independent keys / 24 encrypted fixtures**. Three keys per author; discovery widths approximately 100 words for every author and 1,000 for Cicero/Sallust/Palladius where enough text exists. Preserve full sentences, so exact lengths vary. Predict a disjoint final passage of approximately 300 words under the same key. Longer/shorter discovery fixtures share their author's keys and held-out passages; these are paired observations, not 24 independent texts/keys. Authors and many source passages were inspected in earlier experiments, so this is an exploratory downstream benchmark, not an untouched final corpus.

Explicit checks reject exact training/test sentence overlap and discovery/held-out sentence-ID overlap. Ordinary public fixtures contain ciphertext, boundaries, identifiers and split/width metadata, **not key seeds, plaintext, grammatical labels or correct function-word anchors**. Original dictionaries/annotations and key generation metadata are stored in a separate truth directory and used only for evaluation and explicitly labeled oracle arms. Each test hypothesis is written to disk before held-out metrics are computed; evaluation verifies the saved hypothesis remains unchanged.

## Decoder and evidence arms

Baseline uses a smoothed character four-gram model trained on the fit corpus. Search proposes swaps in the 24-letter decryption permutation, with fixed cyclic annealing and an archive ranked only by the discovery objective. Incremental scoring updates affected character windows and word types. Each arm has two identical frequency-based initializations with the same six random perturbations, search seeds 17/43 and **10,000 proposals per restart**. No initialization receives true letter mappings.

Compare:

1. **Baseline:** character evidence only.
2. **Word candidates:** a previously frozen 100,000-form inventory, selected independently of these target authors. A word's equal-letter pattern must match the ciphertext pattern; compatible dictionary membership adds soft evidence, not a hard exclusion.
3. **Inferred POS:** a multinomial classifier sees only substitution-invariant own/neighbor equal-letter patterns and lengths, with three-word context. It predicts nine coarse POS distributions; candidate words are scored using their possible dictionary POS readings. It never sees target spelling, decoded correct context or original roles.
4. **Oracle POS:** supply correct context-specific POS as an answer-given diagnostic.
5. **Oracle roles:** supply correct POS and role-relevant case/number/gender or verb number/person, again an answer-given diagnostic. These are local role/inflection constraints, **not supplied or inferred dependency trees**.

Dictionary readings preserve ambiguity. Oracle labels score only occurrences for which the original dictionary form has a compatible inventory reading, so the control is not penalized by known annotation/inventory mismatch; that eligibility is additional oracle information. Ordinary arms have no such gold-based eligibility. Out-of-inventory words retain an escape path and a soft penalty. An entire key always remains admissible regardless of dictionary membership.

The POS model trains six epochs; calibration negative log likelihood selects epoch 1. Calibration POS accuracy is 40.22%, and test discovery-token accuracy is 42.16%, counting paired/repeated fixtures. These coarse POS figures are not comparable with earlier complete-role signature accuracy.

Weights .03/.1/.3 are compared with the zero-weight baseline; select highest calibration held-out letter accuracy, preferring the smaller weight in ties. Frozen selections: candidates .1, inferred POS **0**, oracle POS .1, oracle roles .03. Calibration is nearly at the prediction ceiling. Selecting zero means the final inferred-POS arm deliberately reverts to the baseline; it does not show that every POS model or integration would be useless.

## Frozen prediction results

Mean per-fixture held-out accuracy at the full budget:

| Discovery evidence | Letter accuracy | Word accuracy | Entire held-out passage exact |
|---|---:|---:|---:|
| Baseline | **99.9286%** | **99.5956%** | 16/24 |
| Word candidates | 99.9092% | 99.4855% | 15/24 |
| Inferred POS, selected weight zero | 99.9286% | 99.5956% | 16/24 |
| Oracle POS | 99.9092% | 99.4855% | 15/24 |
| Oracle roles/inflections | 99.9286% | 99.5956% | 16/24 |

Baseline held-out letter accuracy is 99.9015% from short discovery passages and **99.9738% from 1,000-word discovery passages**. Its lowest test fixture is 99.5327%. Across the repeated test predictions, token-weighted function-word exact accuracy is **99.9149%** and auxiliary-word accuracy **100%**. Those words were recovered through the cipher hypothesis, not supplied as anchors; these figures apply to this easy family and do not establish exact auxiliary recovery for an unknown cipher family.

The complete 24-letter key is exactly correct in only **1/24** baseline fixtures. Rare and discovery-unobserved symbols remain problematic or underdetermined; high held-out text accuracy must not be described as complete key identification. The exported signals explicitly list remaining plaintext alternatives for symbols absent from discovery. A chosen full permutation makes one point prediction for those symbols, and held-out accuracy measures the resulting errors.

All arms have the same 80-bit serialized key size and no word-specific exceptions. This experiment therefore tests predictive key discovery, not a complexity tradeoff among different cipher families. Discovery-model parameters are shared language resources used for search; they are not required by the frozen predictor.

## Early-budget audit: can evidence help find the key faster?

After seeing the calibration ceiling, before reading final test results, add an exploratory audit at **100/1,000 proposals per restart**, retaining the already selected weights. No early-budget model/weight tuning is performed. Independently rerunning each shorter prefix reproduces the corresponding full-run archived objective; the annealing schedule does not depend on total budget.

| Evidence | Held-out letters at 100 steps/restart | At 1,000 steps/restart |
|---|---:|---:|
| Baseline | 33.62% | **97.01%** |
| Word candidates | 35.39% | 95.70% |
| Inferred POS, zero weight | 33.62% | 97.01% |
| Oracle POS | 34.97% | 97.35% |
| Oracle roles/inflections | 33.71% | **97.64%** |

At 1,000, oracle POS beats baseline in 11 fixtures, loses in four and ties in nine; mean letter gain +0.335 percentage points. Oracle roles win three, lose two and tie 19; mean +0.632 points. Median gain is zero for both. Oracle roles also improve mean word accuracy from 87.08% to 89.07%. This is limited, heterogeneous evidence that ideal role information can assist early search; it is not a demonstrated reliable speedup from inferred structure. Weights optimized for the full budget may not be best at the shorter budgets.

Word candidates help very early letter guesses but worsen average accuracy at 1,000 and slightly worsen final prediction. Their median candidate set has **175 words**, but the inventory retains only **75.26% of true word occurrences / 68.28% of true word types** in the paired discovery fixtures. Hard-filtering those sets would discard many correct mappings. The export preserves an out-of-inventory option.

## Deliverables for other models

`signals/*.json` contains per-ciphertext-type pattern-compatible candidate word IDs, occurrence positions, mean inferred POS distributions and the baseline-decoded surface. IDs refer to the frozen `candidate-inventory.txt`; no gold annotations or exact function-word assumptions enter the exporter. It reads zero truth files. These are uncertain intermediate signals, not a recovered parse or calibrated confidence certificate.

`compact-keys/*.bin` contains the actual 10-byte hypotheses. A standalone predictor and two reviewable bundles are saved: one specified Palladius long-discovery case and the baseline's least accurate held-out case. Each bundle contains the key, held-out ciphertext, prediction and evaluation original. [First 100 original/predicted words](../experiments/results/latin-compact-cipher/examples.md) can be compared directly.

```sh
python experiments/results/latin-compact-cipher/predict.py \
  experiments/results/latin-compact-cipher/prediction-examples/palladius-long/key.bin \
  experiments/results/latin-compact-cipher/prediction-examples/palladius-long/ciphertext.txt
```

## What this establishes—and the next decision

We now evaluate the user's requested downstream criterion: a small fixed hypothesis predicts new text without adaptation. The baseline succeeds strongly under known general letter substitution with visible boundaries. This is a meaningful positive result, distinct from our failed arbitrary-word-substitution grammatical-restoration objectives.

The available pattern-based POS extractor gives no demonstrated incremental benefit under full-budget selection. Correct oracle roles show only modest early-budget benefit, while the full task is near the baseline ceiling. This does not justify another expensive grammar-training run or establish that inferred relationships help discover unknown cipher families. No joint dependency/grammar engine is integrated into this decoder.

The next meaningful benchmark should be a predeclared harder **compact** family or discovery regime where the baseline has room to improve, then repeat the oracle preflight before improving grammar extraction. Candidate pattern invariance must be adapted to that family; a pattern feature valid for monoalphabetic substitution cannot simply be assumed valid for every encryption scheme.

## Verification and reproduction

Six focused tests pass: permutation round trips and pattern invariance; incremental/full-objective agreement; zero-weight ablation; exact candidate-pattern filtering; ciphertext-only POS feature invariance; and actual compact-key serialization with invalid-code rejection. Full frozen-model test replay and the exploratory budget replay reproduce keys and metrics. An independent audit recomputes **360** primary/early-budget frozen evaluations, checks hypothesis bijectivity/no exceptions, and verifies early objectives against full-run archives. Compact binaries and standalone prediction bundles reproduce their saved text without language resources.

Calibration uses 312 restart searches / 3.12 million proposals; main test 240 / 2.4 million; early audit 480 / 264,000. These are distinct stages; replay repeats verification work. No new packages/models/downloads were required.

[Main report](../experiments/results/latin-compact-cipher/report.json), [selection](../experiments/results/latin-compact-cipher/selection.json), [early budgets](../experiments/results/latin-compact-cipher/budget-report.json), [audit](../experiments/results/latin-compact-cipher/audit.json), [manifest](../experiments/results/latin-compact-cipher/manifest.json), [main replay](../experiments/results/latin-compact-cipher/validation.json), [budget replay](../experiments/results/latin-compact-cipher/budget-validation.json).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher build
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher train
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher calibrate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher test
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher_budget
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher_audit
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_compact_cipher_signals
```

`build` refuses an existing fixture file. Final test/replay verifies frozen source/resource/selection hashes. Training/model-selection replay is not claimed. Data derives from locally pinned UD Latin Perseus r2.17 (CC BY-NC-SA 2.5), PROIEL r2.17 (CC BY-NC-SA 3.0), and the existing Whitaker-derived inventory; licenses/attribution are retained beside these artifacts. Development fixtures used for early code checks are outside the active manifest and final evaluation.
