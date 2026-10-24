# Coverage-controlled contraction calibration

Giving training both homophones of every held-out contraction unit substantially
improves recovery, but does not identify the generating key uniquely. Across
three revisited one-glyph fixtures, first-key exact continuation rises from
11/24 in the earlier natural-training experiment to **21/24** here. A fresh
Caroli mixed-width hidden-boundary fixture recovers **7/8**, including all seven
novel plaintext word types, within the unchanged five-second solver budget.

External unigram ranking changes some keys but improves **none** of the four
continuations. Verified alternative assignments and independently inspected
homophone grouping explain residual failures. These are synthetic method
results under engineered coverage, not manuscript-language evidence.

## Fixed protocol and scope

Retain the previous 27-rule unambiguous core, complete optional tokenizations,
position/context restrictions and two-/three-unit contraction costs. No nasal
rules or new abbreviations. Multi-unit signs remain distinct abstract expansion
parts, not a representation of physical historical marks. Generation uses the
minimum-unit path. The older experiment and its artifacts remain unchanged.

Reuse the original Caesar/Aquinas/Einhard 32+8 contiguous excerpts. Add one
preselected Caroli excerpt using the same midpoint/barrier-preserving rule.
For each source, append at most sixteen short reference-half word tokens until
every contracted unit appearing in its continuation occurs at least twice in
training. Carrier selection prefers forms outside the continuation set, then
shorter unit paths, higher reference frequency and spelling order. There is no
solver-based passage selection, carrier replacement or vocabulary tuning.

This is **truth-assisted coverage construction**: the experiment designer sees
held-out unit identities. It is not blind passage selection. Carrier examples
also shorten the training distribution and cease to form continuous prose.
The source's top64 reference words, original training words and carriers form
the dictionary. Every optional path is retained; held-out forms are not otherwise
reserved. Letters-only recovery uses the identical engineered word list.

Alternating per-unit choices expose both codes, and continuation choices are
independent uniform draws. Recovery models free H<=2 selection, not the planted
alternation. Public hidden requests contain only ciphertext, alphabets,
dictionary and model settings. They contain no generating key, plaintext,
lengths, code boundaries, ownership groups or coverage targets. All fits use
5,000 ms Z3 budgets and a 45-second worker wall limit. The first returned key is
frozen before scoring; no re-search or repair uses continuation truth.

**Whole-word signs cannot have observed training codes and simultaneously be
novel plaintext word types.** Aquinas adds `et` and `sed`, which also occur in
continuation; `est` already occurred in its original training passage. Einhard
adds `et`. Report the full eight-word denominator and genuinely novel spellings
separately. Novel ciphertext spelling alone would be insufficient under H2.

The one-glyph contraction diagnostics use 74, 80 and 78 output symbols, far
larger alphabets than the manuscript's ordinary EVA inventory. Only the fresh
mixed fixture tests hidden internal boundaries, with 24 output symbols and
prefix-free widths 1–2. Code assignments differ between letters/contractions;
this is not an identical-codebook comparison.

## Seven plan–test–assessment stages

| Stage | Plan and test | Result / next assessment |
| --- | --- | --- |
| 1 | Freeze fixtures and independently auditable both-code coverage | Append 5/8/10/7 carrier tokens to Caesar/Aquinas/Einhard/Caroli; all eight continuation words in each arm fully covered |
| 2 | Caesar H2 one-glyph, hidden first key, letters comparison, shuffle | Contractions 7/8; letters 8/8; shuffle UNSAT. One novel word still wrong despite observed codes |
| 3 | Same covered diagnostic on Aquinas | Contractions 6/8, all 5 novel forms correct; letters 8/8. Errors are repeated whole-word abbreviations |
| 4 | Same covered diagnostic on Einhard | Contractions 8/8, all 7 novel forms correct; letters 8/8. Audit grouping before declaring a uniquely recovered key |
| 5 | Construct alternate whole-word assignments fitting identical ciphertext | 3/9/5 verified alternatives for the three sources: coverage alone cannot identify their meanings |
| 6 | Apply frozen external-frequency ranking to legal swaps of returned keys | Pools of 6/13/6; selected exact scores remain 7/8, 6/8, 8/8. No truth injection into selection |
| 7 | Fresh Caroli H2 mixed-width hidden first key, same ranking, letters and shuffle | Contractions 7/8, all 7 novel forms correct; letters 8/8; shuffle UNSAT. Frequency pool3 retains 7/8; oracle not needed |

Eight positive fits were verified SAT; all four shuffled training fits were
UNSAT. There were **12 solver calls**, no UNKNOWNs and no worker timeouts in
this loop. Mixed contraction fitting took 4.846 solver seconds / 7.336 total fit
seconds including construction. The letters comparison took 2.731 / 4.723
seconds. These are recorded executions, not guaranteed replay performance.

No shuffle key was available for continuation scoring. Four finite-problem
UNSATs are not a population false-positive rate; independent UNSAT proof
certificates were not generated.

## What coverage removes, and what it does not

Across all four covered cases, contraction keys recover 28/32 sampled
continuation words, including **26/27 novel plaintext word occurrences**.
Letters recover 32/32. The first three were revisited passages used to develop
this diagnostic; Caroli is a fresh source, but still only one eight-word sample.
The engineered observation protocol changes training amount, dictionary and
choices, so the older 11/24 versus current21/24 is not an isolated causal effect
of a single changed parameter.

Independent ownership inspection finds the following:

- Caesar: the two true `<ter>` codes are assigned to `<eius>` and `<qui>`.
  `interiectis` becomes `ineiusiectis`; that output also violates the whole-word
  scope of `<eius>`. It is an invalid contraction path, not merely a rare word.
- Aquinas: true `et` and `est` alternatives are split among different word signs;
  the two-unit `sed` is assigned the two-unit `tamen` pattern. Continuation `sed`
  becomes `tamen`, and `est` becomes `et`.
- Einhard: the sampled continuation is entirely correct, but alternative true
  `<per>`/`<rum>` homophones have different recovered owners. Success on one
  random continuation stream does not identify all code alternatives.
- Caroli: the `<qua>` pair is split between `<qua>` and `<qui>`. A repeated
  `quam` becomes `quim`; all seven new word types in this sample are correct.

Thus **both codes appearing in training does not mean the solver recognizes
that they belong together**. It may split them among different plaintext units
and still satisfy every finite-dictionary training constraint. Even preserving
groups leaves a separate ambiguity: whole-word signs can be reassigned to other
whole-word dictionary entries. Stage5 provides constructive SAT witnesses for
that issue, rather than inferring it from a timeout.

As a stricter ownership diagnostic, both generating alternatives have the
correct unit owner for every constituent unit in only 7/8, 5/8, 6/8 and 7/8
continuation words respectively. This is a sufficient guarantee for recovery
under arbitrary homophone draws, distinct from the observed 7/8, 6/8, 8/8, 7/8
scores. It is not an exhaustive estimate of all possible expanded-word matches.

## Frequency test

Candidate generation uses the recovered key and public dictionary only: keep
the first key and all valid single transpositions between available one-unit
whole-word signs. Independently verify each proposed training fit. Freeze
add-one external unigram scores and selection before looking at continuation.
Score only the original32 natural training words, excluding artificial carriers
whose frequency would distort the source prior. Ties favor the first candidate.
The known generating key and stage5 proof candidates never enter these pools.

The Caesar and Aquinas selections change, but their exact continuation scores
remain unchanged; Einhard retains its first key. Caroli's selected swap likewise
does not fix its failure. This limited proposal family does not address splitting
homophone groups, multi-unit `sed`/`tamen`, or initial `qua`/`qui` ambiguity.
No inference that all frequency methods are ineffective follows. Unigram
frequency alone has not supplied a successful rescue in these tests.

## Verification, artifacts and decision

Four new focused tests plus ten earlier contraction tests pass. Independent
validation checks 489 complete optional paths and retained-cost minima, 714
actual code-observation memberships, 61 SAT witnesses including constructive
alternatives, 424 continuation-word predictions and 28 frequency scores.
It checks macro applicability on decoded continuation paths, novel plaintext
membership and both-code owner grouping. Prepared source/config/implementation
hashes and public worker-input hashes are preserved.

```sh
.venv/bin/python -m benchmarks.contraction_coverage_calibration --run
.venv/bin/python -m benchmarks.contraction_coverage_validation
.venv/bin/python -m pytest -q tests/integration/test_contraction_coverage_calibration.py \
  tests/integration/test_contraction_hidden_calibration.py \
  tests/integration/test_complete_contractions.py
```

The launcher resumes completed stages without repeating fits. Artifacts under
`experiments/results/contraction-coverage-calibration/` include the frozen
protocol, seven plans/assessments, public inputs, truth-assisted coverage design,
all fit/proof/ranking witnesses, score pools, ownership/path audits and validation.
No previous frozen experiment was edited; no manuscript solves, downloads,
installations, longer budgets or additional historical rules occurred.

Stop after seven stages. The remaining bottleneck is **identifiability**, not
merely code exposure. A useful next step would separately diagnose homophone
grouping and contextual word meaning; dictionary membership and unigram counts
are insufficient here. Prefer a small frozen word-context comparison on the
verified ambiguity candidates over another inventory or timeout ladder. Keep
whole-word constraints and partial-word contraction scope explicit, and evaluate
on independent positives/controls before any manuscript application. The fresh
covered mixed-width success is encouraging computational calibration, not a
reliable decipherment method or a language conclusion.
