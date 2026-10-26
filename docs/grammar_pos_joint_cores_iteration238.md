# Iteration238: a small stable grammatical core survives, with severe coverage limits

**Preserve the Jerome finding:** one six-word anonymous core survives the strict initialization/deletion intersection, and all six words have100% VERB profiles in the cached reference. It covers337/30000 admitted tokens(1.12%). The algorithm inferred grouping, not the verb name or word identities. This is a potential small grammatical input, not exact nuclei, reliable whole-text POS, or a four-text demonstration.

Aquinas retains five cores with79.31% core-average compatibility, but one retained pair is PRON versus NOUN. Stability therefore still cannot serve as a correctness guarantee. Caesar/Cicero each retain one weak pair, and Dante retains no non-singleton core; no criterion is relaxed to manufacture output.

## Frozen joint-stability rule

Start with236's cores, unanimous across31 initializations of the full admitted graph. Require each word to appear in every one of237's31 sentence-deletion graphs; then split original cores by their complete31 deletion-cluster signatures. Freeze memberships/exclusion reasons before reference evaluation. This intersects31 initialization runs and31 deletion runs, **not** all961 combinations of deletion and initialization. Every deletion used fixed seed23500.

Retain all singletons, missing-word reasons, empty outputs and authors. No POS/Case enters construction or selection. Evaluate the same core-macro/pair-weighted global POS compatibility and oracle purity against199 frequency×Case-profile shuffles. No new raw text, annotations, other reserves, naming model or target-guided threshold/core selection. Dante remains previously consumed development.

## What remains

| Author | Nodes surviving every deletion | Non-singleton cores | Core sizes | Covered nodes | Pair constraints | Admitted token coverage |
|---|---:|---:|---|---:|---:|---:|
| Aquinas |92/202|5|3,2,2,2,2|11|7|985/30000(3.28%)|
| Caesar |11/60|1|2|2|1|114/27386(.42%)|
| Cicero |26/75|1|2|2|1|137/30000(.46%)|
| Jerome |49/209|1|6|6|15|337/30000(1.12%)|
| Dante |16/76|0|none|0|0|0/26083|

Surviving singleton counts81/9/24/43/16 make the coverage cost explicit. The core intersection reduces1138 original within-core pairs to24; most initialization-stable relationships do not meet the strict whole-pipeline robustness requirement.

## Grammatical quality

| Author | Core-macro compatibility | Pair-weighted compatibility | Core-macro oracle purity | Compatibility upper tail |
|---|---:|---:|---:|---:|
| Aquinas |79.31%|84.40%|89.66%|.005|
| Caesar |52.75%|52.75%|69.19%|.295|
| Cicero |42.82%|42.82%|56.35%|.320|
| Jerome |100%|100%|100%|.010|
| Dante |undefined|undefined|undefined|undefined|

Nulls preserve word-frequency bin and global Case-bearing status; tails are reused-development, correlated diagnostics without multiplicity-adjusted confirmation or per-core confidence. Oracle purity is not inferred named-POS accuracy. Caesar/Cicero do not separate from the control, despite strict stability. Dante's missing result remains missing.

Reference inspection describes all retained Aquinas cores: one three-word ADV-dominant core(two pure ADV, one95.7% ADV/4.3% CCONJ), two pure VERB pairs, one ADP-dominant pair(one pure ADP, one99.5% ADP), and one incompatible PRON/NOUN pair. These descriptions were read after selection and are not naming predictions or a basis for dropping the bad core. Jerome's six members are all pure VERB in the reference; no spelling/lexical identity was used or recovered.

## Implication and audit

This is a materially smaller, more stable anonymous grouping than the earlier whole partitions, with one clean reference-verifiable class in Jerome and useful but imperfect Aquinas groups. It could seed a decoder that consumes soft class co-membership, while the false Aquinas pair rules out treating stability as a hard grammar oracle. Cross-text exact-word intersections and Voynich decipherment remain unachieved.

Independent survival/signature equivalence checks49432 word pairs, all995 profile-null groups, exclusions, empty handling, coverage and25 hashes; all pass. Artifacts: `experiments/results/grammar-restoration/iteration238/`.

Next validate **all** selected joint cores on previously unused perturbation seeds23900–23930, without updating memberships: primary10% sentence deletion, secondary20% stress, same graph/clustering rules/fixed23500 initialization. Report conditional/unconditional retention and intact-core survival, including every weak core and Dante's empty output. These are new perturbations of the same development text, not new authors or fresh grammatical labels. This tests whether the selected Jerome/Aquinas relationships generalize beyond the deletion seeds used to define them before considering a downstream decoder experiment.
