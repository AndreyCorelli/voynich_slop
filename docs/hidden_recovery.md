# Hidden-plaintext synthetic recovery

This step implements TODO.md section 14 with a finite dictionary as the explicit
language model. It does not implement grammar, corpus frequencies, or morphology.
Vocabulary membership is the entire linguistic assertion.

## Public inputs and independent verification

`recover_dictionary` accepts observed tokenized ciphertext, alphabet definitions,
cipher-family bounds, a dictionary, a timeout, and optional plaintext word-length
bounds. It never accepts the generating plaintext, key, offsets, or choices.
The default maximum plaintext word length is derived from the public dictionary.

For each observed word, prune dictionary candidates only by the public word-length
bounds and the interval implied by minimum/maximum code length. Z3 chooses a word
and its length. Tokens after that length are inactive, have zero encoding length,
and are omitted from the extracted explanation. Ciphertext word boundaries are
preserved; spaces and the number of words are public assumptions.

Every SAT explanation is checked by ordinary Python for:

- Complete-word dictionary membership and word-length bounds.
- Homophone and code-length limits and valid ciphertext symbols.
- Prefix-free codebook validity and unique decoding.
- Exact ciphertext reproduction using recovered occurrence choices.
- Decoding back to the recovered plaintext.
- Agreement between recovered offsets and independently computed segmentation.

Original plaintext equality is only a diagnostic. Equivalent explanations count
as successful recovery. UNKNOWN and UNSAT do not have recovered explanations.

`HiddenRecoveryRequest` serializes the public inputs and rejects unknown top-level
fields. The benchmark writes and reloads each hidden request before solving it.
Original plaintext, key, and choices are saved separately under `ground_truth/`;
the replay path does not load them. Public requests are enough to rerun a solver
experiment without access to its generating model.

## Solver representations and reductions

Both implementations use finite integer codebooks and symbolic ciphertext offsets.
`ite` uses nested conditional lookup; `array` uses constrained integer arrays for
code counts, lengths, and glyphs. The representations encode the same family.
Tests cover both, including an exhaustive Python oracle for tiny codebooks and
dictionary sequences. Array lookup was the default at this milestone after comparison
with the existence-preserving reductions enabled. It has since been replaced by
the [finite-domain representation](staged_recovery.md).

Existence-preserving reductions:

1. Remove unused homophones and order the remaining alternatives canonically.
   Every active code for an observed letter must occur in the explanation.
2. Unobserved letters retain one code, extended to the maximum permitted length.
   Extending an unused prefix-free code cannot affect observed encoding or
   introduce a prefix collision. Labels of statically unused letters may be
   ordered canonically because their codes can be permuted freely.
3. Identical ciphertext words imply identical plaintext words under unique
   decoding. State that consequence directly instead of deriving it through the
   entire codebook for every repeated word.
4. Known plaintext tokens become integer constants; genuinely symbolic tokens
   remain variables.

These preserve existence of an explanation, not every equivalent codebook.
Extending unused codes can change a complexity score. This reduction must be
revisited before optimizing complexity or counting all explanations. Every
configured plaintext letter still consumes at least one codebook entry.

## Reproduction

```sh
uv run pytest -q
uv run python benchmarks/hidden_recovery.py \
  --representation ite \
  --output experiments/results/hidden-recovery-final.json \
  --artifact-dir data/generated/hidden-recovery-final
```

Defaults are seeds 7, 17, and 1729; 10, 25, and 50 words; and a 10-second solver
timeout. Plaintext selection and key generation each use the stated seed in
separate random generators; occurrence choices use seed + 1. Larger samples
extend the same seeded 50-word plaintext. Ciphertext has eight atomic symbols.
All profiles use H ≤ 2, code lengths 1–3, global prefix-freeness, preserved word
boundaries, and no nulls or context.

Profiles:

- `small-hidden`: four plaintext symbols and five hand-authored Latin words.
- `latin-known`: 24 configured plaintext symbols and a 35-word fixture; plaintext
  is supplied to assess codebook-search cost separately from language ambiguity.
- `latin-hidden`: the same 24-symbol alphabet and 35-word fixture, with plaintext
  and word lengths hidden.

The alphabet is explicitly `abcdefghiklmnopqrstuvxyz`. Unused letters are retained.
An earlier description called this a 23-symbol alphabet; it has 24 symbols because
both `u` and `v` are present. The saved inputs and capacity counts were correct.
The fixtures are not downloaded corpora or representative distributions of Latin.
No grammar or sentence plausibility is asserted.

For a pilot representation comparison:

```sh
uv run python benchmarks/hidden_recovery.py --representation array --sizes 10 \
  --timeout-ms 5000 --output experiments/results/hidden-array-pilot.json \
  --artifact-dir data/generated/hidden-array-pilot
```

Reported runtimes measure Z3 checking. Construction time, actual variables,
constraint counts, codebook capacity, versions, samples, and reason for UNKNOWN
are also saved. Results are checkpointed after every experiment. Single runs are
observations, not statistical estimates or performance guarantees.

## Recorded results

Python 3.14.4, Z3 4.16.0, macOS arm64. The final conditional-lookup run completed
27 experiments with the following outcomes:

| Profile | SAT and independently verified | UNKNOWN (timeout) | Solver time |
| --- | ---: | ---: | --- |
| Four-symbol hidden plaintext | 9/9 | 0 | 1.409–3.448 s |
| 24-symbol known plaintext | 9/9 | 0 | 1.157–5.723 s |
| 24-symbol hidden plaintext | 0/9 | 9 | Ten-second budget |

At 50 words, small hidden recovery took 2.845, 3.173, and 3.448 seconds across
the three seeds. Full-alphabet known recovery took 3.610, 5.723, and 4.249 seconds.
All 18 conditional-lookup SAT results also happened to match the original plaintext; this was not
required or assumed. No UNSAT results occurred: each sample was generated by a
legal encoder in the configured family. All nine UNKNOWN reasons were `timeout`.

At this milestone, 89 tests passed. Tests covered hidden recovery for all three cipher families across three seeds and
both representations. The exhaustive oracle compares 36 tiny
ciphertexts per representation against independently enumerated legal Python
encoders and dictionary plaintexts.

After the reductions, array lookup improved both validated profiles on the same
seeds and samples:

| Profile | Conditional lookup | Array lookup |
| --- | --- | --- |
| Small hidden, 10 words | 1.409–2.683 s | 0.412–1.084 s |
| Small hidden, 25 words | 2.066–3.002 s | 0.872–2.235 s |
| Small hidden, 50 words | 2.845–3.448 s | 1.759–2.314 s |
| Full known, 10 words | 1.157–1.492 s | 0.553–0.666 s |
| Full known, 25 words | 2.242–3.390 s | 0.807–1.650 s |
| Full known, 50 words | 3.610–5.723 s | 2.267–3.495 s |

These are ranges across three single runs, not speedup guarantees. The earlier
array pilot before reductions timed out on all nine 10-word cases at five seconds;
representation and codebook symmetry need to be evaluated together. The final
array report is `experiments/results/hidden-array-matrix.json`, generated with:

```sh
uv run python benchmarks/hidden_recovery.py --representation array \
  --output experiments/results/hidden-array-matrix.json \
  --artifact-dir data/generated/hidden-array-matrix
```

The final array matrix likewise has nine verified small-hidden results, nine
verified full-alphabet known results, and nine full-alphabet hidden timeouts.
The public-input-only replay was separately checked and returned verified SAT.

At this milestone, synthetic validation succeeded on a small vocabulary with hidden
plaintext, lengths, key, segmentation, and choices. The broader-vocabulary gate
had not passed within the measured budget; the [next milestone](staged_recovery.md)
now verifies all nine broader cases. Do not interpret subsequent Voynich
failures as evidence against a cipher family until synthetic recovery is reliable
at comparable alphabet sizes, vocabulary ambiguity, and text lengths.

Next, investigate stronger dictionary search propagation, a staged progression in
vocabulary size and homophone/code-length bounds, and fair representation or
incremental-solving comparisons. Explicit n-gram constraints may later provide a
stronger language model. Null machinery and complexity optimization remain later
milestones; more flexibility would further increase the unresolved search cost.
