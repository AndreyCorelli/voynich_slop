# Text-wide cycling across eight further German vocabularies

The Kottanerin dictionary admitted a verified free-selection fit but returned
UNSAT under text-wide cycling. This experiment checks whether that cyclic
obstruction persists in the other eight dated German witnesses, separately.

The cipher settings are unchanged: original Voynich words 2–23, 22 words and
104 EVA characters, globally prefix-free H2/L3 codes, no nulls, finite/trie
dictionary recovery and observed substring code domains. Only the vocabulary,
its alphabet and the solver budget change. There are no plaintext or key hints,
frequency filters, modern spelling replacements or pooled dictionaries.

## Vocabularies

| Source | Witness date | Region | Unique words | Normalized tokens |
|---|---|---|---:|---:|
| 123, Neidhart | 1486 | Swabian, Ulm | 3,191 | 17,662 |
| 133, Pillenreuth | 1463 | East Franconian, Nuremberg | 2,425 | 12,833 |
| 143, Tauler edition | 1498 | Upper Saxon, Leipzig | 2,261 | 11,737 |
| 153, Koelhoff | 1499 | Ripuarian, Cologne | 2,625 | 10,937 |
| 223, Burlaeus edition | 1490 | East Swabian, Augsburg | 2,764 | 11,343 |
| 233, Brunschwig | 1497 | Alsatian, Strasbourg | 3,141 | 17,214 |
| 243, Wonnecke | 1485 | Hessian, Mainz | 2,210 | 14,340 |
| 253, Rothe witness | Later 15th century | Thuringian, Eisenach | 2,562 | 12,384 |

Sources are XML members of the cached, checksum-verified
[Bonner Frühneuhochdeutschkorpus](https://korpora.org/FnhdC/) release.
Dates describe the witnesses/editions, not necessarily the original
compositions. Text 213 remains excluded because its additions extend to 1530.
The corpus and derived vocabularies remain local research artifacts.

Normalization matches the [initial German experiment](german_selection.md):
actual separate `morph` word divisions, historical spelling, long s to s,
distinct ä/ö/ü, ß to ss, and expansion of documented abbreviation marks.
Unresolved abbreviations, unsupported forms, numbers and editorial text are
excluded. Per-source exclusion counts and token frequencies are saved in the
vocabulary artifacts; a finite source dictionary is not a complete inventory
of that regional variety. The generalized builder reproduces the existing
Kottanerin vocabulary exactly, including its artifact hash.

## Execution

Run/resume the short 30-second probes:

```sh
.venv/bin/python -m benchmarks.german_regional_cycles --resume
```

Prepare without solving:

```sh
.venv/bin/python -m benchmarks.german_regional_cycles --prepare-only --resume
```

Reproduce/resume the seven-source longer batch (now completed):

```sh
.venv/bin/python -m benchmarks.german_regional_cycles \
  --sources 123 133 143 153 223 233 243 \
  --timeout-ms 1800000 --resume
```

Sources can be selected explicitly with `--sources 123 133`, for example,
to retry only unresolved cases. The default short report is
`experiments/results/german-regional-cycles.json`; the longer command writes
`experiments/results/german-regional-cycles-1800000ms.json`. Each budget has
separate public request paths, so longer preparation does not overwrite the
short requests. Common vocabulary artifacts are under
`data/generated/german-regional-cycles/vocabularies/`.

Runs are sequential and checkpoint after each source. Seven 30-minute solver
budgets can total three and a half hours, plus formula construction. Resume checks source,
code, request and environment hashes, skips completed rows, and independently
re-verifies SAT witnesses. An interrupted source starts again; completed
UNKNOWN rows are also skipped on resume. To increase the budget, use a new
budget/report rather than resume the same completed attempt.

UNKNOWN leaves feasibility unresolved. UNSAT applies only to the particular
finite dictionary and cipher model, not German generally. SAT demonstrates
dictionary compatibility, not grammatical prose or language identification.

The focused suite has 45 passing cases, covering unchanged Kottanerin
extraction, source isolation, budget separation, checkpoint resume, rejection
of tampered cached requests, historical normalization and synthetic controls.

## Recorded short results

| Source | Result | Solver seconds |
|---|---|---:|
| 123, Swabian | UNKNOWN | 30.11 |
| 133, East Franconian | UNKNOWN | 30.09 |
| 143, Upper Saxon | UNKNOWN | 30.09 |
| 153, Ripuarian | UNKNOWN | 30.08 |
| 223, East Swabian | UNKNOWN | 30.09 |
| 233, Alsatian | UNKNOWN | 30.10 |
| 243, Hessian | UNKNOWN | 30.10 |
| 253, Thuringian | UNSAT | 16.03 |

Thuringian joins Kottanerin as a finite dictionary excluded by text-wide
cycling on this block. The other seven remain unresolved; this is not an
all-German UNSAT result. No pooled dictionary is tested at this stage.

All eight input and vocabulary hashes were checked, and checkpoint resume
completed without rerunning solved rows. UNSAT is solver-reported; an independent
proof certificate has not been checked.

## Recorded longer results

The user-run 30-minute retries completed all seven cases:

| Source | Result | Solver seconds | SAT mean word length | Words of length ≤2 |
|---|---|---:|---:|---:|
| 123, Swabian | Verified SAT | 757.67 | 2.36 | 15 |
| 133, East Franconian | Verified SAT | 418.57 | 2.27 | 16 |
| 143, Upper Saxon | Verified SAT | 186.93 | 2.18 | 17 |
| 153, Ripuarian | Verified SAT | 356.70 | 2.23 | 16 |
| 223, East Swabian | UNSAT | 223.23 | — | — |
| 233, Alsatian | Verified SAT | 626.60 | 2.55 | 11 |
| 243, Hessian | UNSAT | 62.02 | — | — |

Every saved request matches its prepared input and short-run request except
for timeout. Archive/member-derived vocabulary hashes, request hashes and
the fixed baseline were checked. All five SAT witnesses were independently
verified for global prefix-free keys, H2/L3 bounds, dictionary membership,
encoding, decoding, text-wide cycling and actual emitted codes in the
observed substring pool. The audit, full plaintexts and length statistics
are in `experiments/results/german-regional-cycles-30min-validation.json`.
UNSAT outcomes remain solver-reported, without independent proof checking.

```text
123: zu in ch vol der ir vom zuom am tü zyt in volg ch by ir an as am i ze ins
133: lib ob hy jr nit on jm kam am zw hut ob jr hy sun on ab al am o ze oben
143: jch on zu im we ob ir jst yr dz jst on ich zu da ob yn ym yr o ja one
153: vil an jt dir rc as du vmb ys zo vmb an doe jt zu as yn yr ys a vp ane
233: alt dün din jch os düm o ach du yr ader dün jst du im düm dz dz du dü al düne
```

Across the nine regional dictionaries, text-wide cycling now has five verified
SAT fits and four UNSAT outcomes (113, 223, 243 and 253). The obstruction
found for Caesar and Kottanerin does not persist across all sampled German
vocabularies. This does not identify the manuscript language or establish
grammatical plaintext: the recovered word sequences are dictionary fits.

All five SAT means are below every eligible 22-word window mean in their
respective historical source samples (zero windows at or below each witness
mean). Overlapping-window statistics are descriptive, not language likelihoods;
the solver was not asked to maximize plaintext length or naturalness.

The subsequent [attested-passage check](german_passages.md) tests actual
contiguous 22-word source passages. Of 66,638 windows, eight pass the
positionwise length filter, and all eight are UNSAT. Each also contradicts
the requirement that equal ciphertext words decode equally. This stricter
source-passage hypothesis fails for these samples while the five unrestricted
dictionary SAT witnesses remain valid.
