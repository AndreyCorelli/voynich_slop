# Natural-text Latin and Swabian calibration

All four positive hidden-word fits are verified SAT, recover every one of their
24 training words, and predict all six novel held-out words exactly. The four
known-word fits also recover/predict correctly. All four paired randomized
controls return UNSAT. No timeout occurs under the fixed five-second solver limit.

| Source / generating profile | Known-word solver | Hidden-word solver | Hidden training exact | Novel held-out exact | Paired shuffle |
|---|---:|---:|---:|---:|---|
| Caesar / length two | 0.097 s | 1.161 s | 24/24 | 6/6 | UNSAT, 1.027 s |
| Caesar / lengths 1/2/3 | 0.106 s | 0.962 s | 24/24 | 6/6 | UNSAT, 0.318 s |
| Swabian 123 / length two | 0.087 s | 1.049 s | 24/24 | 6/6 | UNSAT, 1.123 s |
| Swabian 123 / lengths 1/2/3 | 0.090 s | 1.080 s | 24/24 | 6/6 | UNSAT, 0.875 s |

Construction is 0.33–0.98 seconds per fit. The hidden positive arms collectively
have 24/24 exact held-out occurrences, but they reuse two passages under two keys,
so these are not 24 independent language observations. First-key success also
does not prove all compatible keys would predict correctly.

## Real contiguous passages

The cached normalized Caesar corpus and corrected German source 123 XML stream
are used without downloading new data. Selection begins at each stream midpoint
and chooses the first contiguous 24+6 eligible records. Every word must belong to
the existing corrected source dictionary; exclusions/empty records are barriers,
not silently skipped words. At least three distinct held-out types must be novel,
and every held-out letter must occur in training. No solver or score enters this
selection. Both selected blocks happen to have six distinct novel held-out types.
The source indices, raw/normalized metadata and source/normalization code hashes
are preserved. These are contiguous normalized word streams, not filtered
short-word projections or repetitions engineered from a fixed vocabulary.

Caesar records 10254–10283 (training ends at 10277):

> rei student sed quicquid possunt pedestribus valent copiis quo facilius finitimorum equitatum si praedandi causa ad eos venissent impedirent teneris arboribus incisis atque inflexis

Immediate held-out words:

> crebrisque in latitudinem ramis enatis et

Swabian 123 normalized records 9097–9126 (training ends at 9120):

> er yn her kombt als ob er joch etwas gar gross tuon wöll und zeletst sagt er von dreien tagen darby du dess inbrünstigen

Immediate held-out words:

> buolhertz oder des hurübels irrsal mercken

The original cached normalization is retained, including its treatment of
historical orthography. No new linguistic normalization claim is made. Alphabet
sizes are 19 for this Latin passage and 24 for this Swabian passage. These alphabet
sizes differ; results are within-source model checks, not a matched comparison
of language difficulty.

## Assisted, frozen protocol

Each source has a 64-word dictionary containing the union of training and held-out
spellings, then filled with first distinct corpus words using only that passage's
alphabet. This is explicit oracle-assisted vocabulary/alphabet construction.
The true words are guaranteed present; hidden recovery still must choose their
identities from the dictionary. This is not unrestricted language identification
or a blind out-of-corpus vocabulary test. Structural passage selection also sees
held-out plaintext to ensure novel/code-covered evaluation, so it is not a fully
blind holdout design.

For each passage, generating seed 4501 creates one length-two key and one
prefix-free mixed length-1/2/3 key, with all those lengths exercised in training.
Each recovered model permits H1 L1–3, free selection, flat membership with equality
reuse and observed code domains. The generating profile is not supplied as a
constraint. The known-word arm receives training plaintext only, keeping the key,
individual code lengths and segmentation hidden. The hidden-word arm receives
only the public training request, with identities and lengths hidden. Neither
receives continuation constraints, statistical guidance or generating key data.

A paired typewise glyph shuffle with seed 4502 preserves all word lengths,
per-word glyph multisets and the full equality partition across train/holdout.
Shuffling sees held-out ciphertext only to preserve that partition. The randomized
solver receives training ciphertext only. No generating-key or solver criterion
selects shuffles; bounded unavailable cases would be preserved without tuning.
Controls are not assumed impossible under the model. Their UNSAT results apply
to their bounded changed inputs, and are solver-reported without independent
proof certificates. They receive no continuation score because no SAT key exists.

Four positives and four controls were frozen before the twelve fits. Each fit
retains a configured five-second solver timeout; construction is reported
separately. Completed arms checkpoint and skip on resume. Old synthetic results
remain preserved. This differs from earlier natural 30+22 full-vocabulary H2
controls and projected short-word fixtures: it uses contiguous mid-corpus passages,
H1, genuinely varied generating lengths and assisted 64-word vocabulary.

Two focused tests pass, checking contiguous selection, barriers and coverage
requirements, solver-input isolation, matched budgets, frozen passage metadata,
unscored UNKNOWN and checkpoint reuse. Actual artifact validation passed for all
twelve arms, reconstructing source selection/dictionaries and randomized controls,
checking full witnesses and known identities, and recomputing frozen predictions.

Artifacts: `experiments/results/natural-passage-calibration/`.

```sh
.venv/bin/python -m benchmarks.natural_passage_calibration --validate
```

## Where this points

The method can recover predictive keys from genuine contiguous normalized text
at this assisted scale, with and without varied code lengths. That is more useful
calibration than SAT on repeated-word fixtures alone. It does not establish
reliability for larger vocabularies, unseen texts, full alphabets, other ciphers
or Voynich. Only one passage per language, one generating seed and one shuffle
seed are included, with substantial structural assistance in construction.

Next priority: freeze a small set of additional nonoverlapping passages per
language under the same rules and budgets, retaining the known-word and randomized
control arms. Replicate recoverability and discrimination before another
vocabulary expansion or manuscript sweep. Any future unassisted vocabulary test
must build its dictionary independently of held-out plaintext.
