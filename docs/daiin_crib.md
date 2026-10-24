# Conditional daiin = vnd word-family probe

The ordered, one-code-per-letter interpretation of `daiin = vnd` has a strong
structural problem: it cannot represent any multi-letter German word beginning
with `d` among the clean observed manuscript word types.

## Model and inputs

The probe uses the existing processed Zandbergen–Landini EVA corpus, retaining
records with no exclusion reason and only single ASCII alphabetic tokens.
There are 37,608 tokens, 7,457 types, and 847 occurrences of `daiin`.
Input SHA-256 hashes and Z3 version are recorded in the JSON artifacts.

Each represented plaintext letter receives one nonempty code of 1–3 EVA
characters. Codes are globally prefix-free; order and word boundaries are
preserved; nulls and homophones are excluded. This is a **partial-key presence
test**: selected targets must encode to observed word types. Remaining text
has no dictionary, grammatical, or key-extension constraints. A SAT witness
therefore does not establish a full alphabet key or full-text German decoding.

The target list is `von vor vil vns nach nicht nun noch der die das dem den des`.
Thirteen forms occur in the existing Kottanerin vocabulary (Middle Bavarian,
1445–1452); `nun` does not and is excluded. Corpus counts establish attestation,
not a claim that every target must occur in Voynich.

## Results over all clean word types

Five of six nonempty three-way segmentations of `daiin` are prefix-free.
Exhaustive bounded alignment finds no possible encoding for `von` or any of
`der die das dem den des`, across all five segmentations. The other six targets
have marginal candidates, but Z3 proves that at most **five of the thirteen**
can coexist under a shared key. Six or more returns UNSAT; five returns SAT.
The saved SAT witness is checked outside Z3 for prefix freedom, crib encoding,
and presence of every represented target in the observed corpus.

The `d` obstruction is stronger than this bounded solver result. Since `d` is
the final letter of `vnd`, its code must be a suffix of `daiin`. With nonempty
codes for the preceding two letters, the only possibilities are `n`, `in`,
and `iin`. There are **no proper word extensions** of any of these strings in
the filtered corpus. The standalone word `n` occurs three times and `iin`
once, but neither can encode a multi-letter word starting with `d`.
This independently checked necessary condition does not require prefix freedom
or the maximum code length of three.

## Frequent-type comparisons

A separate matched comparison restricts candidate locations to the **61 types
occurring at least 100 times**. It uses the same thirteen targets and model.

| Crib for daiin | Maximum simultaneous targets |
| --- | ---: |
| vnd | 2 |
| ain | 6 |
| mit | 6 |
| ist | 6 |
| auf | At least 7; an upper cardinality check timed out |
| aus | 7 |

These are handpicked alternative cribs, all attested in Kottanerin, rather than
randomized controls or calibrated significance tests. Results over frequent
types must not be compared directly to the all-types maximum of five.
UNKNOWN is retained as UNKNOWN, never treated as UNSAT.

## Interpretation

The attack successfully yields falsifiable restrictions, and this particular
crib fares poorly under the tested single-code, ordered EVA-character model.
Requiring even one of the listed `d`-initial words makes that conditional model
impossible. Not requiring those words leaves surviving partial fits; the test
does not exclude German, homophonic codes, alternative cipher units, changed
word boundaries, or an encoding of expanded rather than literal spelling.
No held-out predictive evaluation is claimed: all clean word types were used
for this initial compatibility screen.

## Reproduce

```sh
.venv/bin/python -m benchmarks.daiin_crib --timeout-ms 3000
.venv/bin/python -m benchmarks.daiin_crib --timeout-ms 3000 --min-count 100 \
  --cribs vnd ain mit ist auf aus \
  --output experiments/results/daiin-crib/frequent-controls.json
.venv/bin/python -m pytest tests/unit/test_daiin_crib.py -q
```

The main artifact is `experiments/results/daiin-crib/report.json`. The tests
check exhaustive crib segmentation, repeated-letter consistency, a synthetic
case with individual support but a joint contradiction, and the independent
final-letter obstruction.
