# Grammar restoration: first iteration

## Audit and frozen experiment plan

The first iteration covers Phase 0 and a bounded Phase 1 pilot of [the task plan](todo/grammar_restoration_todo.md); no dictionary optimization is authorized by a diagnostic pass alone. Existing original/uniform-backoff perfect-start artifacts, their first corruptions, the Whitaker morphology adapter, and UD Latin PROIEL/Perseus r2.17 are available locally. The existing `StructuralOracle` uses hidden plaintext and cannot serve as an inference scorer; the joint-grammar solver is explicitly a toy grammar with given sentence boundaries. Neither is silently reused as a blind Latin parser.

Use a dictionary-backed, ambiguity-preserving morphological adapter with a token-only structural interface. Begin with a deliberately limited agreement/government relaxation, not a general dependency parser: modifier–nominal agreement, nominative–finite-verb agreement when a subject is expressed, and preposition case government. Permit either head direction for modifiers/subjects, omitted subjects, participles, and morphological alternatives. Missing analyses receive no fabricated grammatical interpretation and must be reported separately. Latent segmentation is bounded and scored with an explicit fixed prior; no reference punctuation reaches inference. Best analysis compatibility is used without summing over readings, so duplicating an analysis cannot increase score. This relaxation need not assign globally consistent analyses across different obligations; that is an explicit limitation to test, not a parse claim.

Before looking at outcomes, freeze the following pilot gate: at least 8/10 saved first corruptions must score strictly below intact; at least 70% of covered, morphologically incompatible substitutions must score below intact on development; on each of two held-out authors, at least 65% must do so and the 95% passage-cluster bootstrap lower bound must exceed 50%. Ties count as failures. No post-result tuning. Failure means revise the model and do not run Phase 2 or full decoding. These are provisional engineering thresholds, not statistical guarantees.

Cicero is development; Sallust and Suetonius are held-author confirmation for this scorer (their texts have appeared in other repository experiments, so they are not newly sealed data). Use deterministic first eligible 64-token flat windows, six per author, without vocabulary screening. Source sentence boundaries remain evaluation metadata only. Annotated excerpts may be discontinuous; do not claim manuscript-length continuous prose. Normalize lowercase, j→i, v→u, strip diacritics, and omit punctuation. Synthetic substitutions use a fixed source-only morphology inventory, seed 20261020, with explicit attestation/frequency/compatibility strata. Shared-morphology replacements are hard controls, not necessarily syntactic errors; semantic invalidity cannot be certified from morphology alone.

The ten previously audited corruptions use bounded flat contexts around changed occurrences to keep this falsification pilot small; score both versions on identical crops, without reference punctuation. They do not reproduce the original full-document objective. Report every crop, every mutation, components and inferred boundaries, and distinguish absence of structural evidence from positive grammatical validation.

## Outcome: development gate failed

The baseline rejected **0/10** saved corruptions: **8 tied and 2 were preferred to intact**. Do not integrate it into dictionary search. This is a failure of this independent-constraint relaxation, not evidence that Latin grammar cannot improve decoding.

The pilot evaluated **18 flat passages × 64 tokens = 1,152 reference tokens**, six passages per author, and **144 synthetic substitutions** (48 per author, one or two globally replaced types per passage). The source-only replacement inventory used 2,000 frequency-ranked forms from **105,593 Jerome/Palladius tokens**; forms without dictionary analyses were omitted from that replacement pool. The boundary prior used **11,134 source sentence lengths**, with mean **9.484 words**, but no target boundaries. Target passages were not filtered for coverage. Whitaker supplied analyses for **87.33%** of reference tokens, with no recorded upstream annotation exceptions; an empty reading set is still an analysis failure, not successful coverage.

| Author / role | POS-disjoint substitutions: intact preferred | Ties | Corruption preferred | 95% passage-cluster interval for intact preference |
| --- | ---: | ---: | ---: | --- |
| Cicero / development | 4/12 (33.33%) | 8 | 0 | 8.33–50.00% |
| Sallust / confirmation | 2/12 (16.67%) | 9 | 1 | 0.00–33.33% |
| Suetonius / confirmation | 4/12 (33.33%) | 8 | 0 | 8.33–66.67% |

The manifest calls this stratum `incompatible`, but it means **disjoint dictionary POS sets**, not a linguistically certified ungrammatical sentence. A POS replacement can be grammatical in some contexts. This is a coarse structural-negative proxy; its failure suffices to reject this pilot, but a future benchmark should independently certify actual agreement/government violations before making strong grammar-discrimination claims. Intervals use 1,000 seeded bootstrap resamples of six passages within each author; the small, same-work excerpt clusters do not justify precise population estimates or an across-author confidence claim.

Other strata:

| Author | Same-POS, disjoint analyses: intact preferred | Shared analysis: intact preferred | Random replacement: intact preferred |
| --- | ---: | ---: | ---: |
| Cicero | 1/12 | 1/12 | 2/12 |
| Sallust | 4/12 | 0/12 | 3/12 |
| Suetonius | 6/12 | 2/12 | 4/12 |

Shared-analysis replacements are lexical-identity hard controls; morphology alone does not establish that their meaning is wrong or that their contextual syntax is valid. No semantic validity labels were inferred. All synthetic replacement forms are source-attested; 76/216 replaced original types across trials were absent from source training. Per-trial source counts, passage counts, POS sets, analysis counts, changed-token/type counts and component deltas are saved. There is no balanced attested/unattested replacement factorial in this pilot, and frequency/context strata were recorded rather than individually powered. One- and two-type substitutions were tested; this does not cover widespread dictionary corruption.

## Why it fails

The scorer assigns independent soft obligations: modifier–nominal case/number/gender compatibility within eight positions, preposition government for an explicit small Latin preposition table, and third-person finite-verb number agreement when candidate nominatives occur nearby. It permits omitted subjects and substantive adjectives/participles; a missing verb receives only a small ellipsis penalty. It does not infer verb valency, coordinated arguments, subordinating structure, accusative–infinitive constructions or globally consistent dependency attachments. Different obligations can use mutually inconsistent readings or heads. These limitations were intentional for falsification, but make the score too permissive to act as the proposed decoder's grammar objective.

For `intulerat → perlectam`, both words are analyzed, but some other verb and a compatible nominal in the crop satisfy the relaxed checks. All four structural components remain unchanged. The model cannot require the clause to retain its predicate or attach the participle coherently, so it ties this known corruption.

For `celtae → exceptans`, the structural penalty totals remain unchanged, but a different inferred segmentation improves the boundary prior by **0.155654**. For `pisonem → indiligentiae`, the relaxed subject penalty improves by **0.5**. Both show that even this frequency-free score has exploitable shortcuts. Unknown readings receive no direct reward or penalty, but can remove obligations or potential attachments; coverage changes must therefore be inspected, not interpreted as grammatical improvement.

Disabling latent segmentation and scoring the complete 64-token passage as one region still rejects only **3/12, 1/12 and 4/12** POS-disjoint substitutions on Cicero, Sallust and Suetonius respectively. Boundary inference is therefore not the only weakness. Its own evaluation is poor: **3 true positives / 36 predicted internal boundaries / 79 reference internal boundaries**, or **8.33% precision and 3.80% recall**. These are sentence-boundary evaluations; the model's short regions are not validated clauses. In a few synthetic trials, segmentation alone turns a flat-region tie into a preference for corruption.

## Score and approximation contract

Scores are explicit **unnormalized heuristic penalties**, with separately logged modifier, government, subject, predicate and boundary components. Comparisons use equal-length streams; total scores may be divided by 64 for per-token reporting without changing rankings. There is no corpus word-frequency or training-membership term in the score. There is no calibrated grammar probability or confidence estimate.

Latent boundaries use exact dynamic programming over segment lengths **4–24**, with a normalized, truncated discrete length prior proportional to `exp(-0.5 * ((length - source_mean) / source_mean)^2)`. Each segment adds its log length-prior probability, so gratuitous splitting costs score. This is a prior over individual lengths, not a globally normalized distribution over all segmentations conditional on the observed document length. No sum over analyses/parses is performed, so duplicated readings do not receive a multiplicity bonus. The independent compatibility checks are a relaxation rather than a coherent best parse. Full parsing, beam error analysis and marginalization remain unimplemented.

The scorer receives only surface tokens. Reference UD segmentation is loaded solely for evaluation; no target POS, morphology, dependency heads or punctuation reach the score. The Latin adapter uses the pinned independent Whitaker resource, retaining all returned inflections while deduplicating identical POS/feature readings; lemma identity, lexical frequency and target annotations do not affect structural penalties. Candidate generation uses source counts, separately from scoring. The existing injective optimizer was not modified or run.

## Reproduction, artifacts and verification

```sh
.venv/bin/python -m benchmarks.grammar_restoration_iteration1
.venv/bin/python -m benchmarks.grammar_restoration_validate
.venv/bin/python -m pytest -q tests/unit/test_grammar_diagnostic.py
```

The experiment refuses to overwrite `experiments/results/grammar-restoration/iteration1/`; retain it and choose a new output directory for another design. It stores the frozen manifest, source-only pool, full morphology lattices, reference streams and evaluation-only boundaries, every mutation/mapping, components and inferred boundaries, all ten cropped first-corruption checks, summary and validation. The validator reconstructs all scores using saved morphology alone, without raw annotations or the live analyzer, and checks original corrupted contexts against the earlier artifacts, mutation constraints, summaries, gate decisions and hashes. **Four focused tests pass**, including agreement/government examples, omitted subjects, analysis-duplication invariance, unknown coverage, an exhaustive segmentation comparison and rejection of a reference-boundary argument. Runtime was approximately **1.43 seconds** for the pilot; peak memory was not measured. These timing figures do not forecast dictionary-search cost.

Source provenance and licenses are retained in `data/latin-grammar-benchmark/{proiel,perseus}-r2.17/README.md` and `LICENSE.txt`, with exact source hashes in the manifest. PROIEL supplies Cicero's late-Republican prose and Jerome/Palladius late-antique training material; Perseus supplies Sallust's late-Republican and Suetonius's Imperial prose excerpts. `source_work_ids` in each saved passage lists available work IDs for that author, rather than a precise attribution of each token to a work; exact passage tokens and deterministic offsets are retained. Orthographic/tokenization and treebank conventions differ, and these excerpts are not diplomatic medieval manuscript transcriptions. Candidate-vocabulary coverage and restoration accuracy are not applicable to this standalone plaintext-ranking test; morphology coverage is reported separately.

## Recommendation

**Revise the model before Phase 2.** Keep these negative fixtures and require an explicit assignment of consistent morphological readings and dependency roles, including a predicate/argument explanation, rather than allowing any nearby compatible word to discharge an obligation. Build independently checked, minimal agreement/government violations and grammatically compatible lexical controls; evaluate those on development before changing the frozen author-level benchmark. Improve coverage and boundary handling without allowing missing analyses or boundary relocation to erase conflicts. Full correct-dictionary stability, blind recovery, and integration into the decoder remain unrun under the task plan's gate.
