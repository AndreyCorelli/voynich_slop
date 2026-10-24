# Bounded nulls, complexity minimization, and CLI

This milestone adds dedicated null glyphs, full-codebook complexity minimization,
and reproducible command-line experiments. No external corpus was downloaded.

## Model assumptions

A glyph selected as a null has global ownership: it cannot appear in any
codeword, including mappings for unused plaintext symbols. Nulls may occur before,
between, or after complete codewords. They cannot interrupt a codeword. Decoding
skips their dedicated glyphs; independent re-encoding checks their exact positions.
Spaces remain preserved, and consecutive-null limits reset at each word boundary.

`nulls` contains `enabled`, `max_distinct_symbols`, `max_occurrences`, and
`max_consecutive`. All budgets are nonnegative integers. Disabled nulls require
zero budgets; enabling nulls with any zero budget permits no null occurrences.
The solver enforces all three limits together. Null positions in results are
absolute observed positions within each word. `code_spans` records complete
codeword spans; null-bearing results use these instead of conventional segmentation
offsets.

Null recovery avoids the raw ciphertext-prefix dictionary pruning used by the
earlier solver: leading nulls invalidate that inference. Minimization keeps the
entire codebook symbolic, including unused plaintext symbols. Deferred completion
of unused mappings would preserve feasibility but could distort a minimum.
Prefix-free codes, explicit dictionary membership, and the configured cipher
bounds remain assumptions. These extensions require the `finite` representation.
Feasibility uses the finite-domain tactic; minimization uses native Z3 Optimize.

## Objectives and evidence

Lexicographic minimization uses this priority order:

1. Distinct null symbols.
2. Null occurrences.
3. Additional homophones beyond one mapping per plaintext symbol.
4. Total codebook glyphs, including unused mappings.

Weighted minimization sums structural counts with configurable nonnegative integer
weights. Defaults are mappings = 1, additional homophones = 1, extra code glyphs = 1,
distinct null symbols = 2, and null occurrences = 1. Extra code glyphs count
codeword lengths beyond one glyph per mapping. These weights are conventions,
not linguistic evidence. Results retain raw counts, weights, and the weighted
score. Context rules and exceptions remain disabled.

SAT explanations are independently encoded and decoded, and checked against
dictionary, domain, cipher, and null bounds. `optimality_proven` is true only when
every objective's lower and upper bounds agree with its model value; Python
measurements also independently reproduce those values. SAT alone does not prove
a minimum. UNKNOWN, including timeout, is inconclusive and exports no recovered
explanation. Different valid plaintexts and keys may explain the same ciphertext.

## Reproduction

After `uv sync`, run these commands from the repository root:

```sh
uv run voynich-smt synthetic generate \
  --config experiments/configs/nulls-demo.json --words 5 --seed 7 \
  --output data/generated/demo-input.json \
  --ground-truth data/generated/demo-truth.json
uv run voynich-smt solve data/generated/demo-input.json \
  --output experiments/results/demo-feasible.json
uv run voynich-smt solve data/generated/demo-input.json \
  --optimize lexicographic --output experiments/results/demo-lex.json
uv run voynich-smt solve data/generated/demo-input.json \
  --optimize weighted --output experiments/results/demo-weighted.json
uv run voynich-smt sweep data/generated/demo-input.json \
  --null-symbols 0 1 --output experiments/results/demo-sweep.json
uv run voynich-smt compare experiments/results/demo-lex.json \
  experiments/results/demo-weighted.json
uv run voynich-smt corpus info data/generated/demo-input.json
uv run python benchmarks/nulls_optimization.py
uv run pytest -q
```

Generation stores public requests separately from private plaintext, key, choices,
and insertions. Solving reloads only the public request. Seeded generation inserts
nulls at valid boundaries and verifies a round trip. Source, public output, and
truth paths must differ.

`solve` accepts `--timeout-ms`. `--optimize` selects the finite backend and the
requested objective. Custom weights live in the request's `optimization.weights`
object. `sweep` varies only the distinct-null-symbol budget, retaining occurrence
and run limits; it checkpoints results. `compare` displays scoring-weight
identifiers alongside scores. `corpus info` describes the tokenized ciphertext
and dictionary in a request; it does not list downloaded corpora.

Saved solve reports include the effective request, normalized request checksum,
original input checksum, Python/Z3/platform versions, and solver results. Exit
codes are 0 for completed SAT or UNSAT, 2 for invalid input, and 3 for UNKNOWN.

## Measured validation

The suite passes **234 tests**, including exhaustive tiny optimization oracles,
unused-codebook minima, null boundary restrictions, budget UNSAT cases, and CLI
replay. The benchmark uses a four-symbol alphabet, five dictionary entries,
verbose codes of length 1–2 with at most two homophones, and four generated null
occurrences. It compares identical ciphertexts across three modes for seeds
7, 17, and 1729 at 5, 10, and 25 words.

All **27/27 runs returned verified SAT**. All **18/18 minimization runs proved
their objective minima**. Observed solver times, rounded in seconds:

| Words | Feasibility | Lexicographic | Weighted |
| --- | --- | --- | --- |
| 5 | 0.036–0.043 | 0.440–0.487 | 0.929–0.971 |
| 10 | 0.052–0.056 | 0.554–0.725 | 1.806–2.314 |
| 25 | 0.124–0.135 | 1.402–2.044 | 5.159–9.996 |

Results are saved in `experiments/results/nulls-optimization.json`; public inputs
and private truth are under `data/generated/nulls-optimization/`. Times are
observations on the recorded machine. Weighted minimization approaches the
ten-second timeout at 25 words, so larger vocabularies and samples need further
scaling evaluation. This fixture does not establish unrestricted Latin or Voynich
recovery.

The next research milestone is provenance-tracked EVA and public-domain Latin
acquisition, explicit normalization, and matched synthetic/randomized controls.
Real-text comparisons should retain bounded assumptions and report UNKNOWN
without interpreting it as evidence against a language or cipher.
