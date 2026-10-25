# Iteration 143: frozen joint model replicates on Curtius and Suetonius, fails on short Apuleius

**Preserve the replication:** the unchanged iteration-142 primary model gets **Curtius 12/15 (80%)** and **Suetonius 12/16 (75%)**, with AUC above all sixteen frequency-preserving word shuffles for each. **Apuleius fails at 6/13 (46.15%)** on its 4,015-token stream. Together with the earlier four texts, the same model reaches 71–80% binary class agreement on six of seven full texts; this is promising development evidence, not uniform reliability.

## Frozen additional-author check

Use exactly the three previously inspected Ravi–Knight development streams: Apuleius I (4,015 tokens), Curtius III (7,135), and Suetonius's Augustus (13,812). Their development metadata and earlier trigram design verify prior inspection. No remaining sealed work is opened, and normalization/tokenization are unchanged.

All iteration-142 models are frozen, with **uncalibrated joint probabilities and the fixed 0.5 boundary primary**. Matched single-feature raw controls remain fixed too; no model is chosen per author. Neither scalar calibration nor PP inference is run. Features use opaque ID equality, counts, and order only, without known mappings or supplied sentence boundaries.

The same sixteen-type function-word catalogue remains given. Every present type is evaluated, with missing types and occurrence support reported rather than filtered. All original streams and sixteen fixed global word-order permutations per author (seeds 14300–14315) are frozen before features. All predictions are frozen before references and metrics. No new annotation, training, reference correction, reserve feature, lexical restoration query, or default change occurs.

These texts were used in earlier unrelated development; this is additional-author replication for this frozen model, not an untouched-corpus confirmation. Unequal volumes and raw/treebank segmentation remain confounds.

## Primary and fixed controls

| Text | Tokens | Corrected-only raw | Role-only raw | **Frozen joint primary** | Joint AUC | Joint NLL |
|---|---:|---:|---:|---:|---:|---:|
| Apuleius | 4,015 | 6/13 | 8/13 | **6/13 (46.15%)** | 0.6500 | 0.7357 |
| Curtius | 7,135 | 9/15 | 11/15 | **12/15 (80%)** | **0.8214** | **0.5704** |
| Suetonius | 13,812 | 11/16 | 11/16 | **12/16 (75%)** | **0.7813** | **0.5824** |

The all-ADP majority baseline gets eight types correct in each work. Curtius and Suetonius improve on it and on both single-feature controls, with NLL below the balanced prior's 0.693. Apuleius loses to the majority baseline and has worse-than-balanced-prior NLL; its better role-only control is retained but not substituted as a target-picked model.

For Curtius, six of eight ADPs and six of seven CCONJs are correct. For Suetonius, seven of eight ADPs and five of eight CCONJs are correct. Thus the successful results are not majority-class guesses. Apuleius gets two of eight ADPs and four of five CCONJs correct, missing most prepositions.

## Word-order controls

| Text | Actual joint AUC | Maximum of sixteen null AUCs | Nulls at least actual |
|---|---:|---:|---:|
| Apuleius | 0.6500 | 0.9750 | 11/16 |
| **Curtius** | **0.8214** | **0.6339** | **0/16** |
| **Suetonius** | **0.7813** | **0.7500** | **0/16** |

The actual order-sensitive result replicates on Curtius and Suetonius, but is not supported against these nulls on Apuleius. These are finite correlated controls, not formal significance or cross-text reliability guarantees.

## Missing types, support, and references

Apuleius lacks `aut`, `c`, and `que`. Curtius lacks `que` and has one standalone `c`; Suetonius has twenty standalone `c` tokens and two standalone `que` tokens. The raw `c` tokens may be initials rather than the treebank conjunction component used by the source reference. No present type is silently removed or relabeled.

The pre-existing common-fourteen compatibility view gives **Apuleius 6/13**, **Curtius 11/14 (78.57%)**, and **Suetonius 10/14 (71.43%)**. The two successful works therefore remain above 70% when that earlier presence-defined comparison set is used, while reference ambiguities remain a limitation.

The occurrence-supported subsets (at least five tokens) give Apuleius 6/11, Curtius 11/12, and Suetonius 11/15. These secondary strata are reported, not adopted as a policy. Original sentence-count support is unavailable for the raw streams.

Wrong types are Apuleius `a`, `ab`, `ac`, `de`, `ex`, `sed`, `sine`; Curtius `de`, `sed`, `sine`; Suetonius `ac`, `atque`, `de`, `sed`. **`sed` remains wrong in all seven full texts**, including the original four. Preserve this systematic failure rather than adding a plaintext-specific exception.

## Meaning and next check

The highlighted iteration-142 result now has two successful frozen additional-author replications, alongside a clear failure. It remains a candidate grammatical input to another decipherment method: no known translations or sentence boundaries are needed, but function-word membership and word boundaries remain supplied. Neither exact word identities nor shared lexical nuclei are recovered.

Apuleius is substantially shorter than every successful full stream. That is a plausible explanation to test, not a demonstrated cause or a validated minimum-length rule; author/content differences could also matter. The next proposed check holds token counts constant for this **joint** model across all seven works, using fixed nested windows and the same classifier. Earlier token-budget tests used the single-overlap model and cannot establish this new model's length requirements. Keep the short-text failure and avoid choosing a favorable window or excluding an author.

## Verification

Independent review verifies twenty frozen input hashes plus the pre-existing common-set manifest, reconstructs all 51 transformations and exact counts, recomputes 748 paired features with independent implementations, replays 2,244 probabilities and 918 metric groups, and confirms model identity with iteration 142. Only previously inspected development works are opened. Eighteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration143/`.
