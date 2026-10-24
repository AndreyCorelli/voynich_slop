# Contraction-aware hidden recovery: seven bounded stages

The method can recover useful contraction keys in the simplest synthetic cases,
but this experiment does **not** clear the mixed-width hidden-boundary gate or
show a reliable advantage over letters-only recovery. Independent-source
prediction degrades mainly because new contraction signs have not been observed
in training. A covered whole-word sign is also ambiguous in one recovered key.
No manuscript experiment follows from these results.

## Frozen method

Use the existing 27-rule `broader-core` inventory without changing any expansion,
position, context restriction or retained graphic-unit cost. Ambiguous nasal
profiles and the optimistic one-unit envelope are excluded. Each contraction
with cost two or three becomes exactly two or three distinct abstract units.
Their fixed expansions concatenate back to the original spelling. These labels
preserve capacity costs but are **not a transcription of actual historical
marks**; distinct part labels add alphabet complexity. This is a reversible
abstract cipher calibration, not a claim about medieval sign shapes or usage.

Dictionary paths include every optional, nonoverlapping contraction alternative
and the unabbreviated word. A 4,096-variant ceiling raises an error instead of
silently pruning paths. Generation deterministically chooses a minimum-unit
path; homophone choices are independently random. Thus contraction use itself is
maximal/deterministic, not a fitted historical frequency of abbreviation.

Freeze three contiguous natural Latin excerpts: the first eligible 32 training
words and immediate eight held-out words at the midpoint of each source's
largest preserved segment. Excluded-token barriers are respected. There is no
coverage-based passage replacement. The dictionary contains the reference
half's top 64 forms plus distinct training forms; held-out words are neither
reserved nor injected. **The vocabulary is training-assisted**, although the
solver sees no plaintext, key, source positions, true lengths or internal
boundaries in hidden arms. Training spellings can therefore always be expressed;
held-out decoding is allowed to recover forms absent from the dictionary.

Each first returned key is frozen before continuation scoring. There is no
frequency reranking, key repair or alternative-key search. A typewise shuffle
of the full positive ciphertext preserves word lengths, glyph counts, per-word
multisets and repeated-word identity; then split into training/continuation.
Shuffle outcomes are measured, not assumed negative. The two arms use the same
source excerpt and language-model construction rule, but have different token
alphabets and sampled code assignments. This is not a paired identical-codebook
comparison, and mixed-width emission proportions need not match.

Every fit has a 5,000 ms solver budget and 45-second worker wall limit, including
construction. One-glyph outputs use a sufficiently large alphabet and reveal
internal boundaries trivially; they are diagnostics, not manuscript-compatible
homophonic mechanisms. Mixed outputs use a 24-symbol prefix-free code tree with
both one- and two-glyph codes, H<=2 and free selection. No nulls or spacing edits.

## Plan, run, assessment

| Stage | Question / change | Contraction arm exact continuation | Letters arm exact continuation | Assessment |
| --- | --- | --- | --- | --- |
| 1 | Audit all core rule costs, complete optional paths and generating round trips | No recovery solve | No recovery solve | Reversible fixtures pass; proceed to simplest diagnostic |
| 2 | Caesar, H1, one-glyph outputs, hidden key/words | 6/8 | 7/8 | All six generating-code-covered contraction words recovered |
| 3 | Same Caesar, H2, one-glyph outputs, free choices | 6/8 | 6/8 | Meets preset exploratory replication threshold; all six covered words recovered |
| 4 | Same Caesar, H2, mixed widths 1–2, hidden boundaries | UNKNOWN | 6/8 | Main contraction gate unresolved; diagnose boundaries separately |
| 5 | Same mixed fixtures, explicitly revealed generating boundaries | 6/8 | 6/8 | Oracle succeeds; boundary search contributes to difficulty, not a hidden-arm success |
| 6 | Independent Aquinas, H2 one-glyph family selected from hidden Caesar arms | 3/8 | 6/8 | Four contraction words covered; three correct, one whole-word-sign ambiguity |
| 7 | Independent Einhard, same frozen selected family | 2/8 | 7/8 | Only two contraction words covered; both recovered; source replication is weak overall |

All reported exact words are also novel ciphertext words relative to their
respective training input. Family selection was preset to choose the most
complex hidden Caesar arm with >=6/8 exact and >=4 novel exact predictions.
Oracle success was ineligible. H2 one-glyph outputs were selected; no budgets or
rules changed after observing results. This exploratory threshold is not a claim
of reliable complete recovery, and the independent replications do not meet it.

All five shuffled training controls returned UNSAT. No fitted shuffle key was
available for continuation scoring; these are solver-reported rejections of
these five finite problems, not an estimated population false-positive rate or
independent UNSAT proof certificates. Across the 17 fits: eleven verified SAT,
five UNSAT, one UNKNOWN. No worker wall timeout occurred. The UNKNOWN remains
unresolved rather than evidence against contractions.

## Coverage, ambiguity and shortening

On the three natural H2 one-glyph positives, contraction recovery obtains
**11/24 exact words**, compared with **19/24** for letters. Generating-code
coverage is 12/24 versus 19/24; correct recovery among the covered words is
11/12 versus 19/19. Coverage masks are truth-assisted diagnoses applied after
fitting, not solver inputs or a replacement for reporting the full denominator.

- Caesar's held-out `interiectis` introduces the `<ter>` contraction absent from
  training; `hae` also lacks a selected generating-code observation.
- Aquinas introduces whole-word `et` and the two-unit `sed` contraction in
  continuation. Its covered `est` is decoded as `etiam` by the returned key.
  Both whole-word signs are dictionary-compatible explanations of a short code;
  knowing a code occurred does not establish its correct ownership.
- Einhard's continuation introduces initial `con`, whole-word `et` and final
  `us` after `b`; these signs were absent from training even though corresponding
  ordinary letters occurred. The solver cannot infer their unused mappings
  reliably from the held-out text it never saw.

Training contractions reduce 210 letters to 198 units in Caesar (5.7%),
176 to 158 in Aquinas (10.2%), and 194 to 175 in Einhard (9.8%). The H2 one-glyph
cipher means are respectively 6.19, 4.94 and 5.47 glyphs/word. The mixed Caesar
contraction ciphertext averages 11.75, versus 11.13 for the separately sampled
letters key: expansion can outweigh abbreviation, and fewer plaintext units
alone do not guarantee shorter ciphertext under different keys. This experiment
does not resolve manuscript-length or word-boundary compatibility.

These outcomes expose an observation-cost tradeoff: contractions shorten
plaintext but introduce rarer units that need their own mapping evidence. They
do not exclude contraction-based Latin encryption. Successful diagnostic fits
also do not establish natural prose identification or historical probability.

## Verification and preserved corrections

Six new focused tests plus four existing complete-contraction tests pass.
Independent forward enumeration checks all 361 fixture dictionary/held-out paths
and their minima against the prior retained-cost calculation. Validation
regenerates all twelve paired fixtures, independently checks 88 held-out word
decodings, and verifies all eleven returned SAT witnesses by re-encoding.
Source, inventory, public-input and implementation hashes are recorded.

The initial oracle input stored code lengths instead of the API's cumulative
offsets and was rejected before solving. A separately hash-pinned adapter fixes
only that representation; rejected input and completed earlier stages remain
intact. Independent validation also normalizes list/tuple representation for
ciphertext novelty checks, preserving the original outputs and writing corrected
metadata separately. Exact scores and family selection are unchanged. Use the
adapter launcher for resuming, and `summary.json` / `evaluations-corrected.json`
for analyzed results.

```sh
.venv/bin/python -m benchmarks.contraction_hidden_calibration_run
.venv/bin/python -m benchmarks.contraction_hidden_validation
.venv/bin/python -m pytest -q tests/integration/test_contraction_hidden_calibration.py \
  tests/integration/test_complete_contractions.py
```

Artifacts: `experiments/results/contraction-hidden-calibration/`, including
frozen preparation, seven plans and assessments, public worker inputs, truth
fixtures, raw results, adapter provenance, corrected predictions and validation.
The launcher resumes saved stages without rerunning them. No Voynich solves,
corpus downloads, library installations or historical-rule additions occurred.

## Next decision

Do not widen the inventory or increase timeout budgets yet. The useful next
check is a separately labeled **coverage-controlled contraction calibration**:
arrange training to observe both homophones of each tested sign, retain unseen
continuation word types, and test whether valid alternatives still misidentify
whole-word signs. Such engineered coverage is a diagnostic, not blind natural
passage recovery. If that passes, return to a genuinely hidden mixed-width
replication; if ambiguity persists, more search time cannot by itself identify
the generating plaintext. Seven stages stop here.
