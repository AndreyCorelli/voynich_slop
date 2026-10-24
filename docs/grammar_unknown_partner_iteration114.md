# Iteration 114: independent unknown-partner alternative

**Reject this addition.** Comparing a proposed swap against the strongest independently scored singleton does not remove the literal-absence mistake, and it sacrifices correct repairs.

The previous within-pair reciprocal check reduced to requiring two positive endpoint margins. This experiment instead masks each candidate type alone, using the frozen iteration93 classifier, and computes its class-flip score from mean occurrence probabilities. Supported singletons compete globally, including candidates outside the proposed pair. The alternative score is the maximum singleton flip score or zero (no error); the contrast is the jointly masked pair gain minus this alternative. Because masks differ, this is a heuristic score contrast, not a calibrated likelihood ratio or Bayes factor.

The base111 gain/gap/stability rule remains frozen. Calibration uses only the previous110 complete67 cases and1072 catalogue omissions, with no author evaluation. Visible singleton evidence remains available even if that type is excluded from the repair catalogue. Before evaluation, the design requires at least90% call precision separately in complete/omission conditions, zero unsupported/clean wrong calls, at least39 complete and540 omission correct repairs (80% of base coverage), and20 distinct omission successes. The cutoff grid includes all attainable source contrasts, zero, and no extra restriction. Selection maximizes retained correct repairs, then takes the highest tied cutoff. All113 literal-loss cases are evaluated afterward, without changing the selected cutoff. The challenge was already inspected in113 and is not independent confirmation.

The selected cutoff is **−0.3011125916**. It retains every earlier source calibration repair:48/0 complete and674/0 catalogue omissions. A negative cutoff allows some pairs to score below the singleton alternative; it is a source-selected tolerance, not evidence that the pair always wins that comparison.

| Literal-loss errors,1024 cases | Correct | Wrong | Abstain |
|---|---:|---:|---:|
| Frozen111 baseline |667|1|356|
| Added calibrated contrast |664|1|359|
| Pair must beat singleton, cutoff0 (diagnostic) |442|1|581|

All three methods abstain on the48 controls. The calibrated addition rejects three correct repairs and no wrong repairs. The zero-cutoff diagnostic rejects225 correct repairs and no wrong repairs; it also fails the predeclared source coverage guards (31 complete and435 omission correct repairs).

The wrong call remains `sine/sed` → `ac/sed` when `sine` has disappeared. The pair score is.83902454; the strongest supported singleton score is.42420051; their contrast.41482403 passes both cutoffs. Joint and singleton endpoint evidence agree here: `ac` contributes.42420051 and `sed` contributes.41482403. Thus independent masking does not expose an interaction that explains away this pair.

A post-hoc matched-clean diagnostic identifies the underlying local problem: **`ac` has the same positive flip score.42420051 before and after the corruption.** The model already favors flipping this correctly mapped type in that context. `sed` flips from−.41482403 to+.41482403. The pair score combines one corruption-induced signal with one pre-existing false signal. This is a diagnostic with a known clean counterpart, not an available target-time oracle or a word-specific correction rule.

The Caesar/Jerome grammatical restoration findings remain preserved. This experiment adds no grammatical restoration or lexical nuclei, changes no default policy, consumes no new grammatical annotations, and leaves reserved/sealed data untouched.

Verification:23 focused tests pass. The audit verifies17 frozen input hashes, replays all193 source cutoff settings (143 qualify), independently verifies1340 singleton scores and2144 challenge actions, and samples inference in all16 deletion views. Artifacts and the matched-clean diagnostic are in `experiments/results/grammar-restoration/iteration114/`.

Next diagnostic: quantify how often clean-context false flip evidence supplies the second endpoint of a proposed swap, using source-only matched clean/corrupt contexts. Determine whether this is systematic contextual class bias before designing another abstention rule; do not use clean counterparts as deployment inputs or add an `ac` exception.
