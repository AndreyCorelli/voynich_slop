# Latin trigrams and short phrase context

This bounded experiment adds adjacent three-word context to the frozen larger
Latin word model. It does not add topic hints, hidden vocabulary, supplied
sentence boundaries, guessed anchor translations or any change to the cipher
channel. Training, vocabulary and spelling normalization are unchanged from
[the larger-corpus experiment](scalable_latin_corpus_morphology.md).

## Model and source

The exact same 747 source/book streams contain **5,935,259 tokens**. The shared
inventory has **2,666,235 forms**. Independent counting finds **5,111,173 distinct
trigrams**; **4,745,495 (92.85%)** occur only once. This is substantial surface
sparsity, even after increasing source data. Distinct-trigram singleton percentage
is not the fraction of test tokens unsupported by the model.

The existing normalized absolute-discount trigram model is reused:

`P3(c|a,b) = max(n(a,b,c)-d,0)/n(a,b)
            + d*distinct(a,b)/n(a,b) * P2(c|b)`

`P(c|a,b) = (1-w)*P2(c|b) + w*P3(c|a,b)`.

Unobserved two-word contexts back off to P2. Discount d=.5; mixture weights
w=.25, .5 and .75 are frozen before outcomes. Probabilities normalize over the
full inventory plus EOS, retaining positive support for dictionary-only forms.
BOS/EOS occur only at actual source/book boundaries. Training sentences are not
exposed as boundaries, and arbitrary scoring chunks do not reset context.
This is adjacent three-word phrase modeling, not longer-range syntax.

Training stream hash exactly matches the frozen bigram parent. Projecting every
trigram onto its final pair reproduces the parent's complete pair counts; the
model constructor verifies this equality. The original language/tokenization
contract remains `la / latin-iu-continuous-v1`. The optional `config` argument
added to the existing trigram training API preserves English defaults and permits
correct Latin metadata when using that API directly.

Construction and serialization took 47.93 seconds; peak process RSS was 3.74 GB.
The model SQLite artifact is approximately 156 MB, in addition to the shared
inventory. These are measured build costs, not guarantees at larger scales.

## Development selection and interpretation

Use the same three author-held-out development works: Apuleius I, Curtius III,
and Suetonius Augustus. Truth supplies evaluation controls only, never training
forms, candidate lists or actual search starts. Covered reference words are
correct and missing forms use distinct unobserved proxies. Inventory token
coverage is 94.25%, 98.19% and 97.13% respectively, limiting interpretation of
reference scores as true Latin likelihood.

The original bigram already fails reference-versus-frequency likelihood tests.
Therefore this new experiment explicitly declares an **incremental context gate**
before any trigram outcomes: on at least two of three works, the reference must
beat null/random keys and median 10/25/50% corrupted keys, and the trigram-minus-
bigram contribution must favor the reference over the frequency key. Full
reference-versus-frequency likelihood remains separately reported; passing this
incremental check does not establish an adequate global objective.

All three weights pass the incremental checks on all three works. Choose the
weight with the greatest pooled reference-minus-frequency per-token score margin;
ties prefer .5 then the lower weight. This selects **w=.75**, before inspecting
new reconstruction results.

| Weight | Pooled reference minus frequency, per token/event |
|---|---:|
| .25 | -.94486 |
| .50 | -.92425 |
| .75 | -.90445 |

The original bigram margin is approximately -.9878. Three-word context narrows
that gap, but **all full likelihood comparisons still favor the wrong frequency
key**. Previously optimized wrong Apuleius smoke keys are also retained as stronger
controls, rather than claiming that the initial frequency key exhausts wrong
reconstructions. Gate success justifies a bounded actual decoding test, not a
claim of restored meaning or a correct global optimum.

## Paired comparison on inspected Gellius

Gellius I has 9,670 continuous normalized tokens. It was already inspected during
the previous objective experiment, so this is a replication/comparison and is
not labeled fresh validation. The three existing bigram control chains are reused
only after model/cipher identities, complete search/retrieval protocols and all
initial dictionary assignments match. The only protocol difference is model
identity; the new score uses trigram events and the old score uses bigram events.

Both methods use frequency initialization, seeds 3/5/7 and 4,000 proposals per
chain, with a 600-second allowance per chain. The full injective dictionary,
existing bigram candidate retrieval, annealing, random exploration and candidate
budgets are unchanged. All occurrences affected by replacements/swaps/cycles are
scored using the full respective model. No trigram-specific candidate index is
added in this first inexpensive experiment; candidate generation can therefore
miss proposals valuable mainly for their three-word contexts.

| Method | Seed 3 | Seed 5 | Seed 7 | Mean token recovery | Score-selected run | Correct / top 50 |
|---|---:|---:|---:|---:|---:|---:|
| Bigram control | 7.78% | 6.88% | 6.70% | 7.12% | 6.88% | 3/50 |
| Trigram .75 | 7.48% | 10.90% | 8.55% | **8.98%** | **8.55%** | 3/50 |

Mean literal recovery gains **1.86 percentage points**. The source-score-selected
run gains 1.68 points. The best literal seed is not selected by truth. The top-50
list is ranked by agreement first, then public frequency, with opaque-ID ties;
it is not a calibrated 50-word dictionary.

The primary unanimous-three-run/public-count>=100 set becomes cleaner:

- Bigram: five types, two correct (`et`, `in`); wrong `est→non`, `non→est`,
  `quod→ut` (original→restored).
- Trigram: two types, both correct (`et`, `in`), covering the same 508/9,670
  correct positions, **5.25% token coverage**. The three false primary anchors
  are no longer unanimous.

This is an observed precision/coverage improvement, not validated 100% accuracy
on new data. All chains share frequency initialization, and two correct types
provide little statistical support. The majority pool has seven correct types
among 2,176 proposals, versus six among 2,176 for bigram; it still cannot supply
a reliable 50-word nucleus through ranking alone.

The frozen rule for fresh confirmation is: mean gain >=1 point without top-50
regression, or >=2 more correct top-50 mappings without mean regression, or more
correct primary anchors without more wrong primary anchors. Gellius meets the
first criterion. No additional weight or search setting is tuned on Gellius.

## Fresh Livy confirmation

After selecting and freezing .75, compare the original bigram and that trigram
model on previously untested Livy I (16,983 tokens). Livy is excluded author-wide
from source text and annotated resources. Its original source split is sealed;
only this work is opened after the frozen-method promotion check. Ammianus XIV
and Quintilian I remain sealed. The same seeds, proposal caps and other settings
apply. No fresh result is used for retuning or selecting a favorable seed.

All six matched chains complete 4,000 proposals and pass full-score checks.

| Method | Seed 3 | Seed 5 | Seed 7 | Mean token recovery | Score-selected run | Correct / top 50 |
|---|---:|---:|---:|---:|---:|---:|
| Bigram control | 0% | .49% | 1.91% | **.80%** | .49% | 0/50 |
| Trigram .75 | 0% | .74% | 0% | .25% | 0% | 0/50 |

The fresh mean regresses by **.55 percentage points**. Neither method produces
any correct primary unanimous frequent mapping: bigram selects three wrong
types, and trigram selects six wrong types. The trigram set is `in→et`,
`et→non`, `ad→in`, `cum→ut`, `ut→est`, `ab→ad` (original→restored).
Strong agreement again reflects shared model/initialization error rather than
validated translation confidence. The entire majority pools contain 1/4,225
correct types for bigram and 0/4,240 for trigram.

This low recovery is not explained by a low vocabulary ceiling: 98.40% of token
positions are covered, and words at 96.87% of positions were observed in source
training. Coverage is not contextual knowledge or a recovery guarantee. Both
methods start from the same frequency key at 1.53% literal accuracy; optimizing
their language scores can move away from truth. These observations do not
isolate the relative roles of initialization, objective, retrieval, corpus
mismatch and sparse phrase evidence, and do not establish an intrinsic Latin
limitation.

**Decision:** the Gellius gain does not transfer to this fresh work. Do not
promote the trigram model or claim a reliable Latin nucleus. Preserve the .75
experimental resource and all outcomes, keep global defaults unchanged, and
leave Ammianus/Quintilian untested. This rejects this particular short-context
model/search combination as a general improvement; it does not rule out richer
context models or improved trigram candidate generation.

New search times are 286.80 seconds for Gellius trigrams, 193.47 for fresh Livy
bigrams and 353.87 for fresh Livy trigrams: about 13.9 minutes total, excluding
resource loading, source build, development screening and external evaluation.
The reused Gellius baseline used 162.15 seconds previously. Trigram peak process
RSS is about 4.22 GB on Gellius and 4.37 GB on Livy. Proposal caps are matched;
actual compute costs are not equal. No weight or restart is retuned after the
fresh result.

## Integrity, implementation and artifacts

The training builder reads only independent source records and the generated
inventory. Public fixtures and private evaluation are separate; each actual trial
uses its own fixture copy and renames private evaluation material during search.
Saved current/archive keys are independently rescored by the occurrence-level
scorer and checked against checkpoints. Consensus extraction uses only public
inference traces/keys; truth is used separately to evaluate its accuracy.
Fixed first/midpoint 100-token original/restored
excerpts are retained instead of choosing favorable passages.

Existing trigram normalization, exhaustive tiny dictionary deltas, serialization
and checkpoint tests are reused. A new Latin end-to-end test checks the language
contract, exact control-score aggregation across all three weights, normalized
conditionals and a three-seed public-only run with truth created after inference.
All **155 relevant tests pass**, and every real current/archive key passes the
independent occurrence-level/checkpoint evaluator. Numerical correctness is not
evidence of semantic restoration.

Driver: `benchmarks/scalable_latin_trigram.py`. Run `build`, `screen`,
`replication`, then `confirm` only when the frozen criterion passes, and
`summarize`. Use the same new `--output` root for each stage; initial construction
requires exclusive new output. Cached larger-corpus resources are prerequisites;
no new download or neural dependency is required. Artifacts live under
`experiments/results/scalable-latin-trigram/v1/`:

- `design.json`, `development.json`: predeclared grid, controls, gate scope and selection.
- `resources/`: shared inventory, new trigram model and source/cost identities.
- `fixtures/`, `isolated-fixtures/`: public ciphers and separate private truth/provenance.
- `replication-trigram/`, `replication-comparison.json`: all Gellius chains,
  numerical/literal/anchor checks, traces and fixed excerpts, plus paired controls.
- `confirmation-*`, `confirmation-comparison.json`: frozen fresh-work comparison.
- `summary.json`: final result, resource statistics and decision.

No global decoder or model defaults change automatically.
