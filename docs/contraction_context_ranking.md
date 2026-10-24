# Word-context ranking versus homophone grouping

Seven stages tested a fixed adjacent-word Latin score on the existing verified
contraction-key alternatives. It selects **the same keys as unigram ranking in
all four pools**. Exact continuation remains Caesar7/8, Aquinas6/8, Einhard8/8,
Caroli7/8: 28/32 total, including26/27 novel plaintext word occurrences.
No additional solver calls or candidate searches occurred.

The stronger methodological finding is structural: **the existing whole-word
label swaps preserve every homophone-group split**. No score can choose a
correct grouping from these pools if the first key's grouping is wrong. This
is verified independently for all28 recovered candidates. Stop scorer tuning
on these fixed pools; diagnose grouping separately before scaling recovery.

## Frozen experiment

Use the unchanged coverage experiment's complete pools: first recovered key
plus legal single swaps of one-unit whole-word signs. Pool sizes are6,13,6,3.
Neither generating keys nor truth-assisted proof candidates enter selection.
Hold-out plaintext, carriers and ownership diagnostics do not enter scoring.

Build each prior from the actual first-half source stream, retaining ordinary
adjacent words and excluding pairs crossing discarded-token barriers. Do not
project onto a short-word list or bridge removed words. Vocabulary is the full
reference word distribution plus one unknown category. Reference token counts:
Caesar10246, Aquinas3659, Einhard3785, Caroli7553.

For the first training word use add-one unigram probability. For each next word
use an equal-weight mixture of add-one unigram and add-one conditional bigram
probability; average natural log probabilities. Weight0.5 and smoothing1 are
fixed before scoring, with no parameter sweep or subsequent adjustment. Include
unknown forms and score only the original32 natural training words; artificial
coverage carriers do not contribute. Original spelling is restored from macro
parts. First candidate wins exact score ties.

This is a **soft word-context score**, not a Latin grammar parser or a hard
syntactic constraint in Z3. It tests selection of already verified keys. It
cannot create another grouping, expand the candidate pool or establish Latin
sentence validity. All four passages were already examined in the previous
experiment: this is retrospective method comparison, not new blind validation.
The reference/evaluation halves are disjoint within each source, not independent
authors. No new historical rules, corpora or manuscript experiments.

## Seven stages and assessments

| Stage | Test | Assessment |
| --- | --- | --- |
| 1 | Freeze full-word reference priors and barrier handling | Proceed with unchanged pools; no outcome-based smoothing changes |
| 2 | Caesar recovered-key context ranking | Same selected swap as unigram;7/8 exact unchanged |
| 3 | Aquinas, unchanged score | Same selected swap;6/8 exact unchanged |
| 4 | Einhard, unchanged score | All six training scores tie; first key retained;8/8 exact |
| 5 | Caroli mixed-width pool, unchanged score | Same selected swap;7/8 exact unchanged |
| 6 | Separately rank generating keys plus constructive alternative meanings | Unique top generating key in Caesar; five-way top tie in Aquinas; an alternative beats generating key in Einhard |
| 7 | Inspect ownership grouping separately; record missing ranking controls | All label swaps preserve grouping defects; no recovery or specificity gain established |

Stage6 is explicitly **truth-assisted score-capacity diagnosis**. The generating
key is inserted first, so its rank1 in an exact tie does not show identification.
The proof pools have4,10,6 keys. Caesar's generating key is uniquely best;
Aquinas's shares the top score with four other assignments; Einhard's is rank2
behind a wrong ownership alternative. These pools are small and intentionally
constructed. They neither supply hidden recovered candidates nor prove that
longer solver runs would find useful keys.

The context-selected grouping counts among held-out target units are identical
to those of the first key: Caesar14/15, Aquinas16/18, Einhard20/22, Caroli20/21.
(Label correctness can change separately.) Each proposal applies a bijective
renaming to code owners. Therefore two distinct owners remain distinct; an
incorrectly split true pair cannot merge under such a proposal. This invariant
also holds when the context model itself changes.

The four previous shuffle training problems returned UNSAT and supply **no
fitted negative keys**. Consequently this experiment cannot measure ranking
specificity or a false-fit rate. Successful classification of the prior finite
solver problems must not be credited to the new language score.

## Checks and artifacts

Three focused tests pass: exclusion barriers, context sensitivity with equal
unigram counts, and independence of selection from truth, continuation and
appended carrier metadata. Independent validation reconstructs reference
counts/pairs, reproduces48 context scores, verifies48 recovered/proof SAT
witnesses, and checks519 target-unit grouping invariants across recovered pools.
Ownership checks decode every generating code independently. No new Z3 calls.

Artifacts are under `experiments/results/contraction-context-ranking/`: frozen
reference models, unchanged candidate pools, seven plans and assessments,
complete ranks, grouping audit, report and independent validation. Prior frozen
modules and result artifacts remain untouched.

```sh
.venv/bin/python -m benchmarks.contraction_context_ranking
.venv/bin/python -m benchmarks.contraction_context_validation
.venv/bin/python -m pytest -q tests/integration/test_contraction_context_ranking.py
```

The launcher resumes completed stages without repeating scoring work. These
results add no manuscript-language or historical-mechanism conclusion.

## Next decision

The next useful experiment is a **separately labeled oracle-grouping diagnostic**
on the existing one-glyph covered positives: reveal which observed codes share
an unknown owner, without revealing their Latin labels. Compare with the fully
hidden arm using the same word dictionary and held-out forms. One-glyph outputs
keep boundary information fixed, isolating group membership. Preserve the
whole-word alternative witnesses: even correct grouping cannot by itself identify
the meaning of a whole-word sign. This is a truth-assisted instrument diagnosis,
not manuscript recovery or a deployable grouping method.

If correct groups substantially improve recovery, candidate generation needs to
change groups jointly with meanings; further rescoring of label-only swaps
cannot repair the present failure. If ambiguity remains, document the limit of
the dictionary/word-context model before another broad search. No timeout ladder
or larger contraction inventory is supported by these results.
