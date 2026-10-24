# One EVA tokenization sensitivity

This fixed comparison groups `ch`, `sh`, `cth`, `ckh`, `cph`, and `cfh` as
single ciphertext units, using longest matches within each word. All other
characters, including `qo` and `iin`, remain separate. Raw transcription and
word boundaries are unchanged, and concatenating the units exactly restores
each original word.

The [Zandbergen–Landini transcription reference](https://www.voynich.nu/transcr.html)
lists ch/sh and benched-gallows shapes separately in its historical alphabet
comparison (Table 1). Its EVA discussion explains that analysts must choose
which combinations to treat as units. This motivates one limited sensitivity
inventory; it does not establish semantic units or constitute a full Currier
conversion. The primary source was checked on 2026-10-09. No other alternative
inventory was tried.

## Fixed-block consequences

The same 22-word block used in the historical length analysis changes from
**104 atomic EVA characters to 85 grouped units**. With at least one output
unit per plaintext input unit, its mean ceiling changes from **4.727 to 3.864**.
If reversible plaintext contractions are allowed, this bounds input units
rather than expanded letters. The ciphertext equality pattern is unchanged:
the grouping is deterministic and reversible.

Holding L1–3 fixed now means 1–3 **grouped units**, which can represent more
than three EVA characters. This is a different bounded cipher family, not a
mere renaming of old keys. Grouping can repair a word that previously needed
more than three output characters per letter, but also makes the upper bound
on plaintext unit counts stricter. Existing SAT/UNSAT solver results are not
automatically transferable; grouping may cross old codeword boundaries.

## Passage screen

The paired scan uses the cached historical corpora with their existing source
normalization, barriers and segmentation. Corpus mean-length distributions
are unchanged; the table compares the counts beneath the two ceilings.

| Sample | 22-word windows | Total letter count ≤104 | Total letter count ≤85 | Length-compatible, grouped | Length + repeats, grouped |
| --- | --- | --- | --- | --- | --- |
| Caesar | 20,400 | 242 | 0 | 0 | 0 |
| Six medieval Latin works | 80,024 | 3,717 | 196 | 0 | 0 |
| Nine 15th-c. German varieties | 66,638 | 46,964 | 6,631 | 0 | 0 |
| Medieval Italian | 13,895 | 8,127 | 936 | 0 | 0 |
| Old Czech, diplomatic | 1,403 | 607 | 40 | 0 | 0 |

German source 113 had six atomic-EVA length survivors and source 123 had two;
both fall to zero. Their repetition filters already excluded those passages.
German streams here retain **legacy historical-length normalization**, including
known bracket-fragment limitations. They are not the corrected solver
vocabularies; paired sensitivity counts must not be presented as a fresh
lexical audit. Source-separated metrics and this caveat are recorded in JSON.

Caesar and all six medieval Latin sources were also screened with the existing
seven reversible contractions. Those grouped scans likewise have zero
positionwise survivors. All 25 source/profile rows retain the same repetition
counts between tokenizations, as required by reversible grouping.

These are necessary passage constraints, not SAT results, language rankings
or an exhaustive corpus search. They exclude the scanned attested passages
under the stated boundaries and expansion limits; arbitrary dictionary
combinations remain a separate question. The scan does not establish which
token inventory corresponds to the manuscript's encoding units.

## Reproduction and stopping point

```sh
.venv/bin/python -m benchmarks.eva_tokenization
.venv/bin/python -m pytest -q \
  tests/integration/test_eva_tokenization.py \
  tests/integration/test_historical_word_lengths.py
```

All **21 focused tests pass**. The report, complete unit-count histograms,
tokenized ciphertext, source manifests and hashes are saved under
`experiments/results/eva-tokenization/`. No dependencies or corpora were
downloaded, no raw data was edited, and no solver was called.

This completes the agreed cheap one-inventory comparison. Do not add further
groupings in response to the result. If this branch is revisited, its next
distinct question is dictionary compatibility with a grouped-unit encoder,
which first requires its own synthetic calibration and an explicit comparison
of code-length conventions. Passage scans alone do not justify another long run.
