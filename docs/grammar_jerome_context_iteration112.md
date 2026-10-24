# Iteration 112: frozen long-context repair on Jerome

**Preserve this finding:** the omission-aware policy from iteration111 transfers to a second cached author: **25 correct repairs, zero wrong repairs**, across all64 synthetic cross-class swaps. Every successful repair changes the scored sample and restores its complete clean PP probability vector. This extends the Caesar result; it does not establish fresh-data reliability or lexical nucleus recovery.

The original100 Jerome sentences (913 tokens, existing iteration40 annotations) are the only scored positions. Exactly729 additional sentences supply FORM-only context, giving829 sentences/7713 tokens. Before projecting forms, the streaming reader excludes all200 reserved sentence IDs and all4070 source-partition IDs; it filters author by source metadata. It reads integer token IDs and FORM, drops punctuation-only forms using letters, and normalizes case/u-v/i-j without using POS or dependency columns. The same projection exactly reproduces all100 original word sequences. Additional sentences exclude original IDs and duplicate normalized sequences; selection uses SHA256(`jerome112|sent_id`), independent of scores. Treebank sentence/token segmentation remains a privilege.

Both source policies, models, supplied195 anchor mappings, candidate catalogue, count gates, volume routing, and PP thresholds remain frozen. There are64 errors plus three clean/same-class controls per input view. The policies deliberately abstain at100 sentences and activate the long-context branch at829; consequently the base-versus-expanded comparison is a comparison of the complete conditional procedure, not an isolated causal estimate of additional context. No target tuning, new annotations, reserved features, or sealed lexical evaluation occurred.

| Frozen policy, expanded829 | Correct | Wrong | Abstain | Correct / calls |
|---|---:|---:|---:|---:|
| 109, higher coverage |31|4|29|88.57%|
| 111, omission-aware |25|0|39|100% observed|

All64 errors affect the scored sample. Forty have a count-supported true repair pair: policy109 repairs31, policy111 repairs25, with no wrong actions in that stratum. The remaining24 unsupported errors produce all four109 mistakes;111 abstains on all24. Both policies abstain on all three controls. These are correlated synthetic probes, not64 independent texts.

The wrong109 actions are retained in the evaluation: `a/ac` and `a/atque` are incorrectly repaired with `a/ex`; `ad/ac` and `ad/atque` with `ad/ex`. Thus the source omission diagnostic predicts a real transfer failure mode of the higher-coverage branch. The stricter branch avoids these four mistakes while giving up six correct repairs.

Across all64 corruptions, the original PP model at its fixed.80 threshold yields:

| State | True positives | False positives |
|---|---:|---:|
| Corrupted, unrepaired |2232|599|
| Repaired with109 |2395|308|
| Repaired with111 |2374|382|
| Clean reference, repeated across64 cases |2560|64|

For111, the gross changes are147 newly correct PP selections, five lost correct selections, two new false positives, and219 removed false positives. Even exact restoration can lose selections that were accidentally correct under corruption; these losses remain counted. Every one of the25 successful repairs reproduces the full clean probability vector under both original and augmented PP models. The clean sample itself still has only40 correct/one wrong selected PP nodes under original.80: these results restore damaged grammatical predictions, not broaden clean grammatical coverage or recover content words.

Verification:20 focused tests pass, including grammatical-column poison and pre-projection exclusion tests. The review replays134 pair rankings and268 blind actions, independently checks PP confusion counts, reconstructs FORM selection/public inputs, and recomputes stored bootstrap columns and new inference payloads. Frozen inputs, predictions, detailed wrong actions, gross changes, and audits are stored in `experiments/results/grammar-restoration/iteration112/`.

Next: challenge literal absence/context loss rather than candidate-catalogue omission alone. Freeze a source-only ablation that removes endpoint occurrences from context while preserving the scored prefix, with availability strata and both policies unchanged; first check feasibility without touching the reserve. Fresh confirmation remains necessary before adoption.
