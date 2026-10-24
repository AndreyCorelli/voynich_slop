# Plaintext word-length plausibility

The verified free-selection witness fits the finite dictionary, but its word
lengths differ sharply from the source corpus. This diagnostic compares it with
all **20,400 uninterrupted 22-word passages** in the footer-free Caesar corpus.
Excluded records interrupt passages; the scan never silently bridges them.
Overlapping passages are descriptive observations, not independent trials.

| Metric | Verified witness | Caesar passage median | Caesar passage range |
|---|---:|---:|---:|
| Mean word length | 2.23 | 6.00 | 3.91–8.09 |
| Median word length | 2 | 6 | 3–9 |
| Words of length at most 2 | 17 of 22 | 3 of 22 | 0–10 |

None of the passages has mean or median as low as this witness, or as many
one-/two-letter words. The witness uses 49 plaintext letters to produce 104
ciphertext EVA characters: expansion is 2.12×. These counts describe one
witness, not an optimal or necessary word-length distribution across all fits.

There is also a model-wide constraint. A plaintext letter emits at least one
EVA character, and spaces are preserved. Therefore any possible fit for this
block has at most 104 plaintext letters, an average of **4.73 per word**, and
a median no higher than **4.5**. With the maximum code length of three, it has
at least 45 letters. These are necessary length bounds, independent of the
key, homophone choices or cycle rule.

Only **242 of 20,400 passages (1.19%)** have a total length within these bounds.
**None** is compatible with all observed word lengths in their actual order,
even before requiring a common key. This excludes literal encoding of those
particular observed Caesar passages under the current assumptions. It does not
exclude unseen Latin passages or all passages having similar aggregate lengths.

The fifth percentile of Caesar passage mean lengths is **5.09**, corresponding
to 112 letters in 22 words. If we choose that as a lower plausibility threshold,
it already exceeds the ciphertext's absolute 104-letter plaintext capacity.
Such a constraint would make the model UNSAT by arithmetic, without a solver.
It is a corpus-based criterion we would choose, not a universal Latin law.

This suggests revisiting the source-language/encoding assumptions before
measuring cycle exceptions. The shortness is partly structural: even allowing
all codes to have length one cannot reach the typical Caesar passage mean;
verbose expansion narrows the capacity further. More dictionary entries alone
do not remove the capacity bound. Alternatives worth evaluating include other
Latin text genres, abbreviations or plaintext units representing more than one
letter, and different word-boundary assumptions. These would be explicit model
changes and are not implemented by this diagnostic.

Run the reproducible analysis:

```sh
.venv/bin/python -m benchmarks.word_length_plausibility
```

Report: `experiments/results/word-length-plausibility.json`. It records corpus,
witness and request hashes, full witness length vectors, empirical quantiles,
tail counts, total and positional compatibility, and the extremal passages'
source record locations. The saved SAT witness and input checksum are checked.
No solver constraint or historical result is changed. EVA character counts do
not necessarily equal manuscript glyph counts.
