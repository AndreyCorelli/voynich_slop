# Remaining Latin passage-length failures

The diagnostic ranks every attested 22-word window by **number of incompatible
positions**, then summed distance from attainable unit counts to permitted
intervals, then source record index. It compares ordinary letters with the
fixed optional seven-unit inventory, without changing contractions or invoking
Z3. Source exclusions and text boundaries interrupt windows.

| Source | Windows | Fewest failures, letters | Fewest failures, seven units | Windows matching the exact repetition pattern |
|---|---:|---:|---:|---:|
| Caesar | 20,400 | 5 | 5 | 0 |
| Aquinas | 7,129 | 2 | 2 | 2 |
| Vita Caroli IV | 14,684 | 3 | 3 | 0 |

The seven units improve aggregate length capacity but do not reduce the best
failed-position count in these samples. Fractions are descriptive counts of
overlapping windows, not language likelihoods.

## What the closest passages need

**Caesar:** the highest-ranked seven-unit window fails on `illos` (needs one
fewer unit), `vicem` (two), `remanent` (three), `neque` (one), and `cultura`
(three). Its full normalized text is:

```text
atque illos alunt hi rursus in vicem anno post in armis sunt illi domi remanent sic neque agri cultura nec ratio atque
```

**Aquinas:** the closest window has two length failures:

```text
verum est dicere quod homo non in quantum est homo habet quod sit in hoc singulari vel in illo aut in anima
```

`dicere` at position 3 has six units but permits at most five. `singulari` at
position 16 has nine but permits at most four: it needs five units of reduction,
not merely one small ligature. Moreover, this passage conflicts at all three
repeated ciphertext pairs. For example, positions 2 and 12 contain `est` and
`quod`, while both ciphertext positions contain `chol`. Distinct reversible
expansions cannot repair that contradiction.

**Vita Caroli IV:** the closest window fails on `celestis` (one excess unit),
`verbum` (three), and `si` (one unit too short). A two-letter `si` can emit at
most six ciphertext characters under L3, but its position requires seven.
Additional contraction cannot repair this last failure because contraction
only reduces unit count. Other windows are separately ranked with all
too-short failures excluded; this example is not a claim that every window
has an irreparable short word.

## Repetition is the larger obstruction

The fixed ciphertext repeats words at pairs of positions 2/12, 6/16 and 9/19.
With a global uniquely decodable key and preserved word boundaries, each pair
requires equal original plaintext words when contraction units have unique
expansions. Only **two of 42,213 windows** across these Latin texts meet all
three equalities, both in Aquinas.

The highest-ranked repetition-compatible passage is:

```text
sicut ex forma et materia relinquitur esse substantiale quando componuntur ita ex accidente et subiecto relinquitur esse accidentale quando accidens subiecto advenit
```

Under the seven-unit profile it fails at **13 of 22 positions**, with total
unit-count distance **53**. Examples include `relinquitur` at two four-character
ciphertext positions (11 units, requiring at least seven fewer), and `accidens`
at a three-character position (eight units, requiring at least five fewer).
This is the sum of independent word-level distances, not an inferred number
of new rules or a global minimum key complexity.

Thus a few extra small reversible contractions would not rescue the closest
length-only passages: they have exact repetition contradictions. Rescuing the
best repetition-compatible passage would require extensive additional
shortening. A larger historically documented inventory remains a legitimate
separate experiment, but these results do not justify selecting arbitrary
rules to make this particular passage fit. Expanding source coverage addresses
the scarcity of repetition-compatible passages; boundary changes or ambiguous
expansions would instead change the model.

## Diagnostic artifacts and tests

```sh
.venv/bin/python -m benchmarks.latin_length_failures
.venv/bin/python -m pytest -q \
  tests/integration/test_latin_length_failures.py \
  tests/integration/test_latin_contractions.py \
  tests/integration/test_historical_word_lengths.py
```

There are **43 passing analysis tests**. Results are in
`experiments/results/latin-length-failures/report.json` and `positions.csv`.
The JSON includes complete failed-position distributions, top ten passages
per source/profile, top repetition-compatible passages, top passages without
too-short failures, and each failed word's attainable counts and required
interval. Original normalized record indices identify the source locations.

Failure categories distinguish too-long words, too-short words that additional
contraction cannot repair, and gaps in attainable counts. All optional
tokenizations are considered; maximally contracting a word never creates a
false failure when its uncontracted spelling can fit. Per-position counts
include every failure, not just the first one encountered.
