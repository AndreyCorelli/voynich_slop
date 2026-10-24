# Natural Latin control with independent morphology membership

This experiment reuses the previously frozen contiguous Caesar passage from the
morphology coverage audit: 24 training words followed by six held-out words.
It does not select a new passage by solver outcome. Normalization remains the
resource's canonical i/u (j→i, v→u), and the existing source record provenance
is retained. No words are inserted, deleted or projected out.

The entire default and broader generated morphology inventories are audited
before fitting. The predeclared strict admission rule is zero missing training
words. Missing holdout forms are reported but do not gate fitting. Both policies
were already frozen before this experiment; the broader policy is a sensitivity
arm, not new target-specific vocabulary or morphology changes.

| Existing inventory | Missing training forms | Missing held-out forms | Fit admission |
| --- | --- | --- | --- |
| Default, 2.55 million forms | introrsus, hostes | None | NOT_ADMITTED |
| Broader, 6.33 million forms | None | None | Admitted |

Only the admitted broader inventory is fitted, with its full 24-letter alphabet,
not a truth-derived restricted alphabet. The natural passage observes 18 letters.
Seed 5401 generates an injective two-glyph substitution key. Code boundaries and
plaintext word lengths are public. Exact equality-pattern filtering scans the
complete inventory using ciphertext patterns only. True words, generating key
and holdout are excluded from solver constraints. The first SAT key is frozen
before training/held-out scoring. All six holdout words are novel and their
codes occur in training.

Seed 5402 constructs a matched shuffle preserving each training word's exact
equality pattern, length and code-count multiset. Consequently global code
counts, observed alphabet and per-word candidate counts also match. The shuffled
text is a randomized control, not a stipulated negative. It is not scored
against the original plaintext. One fit per arm; no retries or alternate-key
rescue.

## Results

| Arm | Status | Filtering | Construction | Solver | Whole worker |
| --- | --- | --- | --- | --- | --- |
| Natural passage encrypted | SAT, verified | 1.593 s | 3.491 s | 1.409 s | About 6.52 s |
| Pattern-preserving shuffle | UNSAT | 1.581 s | 3.440 s | 1.332 s | About 6.38 s |

The first key recovers **24/24 training words** and **6/6 novel held-out words**:
`uidebantur fluminis erat altitudo pedum circiter`.

Each word has a nonempty candidate subset, ranging from 29 to 13,229 forms.
Shuffle counts match the positive word by word, so rejection cannot use an
empty-pattern shortcut. The 30-second solver budget and 60-second worker limit
are unchanged. Neither fit times out. Durable phase records distinguish loading,
filtering, construction, solving and verification.

SAT verification reconstructs consistent repeated-code mapping, injectivity,
full-inventory training membership and frozen held-out scores. UNSAT is a solver
result without an independently checked proof certificate. A dedicated worker
test checks selected-inventory filtering and held-out scoring. Artifact
validation regenerates the passage audit and inputs, checks source/code identities
and shuffle invariants, rebuilds candidate counts and verifies scores.

```sh
.venv/bin/python -m benchmarks.latin_pattern_natural --run
.venv/bin/python -m benchmarks.latin_pattern_natural --validate
```

Artifacts: `experiments/results/latin-pattern-natural`.

## Interpretation and next priority

The exact-pattern method now recovers a natural, independently sourced Latin
passage, not merely forms sampled from its own inventory. This strengthens the
calibration evidence for computational feasibility and prediction under the
current model. It does not remove the coverage limitation: default strict
morphology cannot represent the true training passage. Broader coverage was
reported explicitly rather than treating a default-inventory contradiction as
an encryption failure.

This is still one short Caesar passage, with public fixed code boundaries and
word lengths, one code per letter, no nulls and an injective key. It does not test
hidden segmentation, verbose mixed-length homophones or Voynich plaintext.
Canonicalization and the generated inventory's permissiveness remain material
assumptions. The first key's exactness does not establish observed-key uniqueness
for this passage; no second-key query was run.

The next useful check is to freeze additional nonoverlapping natural passage
controls and report admission/coverage before fits. Keep the same inventory
policies and no silent OOV rescue or passage reselection. Replication across
natural passages would test whether this result depends on one particularly
constraining block before relaxing public boundary/length assumptions.
