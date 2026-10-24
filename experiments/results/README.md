# Experiment results

Store generated JSON results here: assumptions, source/sample identity, seed,
solver status and reason for UNKNOWN, runtime, statistics, capacity measurements,
recovered explanation, and independent verification outcome.

`guided-extension.json` records full-prefix trials with an exact suffix key,
rotatable observed mappings and progressive releases. Conditional UNSAT rows
retain their exact pin assumptions and cores. The zero-pin outcome is reported
separately from those exclusions. Historical release schedules and the standalone
one-pin proof have their own reports and preserve their original wrapped inputs.

`learned-search.json` records suffix candidates, whole-prefix conditional extension
checks and independently checked analytic/core exclusions. Its outcome scope is
explicit: rejected mappings and UNKNOWN do not establish full-model UNSAT.

`learned-prefix.json` records the unrestricted full-prefix solve with proved
exclusions, including proof/input provenance, solver and total wall time.

`cycle-performance.json` records paired cycle formula timings, independently
verified synthetic witnesses and a full-prefix retry with no mapping restrictions.
`cycle-history-probe.json` and `cycle-state-probe.json` preserve the matched initial
full-vocabulary seed-7 probes imported by exact normalized request hash.

`dictionary-selection.json` records entry/trie control comparisons and provenance
for the user's 30-minute seed-7 trie timeout. UNKNOWN on these known positives
is a solver diagnostic, not a cipher rejection.

`synthetic-prefix.json` records independent full-vocabulary positive-control
prefix solves. The first sampled UNKNOWN is a solver-budget boundary, not UNSAT.

`synthetic-prefix-gap.json` preserves the three-word follow-up: verified SAT.
Together the two prefix reports show verified fits at 1/2/3 words and UNKNOWN
at 4/6/8/11 under the recorded 30-second budget, with known witnesses throughout.

`segmentation-diagnostic.json` compares oracle-boundary SAT with a fresh hidden
UNKNOWN on the same four-word positive control. Boundaries also reveal word lengths;
this is an oracle diagnostic, not hidden recovery or manuscript evidence.

`word-length-diagnostic.json` records verified SAT with lengths alone and exact
boundaries, alongside a fresh fully hidden timeout. Oracle success is separate
from full hidden calibration.

`length-search.json` records public length branching. SAT is a verified full-instance
fit. A branch UNSAT excludes only its vector; UNKNOWN remains unresolved. Global
UNSAT requires exhaustive proved rejection, not exhaustion of a time/branch budget.

`length-search-intermediate.json` preserves the separate six/eight-word calibration.
Its bounded length search must not be interpreted as a full-model UNSAT proof.

`solver-engines.json` records fresh equivalent-formula engine comparisons on a
conditional public length branch. Scope is the branch, not the whole hidden model.

`solver-engines-initial.json` preserves the initial probe with post-check constraint
counts. The main engine report instead validates identical pre-check formula hashes.

`length-search-diverse.json` records strategy identities and public candidate counts
as well as branch outcomes. Optional ordering changes do not remove allowed vectors
or convert timeouts into exclusions.

`observed-codes.json` compares explicit public substring domains with the matched
historical hidden-control baselines. Only used codes are domain-restricted;
unused pinned mappings and key completion remain outside this restriction.

`observed-codes-11-30min.json` is the user-run verified full-vocabulary seed-7 SAT
witness. `observed-codes-validation.json` records independent witness validation
and preparation/provenance of the unstarted 23-word Voynich long-run request.
