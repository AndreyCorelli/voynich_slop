# Larger-corpus and morphology-backed Latin: development gate results

Implemented the combined experiment from the
[plan](todo/scalable_latin_corpus_morphology_plan.md). The accepted cleaned resource
version is `experiments/results/scalable-latin-corpus-morphology/v2/`. This is a
negative development result: all tested objectives fail the predeclared gate.
No new text-restoration percentage, improved anchor nucleus, or Voynich result
is claimed. Historical experiments and decoder defaults remain unchanged.

## Corpus and independence

The CLTK Latin Library collection is cached at commit
`76229acaf02efd1964ac32009408a90b6f279758`, with its upstream README and Public
Domain Mark 1.0 declaration retained. The executable builder admits explicitly
registered author directories only; other sources are quarantined rather than
silently assigned author identities. The admitted corpus contains **5,935,259
normalized tokens, 747 book/source files and 30 registered authors**. Thus the
available clean corpus is about **35.1 times** the old 169,100-token source;
20 million tokens were not available from the selected sources.

A source-only line cleaner removes short navigation/heading lines, uppercase
and mostly uppercase titles, Roman-numeral navigation, known English footer and
editorial markers, and leading embedded CAPUT labels. It retains words inside
editorial angle brackets. Lowercasing, diacritic stripping and j/i, v/u merging
match the old continuous Latin contract. Word order and attached enclitics remain;
sentence boundaries and punctuation are absent from model streams. Individual
source files are separate documents, without cross-file transitions.

This is a prose-oriented format filter, not an authoritative Latin detector or
critical edition. Short Latin lines can be lost, surviving lines are joined, and
unmarked editorial text can remain. Source inspection found mixed-case titles
and navigation missed by the initial cleaner. That initial `v1/` corpus and its
negative runs are preserved; `v2/` corrects those generic source-format rules.
The cleaning change was motivated by source inspection, not by selecting a
favorable recovery result. Both versions reject all tested objectives.

Evaluation author/work choices were frozen before model outcomes:

| Split | Source file/work | Actual target tokens |
|---|---|---:|
| Development | Apuleius, Metamorphoses I | 4,015 |
| Development | Curtius, Historiae III | 7,135 |
| Development | Suetonius, Augustus | 13,812 |
| Validation | Gellius, Noctes Atticae I | 9,670 |
| Sealed test | Livy, Ab urbe condita I | 16,983 |
| Sealed test | Ammianus, Historiae XIV | 8,142 |
| Sealed test | Quintilian, Institutio I | 17,560 |

These are real source lengths, not manufactured 35k-token streams. All works by
these authors, and all Caesar works, are excluded from raw and annotated training.
Author/format inspection does not make these previously unknown literary works;
"sealed" means their recovery outcomes are reserved, not that acquisition and
preparation never access their plaintext. Validation and sealed-test recovery
were not evaluated. Caesar supplied no fitting labels or objective scores here.

Whole-document hashes, deterministic bottom-hash 12-gram near-duplicate screens
with exact verification, and held-out passage overlap screens are recorded.
Unknown sources, short documents and suspect passage overlaps are excluded as
whole documents; test phrases are not selectively removed to improve a score.
No admitted exact/near duplicate was detected under this policy. Three admitted
Cicero files have 4, 5 or 6 matching held-out 12-grams, below the frozen 12-match
whole-file exclusion threshold. Overlap screens do not prove independence and
cannot remove every quotation or alternative edition. No held-out vocabulary
enters resource construction.

## Inventory, morphology and source annotations

All model variants share **2,666,235 surface forms**: the entire pinned default
generated vocabulary union all admitted training forms. This is 108,998 more than
the historical 2,557,237-form inventory, because the training corpus changed.
Within the new experiment, vocabulary is fixed across all corpus sizes and
mixture variants; comparison with the old experiment is not a pure fixed-inventory
ablation.

The pinned Whitaker analyzer produces **5,954,522 distinct lemma/grammatical
analyses**, retaining ambiguity and enclitic information. Analysis duplicates
are removed before assigning probability mass. Compact memory-mapped arrays
store offsets and lemma/grammar IDs; a checkpointed batched analyzer retains the
full dictionary, including unsupported forms. Full catalog preparation took
approximately two minutes. Known PACK-table failures (`cu`, `qu`, `qune`) are
recorded rather than assigned invented analyses. The resource's incomplete
filters, theoretical forms and known pronoun issues remain limitations.

Independent cached PROIEL/Perseus training annotations provide compatible
POS/features, excluding evaluation authors. The explicit crosswalk matches
available case, number, gender, person, mood, voice and degree information;
common gender permits masculine/feminine. It does not equate UD tense/aspect
with Whitaker tense, or UD lemma strings with Whitaker lexeme IDs. Unresolved
lexical identity remains ambiguous. 142,048 of 166,828 eligible annotated source
tokens have a compatible analysis; 24,780 do not. Missing inventory and nonsingle
surface rows are separately recorded. These are source annotations, never tags
or guessed translations supplied for ciphertext.

Analysis priors use three bounded source-unigram soft-allocation iterations,
anchored by fractional annotation counts. This is a deliberately limited
implementation of ambiguity estimation, **not sequence likelihood EM**, and not
an independently validated grammatical disambiguator. It departs from the planned
held-out-likelihood stopping procedure; the fixed estimator and all three
iterations are recorded rather than presented as converged inference. A future
contextual analysis estimator would be a new variant, not the model tested here.

## Normalized factor model

Three conditional channels are combined by an arithmetic probability mixture:

- The existing full-support sparse surface bigram.
- A lemma-transition model with surface emissions shared across inflections.
- A grammatical-bundle transition model with surface emissions.

Each analyzed input marginalizes its normalized possible analyses. Training
transitions use fractional expected counts, not one full count per alternative.
Emissions apportion `count(word) + beta * base(word)` across analyses and normalize
within each state. State transitions use additive prior mass `alpha=1`; emissions
use `beta=1`. Each factor channel mixes in 1% of the full surface base distribution,
so unobserved or unanalyzed forms retain positive probability. Unsupported input
analyses back off without merging unknown words into one fake lemma identity.
EOS has its own state/emission, and BOS is conditioned on a nonempty document.

The resulting conditionals sum to one over the entire vocabulary plus EOS.
Probabilities are not renormalized over a retrieved shortlist. This local model
shares inflectional evidence but does not enforce a consistent latent analysis
across a sentence or capture long-distance agreement. It differs from the earlier
failed distributional word-class model, but remains an adjacent-context model.

The common loader, exact all-occurrence dictionary delta scorer and checkpoint
machinery support the new model. Optional sparse factor candidate indexes are
implemented. Their retrieval is explicitly approximate; it is not claimed to
inherit the old surface-only exact top-k guarantee. No production retrieval-recall
or full decoding comparison is performed because every objective fails first.

## Fixed objective screening

At each training size, test these mixtures `(surface, lemma, grammar)`:
`(1,0,0)`, `(.75,.25,0)`, `(.75,0,.25)`, `(.5,.25,.25)`,
`(.25,.375,.375)`.

For each development work compare a nearly correct feasible reference with a
frequency-ranked injective key, an unobserved-form key, three random injective
keys, three shuffled streams, and three corruptions at each of 10%, 25% and 50%
of word types. Inventory-missing true types use distinct unsupported proxies for
reference diagnostics only; the missing rates are retained per work. No oracle
key enters actual inference.

Inventory token coverage is 94.25% for Apuleius, 98.19% for Curtius and 97.13%
for Suetonius. Reference scores therefore include unsupported proxies at 231,
129 and 396 positions respectively; they are not the likelihood of completely
correct Latin. This limits interpretation of the gate and leaves vocabulary
coverage as a contributing factor, rather than proving an objective-only cause.

The predeclared promotion rule requires the reference to beat the frequency and
null controls and median corruption at every level on at least two of three
works. All 15 size/mixture combinations beat the null and median corruption
controls on all three works, but **none beats the frequency key on any work**.
The whole-text reference discrimination gate therefore fails in every case.

The table summarizes development log likelihood per token/event; higher is
better. The final column is `reference - wrong frequency key`, so negative means
that the wrong dictionary wins. These are objective diagnostics, not recovery.

| Training tokens | Mixture | Feasible reference mean log probability | Reference minus frequency key |
|---:|---|---:|---:|
| 1,012,874 | Surface only | -10.2199 | -1.3685 |
| 1,012,874 | Surface + lemma + grammar (.5/.25/.25) | -10.0029 | -1.4768 |
| 5,005,992 | Surface only | -9.9497 | -1.0249 |
| 5,005,992 | Surface + lemma + grammar (.5/.25/.25) | -9.6878 | -1.1890 |
| 5,935,259 | Surface only | -9.9380 | -0.9878 |
| 5,935,259 | Surface + lemma + grammar (.5/.25/.25) | -9.6723 | -1.1694 |

More data improves the correct text's likelihood and narrows the surface model's
preference for the wrong frequency key. Adding morphology improves reference
likelihood too, but also improves the wrong key, leaving a larger discrimination
gap than surface-only at the same size. Better likelihood alone is not evidence
of better decipherment. These results reject this particular factorization and
estimator at the gate; they do not establish that Latin morphology cannot help.

## Cost, decision and limits

The 103,512-token pilot counted 26,666 types and 87,600 edges in 0.016 seconds;
full ambiguity annotation of its distinct forms took 0.94 seconds. The full
2.67M-form catalog took about two minutes. Building the surface models took
4.47, 18.68 and 21.19 seconds at the three scales; factor construction took 4.17,
12.70 and 14.38 seconds. Model-loading overhead, gates, acquisition, vocabulary
construction and serialization are not all included in those phase timings.
The model runs overlapped, so these are not controlled throughput comparisons.
Peak process RSS was approximately 1.32–2.58 GB. Current sparse Python count
storage fit these measurements; the optional compact count-store optimization
was not implemented. The corpus's largest author contributes about 21%, and the
nested whole-book order balances author token totals while sources remain.

**Decision:** stop full decipherment for all rejected variants, as specified by
the plan. Preserve surface models, fitted ambiguity weights, full morphology
catalog, protocols and per-work controls. Full factor models can be reconstructed
from these inputs; rejected variants are not installed as defaults or serialized
as selected winning models. Validation selection, sealed-test decoding, anchor
confidence calibration and new recovery passages remain intentionally unrun.

The plan has therefore reached its development stop condition, not a completed
successful restoration system. Learning longer-range grammatical relationships,
better contextual analysis posteriors, or correcting the objective's preference
for frequent lexical substitutions requires a separately declared next experiment.
Merely increasing the search cap would not resolve this failed check.

All **147 relevant tests pass**, including direct factor marginalization and
normalization, full support with/without unknown forms, duplicate-analysis
invariance, annotation compatibility, exhaustive tiny dictionary-move deltas,
serialization, checkpoint continuation, corpus quarantine/deduplication and a
three-seed public-only end-to-end morphology decoding smoke test. Numerical
correctness does not establish linguistic adequacy.

## Reproduction and artifacts

The cached upstream corpus and pinned morphology vendor are required. For a new
output root, run the following with the same `--output` on every command:

```sh
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology prepare --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology pilot --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology resources --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology train --size 1000000 --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology train --size 5000000 --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology train --size 20000000 --output /tmp/latin-morph-reproduction
.venv/bin/python -m benchmarks.scalable_latin_corpus_morphology summarize --output /tmp/latin-morph-reproduction
```

The `20000000` size is the requested upper bound and consumes all available
5.94M tokens; its reports never label them as twenty million actual tokens.
Inventory and analysis builds checkpoint independently. Preparation requires an
exclusive new root, and model resumes bind corpus/design identities.

Artifacts in the accepted `v2/` directory:

- `design.json`, `corpus-build.json`, `pilot.json`, `summary.json`.
- `corpus/corpus.json`: admitted/rejected files, hashes, duplicates, nested subsets.
- `corpus/training/`: normalized independent book streams.
- `corpus/evaluation-only/`: private preparation/provenance, separate from training.
- `resources/`: shared inventory and memory-mapped, resumable morphology catalog.
- `models/{1000000,5000000,20000000}/`: surface model, training protocol, source
  annotation report, ambiguity weights/fit trace, full per-work gates and costs.

The source collection is https://github.com/cltk/lat_text_latin_library; its
pinned local documentation is the provenance used for this build. Feature
harmonization limitations are consistent with the documented differences between
Latin UD treebanks: https://universaldependencies.org/la/overview/introduction.html.
