# Natural calibration with unseeded vocabulary

All four encrypted fixtures return UNSAT. Paired shuffles yield three UNSAT
and one UNKNOWN (Swabian fixed-two shuffle, 60.042 seconds). No SAT keys exist
to score. Positive solver times range from 11.552 to 49.685 seconds. Two tests
and eight-case artifact validation pass. These results must be read alongside
the pre-solve coverage failures below, not as rejection of real encryption.

The independently built 256-word dictionaries exclude the true explanation on
both new passages before solving: Latin misses 17/24 training occurrences, and
Swabian misses 10/24. The fixed model allows only one unknown occurrence.
There are therefore zero admitted generating explanations on which to measure
true-key recovery. This is a vocabulary coverage failure, not evidence against
the languages or cipher family.

| Source | New contiguous records, inclusive | Training included | Training missing | Held-out dictionary members |
|---|---|---:|---:|---:|
| Caesar Latin | 10357–10386 | 7/24 | 17/24 | 1/6 |
| Swabian 123 | 9284–9313 | 14/24 | 10/24 | 2/6 |

Missing types each occur once in these passages. No true training word violates
the public dictionary-derived maximum length; membership coverage alone excludes
the generating explanation.

## Frozen selection

Each language uses its established full-source normalized alphabet. Select the
first 256 distinct eligible words in the source's first half, in record order,
without reserving any true training or held-out word. Eligibility uses the existing
corrected full-source inventory and normalization. Vocabulary provenance lies in
a disjoint earlier record range, but this remains same-source calibration, not an
external corpus or genre test. This corpus-order vocabulary is not asserted to be
a representative or optimized Latin/German lexicon.

Select the first eligible contiguous 24+6 block after that source's last original
replication passage. Keep the existing structural novelty and letter-coverage
selection rules; do not choose a different block after seeing vocabulary coverage.
No records are skipped within a selected block. Coverage is audited before solving.
All eight requests are frozen: two profiles per language and paired typewise
shuffles. Profiles are fixed-two and mixed-one-two-three; key seed 4501, shuffle
seed 4502. H1 L1–3, free selection, one unknown occurrence and 60-second budgets
remain fixed. There are no retries or additional cases; construction time is extra.

Generating encoders are checked for cipher correctness under an augmented
verification dictionary, explicitly separate from legal model admission. For an
admitted generating explanation the one-OOV verifier would also run. Missing
vocabulary is not provided as a recovery hint. SAT would be a possible alternative
explanation and would receive frozen exact continuation scoring; UNSAT would not
refute real encryption. Controls receive compatibility scoring only. UNKNOWN
remains unresolved and UNSAT is solver-reported without proof certificates.

```sh
.venv/bin/python -m benchmarks.unseeded_vocabulary_calibration --run
.venv/bin/python -m benchmarks.unseeded_vocabulary_calibration --validate
```

Artifacts: `experiments/results/unseeded-vocabulary-calibration/` saves source/code
hashes, disjoint vocabulary provenance, passage records, coverage audits, generating
cipher witnesses, shuffles, checkpointed results and validation. Completed cases
skip on resume. Two tests check prefix-only dictionary construction, occurrence
coverage counting, fixed solver inputs/budget, resume and unscored non-SAT handling.
Validation reconstructs dictionary, selection, coverage and shuffles, verifies SAT
witnesses and recomputes frozen scores.

The next useful step is a coverage study of independently built, larger or
frequency-selected vocabularies before more recovery runs. Raising the OOV budget
from one to ten/seventeen would greatly weaken the language constraint and should
not be used to rescue this particular test after seeing its failures. No manuscript
language conclusion or population false-fit estimate follows.
