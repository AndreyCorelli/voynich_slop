# Latin frequent-word anchors: Caesar benchmark

The primary question is whether independent searches recover a useful set of
frequent Latin structural words, even when the full restored passage remains
unreadable. Literal token recovery is secondary; grammatical and semantic
recovery are not automatically inferred from word accuracy.

## Frozen design and resources

The target is the complete available normalized *De Bello Gallico* I–IV from
cached Project Gutenberg eBook 218: 20,484 tokens, 5,663 types, one continuous
document. Its first up-to-35,000 tokens were requested before recovery; the
source is shorter, so no text is repeated or vocabulary filtered. Punctuation,
sentence/paragraph boundaries, book headings, and editorial material are removed
by the existing Caesar parser. Lowercase i/u spelling is applied consistently to
target, training, and inventory. Enclitics stay attached when represented as a
surface multiword token. This is a synthetic globally consistent injective
whole-word substitution cipher with retained word boundaries and word order.

The dictionary is the entire previously generated Whitaker-derived default
inventory, union independent training forms: **2,557,237 forms**. No Caesar
vocabulary is supplied to inventory construction. Generated forms may be unattested
or overpermissive; this is not a claim of complete Latin coverage.

Training uses only the cached UD r2.17 PROIEL and Perseus train splits. An explicit
source registry excludes Caesar from both: PROIEL's *Commentarii belli Gallici*
and Perseus `phi0448.phi001`. The latter appears in the cached data despite being
absent from that README's summary author list. Unknown sources fail validation.
The audit excludes 23,493 Caesar tokens and retains **169,100 tokens**, 13 work
streams and 116,846 observed bigram edges. Sentences are concatenated within each
work in recorded order. These are sometimes discontinuous annotated excerpts;
artificial joins and a mixed biblical/classical/agricultural domain remain
limitations. The target has zero exact normalized 12-word windows in training;
this does not rule out all quotations or paraphrases.

The inventory misses 843 target types / 1,332 occurrences, so the literal token
ceiling is **93.50%**. Training-attested forms cover **80.16%** of target tokens.
The resource build took 9.37 seconds on this machine, with a 245 MB process
high-water mark. The SQLite inventory is about 105 MiB and the model 21 MiB.
A public-only 2,000-token/100-proposal smoke run completed and peaked at 432 MB.

## Search and evaluation

Use the unchanged untempered bigram objective, mixed type scheduler, original
sampled-context retrieval, 10,000 active-entry budget, and 4,000 proposals per
chain. The main test has three random starts, seeds 3/5/7; a separate diagnostic
uses three frequency starts with identical seeds and proposal limits. Each chain
has a configurable 600-second wall-clock allowance and 10-second reserve; this
is a limit, not an expected duration.

The primary anchor rule is unanimous agreement across all three starts and at
least 100 public occurrences. Report type/token precision and token coverage
separately, including wrong unanimous assignments. Random-start and shared
frequency-initialized agreement are never pooled. An exploratory grid reports
votes >=2/3 and public counts >=1/20/50/100. Also report per-run recovery among
the top 10/20/50 public-frequency types and across five frequency bands.

Possible word classes come only from the independent training annotations and
can be ambiguous or absent. They do not establish contextual grammatical roles
in Caesar. ADV includes content adverbs. All word identity checks and original
text are evaluation-only. The public runner does not read plaintext or original
annotations; integration tests remove both plaintext and training sources during
inference. Complete keys and archived scores are verified by full rescoring.

Fixed 100-token excerpts at offsets 0, 1/5, 2/5, 3/5, and 4/5 of the stream are
saved for human review. These windows are not inferred paragraph boundaries.
No mappings are frozen for downstream attacks.

## Provenance and reproduction

Original cached inputs and licenses remain in place:

- `data/raw/pg218.txt` and its source/hash manifest: Gutenberg eBook 218.
- `data/latin-grammar-benchmark/{proiel,perseus}-r2.17/`: original CoNLL-U files,
  READMEs, contributor attribution, and LICENSE.txt files.
- `experiments/results/latin-form-inventory/upstream-default.txt.gz`: pinned
  generated dictionary; generation and limitations in [Latin form inventory](latin_form_inventory.md).

Run sequentially:

```sh
.venv/bin/python -m benchmarks.scalable_latin_caesar build
.venv/bin/python -m benchmarks.scalable_latin_caesar prepare
.venv/bin/python -m benchmarks.scalable_latin_caesar smoke
.venv/bin/python -m benchmarks.scalable_latin_caesar search-random
.venv/bin/python -m benchmarks.scalable_latin_caesar search-frequency
.venv/bin/python -m benchmarks.scalable_latin_caesar measure
```

Outputs are exclusively created under
`experiments/results/scalable-latin-caesar/v1/`. The design is saved before
resource construction and inference. Resource and cipher hashes bind the run;
Latin contracts are distinct from the existing English contract. English behavior
is unchanged. All 124 relevant tests pass, including source exclusion, unknown
source rejection, multiword-token handling, continuity, language binding,
public-only search, and anchor accounting.

## Results

All six chains completed 4,000 proposals. The dictionary size was computationally
manageable, but the English recovery did **not** transfer well to this Latin setup.

| Initialization | Seed 3 literal | Seed 5 literal | Seed 7 literal | Mean literal | Source-selected literal |
|---|---:|---:|---:|---:|---:|
| Random, primary | 2.34% | 2.45% | 7.85% | 4.21% | 2.34% |
| Frequency, diagnostic | 5.11% | 6.25% | 5.11% | 5.49% | 5.11% |

The initial frequency-only dictionary recovers just 0.0098% of tokens. These are
exact normalized surface-word scores, not lemma, grammar, or meaning scores.
Source-score selection again fails to pick the most accurate run.

### Frequent anchors

The fixed unanimous/count>=100 rule gives:

| Initialization | Proposed anchor types | Correct types | Token precision | Proposed token coverage | Correct token coverage |
|---|---:|---:|---:|---:|---:|
| Random | 1 | 1 | 100% | 2.34% | 2.34% |
| Frequency | 4 | 2 | 77.47% | 6.22% | 4.82% |

The random-start anchor is **et → et**, all 479 occurrences. The apparent 100%
precision is based on a single recovered type; it is not a calibrated guarantee.
Unanimous agreement without the count threshold also includes one wrong singleton,
`marcomanos → uite`. The threshold excludes it, as predeclared.

The frequency-start unanimous frequent mappings are:

| Original | Restored | Occurrences | Result |
|---|---|---:|---|
| in | in | 508 | correct |
| et | et | 479 | correct |
| non | de | 170 | wrong; unchanged shared initial assignment |
| a | quod | 117 | wrong; changed from initial assignment in all supporters |

Removing unchanged shared-prior assignments would eliminate one error, but not
`a → quod`; that post-hoc change is not the primary rule. Shared initialization
is only one source of false agreement. Frequent majority agreement across random
runs is much worse: 1/7 correct types, 28.31% token precision, 8.26% proposed token
coverage. For frequency starts, majority agreement gives 2/11 correct types,
39.31% token precision, 12.26% proposed coverage. These are exploratory rules;
neither justifies treating frequent mappings generally as reliable anchors.

Among the ten most frequent public types, random runs recover 1, 1, and 5 types;
frequency runs recover 2, 3, and 2. Their original forms are `in et ad cum quod se
ex qui ut non`. Results are inconsistent even within this structurally useful
set. All top-20/top-50 and frequency-band details are retained in the anchor audit.

### Cost and diagnosis

The three random chains used 76.98 seconds of search time in total; frequency
chains used 112.54 seconds. Peak RSS was about 448 MB and 461 MB respectively
(process high-water marks, not per-object allocations). Loading/evaluation time
is additional; one evaluation ran alongside frequency search, so timings are
approximate. The million-form vocabulary is feasible for this sparse experiment;
this does not imply exhaustive search or adequate candidate coverage.

A supplementary evaluation-only reference assigns every covered word correctly
and uses distinct untrained forms for the 843 missing types. Its score is
-217,810.15; forward/reverse proxy choices agree exactly. Random recovered keys
score -231,974 to -232,483, so this particular near-correct reference ranks higher
than all random outputs. Frequency outputs score -159,214 to -159,415, much
higher than that reference despite their poor literal recovery. This establishes
both that the short random searches have not reached even that reference score,
and that the current objective can prefer very wrong keys to a mostly correct
one. It does not identify the global optimum or isolate the cause. The reference
never enters inference and is not counted as a recovery result.

Potential contributors include the small/domain-mismatched corpus, very sparse
contexts for target content words, the uniform treatment of untrained forms,
proposal coverage, and insufficient search. This experiment does not distinguish
them. It does **not** support a general claim that Latin is unidentifiable, nor
that additional iterations alone would solve it.

The useful positive signal is narrow: independently found `et` is a genuine
anchor at 479 positions. Comparable English-level structural-word coverage has
not yet been demonstrated. No algorithm defaults were changed or inferred
mappings frozen. All **124 relevant tests pass**, including a crafted unanimous-
wrong-anchor case verifying that apparent agreement does not inflate precision.

Artifacts under `experiments/results/scalable-latin-caesar/v1/`:

- `summary.json`: literal and primary anchor summaries for both initializers.
- `resources/{protocol,report,source-audit}.json`: frozen provenance/exclusions.
- `fixture/evaluation-only/`: truth, coverage, provenance, objective reference.
- `{random,frequency}/anchors-evaluation.json`: every mapping, restart alternatives,
  top-frequency tables, threshold grid, frequency bands and possible word classes.
- `{random,frequency}/inspection.md`: five fixed original/restored 100-token excerpts.
- `{random,frequency}/seed-*/checkpoint.json`: complete resumable search states;
  live traces and original inference/evaluation reports remain alongside them.

## Follow-up without target-specific hints

The [target-independent follow-up](scalable_latin_target_independent.md) tests
20,000-proposal searches, observed/full-inventory proposal sampling, and existing
three-word cycles with unchanged resources. None improves frequent-anchor
recovery reliably. Most frequent correct candidates were already considered;
all 100 available wrong frequent assignments in original saved keys lower the
score when individually corrected. This supports investigating score/local-search
mismatch without adding topic or vocabulary hints. All 126 relevant tests pass;
no defaults change.

The subsequent [profile/association comparison](scalable_latin_profiles_association.md)
adds no target-specific knowledge. Profile starts yield 2/50 correct shortlist
mappings and no frequent unanimous anchors; the original frequency control has
3/50. Both skip-association variants give 0/50. The association objective rates
an entirely unobserved-form dictionary above a nearly correct reference, exposing
a neutral-node failure. All 132 relevant tests pass; no defaults change.

The [learned-class and confidence follow-up](scalable_latin_classes_confidence.md)
rejects its class score at a development gate. A separate confidence model, fit
only on one non-training work and checked on another, filters Caesar to `in` and
`et` at the exploratory .5 cutoff. The fixed high-trust validation requirement
fails; the .8 rule selects no Caesar mappings. Top-50 precision remains 3/50.
No defaults change; all 138 relevant tests pass.
