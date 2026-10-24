# German vocabulary on the fixed 22-word Voynich block

This experiment replaces the Caesar dictionary with one dated regional German
vocabulary: **Die Denkwürdigkeiten der Helene Kottanerin**, manuscript witness
dated **1445–1452**, Middle Bavarian (Vienna), text 113 in the
[Bonner Frühneuhochdeutschkorpus](https://korpora.org/FnhdC/).
The first listed period-III source is used as a single regional starting point;
its short-window distribution is not evidence that it is the manuscript language.
The corpus is used locally under the provider's research-use terms.

The dictionary contains **2,160 unique words from 14,060 normalized tokens**.
All words are retained, without frequency or ciphertext-length filtering.
The source archive is checksum-verified before parsing. The vocabulary artifact
records archive provenance, the member checksum, normalization version, token
frequencies and extraction counts.

## Orthography

The XML's actual separate `morph` word divisions are retained. Editorial
insertions, headings, bibliography and annotations are excluded. Historical
spellings such as `vnd` remain unchanged; lowercase and long-s normalization
are applied. Ligatures and documented abbreviation signs are expanded.
Numbers, unresolved abbreviation marks and unsupported letters are excluded
as whole forms, rather than guessed or partially retained.

Umlaut variants are unified: `u` with superscript `e` and `ü` become the same
letter, but **ä/ö/ü remain distinct from a/o/u** for substitution-key recovery.
Other diacritics do not add letters; thus historical `wër`, `leẅten` and `dÿ`
normalize to `wer`, `lewten` and `dy`. `ß` is represented as `ss`, consistently
with the earlier length-analysis convention; this is an explicit alphabet
choice, not a claim that it is the only possible cipher alphabet.

The resulting plaintext alphabet has **28 symbols**:

```text
a b c d e f g h i j k l m n o p q r s t u v w y z ä ö ü
```

## Matched selection comparison

Both requests use the certified original words 2–23: 22 words, 104 EVA
characters, from `qopal` to `chololy`. They preserve the previous null-free
finite/trie solver configuration, global prefix-free H2/L3 coding, word
boundaries and observed substring code domains. The baseline request hash is
checked before preparation.

The two German requests differ only in homophone selection:

* **free:** any available homophone at each occurrence;
* **text-cycle:** each plaintext letter's ordered homophone cycle continues
  across the whole text.

Relative to the Latin experiment, both the dictionary and its plaintext
alphabet necessarily change. Dictionary sizes also differ: 2,160 versus
5,658. There are no supplied plaintext words, word lengths, code keys or other
hidden hints. Public length/prefix candidate pruning is recorded in the report.
Vocabulary membership alone does not require grammatical German or corpus
word order; the model is the same finite-word hypothesis used for Latin.

## Execution and artifacts

The recorded 30-second probes both returned **UNKNOWN**: free selection in
30.09 solver seconds, text-wide cycling in 30.08 seconds. These outcomes do
not distinguish the selection policies. The next recommended longer retry
is free selection, which tests the more permissive model first.

Run or resume the two 30-second checks:

```sh
.venv/bin/python -m benchmarks.german_selection --resume
```

Prepare requests without solving:

```sh
.venv/bin/python -m benchmarks.german_selection --prepare-only --resume
```

The report is `experiments/results/german-selection.json`; vocabulary and
public requests are in `data/generated/german-selection/`. Completed rows are
checkpointed; resume checks source/configuration/request hashes and
independently re-verifies any SAT witness.

Long individual retries, without keeping the assistant waiting:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-selection/inputs/free.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-selection-free-30min.json
```

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-selection/inputs/text-cycle.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-selection-text-cycle-30min.json
```

UNKNOWN leaves feasibility unresolved. SAT witnesses must pass independent
dictionary, encoding, decoding, prefix-free key and selection verification.
UNSAT excludes only this finite vocabulary and exact cipher configuration;
it would not exclude German generally.

The focused regression suite contains 36 passing cases, including verified
synthetic umlaut controls under free and text-wide cyclic selection, historical
normalization, unchanged cipher parameters, and the existing length-analysis
and selection-comparison checks.

## Verified longer free-selection result

The user-run retry returned **SAT in 446.27 solver seconds**. A separate
audit matched the prepared request except for timeout, checked the request
and vocabulary hashes, and independently verified dictionary membership,
global prefix-free key legality, H2/L3 bounds, re-encoding, decoding and
membership of every emitted code in the observed substring pool. The audit
is `experiments/results/german-selection-free-validation.json`.

Its plaintext is:

```text
rot and and slüg rait and sy rab ab vnd rait and slüg ab si and am am ab an red ander
```

This is a dictionary fit, not an established grammatical passage. It has
64 plaintext letters, mean word length 2.91, median 3, eight words of at most
two letters, and character expansion 104/64 = 1.625. The Latin free-choice
witness had 49 letters, mean 2.23 and 17 words of at most two letters.
The German fit is less dominated by short words, but remains at the minimum
window mean observed in the Kottanerin length sample: only 4 of its 12,585
overlapping windows have means this low (0.032%). This is descriptive;
the solver was not asked to maximize plaintext length or naturalness.

The witness with its saved homophone ordering does not obey text-wide
cycling. That does not exclude other German keys, homophone orders or
plaintexts under cycling. The subsequent cyclic retry returned UNSAT.

## Longer text-cycle result

The user-run text-wide cyclic retry returned **UNSAT in 229.95 solver
seconds**. Its request matches the prepared cyclic input except for timeout,
and matches the free-selection request except for selection. Input and
vocabulary hashes were rechecked. The audit is
`experiments/results/german-selection-text-cycle-validation.json`.
This is a request/provenance audit, not an independent UNSAT proof check;
`verified=False` means there is no verified SAT witness.

| Vocabulary | Free selection | Text-wide cycling |
|---|---|---|
| Corrected Caesar plus i/iv/iulius, 5,658 words | Verified SAT, 321.07s | UNSAT, 232.50s |
| Kottanerin German, 2,160 words | Verified SAT, 446.27s | UNSAT, 229.95s |

Both finite vocabularies fit this block with free selection, and both fail
with text-wide cycling. Changing to this German dictionary does not remove
the cyclic obstruction. These outcomes exclude neither German nor Latin
generally and do not measure relative language plausibility.

The [regional cyclic probes](german_regional_cycles.md) now prepare and test
the other eight dated regional vocabularies individually, addressing the
single-source coverage limitation while preserving cipher rules and regional
spelling. If all are UNSAT, a separately labeled pooled dictionary could test
whether mixing their word inventories removes the obstruction.
