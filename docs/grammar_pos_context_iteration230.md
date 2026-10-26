# Iteration230: local POS agreement is useful in places, not a universal recovery result

On frozen rich endpoint-disjoint10 lists, actual shared-context POS agreement is80% Aquinas,65% Caesar,87% Cicero,90% Jerome and60% Dante. But only Cicero's rich list separates at fixed.05 from its within-word POS-profile shuffle control. Most selected-pair agreement reflects global word-class affinity rather than newly detected context-specific alignment. Preserve the relational input without upgrading it to robust named-POS restoration.

## Frozen diagnostic

All five admitted graphs and every previous selection remain fixed:225 learned tied lists,226 learned disjoint lists,227 untrained tied/disjoint lists,229 Dante lists and each whole graph. Freeze all125 list groups before cached POS projection. No new features, model, ranking, cutoff, raw annotation or reserve.

Per edge, average Cartesian POS equality within each shared lexical-neighbor frame, then average frames equally. The analytic expectation under within-word POS shuffling is the global word-profile dot product measured earlier. Shuffle POS across all lexical occurrences within each opaque word, preserving complete word-POS profiles,199 seeds23000–23198; share each author's assignment across its fixed lists. Report observed agreement, expectation, surplus, null range and upper-tail `(1+exceedances)/200`. These are unadjusted descriptive family tests on reused authors, not per-pair confidence or independent confirmations.

## Whole-graph context-specific agreement

| Author | Observed shared-context agreement | Global-profile expectation | Surplus | Upper tail |
|---|---:|---:|---:|---:|
| Aquinas |21.59%|21.13%|+0.46pp|.090|
| Caesar |49.35%|44.24%|+5.10pp|.020|
| Cicero |40.00%|36.91%|+3.09pp|.005|
| Jerome |58.01%|55.37%|+2.64pp|.005|
| Dante |38.16%|34.73%|+3.43pp|.005|

Aggregate local POS structure survives global-profile preservation in four authors at the fixed descriptive threshold, but not Aquinas. This is distinct from224's test of which POS profiles are linked: that permuted profiles among words, whereas this test preserves each word's profile and varies which occurrence receives which tag.

## Frozen rich disjoint10

| Author | Observed agreement | Expectation | Surplus | Upper tail |
|---|---:|---:|---:|---:|
| Aquinas |80.00%|79.18%|+0.82pp|.160|
| Caesar |65.00%|67.97%|−2.97pp|.760|
| Cicero |87.00%|78.91%|+8.09pp|.010|
| Jerome |90.00%|88.67%|+1.33pp|.385|
| Dante |60.00%|55.48%|+4.52pp|.195|

The rich tied10 lists instead yield70%,75%,87%,90%,60%, with tails.250,.255,.010,.385,.655. Endpoint separation changes which relations are selected; the stronger disjoint Aquinas result does not indicate a new calibrated threshold or context-specific excess. Caesar disjoint selection actually falls below its profile expectation. The changed evaluation therefore does not rescue a consistent four-text grammatical restoration claim or Dante's moderate performance.

## Fixed untrained support disjoint10

Observed agreement60%,66.67%,97%,70%,60%; respective profile expectations59.14%,54.56%,88.10%,66.94%,59.20%. Surplus tails.160,.005,.005,.080,.645. Caesar and Cicero show useful conditional local structure under this particular fixed list, but Caesar's preceding tie-order/global-profile tests remain weak. Do not select this list after seeing gold or discard the other untrained/control results; all are preserved in the125-group artifact.

Named POS values enter evaluation only, not the original pair selection. Agreement between two opaque contexts does not identify which POS either occurrence has. Distinct endpoints may still share context observations, and words with invariant POS profiles contribute agreement that every shuffle preserves. No exact Latin nuclei, named token-POS predictions or Voynich plaintext is restored.

## Audit and next experiment

Independent rational global-profile expectation, outer-product Cartesian scoring, within-word permutation replay and fixed selection reconstruction verify217000 observed/null edge scores,125 groups and30 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration230/`.

Next test a concrete downstream use rather than another compatibility metric: predict named POS profiles from source-trained anonymous node features, then average predictions only over the fixed selected disjoint pairs. Use the existing12 node features, source-author-balanced multioutput ridge.1, the fixed17-UPOS inventory, clip negative predictions to zero and normalize; compare source-prior and node-only baselines. Pair refinement is exactly half self/half partner for support-selected and rich-selected disjoint10, with all other nodes unchanged. Freeze all target outputs before evaluation on four development folds plus additional Dante; report graph-node coverage, expected top1 accuracy against global POS profiles and per-author gains/losses. Target labels must enter neither baseline nor pair selection. This tests whether the inferred relations actually improve a grammatical prediction task, without claiming whole-text coverage or named POS success in advance.
