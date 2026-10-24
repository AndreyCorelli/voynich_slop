# Word-to-word decoding: attempts and outcome

**Outcome:** the implemented approach failed to demonstrate useful decoding.
Recovery remains low, and better objective scores often correspond to worse
plaintext recovery. It has not justified a manuscript-scale search.

## Setup

Search for a globally consistent mapping from ciphertext words to Latin surface
forms, maximizing language-model scores with simulated annealing and restarts.
Training-derived candidates and morphology, incremental scoring, archives,
checkpoints and independent validation were implemented.

Tests used synthetic word-substitution ciphers generated from known Latin by
Julius Caesar—not Caesar letter shifts. Both one-to-one and homophonic mappings
were tested initially. Later experiments used three separate development bundles,
a full vocabulary of 12,327 training forms, and one-to-one constraints.

## What we tried

| Attempt | Result |
| --- | --- |
| Smoothed word bigrams/trigrams, collapse penalties and large budgets | The 16.8-million-mutation calibration found wrong dictionaries scoring above truth in every longer run. |
| Decoded-frequency penalties and injective mappings | Another 6 million mutations produced limited recovery gains; objective misranking persisted. |
| Larger contexts and disjoint-book training | Recovery remained around 4%; exhaustive local changes showed many ways to improve the score away from truth. |
| Latin RoBERTa scoring | Preferred truth in 74% of selected near-truth counterexamples, but failed on the remainder. |
| Neural reranking and diverse restart archives | Initial reranking left recovery unchanged; broader candidate pools produced small, inconsistent gains. |
| Candidate-pool size and partial-context diagnostics | Average neural-selected recovery stayed near 2.3%. N-gram top-1 ranking beat neural ranking in every tested context condition. |
| Uncertain candidates, morphological agreement and coordinated moves | Combined recovery was 2.34% versus 2.31% baseline. Archive consensus was unreliable; agreement still rewarded wrong mappings. |
| Training-attested phrase proposals and 5× budgets | Across 6.48 million mutations, all 18 longer-run scores improved, but average recovery fell in every arm. Baseline: 2.31% → 1.72%; phrase proposals: 1.79% → 1.10%. |
| Widening to 32,004 words, full oracle vocabulary and a frozen holdout | 13.38 million mutations: recovery reached 6.74%, below the starting frequency mapping’s 6.94%; only 9–11 of 8,220 assignments were correct. |
| Zero-corruption oracle start | Starting at 100% accuracy, strict score ascent falls to 82.80% at 32,004 words; annealing falls to 69.58%. |
| Exact optimization of small restricted cases | Annealing found an optimum in 34/36 runs, while truth was below the optimum in all 18 five-token cases. |

## Interpretation

The objective is a demonstrated bottleneck: it rewards incorrect decodings.
Proposal generation and exploration also remain weak, but adding compute alone
has not solved the problem. No coherent interpretation was demonstrated.

These are limited, coverage-screened, same-author development experiments.
Small exact audits included correct words in their candidate sets explicitly.
They do not prove that every word-mapping approach is impossible. The final test
remains unscored.

Latest verification: 151 focused tests passed; the exact audit and both phrase
budget experiments, widening study and zero-corruption diagnostic independently validated.

Detailed protocols and artifacts: [experiment index](word_mapping.md),
[bootstrap refinements](word_mapping_bootstrap.md),
[phrase proposals and exact audit](word_mapping_phrase.md),
[widening calibration](word_mapping_widening.md),
[zero-corruption baseline](word_mapping_zero_corruption.md).
