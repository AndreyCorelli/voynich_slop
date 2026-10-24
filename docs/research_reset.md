# Research reset: prioritize informative tests

For the current cross-dimensional inventory and branch decisions, use the
[structural coverage map](approach_coverage.md). This earlier reset predates the
subsequent contraction and context-ranking calibrations; its proposed priorities
are retained as historical rationale.

This review returns to the question in [TODO.md](../TODO.md): what is the simplest bounded reversible encoding that explains plausible plaintext, and does its inferred machinery generalize? It starts no new experiment. Prior artifacts and frozen models remain intact.

## What the accumulated work supports

| Area | Established within tested scope | Still unresolved |
|---|---|---|
| Dictionary cipher fits | Verified short Latin and corrected German SAT explanations exist under specified models. Changing choice policy can change UNSAT to SAT. | Grammatical plaintext, a reliable whole-manuscript explanation, or language identification. |
| Particular fitted keys | The saved Latin/Swabian/Alsatian keys fail complete next-block coverage without repairs. | Whether another key in those families generalizes. |
| Length and repetition restrictions | Specific widths, corpus passages and boundary conventions can be excluded by exact necessary conditions. | An exclusion of a language or all cipher families. |
| Synthetic cipher recovery | Some natural Latin H2 cases recover well with public fixed-two code boundaries; dictionary gaps, unseen codes and alternative keys are explicitly recorded. | Reliable recovery/prediction with manuscript-compatible widths and hidden boundaries. |
| Local statistics | Manuscript suffix dependence replicates; deliberate ordering can reproduce suffix gains and repeat suppression together. | Which historical mechanism created the signal. |
| Longer-range statistics | Frozen predictors detect planted effects; persistent states and templates also produce gains, and the cross-family specificity criterion fails. | Attribution to direct copying, encryption, a language or any historical process. |

Evidence: [Latin mixed comparison](latin_mixed_comparison.md), [corrected German fits](german_regional_audit.md), [frozen-key extension](frozen_key_holdout.md), [natural H2 context](latin_h2_random_context_loop.md), [full width audit](manuscript_width_audit.md), [joint predictor calibration](joint_predictor_calibration.md), and [cross-family specificity failure](long_range_families.md).

None of these experiments supplies comparable likelihoods or priors for broad historical hypotheses. The priorities below rank expected information and tractability, **not the probability that a hypothesis is true**.

## Priorities

### 1. Close the missing cipher-recovery gate

Test a common prefix-free codebook with H<=2, output widths 1–2, preserved word boundaries, no nulls, and hidden internal code boundaries. Use free homophone selection initially. Keep the language inventory fixed, use existing cached natural-source controls, and report missing vocabulary before solving. Widths 1–2 pass manuscript word-length arithmetic, unlike the fixed-two convention used in the successful recent natural H2 controls; arithmetic compatibility alone does not establish feasibility.

Compare a genuinely hidden-boundary arm with a separately labeled oracle-boundary diagnostic on the same synthetic fixtures. The primary arm must receive no plaintext, code offsets, plaintext lengths or generating key. Freeze independent evaluation text; score the first returned key without rescue. Report complete decoding, exact plaintext prediction, novel types, unseen codes, alternative valid explanations, solver time and construction time. Include matched randomized controls, whose rejection is measured rather than assumed.

This is the highest-priority **method gap**, not a manuscript decipherment attempt. It asks whether our instrument can recover useful predictions under a closer code convention. The [width audit](manuscript_width_audit.md) already recommended this gate before the statistical branch began. Earlier variable-width SAT and oracle-boundary diagnostics did not establish reliable natural-text hidden recovery, so they do not close it.

Keep the first gate small: three preset positive/control pairs with bounded worker/solver budgets, plus oracle diagnostics where needed. Do not begin another vocabulary/timeout ladder. Retain coverage failures and unresolved fits rather than replace them. If recovery or unseen-word prediction is unreliable, do not interpret manuscript failure; record the limit and stop the branch. If it works, replicate on a new source before a manuscript comparison.

Natural expanding controls can still be longer than Voynich, and preserved spaces remain an assumption. Report their length distributions explicitly. Successful recovery at mixed widths would calibrate a component, not validate plaintext length, spacing or language assumptions for the manuscript.

### 2. Revisit a single structural assumption, if the gate exposes a need

The meaningful alternatives are bounded changes to word boundaries, reversible plaintext units/contractions, or a small explicitly modeled state. Each must have its own known-positive calibration and a capacity cost. Relax only one assumption per matched comparison.

Spacing has already received a two-edit passage screen; simply increasing that edit budget would repeat a narrow exact-passage search. The bounded contraction pilot already showed contractions were unnecessary for one short free-selection dictionary fit. Expanding the inventory to obtain another SAT result would not resolve that fit's predictive weakness. More flexible contractions or state are therefore alternatives to specify and calibrate, not immediate sweeps.

Evidence: [boundary edits](word_boundary_edits.md), [contraction length screen](latin_contractions.md), and [mixed dictionary comparison](latin_mixed_comparison.md). These are restricted results; they do not close all boundary or contraction mechanisms.

### 3. Compare languages only after holding the mechanism and coverage protocol fixed

Latin versus German is currently confounded by vocabulary size, short entries, normalization, source selection, and model assumptions. Historical length compatibility is useful for screening but is not a language probability. Neither changing dictionaries nor choosing a corpus because its fit is SAT creates a meaningful language comparison.

A later comparison needs one calibrated cipher family, equal selection rules and budgets, explicit OOV/short-form policies, and the same prediction score. Existing source coverage gaps and normalization caveats must stay visible. No new corpus download is necessary for the immediate gate.

### 4. Park generic feature tuning and longer timeouts

Keep the statistical measurements as descriptive tools and controls. Do not launch further suffix, adjacency or distant-lag variants to identify the mechanism: both direct and latent/template causes reproduce them. Longer timeouts cannot resolve multiple already verified explanations or repair missing language coverage. UNKNOWN remains unresolved, not evidence against a model.

## What not to repeat

- The completed longer-range smoothing and family-specificity loops.
- Fixed-two natural controls as though they establish manuscript compatibility.
- Extensions or repairs of the three particular keys already tested on their next blocks.
- Another arbitrary dictionary SAT fit interpreted as readable plaintext.
- Broader inventories, extra languages or longer budgets without a newly specified comparison.

## Proposed next decision

Proceed with the bounded hidden-boundary mixed-width **synthetic prediction gate**, with a protocol written before scoring. No manuscript classification should be attempted during that gate. Its first outcome determines whether to use the calibrated model or leave cipher recovery paused.

This is a return to the original reversible-model question. The statistical detour was useful calibration, but its mechanism-ranking interpretation is now closed; no historical hypothesis has been shown likely merely because it can reproduce the tested summary features.
