# Historically motivated contraction-capacity pilot

The small reversible inventory improves Latin's total-length capacity, but
**no attested 22-word window in these samples meets the ciphertext's
positionwise length requirements**, even with every contraction optional.
No solver is imported or called, and the cipher implementation is unchanged.

## Fixed inventory and historical support

The versioned inventory is
[`experiments/configs/latin-contractions.json`](../experiments/configs/latin-contractions.json).
Each contracted unit has a distinct label and exactly one expansion:

| Unit expansion | Application scope | Historical support |
|---|---|---|
| ae | Any occurrence | [HMML Insular transcription](https://hmmlschool.org/latin-insular-transcription/): an ae ligature, explicitly distinguished from abbreviation |
| per | Any occurrence | [HMML Carolingian transcription](https://hmmlschool.org/latin-caroline-transcription/): marked p, also used within words |
| pro | Any occurrence | [HMML Gothic transcription](https://hmmlschool.org/latin-gothic-transcription/): a distinct marked p, also used within words |
| con | Initial only | HMML Insular transcription: backwards c; restricted to initial con for this pilot |
| et | Whole word only | HMML Gothic transcription: Tironian et |
| est | Whole word only | HMML Insular transcription: a division-like whole-word sign |
| rum | Final only | HMML Gothic transcription: a 2-shaped r with a stroke marking omitted final um, modeled as one unit expanding to rum |

This combines documented medieval precedents from different periods. It is
not a reconstructed fifteenth-century abbreviation system, an exhaustive
inventory, or evidence that these conventions occur in Voynich. Within-word
rules match permitted substrings without a separate syllabification filter,
making the capacity estimate generous. A paleographic sign with a diacritic
is counted as one abstract cipher input unit, not as a claim about EVA glyphs.
The Caesar analysis is a classical-text control under this hypothetical
medieval preprocessing, not a claim about Caesar's writing practices.

`ae` becomes a dedicated `<ae>` unit, not German ä or plain e. `per` and
`pro` have different labels; `con` is not merged with `cum`. We do not use
ambiguous nasal bars or silently delete omitted letters. Different marked
units expand uniquely, and every computed tokenization is checked by
expanding it back to the original normalized spelling.

## Optional contraction semantics

Original word boundaries and spellings remain fixed. Each rule application
is optional, and overlapping occurrences cannot both consume the same letters.
Dynamic programming computes every attainable unit count per word, retaining
one expansion-verified tokenization for each count.

The minimum-unit mean distribution is the **maximum-compression envelope**,
not an observed distribution of scribal abbreviation usage. The 104/22 ceiling
now bounds cipher input units, rather than necessarily bounding the original
expanded letters. For positionwise compatibility, each word may independently
choose any attainable count k satisfying:

```text
k ≤ observed ciphertext-word length ≤ 3k
```

This does not force maximal contraction: a whole-word est unit has length one
and cannot emit four ciphertext characters under L3, but spelling out e/s/t
can meet that length. The scan retains both options. Passing this independent
length filter would still be necessary only, not a prefix-free key or cycling fit.

## Results

The source samples are unchanged from the historical length analysis:
Caesar has 20,400 windows; Aquinas 7,129; Vita Caroli IV 14,684. The pooled
medieval Latin row combines the latter two without crossing text boundaries.
Excluded headings, numbers and gaps interrupt runs.

| Source | Profile | Maximum letter saving | Median minimum-unit mean | Windows able to meet total ceiling | Positionwise compatible |
|---|---|---:|---:|---:|---:|
| Caesar | Letters | 0% | 6.00 | 1.19% | 0 |
| Caesar | ae only | 0.70% | 5.95 | 1.38% | 0 |
| Caesar | Seven units | 4.42% | 5.73 | 3.15% | 0 |
| Medieval Latin | Letters | 0% | 5.64 | 6.67% | 0 |
| Medieval Latin | ae only | 0.30% | 5.64 | 6.99% | 0 |
| Medieval Latin | Seven units | 4.15% | 5.41 | 13.31% | 0 |

Under the seven-unit profile, Aquinas reaches 20.26% total-ceiling-compatible
windows and Vita Caroli IV reaches 9.94%. Both still have zero positionwise
matches. Full P05/median/P95 distributions, integer-total histograms and
per-rule occurrence counts are in the JSON report. Savings aggregate over
all normalized tokens, while ceiling proportions aggregate over eligible
windows; the two denominators differ.

All three profiles therefore exclude the attested passages of these three
texts by necessary word-length bounds alone for this fixed Voynich block.
The result does not exclude Latin, larger documented contraction inventories,
other corpora, arbitrary dictionary combinations, or more general cipher models.

Reversible contractions also preserve the earlier repetition obstruction:
equal ciphertext words decode into equal unit sequences, whose unique
expansions must be equal original words. Ambiguous scribal expansions would
be a separate relaxation and are not tested here.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.latin_contractions
.venv/bin/python -m pytest -q \
  tests/integration/test_latin_contractions.py \
  tests/integration/test_historical_word_lengths.py
```

The focused analysis suite has **35 passing cases**, including optional
contractions, boundary scopes, overlap exclusion, expansion round trips,
preservation of source gaps and the repetition implication. Solver imports
are checked absent from the new analysis module.

Outputs are under `experiments/results/latin-contractions/`: `report.json`,
`summary.csv`, candidate artifacts for each profile/source, and `validation.json`.
All candidate files are empty because there are no positionwise survivors.
Source/inventory/code hashes make the fixed preprocessing reviewable.
