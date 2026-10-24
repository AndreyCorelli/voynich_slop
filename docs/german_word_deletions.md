# Interior-word deletions in the German free-selection conflict

The joint-deletion test completed **UNSAT in 44.60 seconds**. Removing both
`daiin` and `ychtaiin` leaves an **inclusion-minimal 19-word conflict**:
every single-word deletion from this set has an independently verified SAT
witness. By free-selection feasibility monotonicity, every proper subset is
therefore SAT. Minimum cardinality among all possible conflicting subsets
has not been established.

The [joint replay](../experiments/results/german-word-deletions-joint-30min.json)
and [validation](../experiments/results/german-word-deletions-joint-validation.json)
record the effective request, fixed settings, original positions, result and
all 19 independently checked deletion certificates. The UNSAT result remains
solver-reported, without an independently checked proof certificate.

The completed user-run scan has no unresolved single deletions. Nineteen
deletions give independently verified SAT. Two deletions remain UNSAT:
removing `daiin` at block position 13 (62.67 seconds) or `ychtaiin` at block
position 26 (51.34 seconds). Thus there are two separately certified-by-solver
20-word conflicting sets. Their combined deletion subsequently returned
UNSAT, establishing the smaller conflict above.

The [validation](../experiments/results/german-word-deletions-validation.json)
checks every request, same-model settings and all SAT witnesses. UNSAT proof
certificates have not been independently checked.

## Completed minimality check

Removing both positions 13 and 26 leaves 19 words. Its public request is
`data/generated/german-word-deletions/joint-delete-13-26.json`; preparation
and original positions are recorded in
[the joint preparation report](../experiments/results/german-word-deletions-joint-preparation.json).

Every single deletion from this proposed 19-word set is independently
verified SAT by restricting the corresponding existing SAT witness. These
19 certificates are saved in
[german-joint-deletion-minimality-certificates.json](../experiments/results/german-joint-deletion-minimality-certificates.json).
Therefore a decisive joint test settles inclusion minimality:

- Joint UNSAT: the 19-word set is inclusion-minimal UNSAT.
- Joint SAT: each of the two 20-word sets is inclusion-minimal UNSAT; they
  differ by whether `daiin` or `ychtaiin` is retained.
- Joint UNKNOWN: minimality remains unresolved.

Inclusion minimality means no word can be removed from that particular set
while retaining UNSAT; it does not prove minimum cardinality across all
possible manuscript subsets.

Run the prepared test locally:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-word-deletions/joint-delete-13-26.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-word-deletions-joint-30min.json
```

The user-run joint test above has completed; the command is retained for
reproduction.

The 25-word conflict reduces to **21 distinct words** without a new solver
run. The fixed model has free homophone selection, a global prefix-free key,
no nulls and a wordwise dictionary constraint. An identical complete ciphertext
word must decode to the same plaintext under that key; a valid encoding can
be copied to every occurrence. Therefore repeated copies impose no additional
feasibility constraints. This equivalence does not apply to text-wide cycling.

The original conflict contains `chor` at block positions 6, 16 and 27, and
`cham` at positions 9, 19 and 24. Keeping the first of each removes positions
16, 19, 24 and 27. All remaining words retain their order and boundaries;
characters within retained words are unchanged. The new base is a
noncontiguous subsequence of the manuscript block.

The report labels its status `UNSAT_BY_DUPLICATE_EQUIVALENCE`, distinguishing
the deduction from a fresh solver result. It inherits the solver-reported
25-word UNSAT; no independent UNSAT proof certificate was checked.

## Single-deletion checks

All 21 single-word deletion requests are prepared against this fixed
deduplicated base. Deleting either endpoint, block positions 5 and 29, is
already independently verified SAT by restricting the existing endpoint
witnesses to the retained subsequence. No solver run is needed for those two.

The first interior probe deleted `s` at block position 23 and returned
UNKNOWN in 30.09 seconds under a 30-second budget. The subsequent longer
scan returned SAT for this deletion in 417.57 seconds and completed all
remaining single deletions as summarized above. The 21-word set is not
inclusion-minimal because either of the two removable constraints can be
deleted individually while retaining UNSAT.

A SAT deletion shows the removed constraint is necessary for UNSAT in this
fixed 21-word base. An UNSAT deletion provides a smaller, 20-word conflicting
subsequence. Separate UNSAT deletion results must not be combined without
checking the combined deletion: individually removable words can substitute
for one another. This script scans a fixed base rather than adaptively
claiming a minimum-cardinality conflict.

The checkpoint is
[german-word-deletions.json](../experiments/results/german-word-deletions.json),
with source/code hashes, original positions, requests, result provenance and
necessary/removable/unresolved summaries. Public inputs have separate folders
per budget under `data/generated/german-word-deletions/`.

## Continue locally

```sh
.venv/bin/python -m benchmarks.german_word_deletions \
  --timeout-ms 1800000 --max-solves 19 --resume
```

The larger budget retries deletion of `s` first, then scans remaining
unresolved interior deletions. Results are saved immediately. The script
stops on UNKNOWN, without treating it as evidence of necessity or
removability. At most 19 fresh solves are requested, each with a 30-minute
budget plus formula construction. No long run was started by the assistant.

Default execution performs at most one fresh short solve. `--prepare-only`
prepares requests without solving. Resume checks code and source hashes,
exact remaining word positions, unchanged model settings and request hashes,
and independently checks every cached SAT witness. Completed decisive
results are skipped; UNKNOWN is retried only with a larger budget.

Focused tests cover duplicate equivalence on small SAT and shared-key UNSAT
cases, the rejection of cyclic selection, projection of free choices with
empty optional span metadata, the real duplicate groups and endpoint
certificates, UNKNOWN handling, larger-budget retries and tamper rejection.
