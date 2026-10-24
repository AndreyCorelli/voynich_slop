# Zero-corruption oracle baseline

**Result:** the current objective does not preserve the correct dictionary, even
when search starts with the exact answer and accepts only strict score increases.
At 32,004 words, greedy optimization reduces token accuracy from 100% to 82.80%;
normal annealing reduces it to 69.58%. These are best-by-language-score mappings.

## Protocol

Use the validated widening experiment's five nested inputs and its full 14,287-form
oracle vocabulary. Construct the exact injective fit dictionary from each decoding
key. Independently verify that it renders the entire fit plaintext with 100% token
and type accuracy. Recurring holdout words also start at 100%; holdout-only words
are not added to the dictionary. Keep the model, scoring rules and proposal families
unchanged. This explicitly uses truth for initialization and diagnosis, not for
optimizing recovery or demonstrating blind decipherment.

Each run has one perfect start, no restarts, 20,000 proposals and seed 101 or 202:

- **Greedy:** accept only score increases greater than 1e-9. Reject both downhill
  moves and neutral moves, including swaps of indistinguishable untrained forms.
- **Annealing:** use the ordinary schedule, temperature 5 down to 0.05, including
  its normal downhill and neutral acceptance.

Every proposal's change in exact token and type recovery is computed from its
changed assignments. Aggregate proposed/accepted counts by score direction and
exact token-recovery direction. Save the first departure from truth, any strict
score-improving witness while still perfect, and trajectory snapshots. Check
snapshots and witness scores with the independent full scorer. Retain the best
mapping by the language objective, including the perfect starting point initially.

Twenty runs consume 400,000 proposals. Earlier experimental implementation and
artifacts remain unchanged. The original final test remains unscored.

## Results

Mean exact token accuracy of the best-scoring dictionary after 20,000 proposals:

| Actual words | Initial accuracy | Greedy | Annealing |
| ---: | ---: | ---: | ---: |
| 503 | 100% | 39.86% | 27.14% |
| 2,022 | 100% | 51.88% | 42.26% |
| 8,024 | 100% | 66.10% | 57.54% |
| 16,021 | 100% | 75.25% | 65.12% |
| 32,004 | 100% | 82.80% | 69.58% |

Both greedy seeds find a strictly higher-scoring incorrect dictionary from the
perfect state at every size. All twenty final selected scores exceed the initial
true score. At 32,004 words, greedy gains about 7,701 score units while reducing
exact type accuracy to 61.46%. Training-attested token accuracy falls from 100%
to 91.35%, so loss is not confined to forms absent from training. Recurring holdout
accuracy falls from 100% to 89.03%. Annealing gives respectively 82.38%
training-attested and 79.94% recurring-holdout token accuracy.

For example, the 32,004-word greedy seed-101 run first leaves truth on proposal 3:
`intulerat` becomes `perlectam`, losing one correct token while increasing the
score by 1.7047. The original form is absent from training, illustrating the
zero-count limitation. Later losses also affect training-attested words.

Larger cases receive fewer proposals per mapping variable under this equal-budget
protocol. Higher retained accuracy at larger sizes therefore cannot be attributed
solely to improved context. The decisive result is failure to preserve truth under
strict ascent, not a fair comparison of convergence across dimensions.

## Interpretation and limitations

The greedy control isolates an objective failure from annealing's deliberate
exploration: wrong mappings can improve the score starting at the exact answer.
A 100% oracle baseline is feasible and reachable by construction; search has no
recovery task to solve initially. This fails the exact-preservation diagnostic.

Candidate coverage is oracle-assisted. Thousands of candidate forms have no
training events and remain statistically exchangeable; language evidence is
incomplete even though every true form is available. Exact recovery loss does not
measure semantic coherence, and the result does not prove all language models or
word-mapping approaches fail. Two seeds and same-author development inputs limit
generalization. The oracle key never becomes the score being optimized.

## Verification and reproduction

151 focused tests pass. Tests compare incremental recovery counters with full
recovery after every step, verify deterministic replay, check malformed oracle
keys and disallowed restarts, and test full experiment replay and tamper rejection.
A separate two-candidate control preserves the perfect mapping under greedy search
when it is actually the score optimum.

```sh
.venv/bin/python -m benchmarks.word_mapping_zero_corruption
.venv/bin/python -m benchmarks.word_mapping_zero_corruption --validate
```

Validation reconstructs the parent's foundation and keys, then deterministically
replays every proposal in all twenty runs, rechecks full scores and recovery,
and compares complete reports. The bounded diagnostic uses full replay rather
than checkpoint/resume. Artifacts are under
`experiments/results/word-mapping/zero-corruption-calibration/`.

Implementation: `src/voynich_smt/oracle_mapping.py` and
`benchmarks/word_mapping_zero_corruption.py`.
