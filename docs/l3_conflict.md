# Length-three codes on the conflicting suffix

Allowing codes of up to three EVA characters **repairs the 11-word conflict**.
The original 23-word prefix is still unresolved. This milestone changes only
maximum code length in the scientific model; vocabulary, alphabets, H2 bound,
prefix-free codebook, word boundaries and text-wide zero-start cycles are fixed.

## Observed results

| Sample and model | Result | Solver check |
| --- | --- | ---: |
| 11-word suffix, original L2 | UNSAT, prior report | 1.34 s |
| Same suffix, L3 | SAT, independently verified | 4.10 s |
| 23-word prefix, L3, flat dictionary, 30 s | UNKNOWN | 30.10 s |
| 23-word prefix, L3, flat dictionary, 120 s | UNKNOWN | 120.07 s |
| Same prefix, factored dictionary, 30 s | UNKNOWN | 30.08 s |
| Same prefix, factored dictionary, 120 s | UNKNOWN | 120.10 s |

The suffix is source records 485–495 of the normalized ZL transcription. The
prefix is records 473–495. These are zero-based indices and exact sample records
remain in the preceding [sample scaling](sample_scaling.md) artifacts.

The verified suffix explanation is:

```text
Ciphertext: chol daiin cthy schey chor chal chag cham cho qokol chololy
Plaintext:  an   fumo  re   cum   ad   in   iv   iv   a   est   ante
```

This is a sequence of accepted Caesar vocabulary entries, not a grammatical
Latin reading or a proposed decipherment. No plaintext, key, original word
lengths or segmentation was supplied to this recovery run. The returned key
actually uses three-character codes for observed letters: `a -> cho`, `i -> cha`
and `r -> cth`. It is not merely exploiting length-three codes for unused letters.
The key, code choices and all word segmentations are saved in the report. Python
verification checks exact re-encoding, unique decoding, vocabulary membership,
bounds and per-letter cyclic selection.

The suffix's SAT result does not prove the prefix SAT. The earlier words constrain
the shared key and occurrence counts. The suffix may infer its own code order;
its fit is a local feasibility result under the same zero-start rule.

## Synthetic recovery validation

Three seeds (7, 17 and 1729) generate 11-word positive controls. Every generated
sample uses at least one length-three code. Truth is saved separately from hidden
public requests, and a synthetic UNSAT result raises an error.

| Recovery profile | Verified SAT | UNKNOWN |
| --- | ---: | ---: |
| Four-letter alphabet, ten-word dictionary, hidden plaintext | 3 | 0 |
| Full 24-letter alphabet and 25-character cipher alphabet, known plaintext | 3 | 0 |
| Full alphabets and 5,665-word dictionary, hidden plaintext | 0 | 3 |

Small hidden checks take 0.030–0.039 seconds; full known checks take 0.460–0.684
seconds. The full hidden checks time out at approximately 30 seconds, with another
22–24 seconds of construction per case. They are feasible by their generated
witnesses, but the solver did not recover a witness within the budget. **Full-size
hidden recovery remains an incomplete validation gate.** The required small-hidden
and full-known gates pass; the report exposes the full-hidden limit separately.

## Equivalent dictionary formulation

Hidden requests now accept `dictionary_encoding: "flat" | "trie"`, defaulting to
`flat` for compatibility. This changes the formula, not the hypothesis.

The flat formula repeats a conjunction for every candidate dictionary word.
The trie formula shares common prefixes, explicitly marks terminal word lengths,
and binds inactive token slots to the same sentinel used by the flat formula.
It preserves exact membership and hidden word lengths. SMT equivalence tests
prove equality of the two formulas on representative branching/prefix dictionaries,
including empty candidate sets and padding. End-to-end cyclic recovery checks and
an independent exhaustive masked-model oracle check the integration.

Trie construction on the prefix took 6.20–6.29 seconds versus 7.09–7.24 seconds
for the flat encoding. Neither formulation resolved the prefix in two minutes.
Trie mode currently supports null-free feasibility; nulls and optimization retain
the existing flat/bounded implementation. Representation remains `finite` here.

## Reproduction and artifacts

```sh
uv run python benchmarks/l3_conflict.py
uv run python benchmarks/l3_conflict.py --resume
uv run voynich-smt solve \
  data/generated/l3-conflict/inputs/conflict-flat-ms30000.json \
  --output experiments/results/l3-conflict-replay.json
uv run pytest -q
```

Configuration is `experiments/configs/l3-conflict.json`; the checkpointed report
is `experiments/results/l3-conflict.json`. Public inputs live under
`data/generated/l3-conflict/inputs/`, and synthetic truth under `truth/`.
Known-plaintext calibration inputs have a labeled wrapper containing the public
plaintext; ordinary hidden inputs remain directly usable by `voynich-smt solve`.
Resume checks configuration, source digest and Python/Z3 versions before reuse.
The runner advances to the prefix only if the suffix is verified SAT.

This measured run used `--import-probes` to import the initial exploratory checks
by the complete normalized request hash. Cached SAT explanations are independently
verified again; their original solver/construction times are retained, and the
reuse source is recorded. No exploratory cache is required for reproduction.

These results show that the L2 restriction matters for the local exclusion.
They do not exclude L3 for the full prefix, establish manuscript language or give
a probability for the broader Latin encryption hypothesis. Improve full-vocabulary
hidden recovery before adding further model dimensions.
