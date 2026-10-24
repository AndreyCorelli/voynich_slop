# Three-step exact-pattern calibration loop

This sequence follows the request to implement one optimization, analyze its
result, choose and run the next step, then repeat that decision once more.
All older inputs and results remain unchanged. The underlying model is public
fixed-two-glyph code boundaries and known word lengths, with one injective
substitution per letter (H1). These exact-pattern optimizations do not apply
unchanged to multiple homophones or hidden segmentation.

## Step 1: exact within-word equality filtering

For each ciphertext word, number distinct codes by first appearance. A plaintext
candidate must have the identical first-occurrence equality signature: repeated
codes imply repeated letters, and distinct codes imply distinct letters under
injectivity. Scan the complete frozen inventory for these signatures and build
smaller exact automata. This uses no true plaintext, generating key or holdout.
Missing signatures give an empty membership relation. Source hashes are checked;
validation independently reconstructs candidate counts and SAT explanations.

Run: `.venv/bin/python -m benchmarks.latin_pattern_filter --run`
Validate: `.venv/bin/python -m benchmarks.latin_pattern_filter --validate`
Artifacts: `experiments/results/latin-pattern-filter`.

The same positive previously returned UNKNOWN after 30 seconds. With exact
pattern subsets it returns **verified SAT**, **12/12 exact training words** and
**3/3 exact held-out words**. Filtering takes 0.281 seconds, construction 2.621
seconds, solving 3.758 seconds; total worker 6.670 seconds. Per-word candidate
counts range from 408 to 7,981; no source words were added or rescued.

The original global shuffle returns UNSAT in 0.00010 seconds after 1.761 seconds
construction. One of its word patterns has zero inventory candidates. This
makes that particular shuffled control easy; it cannot establish that the
method distinguishes the positive from harder random controls.

Decision: first test whether another observed-code key explains the same positive,
then replace the easy shuffle with a pattern-preserving random control.

## Step 2: exclude the first observed-code key

Use the unchanged positive, inventory, pattern subsets and budgets, adding a
single disjunction requiring at least one observed-code mapping to differ from
the first recovered key. This exclusion references the fitted key, not truth.
There is one existence query, with no alternative-key scoring or key selection.

Run: `.venv/bin/python -m benchmarks.latin_pattern_ambiguity --run`
Validate: `.venv/bin/python -m benchmarks.latin_pattern_ambiguity --validate`
Artifacts: `experiments/results/latin-pattern-ambiguity`.

Result: **UNSAT**, solver 3.179 seconds, construction 2.705 seconds, filtering
0.273 seconds, total worker 6.167 seconds. Within this finite model, there is no
second assignment to the **21 observed-code mappings**. The unobserved alphabet
mappings are not constrained by this uniqueness claim. UNSAT is a solver result
without an independently checked proof certificate. Successful recovery and
uniqueness in one engineered control do not establish general key recovery.

Decision: preserve the positive result, and spend the third step on the missing
harder random control rather than additional positive fitting.

## Step 3: harder pattern-preserving shuffle

Use seed 5004 to rename codes within each training word. Permutations operate
only among codes with equal within-word occurrence counts. This preserves exact
word lengths, within-word equality signatures, per-word code counts, global code
counts and the observed alphabet. Singleton frequency classes cannot change;
no retries follow the random result. It breaks shared letter consistency across
words without forcing a known-negative label. Training input has twelve distinct
words; the transform does not promise to preserve distinct word types or
cross-word equality partitions in general.

The control uses the same inventory, exact-pattern solver, 30-second solver
budget and 60-second external limit. The positive is referenced, not refitted.
No held-out accuracy is defined for a shuffle, and its SAT/UNSAT/UNKNOWN status
alone cannot identify manuscript language.

Run: `.venv/bin/python -m benchmarks.latin_pattern_shuffle --run`
Validate: `.venv/bin/python -m benchmarks.latin_pattern_shuffle --validate`
Artifacts: `experiments/results/latin-pattern-shuffle`.

Tests cover injective pattern invariance and exact subset lookup, unique versus
alternative observed-key exclusions, and deterministic preservation of each
word's equality pattern and code-count multiset. Existing layered-equivalence
and worker tests continue to cover the underlying encoding.

Result: **UNSAT**, solver 1.817 seconds, filtering 0.274 seconds, construction
2.724 seconds, total worker 4.825 seconds. Every word has the same nonempty
pattern-candidate count as its positive counterpart. Rejection therefore cannot
be attributed to the prior empty-pattern shortcut. This remains a bounded
solver result without an independently checked proof certificate.

## Analysis and next priority

All three authorized steps are complete. The exact-pattern optimization converts
a timed-out known positive into correct predictive recovery, and the second-key
query finds the observed key unique. A more carefully matched randomized control
is rejected while preserving local equality signatures and frequency counts.
The three new artifact validations pass.

These results establish feasibility and separation for this one engineered
fixture, not an estimated accuracy or accidental-fit rate. The generated forms
are not natural attested prose. Twenty-one-letter coverage and short public
lengths provide strong training evidence; known boundaries and injectivity are
substantial assumptions. No Voynich text was fitted.

The next priority is **independent fixture replication**: freeze a small set of
new inventory reservoirs/training selections with novel covered holdouts and
matched pattern-preserving shuffles before any fits, retain the same budgets and
first-key scoring, and report every case including UNKNOWN. This tests whether
the success depends on one unusually constraining training set. Replication is a
recommendation here; it was not added beyond the three requested steps. Natural
prose and hidden-boundary/homophone extensions should follow successful control
calibration rather than using these results as manuscript evidence.
