# Shortest UNSAT prefix in the restored Latin vocabulary

The fixed baseline is the footer-free Caesar vocabulary plus `i/iv/iulius`
(5,658 entries), with the same H2/L3 prefix-free code model and text-wide
phase-zero cycles. No `by/of` entries are admitted. Only contiguous prefixes
starting at word zero are tested. All public requests use observed codeword
domains and have no key, boundary, length or plaintext hints.

The full 23-word prefix is UNSAT from the validated user-run report. Truncating
the original witness supplies independently checked SAT witnesses for prefixes
of one, two and three words (`pro dc an`). The next original plaintext word,
`by`, is outside this vocabulary; failure of that particular witness does not
establish UNSAT for four words.

The first fresh binary-search probe, 13 words, returned UNKNOWN in 30.07 solver
seconds. The current certified bounds are therefore **3 words SAT / 23 words
UNSAT**. No shortest prefix has been established.

The runner checkpoints every result and independently verifies SAT witnesses.
Resume checks source report hashes, cached request parameters, exact prefix
identity and input hashes. UNKNOWN never moves the SAT or UNSAT bound. Search
stops at the first timeout; a larger budget can resume that unresolved search.
If no remaining untried size exists at that budget, it returns the unresolved
interval. Completion requires adjacent SAT and UNSAT prefix sizes. Restricting
any legal prefix witness to fewer initial words preserves the same cycle phases,
so those adjacent certificates establish shortest-prefix minimality.

Run the short-budget search:

```sh
.venv/bin/python -m benchmarks.clean_latin_prefix --resume
```

Continue with **up to 30 minutes per prefix check**:

```sh
.venv/bin/python -m benchmarks.clean_latin_prefix \
  --timeout-ms 1800000 --resume
```

The longer search has not been launched. It retries the unresolved midpoint and,
if decisive, continues binary search until the boundary is certified or another
check times out. Total duration can exceed 30 minutes; construction is additional
to each solver budget. Completed checks are checkpointed so the process can be
resumed. Ordinary public replay wrappers for all prefix sizes are already saved.

Report: `experiments/results/clean-latin-prefix.json`.
Inputs: `data/generated/clean-latin-prefix/inputs/words-01.json` through
`words-23.json`. Cached rows retain their effective request and input hash even
when the prepared files are regenerated with a new timeout. Existing witness
rows retain historical result timing and explicitly identify witness reuse.

UNSAT conclusions rely on solver reports; no independent proof certificate is
claimed. Even a shortest UNSAT prefix would concern only the fixed vocabulary
and cipher assumptions, not Latin or the manuscript's language in general.

## Certified boundary after the user-run search

The longer checkpointed search completed. All saved requests and input hashes
were checked against the fixed baseline; every SAT witness was independently
checked for key legality, vocabulary membership, re-encoding, decoding, cycle
choices and segmentation offsets. The audit is
`experiments/results/clean-latin-prefix-validation.json`.

| Prefix length | Result | Solver time |
|---:|---|---:|
| 13 | SAT | 302.63s |
| 18 | SAT | 550.10s |
| 20 | SAT | 747.43s |
| 21 | SAT | 525.48s |
| 22 | SAT | 966.71s |
| 23 | UNSAT | 273.64s, imported baseline |

The **shortest UNSAT prefix is exactly 23 words** under this model. The
verified 22-word witness establishes feasibility of every shorter prefix by
restriction. The crossing ciphertext word is `chololy` (word 23); it follows
`qokol` (word 22). UNSAT applies to all possible keys for the 23-word prefix,
not merely to extending this particular 22-word key.

The saved 22-word plaintext is:

```text
pro cn et xl suo dum et sub cvm ab xv cum et sui xl hi et at ad ab e cn
```

It is a vocabulary fit, with numerals and other corpus entries, not a recovered
meaningful Latin passage. The report retains the full ordered codebook and
choices. UNSAT provenance was checked, but no independent UNSAT proof
certificate was checked.

Shortest-prefix minimality does not establish that all 23 words are essential:
a shorter contiguous block ending at word 23 may already be UNSAT. The next
useful diagnostic is to trim leading words while retaining the last word and
find the shortest UNSAT suffix of this 23-word prefix. For an independently
inferred key, text-wide cyclic code lists may rotate to account for the removed
initial history; arbitrary interior deletions would change the problem.


The [checkpointed suffix search](clean_latin_suffix.md) now implements that
diagnostic with explicit witness rotation and independent SAT validation.
