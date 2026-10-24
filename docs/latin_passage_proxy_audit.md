# Passage-level grammatical anomaly audit

Run: 2026-10-12. **Aggregation improves some relative comparisons, but the tested passage objectives do not establish reliable grammaticality discrimination or monotonic improvement with length.** This is an objective audit; no new dictionary search was run.

## Design

Use the full eligible sentences of 11 annotated Latin works (24,404 words). Fit/calibration/test retain the earlier author/work split: four fitting works, three calibration works, four test works. These authors were already examined in the earlier sentence experiment, so this is an exploratory extension, not a fresh independent confirmation. No test rows select weights or thresholds in this run.

For each work generate one original, two globally consistent inflection-corruption mappings and two grammatical noun-substitution mappings. Generated maps are injective, and replacement targets do not occur in the original work: every occurrence of a source form changes consistently. Negative substitutions come from the earlier recorded agreement/government witnesses and preserve the dictionary lexeme and other inflection features. Lower corruption uses one quarter of the eligible changed types; higher uses all eligible types. Grammatical noun substitutions require every occurrence of a source form to have the same annotated noun case/number/gender, preserved by the replacement. Controls match the number of changed tokens in each complete work exactly. They may change meaning.

Damage is deliberately sparse: lower tier changes 0.24–1.12% of words; higher tier changes 0.92–5.42%. Eligible mappings were selected from earlier curated mutations, not exhaustive corruption of the corpus. A changed token is not necessarily a grammatical violation in every context. Labeled negative blocks must contain at least one recorded source dependency witness. Gold annotations are used for curation and audits only; scorers receive decoded words.

Evaluate nonoverlapping blocks that reach 250 or 1,000 words without breaking sentences, and complete works. Incomplete fixed-width tails are discarded. Length comparisons are correlated and use different available blocks; they are not repeated independent trials. Complete test works have 627, 745, 1,612 and 4,204 words. Only Cicero and Sallust supply 1,000-word blocks; only Sallust supplies a test passage beyond 3,000 words.

Nine unchanged proxy implementations are applied to each sentence: two neural masked scores, unigram/bigram/trigram, morphological sequence, adjacent/marginal agreement and dictionary coverage. Dictionary lookup is expanded to all required words. Neural contexts are capped at 64 words by splitting longer sentences consistently; no silent truncation occurs. Statistical training remains the earlier disjoint Caesar corpus. Neural pretraining exposure to these works is unknown.

Passage features are (a) token-weighted means of the nine scores, (b) nine token-weighted low-score sentence rates, using feature-specific tenth-percentile thresholds estimated from fitting originals only, and (c) the token-weighted sentence acceptance rate under the earlier combination coefficients/threshold. This last feature transfers earlier coefficients to the expanded-resource/local-context scores, rather than reproducing the old sentence benchmark unchanged. Tail rates are negated so higher means better. We did not implement new dependency inference or direct violation counting: these are anomaly proxies.

Fit-standardized features feed nonnegative and signed balanced logistic combinations. Calibration chooses among five ridge penalties and fixes classification thresholds. Each single feature also receives a calibration-only threshold. All lengths share a single calibration setting. Selection was saved before test scoring. The calibration-selected single feature is sentence acceptance rate.

## Held-out results

| Scorer | Length | Balanced accuracy | Original beats corruption | Pairs |
|---|---|---:|---:|---:|
| passage_nonnegative | 250 | 51.9% | 94.1% | 34 |
| passage_nonnegative | 1000 | 50.0% | 90.0% | 10 |
| passage_nonnegative | whole_work | 50.0% | 87.5% | 8 |
| passage_signed | 250 | 55.2% | 79.4% | 34 |
| passage_signed | 1000 | 60.0% | 80.0% | 10 |
| passage_signed | whole_work | 56.2% | 87.5% | 8 |
| neural_mean_piece | 250 | 50.0% | 100.0% | 34 |
| neural_mean_piece | 1000 | 50.0% | 100.0% | 10 |
| neural_mean_piece | whole_work | 50.0% | 100.0% | 8 |
| morphological_sequence | 250 | 51.9% | 94.1% | 34 |
| morphological_sequence | 1000 | 50.0% | 90.0% | 10 |
| morphological_sequence | whole_work | 50.0% | 100.0% | 8 |
| sentence_acceptance_rate | 250 | 57.2% | 41.2% | 34 |
| sentence_acceptance_rate | 1000 | 53.3% | 60.0% | 10 |
| sentence_acceptance_rate | whole_work | 50.0% | 87.5% | 8 |

Balanced accuracy averages acceptance of valid passages and rejection of corrupted passages. Pair accuracy asks whether each original scores above its own corrupted counterpart. Pair ranking is the more direct dictionary-search diagnostic when comparing candidates for the same ciphertext, although the true original is unavailable to a decoder. Passing that check alone is insufficient: grammatical alternative decodings should also rank well.

The neural mean ranks every original above its corrupted counterpart here, but its transferred classification threshold accepts all labeled test passages at every length. Its balanced accuracy is therefore 50%. The nonnegative combination also accepts all 1,000-word test passages. The signed combination gets 60% balanced accuracy there by rejecting 8/10 corruptions while accepting only 6/15 valid passages. At complete-work length it accepts only 6/12 valid passages.

Weighted pair accuracy is not monotonically better at greater lengths: nonnegative 94.1% → 90.0% → 87.5%; signed 79.4% → 80.0% → 87.5%. Because the evaluated works/blocks change with length, these numbers do not establish that length itself harms scoring either.

## Can it preserve grammatical alternative vocabulary?

The following whole-work comparisons use exact matching of changed-token counts between the grammatical noun mapping and damaging mapping. This is a post-hoc descriptive contrast; it did not select the objective.

| Scorer | Grammatical control beats corruption |
|---|---:|
| passage_nonnegative | 6/8 |
| passage_signed | 6/8 |
| neural_mean_piece | 7/8 |
| morphological_sequence | 8/8 |

**The strongest encouraging result is morphological-sequence ranking on the eight whole-work control comparisons.** This retains a signal when vocabulary changes, rather than merely favoring the original words. However, eight comparisons are two variants of only four works, including two works below 1,000 words; this is not established reliability at scale. A perfect observed rate can yield a degenerate bootstrap interval and still carry substantial uncertainty about new works or unseen mappings.

Neural whole-work ranking fails one of these grammatical-control contrasts despite perfect original-versus-corruption ranking. The weighted combinations fail two. Thus the objectives are still vulnerable when comparing structurally valid alternative vocabulary, which is the actual intended decoding criterion.

## Earlier optimizer stress mapping

The saved 32,000-word, greedy, seed-101 wrong dictionary is converted from cipher assignments back to source-word substitutions and transferred to recurring forms in the four test works. It is globally type-consistent but is not labeled a certified corruption of those new works; transfer may change grammatical structure, preserve it or introduce collisions with types outside the original dictionary. It is a supplementary stress test, not a classification negative or an adversarial training set.

- passage_nonnegative: original preferred in 34/35 available passage comparisons.
- passage_signed: original preferred in 32/35 available passage comparisons.
- neural_mean_piece: original preferred in 35/35 available passage comparisons.
- morphological_sequence: original preferred in 34/35 available passage comparisons.

These stress comparisons overlap across lengths, and the mapping was optimized under an earlier word-level objective, not the passage objective. They do not establish resistance to a fresh optimizer attacking this new score.

## Uncertainty and conclusion

Work-cluster bootstrap intervals are saved, alongside individual-work metrics. With only four test works, and only two works at fixed 1,000-word width, those intervals are unstable and cannot establish broad reliability. For example, signed-combination whole-work balanced accuracy has a descriptive interval of 50.0–68.8%. Nested lengths, shared dictionaries and repeated occurrences must not be counted as independent evidence.

Neither combination passes the frozen gate of 95% balanced accuracy, 95% original-pair ranking and 95% grammatical-control acceptance at any length. Existing tail-threshold anomaly rates often tie original and damaged passages: sparse damage does not necessarily push a sentence across a broad score threshold. Aggregation cannot make that lost signal reappear.

**Next justified experiment:** calibrate relative structural changes directly and test morphology-sequence ranking on many new works, denser and independently generated global mappings, and wrong dictionaries optimized against the proposed passage objective. Add dependency-aware violation rates if relative rankings fail. Longer search under the currently tested weighted objectives is not justified by this audit. This result concerns the existing proxies and these sparse mutations, not a refutation of corpus-level grammatical anomaly objectives generally.

Automatic labels refer to the intended annotated parse, not a Latin expert ruling out every alternative reading. Original natural text can contain annotation errors, elliptic constructions or unusual grammar. No restored ciphertext decoding was demonstrated.

## Artifacts and reproduction

[Report and predictions](../experiments/results/latin-passage-proxy-audit/report.json), [frozen maps and source sentences](../experiments/results/latin-passage-proxy-audit/dataset.json), [selection](../experiments/results/latin-passage-proxy-audit/selection.json), [control contrasts and work-cluster intervals](../experiments/results/latin-passage-proxy-audit/diagnostics.json), [dataset audit](../experiments/results/latin-passage-proxy-audit/dataset-audit.json), [feature validation](../experiments/results/latin-passage-proxy-audit/validation.json).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_passage_proxy_audit --build
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_passage_proxy_audit
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_passage_proxy_validate
```

The build refuses existing data. Scoring resumes saved per-work sentence features; it asserts the frozen dataset/source identity and recomputes fitting, calibration and passage reports. Independent validation regenerated all 517 passage feature vectors, fitting-only tail thresholds, and all nine raw proxy features for 59 sampled sentences covering every work and mapping family. Resource hashes were checked. Focused tests: 14 passed. Full downstream replay from saved sentence features reproduced selection, passages and report byte-for-byte. This is sampled neural feature replay, not a second full neural scoring run.

Source corpus: [UD Latin Perseus r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17), under CC BY-NC-SA 2.5. Original attribution README and license are copied beside derived artifacts.
