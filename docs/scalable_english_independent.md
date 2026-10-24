# Independent-work English benchmark and frequency initialization

Predeclared experiment: compare random and frequency-ranked initialization on
the same frozen resources, public cipher and seeds (3, 5, 7), at 8,000 proposals
per seed. Keep the mixed scheduler and all other search/retrieval settings.
Each three-seed bundle receives 1,200 seconds of search budget and 30 seconds
reserve, divided across seeds. Both use live public-only diagnostics.
Incomplete runs must not be presented as an equal-proposal comparison.

The source model uses EWT training documents plus the continuous prose of
Jane Austen's *Pride and Prejudice*. Its inventory is the union of normalized
CMUdict entries and training forms. The model and inventory were built before
downloading the target. The CMUdict revision is pinned:
`74790861f652b15e4ac49015a90074ad62a27690`.

The evaluation text is the first 35,000 scoring tokens after the prose incipit
of H. G. Wells's *The War of the Worlds*. There is one continuous document.
Sentence/paragraph boundaries, punctuation, topic, title and vocabulary are
not supplied to inference. Chapter headings within the prose body remain.
The prefix is fixed without vocabulary filtering. Missing words are counted
as unrecoverable; they are never inserted into the inventory.

These are older literary works, so this improves independence and continuity
without establishing contemporary broad-domain performance. EWT may include
incidental quotations: the preparation audit checks exact normalized 12-token
windows rather than making an unconditional contamination claim.

## Frozen resources and preparation audit

- Training: 298,475 tokens in 541 documents; 141,593 observed bigram edges.
- Inventory: 126,896 forms, including 108,574 absent from LM training.
- Target: 35,000 tokens, 4,872 cipher types, one document.
- Missing inventory: 340 types / 620 tokens.
- Literal recovery ceiling from inventory coverage: 98.23% of tokens,
  93.02% of types.
- LM-attested target types: 3,149; LM-attested token fraction: 90.51%.
- Exact shared 12-token windows with training: 0 of 34,989 distinct target windows.

Source resources are frozen independently of target coverage. The 98.23%
ceiling describes vocabulary availability, not achievable recovery. Dictionary-only
words receive positive backoff probability but have no learned context statistics.

## Initialization implementation

`SearchConfig.initialization` and CLI `--initialization` accept `random`
(the historical default) and `frequency`. Frequency initialization ranks cipher
types by public occurrence counts and model words by training unigram counts,
matching ranks injectively. Ties use ascending opaque type/inventory IDs.
It uses no sentence boundaries, target words or gold statistics.
There is no dense type-by-vocabulary matrix.

Frequency starts share the same initial key across seeds; search and retrieval
remain stochastic. These are three search trajectories from one frequency key,
not three independently sampled frequency keys. Both methods retain the initial
key in the score-ranked archive, so the reported winner can be the initial
hypothesis if optimization finds no better score.

Historical checkpoints/protocols without this field retain random initialization.
Evaluation reconstructs the actual configured initializer, reports its literal
accuracy and checks its score. Inventory coverage and LM attestation are
evaluation-only measurements. Diagnostic validation accepts absent gold words
without adding them to the model.

## Provenance

- [Project Gutenberg: The War of the Worlds](https://www.gutenberg.org/ebooks/36)
- [Project Gutenberg: Pride and Prejudice](https://www.gutenberg.org/ebooks/1342)
- [CMUdict source](https://github.com/cmusphinx/cmudict/tree/74790861f652b15e4ac49015a90074ad62a27690)
- [CMUdict license](https://github.com/cmusphinx/cmudict/blob/74790861f652b15e4ac49015a90074ad62a27690/LICENSE)
- Existing EWT source/license manifest: `data/raw/scalable-english/`.

Raw downloads, hashes and licenses are retained locally in
`data/raw/scalable-english-independent/`. Original Gutenberg notices are retained.
No grammar or semantic accuracy is inferred from literal matches.

## Reproduction and artifacts

Frozen resources: `experiments/results/scalable-english/independent-resources-v1/`.
Prepared cipher and private audit:
`experiments/results/scalable-english/independent-wells-35k-v1/`.

```sh
.venv/bin/python -m benchmarks.scalable_english_independent build --ewt data/raw/scalable-english/en_ewt-r2.17-train.conllu --austen data/raw/ravi-knight-english/1342.txt --lexicon data/raw/scalable-english-independent/cmudict.dict --output experiments/results/scalable-english/independent-resources-v1
.venv/bin/python -m benchmarks.scalable_english_independent prepare --resources experiments/results/scalable-english/independent-resources-v1 --source data/raw/scalable-english-independent/36.txt --output experiments/results/scalable-english/independent-wells-35k-v1
.venv/bin/python -m benchmarks.scalable_english_run --resources experiments/results/scalable-english/independent-resources-v1 --public experiments/results/scalable-english/independent-wells-35k-v1/public/cipher.json --output experiments/results/scalable-english/independent-wells-random-8000-v2 --initialization random --proposals 8000 --budget-seconds 1200 --reserve-seconds 30 --trace
.venv/bin/python -m benchmarks.scalable_english_run --resources experiments/results/scalable-english/independent-resources-v1 --public experiments/results/scalable-english/independent-wells-35k-v1/public/cipher.json --output experiments/results/scalable-english/independent-wells-frequency-8000-v2 --initialization frequency --proposals 8000 --budget-seconds 1200 --reserve-seconds 30 --trace
```

All output paths are exclusive; use fresh names for reruns. After search, evaluate
each run with `scalable_english_evaluate`, `scalable_english_diagnostics` and
`scalable_english_diagnostics_validate`, supplying the new resources, the
prepared truth, each run's `traces/`, and an `analysis/` output directory.
`scalable_english_compare_initialization` checks equal completed horizons and
protocol equality except initialization before producing paired results.

The original random v1 attempt stopped at the first 500-step validation:
ordinary summation over one 35k-token document differed from cached scoring by
more than the 1e-8 absolute check. A diagnostic reproduction showed a
2.5e-8 discrepancy; `math.fsum` reduced it to 3.5e-10. The document scorer
now uses stable streaming summation, with the validation tolerance unchanged.
A 50,000-token regression test checks the analytic score, chunk invariance and
incremental validation. The failed attempt is preserved with
`attempt-status.json`; both compared bundles use fresh v2 paths and the same
corrected scorer. Probability distributions and move scoring are unchanged.

## Dictionary-only ambiguity

All 108,574 dictionary-only forms share the same base probability and have
no observed incoming/outgoing edges. Under this model their identities are
statistically interchangeable: exchanging two such forms leaves the score
unchanged. A unit test explicitly checks this property.

9.49% of target tokens are absent from LM training (including 1.77% absent
from the inventory). Merely adding their spellings to a large dictionary
does not supply evidence for distinguishing them. The inventory ceiling is
therefore an availability measure, not a practical score-based recovery forecast.
Broader LM training or shared lexical/morphological representations will be
needed to address this class of ambiguity. The initialization experiment does
not change those statistics.

## Matched results

All six v2 runs completed 8,000 proposals. Random remains the library default;
frequency initialization is an explicit, useful alternative to include in
restart bundles.

| Seed | Random literal token accuracy | Frequency-start literal token accuracy | Random correct types | Frequency-start correct types |
| --- | ---: | ---: | ---: | ---: |
| 3 | 26.90% | 34.10% | 27 | 37 |
| 5 | 26.54% | 20.08% | 23 | 18 |
| 7 | 27.68% | 34.91% | 25 | 42 |
| Mean | **27.04%** | **29.70%** | **25.00** | **32.33** |

The frequency-only initial key achieves 9.39% literal token accuracy for every
seed. Random initial keys achieve 0% in these three draws. Search therefore
adds substantial recovery to both initializers. It raises source-model scores
throughout, but source-score ranking remains an imperfect literal selector.

Source-score-only selection chooses random seed 3 (26.90%) and frequency seed 7
(34.91%). That is an 8.01 percentage-point improvement between selected results;
the mean paired improvement is 2.66 points. Seeds 3 and 7 improve, while seed 5
loses 6.46 points. Three trajectories on one work do not establish a universal
advantage or statistical reliability. Frequency starts all share one initial key.

| Mean over three seeds | Random | Frequency start |
| --- | ---: | ---: |
| Correct types out of 4,872 | 25.00 | 32.33 |
| Primary types visited | 3,274.00 | 3,264.33 |
| True assignments ever offered, including implied swaps | 166.00 | 214.00 |
| Elapsed search time per seed | 166.56 s | 206.16 s |

Candidate support improves, but most true assignments are still never offered.
Even the best frequency run recovers only 42 of 4,872 types (0.86%), accounting
for 34.91% of tokens because they are mostly frequent words. The selected random
run recovers 27 types (0.55%). Do not interpret either token percentage as
grammar or meaning recovery.

Across seeds, mean literal token accuracy among types occurring 100+ times
rises from 59.03% to 65.09%. Among singletons it rises from 0% to 0.013%;
rare-word recovery remains negligible. The middle 20–99 occurrence band declines
slightly on average, so the improvement is not uniform across frequencies.

Total recorded search time is 499.68 seconds for random and 618.47 seconds for
frequency starts (about 18.64 minutes combined). Peak process RSS is approximately
136 MB and 141 MB, respectively. Costs include live trace/checkpoint work and
exclude resource loading and subsequent evaluation. This demonstrates the
126,896-form test within workstation resources; it does not establish
million-form performance with a much larger trained edge graph.

## Fixed excerpt

This is the first predeclared inspection position, not a favorable passage
selected after seeing recovery. Text is normalized and unpunctuated.

Original:

> no one would have believed in the last years of the nineteenth century that this world was being watched keenly and closely by intelligences greater than man's and yet as mortal as his own that as men busied themselves about

Selected random-start restoration:

> so one can never excuse for the monday competitive of the jewish plot that my word was often perfectly cheeseman and beverly had bichsel sad ppl adduct and future as brazen as your brother that as work faith embarrassed are

Selected frequency-start restoration:

> very you they are introduced in the following account of the hurst merely that this order is always finally clan and san be syria transfer jane parents and soon as hills as his own that as more info credit by

Some function-word frames survive, but neither excerpt recovers coherent
original meaning. This is qualitative inspection, not grammatical or semantic
adjudication. Both run directories contain five fixed excerpt positions in
`analysis/inspection.md`.

## Validation, decision and remaining work

109 relevant tests pass. New coverage includes deterministic injective rank
initialization, frequency-start checkpoint continuation, legacy defaults, a
public-only pipeline with source/truth files unavailable, missing-form
accounting, frozen-input changes, strict prefix length, pronunciation-variant
normalization, long-document numeric stability, dictionary-only ambiguity,
and rejection of comparisons confounded beyond initialization.

Both bundles pass checkpoint/current/archive full-score validation and
candidate/move final-key consistency. Independent full-stream rescoring verifies
14 accepted correct-assignment displacement events for random and 23 for
frequency starts. All 340 absent types remain explicitly classified as
`inventory_absent`; no target-derived forms enter the frozen inventory.

Full machine-readable comparison:
`experiments/results/scalable-english/independent-wells-initialization-comparison-v1.json`.

```sh
.venv/bin/python -m benchmarks.scalable_english_compare_initialization --random experiments/results/scalable-english/independent-wells-random-8000-v2 --frequency experiments/results/scalable-english/independent-wells-frequency-8000-v2 --output experiments/results/scalable-english/independent-wells-initialization-comparison-v1.json
.venv/bin/python -m pytest tests/unit/test_scalable_*.py tests/integration/test_scalable_*.py tests/unit/test_ravi_knight_*.py tests/integration/test_ravi_knight_*.py tests/integration/test_word_mapping_pipeline.py -q
```

Use a new comparison filename when reproducing; output is exclusive.

Retain both initializers. Frequency starts deserve inclusion in future
score-selected restart bundles, with random starts preserved for diversity.
A combined-budget portfolio has not been measured here. No search defaults
change based on one work and three seeds.

The next substantial bottleneck is candidate discovery and LM coverage:
only about 3.4–4.4% of true type assignments are ever offered, and dictionary-only
forms are indistinguishable under this model. Multi-occurrence contextual
retrieval, broader source training and eventually shared Latin morphology
remain candidates. Trigram scoring, a million-form trained inventory,
grammatical/semantic evaluation and Voynich restoration have not been implemented
in this increment.

Earlier EWT results cannot be used as a matched comparison with this benchmark:
plaintext, inventory, training corpus and document structure all changed.
