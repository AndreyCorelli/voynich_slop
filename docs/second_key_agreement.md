# Second-key agreement calibration

All six positives admit a second, verified key differing on at least one mapping
used by the first key in training. No additional fit times out. Two keys agree
on 9/18 held-out occurrences, of which 8 are correct and one is wrong. The six
paired shuffles retain their previous UNSAT outcomes and have no first SAT key,
so no second-key solve is attempted for them. Two tests and twelve-case artifact
validation pass.

| Profile / seed | First exact | Second exact | Agreed words | Correct agreements |
|---|---:|---:|---:|---:|
| Fixed two / 4301 | 3/3 | 0/3 | 0 | 0 |
| Fixed two / 4302 | 2/3 | 3/3 | 2 | 2 |
| Mixed 1/2 / 4301 | 1/3 | 2/3 | 0 | 0 |
| Mixed 1/2 / 4302 | 2/3 | 2/3 | 3 | 2 |
| Mixed 1/2/3 / 4301 | 3/3 | 2/3 | 2 | 2 |
| Mixed 1/2/3 / 4302 | 3/3 | 2/3 | 2 | 2 |

The mixed-1/2 seed-4302 pair agrees on its entire continuation while both keys
predict one word incorrectly. Conversely, a fully correct first continuation can
have no agreement with the second key. Thus two-key agreement cannot certify
prediction reliability. Totals are correlated occurrences, not independent
confidence estimates. Second keys solve in 0.896–2.029 seconds with configured
five-second budgets, construction extra.

## Frozen protocol

Inputs and first keys come from [repeated unknown-type calibration](oov_type_calibration.md).
For each SAT first result, exclude the conjunction of its exact H1 code mappings
for symbols used in its recovered training plaintext. At least one of those
mappings must change. Altering only unused codes cannot qualify as a second key.
No true plaintext, held-out text or prediction score enters this exclusion.
The request, one-OOV-type budget, dictionary, bounds, encoding and solver timeout
are unchanged. One additional solve is permitted per eligible case, with no
retries, reranking or outcome-based additions. Exclusions are frozen before solves.

Both keys are independently checked against ciphertext, bounds, type budget and
selection rules, and the second key's mapping difference is verified. Held-out
scoring occurs afterward with each frozen key. Agreement requires both decodings
to be complete and identical; matching partial prefixes do not count. True
plaintext is used only afterward to audit agreement correctness. UNKNOWN or
UNSAT second searches would have no agreement score. First non-SAT cases are
explicitly retained without additional solves.

```sh
.venv/bin/python -m benchmarks.second_key_agreement --run
.venv/bin/python -m benchmarks.second_key_agreement --validate
```

Artifacts: `experiments/results/second-key-agreement/` records protocol, hashes,
first results, exclusions, second witnesses, individual frozen scores, agreement
audits and validation. Completed cases skip on resume. Validation reconstructs
exclusions, verifies distinct witnesses and recomputes scoring/agreement. Tests
cover wrong agreement, incomplete decoding, exclusion scope, non-SAT handling
and resume.

This is a two-key sample, not exhaustive key enumeration or a uniqueness proof.
These engineered, assisted-vocabulary fixtures and one shuffle family do not
establish manuscript language or a population false-fit rate. The result argues
against treating agreement as a certificate; a stronger next calibration would
ask directly whether an alternative compatible key can change each held-out
prediction, with bounded searches and unresolved outcomes preserved.
