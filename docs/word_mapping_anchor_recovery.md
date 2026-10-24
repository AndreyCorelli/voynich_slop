# Function-anchor recovery experiment

Correct function-word mappings do not unlock content-word recovery under the current morphological sequence objective. Even a stronger control that forbids unknown and function-word candidates for unanchored types recovers only 2.6–4.8% strict morphology-compatible content tokens. This is an assisted Caesar recovery experiment, not a successful blind crack.

## Protocol

Use the existing nested Caesar development passages of 503, 2,022 and 8,024 tokens, preserving their segment boundaries. Train the unchanged structural language model on the disjoint 39,346-word book allocation. Use the 100,000-form annotated inventory, overriding its analyses with the same cached morphology used in the prior calibration where available.

Compare 0%, approximately 50%, and 100% of supplied function-word **types**, with two proposal seeds per condition. The half-anchor subset is selected by a fixed shuffle and is nested within the full set. Both seeds start from the same frequency-based dictionary; they vary search proposals, not initialization. Supplying an anchor fixes its surface form, correcting any initialization collision by swapping the displaced assignment. The conditions consequently share the underlying initializer but have different initial dictionaries after supplying anchors.

The full anchor sets contain 58, 121 and 217 types, covering 153, 617 and 2,510 tokens respectively. Function words follow the existing conservative morphology rule: any closed-class or unsupported-POS analysis fixes the word identity. This is not a syntactically disambiguated function-word gold standard. Supplied anchors also reveal type membership, explicitly making this an oracle-assisted control.

Only function mappings enter search inputs. The candidate vocabulary includes supplied function forms missing from the selected dictionary, equally across conditions. No hidden content mappings guide scoring or proposals. Candidate groups share exactly the same model emission distributions; search changes globally consistent group assignments, preserving enough distinct surface forms to render an injective dictionary. Within a group, surface forms are assigned deterministically by ciphertext frequency and training surface frequency. Their lexical identities are not optimized by this objective.

Each of the 18 paired searches receives 10,000 annealing proposals, temperature 2.0→0.02. Proposals mix swaps, training-mass-weighted groups and unrestricted group choices. Anchors cannot move. The scorer sums over latent morphological paths and retains the previous model's smoothing and unknown state. The optimized mapping is the highest-scoring visited dictionary.

## Content recovery

Values are means over two proposal seeds. The denominator is **known-content tokens**, excluding supplied function words and morphology-unknown truth forms: 220, 909 and 3,669 tokens respectively. This matters: it avoids crediting the search for supplied answers, and it does not assess unannotated words. Strict compatibility requires identical full analysis sets; permissive compatibility requires at least one shared signature.

| Passage words | No anchors: strict content | Half anchors: strict content | All anchors: strict content | All anchors: permissive content |
|---:|---:|---:|---:|---:|
| 503 | 0.45% | 1.59% | 1.36% | 2.50% |
| 2,022 | 0.55% | 0.99% | 2.04% | 4.40% |
| 8,024 | 0.87% | 1.09% | 1.17% | 4.48% |

At 8,024 words, the fully anchored initializer starts at 4.14% strict content compatibility and search lowers it to 1.17% while improving objective score. The pinned function mappings remain 100% correct. The unanchored runs recover none of the fixed function words exactly; apparent improvements in the assisted cases must not be credited as discovered function mappings.

All evaluated known-content words are present in the candidate vocabulary. A separate capacity audit verifies that a dictionary with the true emission classes is feasible at every width, including sufficient unknown-state capacity. Missing candidate forms therefore do not explain failure on the evaluated content subset.

In five of the six fully anchored runs, the selected wrong dictionary scores above the true plaintext: gaps at the smaller widths are approximately +538 to +1,166 log-score units; at 8,024 words the two gaps are +109.88 and −8.19. Thus both objective misranking and incomplete optimization can be present; a lower-than-truth run alone would not establish objective failure.

## Stronger known-content-only control

The first experiment exposes an unknown-state escape: in the 8,024-word, fully anchored seed-101 run, 1,302 of 3,669 evaluated content tokens are mapped to unknown analyses, versus 326 initially. Run six additional 10,000-proposal searches with all function anchors supplied and only known-content candidates allowed for unanchored types. No true content words or their features are supplied. This adds the favorable assumption that remaining types should use content candidates; it also forces genuinely unannotated target words into known-content forms.

| Passage words | Initial strict content | Best strict content | Best permissive content |
|---:|---:|---:|---:|
| 503 | 0.45% | 4.77% | 12.73% |
| 2,022 | 2.31% | 2.64% | 10.45% |
| 8,024 | 4.93% | 3.27% | 11.50% |

Removing the escape helps, but does not deliver coherent structural recovery. These scores measure agreement with recorded morphology, not an independently parsed sentence or semantic quality. The true full dictionary is not feasible in the stronger control where genuine unknown forms are forbidden; its results should not be compared with a purported full-gold optimization ceiling.

## Verification and artifacts

Twenty-four distinct searches evaluate 240,000 proposals, and every proposal is replayed for validation. Best dictionaries, initial mappings, supplied anchors, score traces and metrics are saved. The C++ forward scorer is checked against the independent Python implementation for every initial and best dictionary. Local transaction tests verify compiled forward scores, global occurrence updates, anchors, profile capacities and deterministic replay. The focused suite passes 160 tests.

Artifacts are in `experiments/results/word-mapping/anchor-recovery-calibration/`, with stronger-control outputs under `known-content-only/`. The [first 100 words and actual assisted-search output](../experiments/results/word-mapping/anchor-recovery-calibration/first-100.md) distinguish supplied words from predictions.

```sh
.venv/bin/python -m benchmarks.word_mapping_anchor_recovery --steps 10000 --workers 4
.venv/bin/python -m benchmarks.word_mapping_anchor_recovery_checks
.venv/bin/python -m benchmarks.word_mapping_anchor_known_content
.venv/bin/python -m benchmarks.word_mapping_anchor_known_content --validate
```

The generation commands reject an existing manifest; the replay commands validate saved results. No final-test scoring or whole-Caesar campaign is performed.

## Next implication

Function-word bootstrapping alone is insufficient for this scorer. A longer run of the same objective is not supported by these results. Address unknown-state exploitation and add relational grammatical factors or a stronger independent parser-based model, then repeat the assisted-content test. The failure is evidence against this implementation and objective, not against every possible structural decoding approach or the Latin hypothesis.
