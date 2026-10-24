# Next milestone: Latin word anchors on Caesar

The goal is a useful partial dictionary: reliably recovered frequent connective,
relational, and modifying words in their actual positions. Readable restoration
and total literal accuracy are secondary. This is a synthetic whole-word
substitution test, not evidence that Voynich follows the same channel.

## Resource preparation

1. Freeze a Caesar test stream from the cached source, with a contiguous prefix
   chosen by position and length before inspecting solver results. Report its
   actual length; do not repeat text to manufacture 35,000 tokens. Remove sentence
   boundaries, punctuation, headings, and editorial material; retain word order.
2. Freeze a Latin training corpus excluding Caesar entirely for the main test.
   Audit existing UD resources at work/author level: a treebank name alone does
   not establish independence. Other Caesar books are a separately labeled,
   author-assisted diagnostic, not the main test. Audit exact long overlaps.
3. Freeze an independently built surface-form vocabulary, with training forms
   included by a declared resource rule. Existing generated inventories contain
   2.55 million or more forms, substantially beyond the earlier 800,000 estimate.
   Record inventory size, coverage ceiling, model-attested coverage, runtime,
   and memory. Do not filter vocabulary to the hidden test words.
4. Apply one declared spelling convention to all resources. Existing generated
   forms use j→i and v→u; canonicalizing every input the same way is the initial
   practical choice. Keep enclitics attached initially and preserve ambiguous
   morphology. Report orthographic normalization as a benchmark assumption.

## Inference

Use the original, untempered bigram objective and sparse candidate retrieval.
Begin with a small resource/cipher smoke test, then a long continuous stream.
Use at least three independent random starts for anchor agreement; distinguish
these from frequency-initialized runs with a shared starting dictionary.
Hold proposal caps constant in matched comparisons and record actual runtime;
retain the earlier approximate one-hour bundle preference as a configurable
budget, not a language-specific constant. Never supply test vocabulary, truth,
POS labels, or original sentence boundaries to inference.

## Primary evaluation

Report literal precision and token coverage for candidate anchors separately.
Evaluate frequency bands and top 10/20/50 public ciphertext types without choosing
favorable examples after recovery. Report individual mappings, their counts,
run agreement, rank alternatives, and whether they changed from initialization.
Agreement is evidence to calibrate, not an automatic probability of correctness.

Predeclare the initial conservative anchor rule: unanimous agreement across three
random starts and at least 100 public occurrences. Also report a frequency/consensus
threshold grid, clearly labeled exploratory. If the stream is shorter, disclose
that the fixed threshold changes the fraction eligible; do not tune it silently.
Use evaluation-only linguistic annotations or reviewed categories to distinguish
conjunctions, adpositions, pronouns, particles, auxiliaries, and content words.
Ambiguous forms can belong to multiple possible classes. Report exact surface
recovery separately from lemma or grammatical-role plausibility.

Present a fixed opening paragraph and several fixed-position excerpts, with
correct anchor locations marked. Preserve uncertain alternatives for subsequent
attacks; do not hard-freeze inferred mappings.

## Interpretation

A positive sign is a reproducible group of frequent structural words recovered
with high measured precision and useful coverage. High total token accuracy by
itself is insufficient. Latin has no English-style articles, so English anchor
coverage is a comparison point, not a required numeric target. Same-author success
alone is insufficient for transfer to an unknown-topic manuscript. Even a positive
Caesar result would establish usefulness only under the synthetic channel tested.

## Deliverables

Resource and overlap manifests; public cipher/private evaluation split; sparse
Latin resource adapter; resumable runs; frequency-band and consensus precision/
coverage tables; original/restored passages; runtime/memory report and limitations.

## First implementation completed

See [the experiment report](../scalable_latin_caesar.md). The entire cached I–IV
stream is 20,484 tokens; the full generated/training inventory is 2,557,237 forms.
Six 4,000-proposal chains complete with three independent random starts and a
separate three-frequency-start diagnostic. The primary rule recovers only `et`
(479 positions, 2.34% token coverage); the frequency diagnostic has two correct
and two wrong unanimous frequent mappings. The original English-level anchor
hypothesis is not yet established for Latin. All 124 relevant tests pass.
Larger corpus/search calibration and independent grammatical assessment remain
future work; no mappings are frozen and no Voynich inference is claimed.

The [target-independent follow-up](../scalable_latin_target_independent.md) is
complete: six 20,000-proposal runs, six observed/full-inventory mixture runs,
six three-word-cycle runs, and baseline/new trace audits. None reliably improves
anchors. Full inventory/training/target stay unchanged; no topic matching, target
vocabulary filtering, annotations, or guessed anchors enter inference. All 126
relevant tests pass. Future work should distinguish objective mismatch and local
search barriers rather than assume more proposals alone will solve the problem.

[Context-profile and skip-association experiments](../scalable_latin_profiles_association.md)
are complete: three variants, three seeds each, 4,000 proposals per chain, same
full inventory and source texts. Profiles with the original objective recover
2/50 shortlist types; association variants recover 0/50. No frequent unanimous
anchors are added. The association loss prefers an uninformative dictionary to
the nearly correct feasible reference. Preserve defaults; investigate learned
classes or a better-calibrated structural objective rather than treating this
particular graph discrepancy as adequate. All 132 relevant tests pass.

[Learned classes and independent confidence calibration](../scalable_latin_classes_confidence.md)
are implemented and tested. Class scoring fails development random/collapse
controls, so full class decipherment is stopped. Confidence fitted on an
independent Latin work and tested on another filters the old Caesar baseline to
two correct mappings at .5, but its fixed high-trust validation rule fails and
top-50 precision remains 3/50. The current majority pool contains only four
correct types, limiting what ranking alone can achieve. No defaults change;
138 relevant tests pass.

The next planned milestone combines a substantially larger independent corpus
with ambiguity-preserving lemma and morphology channels. See the
[implementation plan](scalable_latin_corpus_morphology_plan.md) for source splits,
normalized scoring, sparse retrieval, objective gates and matched ablations.
This is planned work; no new training or decoding results are claimed.

That milestone has now reached its development stop condition. The
[larger-corpus/morphology report](../scalable_latin_corpus_morphology.md) records
5.94M cleaned tokens, 2.67M shared forms and normalized lemma/grammar mixtures.
All 15 size/mixture combinations still prefer wrong frequency keys over nearly
correct references. Full decoding and sealed-test evaluation are stopped under
the predeclared rule; 147 relevant tests pass and defaults remain unchanged.

The subsequent [Latin trigram test](../scalable_latin_trigram.md) is complete:
development selects .75 interpolation; Gellius gains 1.86 token-accuracy points,
but frozen fresh Livy confirmation falls from .80% to .25% and has no correct
unanimous frequent anchors. This short-context model is not promoted. Both
methods use the same 5.94M source and 2.67M inventory; 155 relevant tests pass.
