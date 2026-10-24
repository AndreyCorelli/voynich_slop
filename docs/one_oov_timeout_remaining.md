# Remaining natural one-OOV timeouts at 60 seconds

All four remaining positives return verified SAT, recover 24/24 training words
and predict all six held-out words correctly. All four paired shuffles are UNSAT.
No fits time out. One integration test and eight-case artifact validation pass.

| Passage / profile | Positive solver | Held-out exact | Shuffle solver / result |
|---|---:|---:|---|
| swabian-1-fixed-two-delete-1 | 27.057 s | 6/6 | 25.336 s; UNSAT |
| swabian-1-mixed-one-two-three-delete-1 | 26.497 s | 6/6 | 22.859 s; UNSAT |
| swabian-2-fixed-two-delete-1 | 24.458 s | 6/6 | 26.519 s; UNSAT |
| swabian-2-mixed-one-two-three-delete-1 | 19.721 s | 6/6 | 19.639 s; UNSAT |

The new runs add 24/24 correct occurrences, including 14/14 novel occurrences.
Together with three original five-second successes and the earlier Latin
60-second replay, every one of the eight natural one-OOV fixtures now has a
verified exact training recovery and correct continuation: 48/48 occurrences,
38/38 novel. All eight paired controls have UNSAT results. Original five-second
UNKNOWN records remain preserved; this is a composite of matched requests with
different budgets, not a claim that they succeeded at five seconds.

A 60-second allowance was productive on these frozen fixtures. It does not
eliminate the wrong-key ambiguity observed in repeated-unknown synthetic tests,
or establish a false-fit rate: the natural dictionaries still retain all other
true training words, and only one missing type occurring once is tolerated.
Manuscript-language inference remains unsupported.


This replay freezes all four remaining natural positive/control pairs that were
UNKNOWN at five seconds: Swabian passages 1/2 under fixed-two and mixed-1/2/3 keys.
Each of the eight cases receives one 60-second solver budget. The previously
resolved Latin pair is preserved and not repeated. No substitutions, retries,
longer budgets or outcome-based additions are permitted.

Only `timeout_ms` changes from 5000 to 60000. Training and held-out ciphertext,
dictionary, one-OOV-occurrence allowance, alphabets, bounds, free selection and
encoding remain unchanged. Construction time is extra. Positive generating
witnesses are independently checked; positive UNSAT would contradict those
witnesses. Recovered SAT keys are independently verified, then frozen-scored
against the unchanged continuation. Control SAT means model compatibility, not
plaintext accuracy. UNKNOWN remains unresolved; UNSAT is solver-reported without
independent proof certificates. These are four correlated pairs, not a population
false-fit estimate or manuscript-language evidence.

```sh
.venv/bin/python -m benchmarks.one_oov_timeout_remaining --run
.venv/bin/python -m benchmarks.one_oov_timeout_remaining --validate
```

`experiments/results/one-oov-60s-remaining/` saves the frozen protocol, hashes,
requests, five-second baseline rows, checkpointed witnesses/scores and validation.
Completed cases skip on resume. One integration test checks fixed selection,
60-second budgets, resume and non-SAT scoring. Artifact validation checks
strict timeout-only changes, matched sources, generating/recovered witnesses,
training identities, OOV count and frozen continuation scores.
