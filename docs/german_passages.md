# Attested German passages on the 22-word Voynich block

**None of the 66,638 eligible source windows fits the fixed block.** Eight
windows pass the necessary positionwise length filter; all eight return UNSAT
under text-wide cycling. Moreover, each has a directly checkable contradiction:
equal ciphertext words would have to decode into different plaintext words.
Thus length and repetition alone exclude this entire finite passage sample,
even without imposing cyclic homophone selection.

This tests contiguous passages from nine selected historical German sources,
not unrestricted German and not the manuscript's language. The earlier five
cyclic dictionary SAT witnesses remain valid; their freely combined words do
not constitute attested source passages.

## Source extraction and constraints

The same dated witnesses and historical normalization used in the
[regional dictionary experiments](german_regional_cycles.md) are retained.
The cached archive and XML members are checksum-verified. Separate `morph`
word divisions, distinct umlaut letters and original normalized word order
are preserved. Every extracted token frequency is checked against that
source's previously defined vocabulary extraction.

Unknown abbreviation forms, number-bearing forms, unsupported letters,
editorial insertions, headings and explicit `§` section markers interrupt
passages. Bibliography/annotation text is excluded. Ordinary punctuation,
paragraph, verse-line and page boundaries can be crossed. Windows never bridge
an interrupted run or move between sources.

All overlapping windows of exactly 22 words are scanned. The bounds require,
at every position i:

```text
plaintext_length[i] × 1 ≤ ciphertext_length[i] ≤ plaintext_length[i] × 3
```

The ciphertext is the same original words 2–23, 104 EVA characters:

```text
qopal chol cthol daimg ycheor chor dam qotcham cham ochor qocheor chol
daiin cthy schey chor chal chag cham cho qokol chololy
```

Survivors are passed to known-plaintext key recovery with their exact attested
word order, the full source dictionary alphabet, global prefix-free H2/L3
codes, no nulls and text-wide cycling. Known plaintext is the explicit
source-passage hypothesis here, rather than a hidden-plaintext recovery hint.
Used mappings necessarily emit observed substrings; a separate observed-domain
restriction is redundant for this fixed-plaintext encoding problem.

## Results

| Source | Eligible windows | Total-length compatible | Positionwise compatible | Cyclic SAT |
|---|---:|---:|---:|---:|
| 113, Kottanerin | 12,585 | 11,372 | 6 | 0 |
| 123, Swabian | 10,562 | 7,948 | 2 | 0 |
| 133, East Franconian | 12,713 | 8,654 | 0 | 0 |
| 143, Upper Saxon | 2,916 | 2,149 | 0 | 0 |
| 153, Ripuarian | 4,227 | 2,227 | 0 | 0 |
| 223, East Swabian | 3,086 | 1,254 | 0 | 0 |
| 233, Alsatian | 5,198 | 3,952 | 0 | 0 |
| 243, Hessian | 5,061 | 2,570 | 0 | 0 |
| 253, Thuringian | 10,290 | 6,838 | 0 | 0 |
| **Total** | **66,638** | **46,964** | **8** | **0** |

All eight solver checks returned UNSAT in less than 0.22 seconds each.
There are no unresolved passages and no longer solver retry is required.

## Independent repetition contradiction

With one global prefix-free key and preserved word boundaries, an observed
word has a unique decoded plaintext. Therefore equal ciphertext words require
equal plaintext words. The converse is not required: homophones may encode
the same plaintext word differently.

In this block, positions **2 and 12** both contain `chol`. Every length-compatible
source passage places different words at those positions:

| Source and zero-based start record | Plaintext at position 2 | Plaintext at position 12 |
|---|---|---|
| 113 / 3359 | lag | da |
| 113 / 3496 | gab | im |
| 113 / 3782 | kam | gen |
| 113 / 3784 | in | das |
| 113 / 3785 | den | tet |
| 113 / 10505 | nü | rüe |
| 123 / 14188 | nit | wo |
| 123 / 15664 | uf | an |

This elementary contradiction independently excludes each candidate under
any uniquely decodable global key in the current word-preserving family,
including free homophone choice. It does not require trusting the solver's
UNSAT status. The Z3 UNSAT proof certificates themselves have not been checked.
Additional conflicting repeated words are recorded in the report.

## Reproduction and artifacts

```sh
.venv/bin/python -m benchmarks.german_passages --resume
```

The runner scans all sources, validates source/configuration/input hashes,
and resumes completed passage checks without rerunning them. Alternative
source subsets and solver budgets are supported, with separate budget paths.

* `experiments/results/german-passages.json`: per-source counts, all eight
  normalized plaintexts, source locations, repetition contradictions and solver outcomes.
* `experiments/results/german-passages-validation.json`: provenance and
  repetition-certificate audit.
* `data/generated/german-passages/budget-30000ms/inputs/`: exact public
  known-plaintext requests, including source dictionaries and alphabets.

Source positions identify the normalized record range and zero-based body
`morph` ordinals, plus parts of forms split by punctuation. Editorial text is
excluded from these ordinals. XML member checksums pin the edition.

The focused suite has **53 passing cases**, covering gap/section boundaries,
word order, inclusive length bounds, the distinction between total and
positionwise compatibility, synthetic cyclic umlaut SAT controls, known
plaintext identity and the direction of the repetition implication.
