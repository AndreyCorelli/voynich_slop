# Independent contextual anchor-class audit — iteration 91

**Outcome: the frozen POS model cannot support this anchor-class audit.** Calibration selects OFF; all evaluated scenarios flag zero mappings. After masking an anchor type, ADP+CCONJ probability is only about1%, and the raw class contrast mostly prefers ADP regardless of the true source-modal class. This is a failure of this frozen-model diagnostic, not proof that contextual anchor-class recovery is impossible.

## Frozen diagnostic

Candidates are the16 common20 anchors with source-modal ADP or CCONJ labels. Build the same195-anchor public input as earlier experiments. For each present candidate type, hide its identity and tag at every occurrence, preserving opaque equality IDs. Predict its occurrences with the frozen source85 POS ensemble, without any anchor-tag override. Mean the probability vectors across occurrences; score disagreement as log((opposite-class probability+1e-12)/(proposed-class probability+1e-12)). Neither the candidate identity nor its proposed tag enters its masked model features. Other supplied anchors remain available as context and may themselves be corrupted.

Require at least5 occurrences,3 sentences, and5% mean probability mass on ADP+CCONJ before making a class decision. Predeclared margin thresholds:0,0.5,1,2,3,4,8,OFF. Calibrate using only source-calibration clean and known in/et-swapped scenarios. Allow at most one clean false flag and at most5% of clean candidate occurrences flagged; maximize detected swapped types, then minimize corrupted false flags, clean flagged tokens, and choose the higher threshold. Freeze before source-test/author evaluation. The four unrehearsed swaps do not enter threshold selection.

Simulated error labels compare proposed classes to the original supplied source-modal mapping; they are attached only after public class evidence is computed. They do not use target reference POS or dependencies. Same-class identity swaps are class-correct negatives. This audits classes only and cannot establish correct lexical anchor identity. No PP integration, mapping correction, lexical search, new annotation, reserve or sealed-test scoring. Cached datasets are reused development material.

## Results

Source calibration has16 present types, but zero meet the support floor in either clean or in/et-swapped input. Both simulated errors are unsupported; OFF wins the fixed tie rule. Unsupported errors count as missed errors rather than being removed from the denominator.

| Clean dataset | Present candidate types | Supported types | ADP+CCONJ mass range | Raw binary class preference |
|---|---:|---:|---:|---|
| calibration | 16 | 0 | 0.97–1.37% | ADP:16 |
| caesar | 13 | 0 | 0.89–1.33% | ADP:13 |
| source | 16 | 0 | 0.97–1.28% | ADP:16 |
| jerome | 13 | 0 | 0.83–1.38% | ADP:12, CCONJ:1 |

The source-calibration and source-test candidate lists contain eight ADPs and eight conjunctions; always preferring ADP therefore gives only50% type accuracy on these clean lists. The full POS argmax is VERB, ADV or NOUN, never either candidate class. Relaxing the5% mass floor alone would not establish useful discrimination and was not used to change the frozen decision.

| Dataset | Scenario | Detected class errors / present errors | False flags | Unsupported errors |
|---|---|---:|---:|---:|
| source | correct | 0 / 0 | 0 | 0 |
| source | rehearsed_in_et | 0 / 2 | 0 | 2 |
| source | unseen_ad_que | 0 / 2 | 0 | 2 |
| source | unseen_ad_sed | 0 / 2 | 0 | 2 |
| source | unseen_de_que | 0 / 2 | 0 | 2 |
| source | unseen_de_sed | 0 / 2 | 0 | 2 |
| source | same_adp | 0 / 0 | 0 | 0 |
| source | same_conjunction | 0 / 0 | 0 | 0 |
| Jerome | correct | 0 / 0 | 0 | 0 |
| Jerome | rehearsed_in_et | 0 / 2 | 0 | 2 |
| Jerome | unseen_ad_que | 0 / 1 | 0 | 1 |
| Jerome | unseen_ad_sed | 0 / 2 | 0 | 2 |
| Jerome | unseen_de_que | 0 / 1 | 0 | 1 |
| Jerome | unseen_de_sed | 0 / 2 | 0 | 2 |
| Jerome | same_adp | 0 / 0 | 0 | 0 |
| Jerome | same_conjunction | 0 / 0 | 0 | 0 |
| Caesar | correct | 0 / 0 | 0 | 0 |
| Caesar | rehearsed_in_et | 0 / 2 | 0 | 2 |
| Caesar | unseen_ad_que | 0 / 2 | 0 | 2 |
| Caesar | unseen_ad_sed | 0 / 2 | 0 | 2 |
| Caesar | unseen_de_que | 0 / 2 | 0 | 2 |
| Caesar | unseen_de_sed | 0 / 2 | 0 | 2 |
| Caesar | same_adp | 0 / 0 | 0 | 0 |
| Caesar | same_conjunction | 0 / 0 | 0 | 0 |

Zero false flags under OFF reflect complete abstention, not a successful detector. Some author candidates or swapped types are absent, and other types have too few occurrences even before applying the mass floor. All present types are retained in artifacts; absence is not counted as a successful error detection.

## Training support diagnostic

The post-score diagnostic summary counts source-fit labels by whether their token was already a supplied anchor:

| Reference POS | Visible anchor examples | Hidden examples |
|---|---:|---:|
| ADP | 2107 | 50 |
| CCONJ | 1835 | 2 |

Thus1835of1837 CCONJ fit tokens and2107of2157 ADP tokens have visible anchor identities/tags. The model has almost no conjunction supervision in the hidden-tag condition used by this audit. This supports a training-distribution explanation for the probability collapse, but does not isolate causality or rule out intrinsically weak context evidence. The counts and class-distribution summaries are descriptive diagnostics added after scoring; they change no policy.

## Decision and next experiment

Do not connect this detector to PP inference. Preserve the clean-anchor grammatical findings and the known-error/unknown-error boundary from89–90; this detector provides no new mapping recovery. Next train an anchor-class model specifically on examples whose entire function-word type is masked. Block validation by type, compare source-class-prior and shuffled-context controls, and calibrate on source data before reusing the frozen swap challenges. First establish above-prior discrimination and acceptable clean false alarms; do not assume that simply removing the mass floor or converting the remaining1% into binary probabilities repairs the model.

Validation: all26 calibration/evaluation scenarios replayed; all reference POS/dependency fields removed without changing evidence; candidate types fully hidden before prediction; calibration and diagnostic summaries replayed; 2,333 prior frozen input hashes verified;90 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration91/.
