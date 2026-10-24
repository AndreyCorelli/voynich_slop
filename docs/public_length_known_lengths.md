# Correct training lengths with word identities hidden

All four selected synthetic cases reach verified SAT within five seconds when
only the correct training plaintext word lengths are revealed. Prediction remains
poor: 0, 0, 0 and 1 of the three novel held-out words are exact, matching the counts
from the public-midpoint fits. Knowing the full training words previously produced
3/3 on each case, with their held-out mappings subsequently proved forced under
that known-word model.

| Case | Length-only solver time | Exact training words | Hidden midpoint exact held-out | Length-only exact held-out | Known-word exact held-out |
|---|---:|---:|---:|---:|---:|
| Length two / 3101 | 0.878 s | 2/18 | 0/3 | 0/3 | 3/3 |
| Length two / 3102 | 1.486 s | 0/18 | 0/3 | 0/3 | 3/3 |
| Mixed / 3101 | 0.688 s | 2/18 | 0/3 | 0/3 | 3/3 |
| Mixed / 3102 | 0.544 s | 4/18 | 1/3 | 1/3 | 3/3 |

Each fit receives the original training ciphertext, full 5,655-word dictionary,
24-letter plaintext alphabet, six ciphertext glyphs, H1 prefix-free L1–3 bounds,
free selection, observed code domains and five-second solver budget. The only
added information is an 18-element tuple of training word token counts. No word
identities, generating key, individual code lengths, segmentation or continuation
are supplied. Full dictionary word search remains active. Generating plaintext
is used outside fitting to derive counts and score results.

The four cases and counts are frozen before solving. Source, implementation,
hidden-report and known-word-report hashes are preserved. Completed cases are
checkpointed and skipped on resume. Recovered SAT witnesses are independently
verified against the complete model and the supplied lengths. Frozen keys are
scored against the unchanged, novel continuation. Protocol and report live in
`experiments/results/public-length-known-lengths/`; earlier results are preserved.

The first public midpoint vectors already had correct lengths in the uniform
two-code cases. They did not in the mixed cases; revealing the correct lengths
still fails to improve their exact prediction counts. Timing differences in this
single-fit comparison should not be interpreted as a stable performance ranking.
The length-only arm uses the existing length-oracle solver path; the public arm
also manages branch schedules and budgets. Both check the same full feasibility
model once lengths are fixed.

These results separate a feasibility bottleneck from predictive identification:
removing length uncertainty gives fast witnesses, but many dictionary word
identities remain compatible with the training ciphertext. On these fixtures,
correct training lengths alone are insufficient to recover predictive keys.
This does not prove every length-only key predicts poorly: only the first SAT
witness was scored. It is an oracle diagnostic on four previously successful
cases, not blind calibration or evidence about the manuscript's language. The
two length-three UNKNOWN cases remain outside this experiment.

Five focused tests pass, checking length-only inputs, unchanged requests and
budgets, unscored UNKNOWN, preserved comparisons, resume without repeated fits,
changed-source rejection and solver validation of supplied lengths. Artifact
validation checks hashes, synthetic and recovered witnesses, fixed lengths,
training match counts and independently recomputed frozen predictions.

```sh
.venv/bin/python -m benchmarks.public_length_known_lengths --validate
```

The next useful bounded test would ask whether a correct predictive explanation
can be selected using training information alone: rank a small fixed set of
length-constrained SAT witnesses by a frozen corpus score, without accessing
held-out predictions during selection. This should first be checked against
preserved prior reranking results, which already showed limited improvement;
avoid repeating an equivalent experiment or expanding a manuscript sweep.
