# Diverse shared-key synthetic calibration

The previous three-word control fit an incorrect key. This experiment freezes
12 distinct training words and three novel held-out words before fitting, using
the unchanged default 2.55-million-form inventory and the same seed-4901 key.

Selection is independent of solver outcomes. Seed 5001 selects a 512-word
reservoir uniformly without replacement from all 32,846 inventory forms of
length three through six. Greedy selection chooses the word covering the most
previously unseen letters, with lexical tie breaking, for twelve iterations.
The holdout consists of the first three remaining lexical words whose letters
are covered in training. This increases observed alphabet coverage from four
to **21 of 23** letters; no outcome-based replacement follows. These are
mechanically generated inventory forms, not attested natural prose.

Training: `abstul ciphom adfert agenti adyta arqui axem abdue abear ablega abundi abusui`.
Holdout: `accias acesce acesue`. Every held-out atomic code occurs in training.

Seed 5002 globally shuffles the atomic two-glyph training codes, then restores
the original word lengths. This preserves total code counts, observed alphabet
and per-word lengths; it does not preserve within-word repetitions, distinct
word types or word equality partitions. This randomized control may itself have
a valid inventory explanation and is not labelled a known negative.

Both fits use the same full alphabet, inventory, shared injective H1 key and
public fixed-two-glyph boundaries and plaintext word lengths. Neither training
truth, generating key nor holdout is supplied to fitting. First SAT keys are
frozen. Only the encrypted positive receives training/holdout accuracy scores;
shuffle status and witness consistency are recorded without treating source
plaintext as the shuffle's truth. One fit per arm; no retries or key rescue.

Budgets remain **30 seconds solving** and **60 seconds per fresh worker**,
including construction. Durable loading/construction/solving/verification phase
checkpoints survive interruption. UNKNOWN and wall timeouts remain unresolved.

```sh
.venv/bin/python -m benchmarks.latin_layered_diversity --run
.venv/bin/python -m benchmarks.latin_layered_diversity --validate
```

Artifacts: `experiments/results/latin-layered-diversity`. Two worker tests cover
shared-key fitting and positive-only scoring. Validation reconstructs frozen
selection/provenance, checks shuffle count/length invariants, verifies generating
and recovered explanations and reconstructs held-out scores when available.
No manuscript fits or conclusions about manuscript language.

## Results

| Arm | Status | Construction | Solver | Total worker |
| --- | --- | --- | --- | --- |
| Known synthetic encryption | UNKNOWN, timeout | 10.20 s | 30.14 s | 40.35 s |
| Global atomic-code shuffle | UNSAT | 10.35 s | 25.16 s | 35.51 s |

The positive's generating explanation is independently verified during artifact
validation, but the solver did not recover a SAT key within budget. Training and
holdout accuracy are **not evaluated**, not zero. The shuffle's UNSAT is a bounded
solver result without an independently checked proof certificate. One paired
control does not estimate a false-fit rate or establish successful discrimination
because the known positive remains unresolved.

Before increasing timeout or revisiting manuscript fits, the next recommended
optimization is exact preprocessing by the observed within-word equality
pattern. Under this public fixed-boundary injective H1 model, repeated codes
must correspond to repeated letters and distinct codes to distinct letters.
Filtering the complete inventory by that pattern is logically sound without
using true letters or the key. Build smaller membership relations from those
exact subsets and rerun these same frozen arms/budgets. This proposal has not
been implemented; it does not generalize automatically to multiple homophones
or hidden code boundaries.
