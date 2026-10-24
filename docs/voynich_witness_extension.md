# Verified 23-word witness and extension

The user-run observed-domain retry returned SAT in 351.30 solver seconds.
Independent replay validation checks the frozen request and input hashes,
prefix-free key, word membership, code bounds, re-encoding, decoding,
text-wide cyclic choices, segmentation offsets and observed emitted-code domains.
The result is a fit to the frozen 5,665-entry vocabulary, not a recovered
meaningful Latin passage:

```text
pro dc an by xl eum ab xv dum iv of dum an xl by spe ab in is iv a dc ante
```

The vocabulary contains Roman numerals and English footer tokens. In particular,
`by` and `of` originate in the raw Gutenberg line
`End of Project Gutenberg's Cæsar's Commentaries, Books I-IV, by Julius Cæsar`,
which precedes the formal END marker. Parser version 1 includes that line.
Alphabet filtering did not establish Latin language membership. The frozen input
and corpus are preserved for reproducibility; future Latin-only experiments
must exclude the footer and regenerate the vocabulary and requests.

Homophones below are ordered; each letter starts with its first alternative
and cycles across the whole text. Asterisks mark unused completion letters.

| Letter | Ordered codes | Letter | Ordered codes |
|---|---|---|---|
| a | cho | b | ct, r |
| c | pal, kol | d | qo |
| e | y | f | hor |
| g* | aaa | h* | aab |
| i | cha | k* | aac |
| l | img, iin | m | or, ham |
| n | l | o | os, oc |
| p | ts, e | q* | aad |
| r | he | s | sch, g |
| t | ol | u | che, tc |
| v | m | x | da |
| y | hol, hy | z* | aae |

The next contiguous ciphertext word is `s`. Checking all 24 words while fixing
exact homophone lists, counts and ordering for the 19 used letters returns
**UNSAT** in about 1.72 seconds. The five unused completion letters remain free.
The solver's sufficient pinned conflict is `a`, `e`, `i`; it is not claimed to
be a minimum core. The single-letter dictionary entries in this frozen request are `a`, `e`, `i`.
Their pinned codes (`cho`, `y`, `cha`) cannot emit standalone `s`.


This is a conditional rejection of the witness's used mappings, not an
unrestricted UNSAT result for the 24-word prefix. Adding homophones to pinned
letters is also excluded by this particular check. A fresh key or revised
homophone lists may still fit the longer sample.

Replay the audit and short extension check:

```sh
.venv/bin/python -m benchmarks.voynich_witness_extension
```

Report: `experiments/results/voynich-witness-extension.json`. Explicit guided
input: `data/generated/voynich-witness-extension/inputs/words-24-used-mappings.json`.

The next useful milestone is to remove footer contamination in a new normalized
corpus, regenerate a Latin-only vocabulary, and retry the 23-word prefix before
scaling it further. Preserve the old results as results for their frozen model.
