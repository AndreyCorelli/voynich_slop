# Context profiles and association alignment for Latin

This is an exploratory comparison on the same frozen Caesar fixture, independent
Latin corpus, and full 2,557,237-form inventory as the [original benchmark](scalable_latin_caesar.md).
No topic matching, target vocabulary, annotations, guessed translations, or
inferred anchors enter inference. Latin and the synthetic injective whole-word
channel remain assumptions. Truth is used only for post-hoc evaluation.

## Context-profile initializer

Nine numerical features describe each observed type: relative frequency and,
separately for left and right neighbors, diversity, entropy, mean neighbor log
frequency, and the fraction of occurrences beside frequency-selected common
neighbors. The common-neighbor reference set is chosen from counts alone (the
32nd frequency cutoff, with ties included); it is not a function-word lexicon.
BOS/EOS are excluded. Raw features use adjacent contexts, with no sentence resets.

Source and target features are separately transformed to within-corpus midrank
percentiles. The frequency coordinate is half-weighted. Source profiles cover
all training-observed forms (26,614 here), not target-selected forms. Unobserved
forms lack a contextual profile. A KD-tree retrieves 64 nearest source profiles
per cipher type; greedy matching visits high-frequency types first and preserves
injectivity. If its candidates are occupied it draws an unused word from the
full inventory. Subsequent search always retains the complete vocabulary.

Each seed adds fixed Gaussian jitter (.025 in percentile space) before matching.
This varies starting keys but does not make their shared feature/model bias
independent. Initial and final consensus are reported separately; apparent
stability is never treated as a calibrated probability.

## Association discrepancy objective

The second test changes the objective rather than merely reducing unigram
frequency pressure. It pools directional word-pair counts at distances 1, 2,
and 4, never crossing actual document endpoints. All 13 original training work
streams are reused. This yields 507,209 pair occurrences and 342,811 distinct
source pairs; no new training text is added.

For each graph, with pair count `n`, outgoing/incoming margins `r`/`c`, and pair
total `T`, define:

```
association(a,b) = clip(log((n(a,b)+1) / (r(a)*c(b)/T + 1)), -3, 3)
weight(a,b) = n(a,b) / (n(a,b)+5)
S(key) = -sum weight(a,b) * (target_association(a,b)
                           - source_association(key[a],key[b]))**2
```

Target terms depend only on the public cipher graph. Source terms use the frozen
training graph. Zero-source-count forms receive well-defined zero association;
they remain eligible. Constants and distances are fixed before results, without
truth-based tuning. Unobserved target pairs are not scored. Add-one smoothing
and corpus-size differences remain modeling limitations.

This is an **unnormalized graph discrepancy**, not a language-model likelihood.
Its maximum is zero. An identical source/target graph scores zero under the
correct mapping; that mathematical test does not imply success on independent
text. No BOS/EOS scores or sentence boundaries are introduced. For multiple
actual documents target factors are calculated per document, matching full
scoring; the source graph pools the independent training work streams.

The existing adjacent-LM retrieval remains unchanged and supplies proposals.
This is a heuristic mismatch to the new objective, explicitly retained to keep
the first experiment bounded. Dictionary moves score every affected skip edge
exactly, including simultaneous swaps/cycles and all occurrences. Checkpoints
bind the objective identity, distances and full sparse source counts. Independent
full scoring recomputes the target graph from decoded ID sequences; injectivity
preserves its public structure.

## Frozen experiment

Three variants, seeds 3/5/7, 4,000 proposals per chain:

1. Profile starts with the original bigram score.
2. Random starts with association discrepancy.
3. Profile starts with association discrepancy.

The original random/frequency runs are controls. The association inventory hash
and parent bigram identity must equal the originals. Raw scores across objectives
are not comparable. Designs and constants are saved before inference.

The main metrics are agreement-first top-10/20/50 word-type precision and the
original unanimous-three-run/public-count>=100 anchor rule. Votes are ranked
before public occurrence count, with opaque-ID tie breaking, exactly as in the
previous English/Latin shortlist audit. Vote-1 padded lists can contain conflicting
assignments and are not high-trust dictionaries; vote histograms, duplicate
predictions and majority-only metrics are retained. No quota is presented as an
actual calibrated nucleus. Initial shortlist accuracy/diversity is reported too.

Every completed key/archive is checked by full rescoring. Unit tests enumerate
all tiny injective keys and replacement/swap/cycle moves, include multiple actual
documents and singleton documents, verify serialization and exact checkpoint
continuation, and reject incompatible event indexes. A complete public-only
profile/association pipeline runs with truth unavailable during inference.
All 132 relevant tests pass. These checks establish numerical implementation,
not linguistic validity.

## Reproduction

```sh
.venv/bin/python -m benchmarks.scalable_latin_profiles_association
```

Requires the existing original Latin fixture/resources and the already declared
`word-mapping` optional dependencies (NumPy/SciPy). Outputs are exclusively created
under `experiments/results/scalable-latin-caesar/profiles-association-v1/`.
Source hashes and Caesar exclusions are inherited from the original frozen
resource protocol; the builder accepts no target or truth argument. The original
resource files remain unchanged. No defaults change.

## Results

All nine new chains complete 4,000 proposals. Their current and archived keys
pass independent full rescoring. Initial keys match exactly between profile/LM
and profile/association at each seed, and between the original random baseline
and random/association; the objective comparison does not secretly change the
starting dictionary. The experiment is exploratory, with no fresh held-out work.

| Method | Correct / top 10 | Correct / top 20 | Correct / top 50 | Primary frequent anchors: correct / wrong |
|---|---:|---:|---:|---:|
| Original random starts | 1/10 | 1/20 | 1/50 (2%) | 1 / 0 |
| Original frequency starts | 3/10 | 3/20 | 3/50 (6%) | 2 / 2 |
| Profiles + original LM | 0/10 | 0/20 | 2/50 (4%) | 0 / 0 |
| Random + association | 0/10 | 0/20 | 0/50 | 0 / 0 |
| Profiles + association | 0/10 | 0/20 | 0/50 | 0 / 0 |

These are the fixed agreement-first shortlist metrics, not token-weighted
accuracy. The profile/LM shortlist's two correct mappings are `in` and `et`,
both supported by two runs. Its first 38 entries are unanimous and wrong;
unanimity alone again fails as confidence. Profile initializers share 210
unanimous initial type assignments, and their initial top-50 lists contain zero
correct mappings. Jitter provides diversity but does not eliminate shared errors.

As an explicitly post-hoc descriptive check, ranking by frequency first gives
3/50 for profile/LM and 3/50 for the original frequency baseline, versus 2/50
for original random starts. Both association variants still give 0/50. This
alternative does not establish an improved reliable nucleus, and it does not
replace the predeclared ranking.

The random-association top-50 list has only six two-run agreements and 44
single-vote padded guesses. Profile-association has 19 unanimous and 31 two-run
agreements in its top 50, all wrong. Neither is a trustworthy 50-word dictionary.
No new variant has a unanimous mapping with at least 100 public occurrences;
precision of an empty anchor set is undefined, not a claim of perfect reliability.

Mean literal token recovery is 3.72% for profile/LM, 0.0244% for
random/association and 0.0212% for profile/association. Source-score-selected
literal recovery is 5.39%, 0.0732% and 0% respectively. A favorable individual
run does not offset failed shortlist precision or justify selecting by truth.

### Objective controls and failure interpretation

A supplementary evaluation-only reference decodes covered words correctly and
uses distinct untrained inventory forms for the 843 missing types. It is not an
inference output or optimum bound. Forward/reverse proxy choices give identical
scores. A second, public control assigns every cipher type to a distinct
training-unobserved form; its word identities are uninformative and it is not a
recovery result. Neither control enters search or changes parameters.

Under the association objective:

- Nearly correct feasible reference: **-5,091.14**.
- Entirely unobserved-form control: **-4,755.27**.
- Best random-start output: **-4,521.49**.
- Best profile-start output: **-4,428.42**.

Higher is better. Thus this association formulation rates a completely
uninformative key above the nearly correct reference. When either endpoint is
unobserved in the source, its source association is zero: such forms act as
neutral nodes. Avoiding mismatched associations can therefore improve the score
without restoring word identities. The null control is not itself a claimed
optimum, and its ranking does not isolate all causes of failure. The inherited
adjacent-LM retrieval, unchanged annealing temperatures in different score units,
source/target sampling differences, smoothing and corpus mismatch may also matter.

The profile/LM feasible reference scores -217,810.15, below that variant's found
key (-170,387.55), consistent with the earlier original-objective mismatch.
These raw values must never be compared to the association score scale.

**Decision:** retain the implementations as experimental options; change no
defaults. This profile design does not produce a reliable nucleus, and this
association loss fails the uninformative-key control. The results do not rule
out other structural methods or imply an intrinsic Latin limitation. A future
association/class model needs to distinguish unsupported evidence from a good
structural match; simply rewarding a smaller graph discrepancy is insufficient.

### Cost, artifacts and validation

The three variants used 88.53, 162.79 and 193.10 seconds of search respectively:
444.42 seconds total (7.41 minutes), excluding build, loading and evaluation.
The resource build used 2.81 seconds. Peak RSS reached 830 MB in the shared
experiment process, including earlier loading/evaluation allocations; this is
not a separately isolated per-model memory comparison. No dense cipher-by-full-
inventory matrix is constructed: source profile vectors cover observed forms,
KD queries keep 64 neighbors, and association factors/updates are sparse.

All **132 relevant tests pass**. The final evaluation was rerun under the final
implementation and exactly reproduces the saved metrics. Parent model/inventory
bindings and the paired initial keys are verified; saved keys, raw traces, and
source-only selection remain available for review.

Under `experiments/results/scalable-latin-caesar/profiles-association-v1/`:

- `design.json`, `summary.json`: fixed protocol and complete comparative results.
- `association-resources/`: frozen source graph, original inventory, provenance.
- Each variant's `shortlists-evaluation.json`: selected 10/20/50 mappings, votes,
  correctness, majority-only metrics, initial shortlists and shared-start counts.
- `anchors-evaluation.json`, `inspection.md`: anchor precision/coverage and five
  fixed original/restored excerpts.
- `objective-diagnostics.json`: feasible reference and uninformative-key control.
- `inference.json`, `seed-*/checkpoint.json`, `traces/`: complete search artifacts.

Original control keys are preserved; their supplementary shortlist audits are
separate files in their existing run directories.
