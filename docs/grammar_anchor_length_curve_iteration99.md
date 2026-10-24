# Context length versus candidate availability — iteration 99

**Positive source-only diagnostic: more pooled context improves exact-pair discrimination even when candidate and error availability are held fixed.** In the fixed eight-candidate comparison, recommendation precision rises77.78%→95.45%→100%observed→100%observed at100/200/400/800sentences, while recovery coverage also increases. Candidate competition is a separate bottleneck: the same matched errors perform worse when all available candidates can compete. Do not turn this small source-calibration curve into a universal text-length rule.

## Frozen design

Keep the93binary classifier and95joint pair rule unchanged: gain cutoff0.6174674057358475, at least5occurrences across3sentences at each endpoint, unique-best-pair/tie abstention. No training or calibration. Merge the eight fixed100-sentence98blocks into four200-, two400-, and one800-sentence blocks. Every primary length level contains the same800source-calibration sentences, disjoint within that level and nested/correlated across levels. The previous829full set is an extra endpoint, adding29sentences.

Matched candidates are the intersection of types meeting occurrence/sentence support in all eight clean100-sentence blocks, selected using public support only, before scoring the curve: a, ad, de, et, ex, in, que, sed. These are fiveADP and threeCCONJ types, giving15cross-class pairs. This is an eight-type REPAIR CANDIDATE set; the public context still uses the supplied195-anchor inventory. It is not an eight-given-anchor experiment.

Three comparisons are frozen: (1)all64cross-class errors with every available candidate among16; (2)the same15matched errors, still allowing all16candidate types; (3)the same15errors with exactly the fixed8candidate types. Both endpoints of every matched error pass support at every length. The supplied remaining anchors stay visible as context even when excluded from repair candidates. All three arms include the same clean and two same-class controls.

The fixed-candidate arm deliberately restricts the tested errors to swaps within those eight types. It is an availability-matched diagnostic, not a deployable filter for arbitrary errors involving excluded types. It does not show that dropping rare candidates makes an arbitrary corrupted dictionary safe.

Reuse603frozen98score cases at100/829sentences and compute469new cases in seven merged blocks; replay all1072scenario decisions. Reference pairs are used only to score outcomes, never to rank candidates. No PP integration, source-test or author evaluation, reserve/sealed-test scoring, new annotation, or lexical search. These are repeatedly explored source-calibration texts, not fresh confirmation.

## Matched candidates and matched errors

| Sentences per block | Blocks | Error probes | Correct pairs | Wrong pairs | Abstain | Recommendation precision | Recovery coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100 | 8 | 120 | 70 | 20 | 30 | 77.78% | 58.33% |
| 200 | 4 | 60 | 42 | 2 | 16 | 95.45% | 70.00% |
| 400 | 2 | 30 | 23 | 0 | 7 | 100.00% | 76.67% |
| 800 | 1 | 15 | 12 | 0 | 3 | 100.00% | 80.00% |
| 829 | 1 | 15 | 12 | 0 | 3 | 100.00% | 80.00% |

Recovery coverage is correct recommendations divided by all tested injected errors, including abstentions. Thus increased precision is not simply achieved by refusing more cases: matched recovery rises58.33%→70.00%→76.67%→80.00%. Without the gain cutoff, unique top-rank correctness on the matched errors is94/120 (78.33%),57/60 (95.00%),30/30 (100%observed),15/15 (100%observed). This supports improvement in ranking/evidence, not only a threshold effect.

Matched clean/same-class false proposals are1/24 at100sentences,0/12at200,0/6at400,0/3at800(and829). Error recommendation precision in the tables excludes controls; controls are reported separately. In98, the quoted96correct/172wrong sparse count included three control errors; the error-only all-candidate row here is96/169.

## Availability and candidate competition

| Sentences | All64errors, all candidates: correct / wrong | Precision | Same15matched errors, all candidates: correct / wrong | Precision | Same15errors, fixed8candidates: correct / wrong | Precision |
|---|---:|---:|---:|---:|---:|---:|
| 100 | 96 / 169 | 36.23% | 67 / 29 | 69.79% | 70 / 20 | 77.78% |
| 200 | 78 / 91 | 46.15% | 29 / 20 | 59.18% | 42 / 2 | 95.45% |
| 400 | 85 / 18 | 82.52% | 17 / 8 | 68.00% | 23 / 0 | 100.00% |
| 800 | 50 / 0 | 100.00% | 12 / 0 | 100.00% | 12 / 0 | 100.00% |
| 829 | 50 / 0 | 100.00% | 12 / 0 | 100.00% | 12 / 0 | 100.00% |

The true pair is supported in180/512all-error probes at100sentences,161/256at200,128/128at400,and64/64at800. More text therefore improves partner availability as well as evidence. However, all matched pairs are supported at every length and still show a strong length effect: missing true partners alone cannot explain the earlier short-sample collapse.

Competition matters even on those matched errors. At200sentences, allowing all candidate types gives29correct/20wrong (59.18%), compared with42/2 (95.45%) in the fixed-eight pool. At400, it gives17/8 (68.00%) versus23/0. The excluded alternatives are distractors under this diagnostic; their presence can make an incorrect partner outrank a supported true pair. The unrestricted matched-error curve is not monotonic at each merge, so do not claim that every incremental context addition improves every case.

With all16candidates, the800-sentence set gives50correct/0wrong/14abstentions on64errors, with64/64raw unique top-rank correctness. The829endpoint gives identical counts; it is reused previous output rather than independent replication. Clean/control false pairs in the unrestricted pool are3/24at100,1/12at200,andzero at400/800/829.

## Interpretation and next step

Preserve two experimental conclusions: pooled contextual evidence is valuable beyond simply making the true pair available; and a confusable candidate pool can still break the rule even when the true pair is supported. The same classifier and cutoff are used throughout, so more context is a plausible research direction rather than another scoring-function adjustment. This does not establish that any particular length is sufficient on a new author.

Limits: the larger levels have only two or one pooled corpus blocks; all levels reuse the same sentences and word pairs; the matched set was chosen for source support and makes an easier restricted task. Topic/author mix and finite-sample variation also change under merges. There is no independent-article precision guarantee, no new lexical nuclei, and no unanchored/full grammatical restoration claim. Earlier source-test and Caesar counterexamples remain valid.

Next confirm the fixed core and length effect on the separately partitioned source-test sentences, keeping the candidate core, classifier, cutoff and grouping rule frozen rather than reselecting them for that text. If the pattern survives, investigate pooling additional unlabeled context for existing author evaluations before retraining the scorer. Such confirmation would still reuse development material and must not be described as a fresh sealed test. Proposed, not run here.

Validation: nested equal-800sentence support verified; matched candidates regenerated using occurrence support only;469new probability cases independently replayed and603reused cases checked against frozen98artifacts; all1072decisions and aggregates replayed; 5,649 prior frozen-input hashes verified;107 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration99/.
