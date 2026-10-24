# Iteration 23: grammatical relations under artificial word ciphers

This controlled benchmark returns to structure recovery without lexical identity. Repetition carries a modest transferable signal. Anonymous ending classes improve the same-author test but show no clear gain on the new author. Supplied dictionary morphology gives a much larger improvement. None of the opaque-signal conditions approaches grammatical restoration, and masked-number prediction alone can reward incorrect links.

## Task and data isolation

Predict directed, labeled links between token positions, without restoring words or supplying reference predicates, POS tags, candidate heads, or dependency labels to the features. The four reference families are UD subjects (`nsubj`, including passive), objects (`obj`/`iobj`), nominal modifiers (`amod`/`det`), and coordination (`conj`). Nominal-modifier labels are syntactic links, not a claim that every such pair overtly agrees. This is a small relation inventory, not a full dependency parser or relative-chain restorer.

The training set comes from the previously declared 800 Jerome/Palladius source training sentences; 767 pass fixed eligibility (3–60 normalized nonpunctuation tokens, no multiword-token ranges, one normalized word per token). New tuning and test IDs are selected in source order after excluding all IDs appearing in prior grammar manifest/truth declarations and the reserved registry.

| Split | Sentences | Tokens | Authors |
|---|---:|---:|---|
| Train | 767 | 8,106 | Jerome 377; Palladius 390 |
| Tune | 40 | 284 | Jerome |
| Same-author test | 100 | 820 | Jerome |
| New-author test | 100 | 1,883 | Caesar |

These are unseen sentences for this learner and undeclared in the audited grammar samples, not a claim that no earlier repository process ever read the underlying treebank. Caesar is absent from both fitting and tuning. The 200 separately reserved sentences are skipped before parsing token annotations and remain unscored. Sentence boundaries are supplied. No pretrained model, external data, or network access is used.

All model and threshold choices were frozen before test scoring. Five fixed feature arms use weighted multiclass logistic regression with hashed sparse features, regularization .003, and one global per-arm threshold chosen from a fixed grid using tuning micro-F1. There is no tuning on the new author. Candidate heads are all other tokens within 12 positions; evaluation retains reference links outside that radius in the recall denominator.

## What each cipher arm reveals

Each plaintext word receives a random fixed-length opaque body plus a freshly monoalphabetically renamed two-character ending. Repeated words remain equal, but bodies, lengths, and identities expose no lexical features. One-character forms have an explicitly padded ending. Actual ciphertext IDs never enter learned features.

- **Geometry:** sentence positions, lengths and distances only.
- **Repetition:** additionally, word-type equality and unlabeled corpus frequency/rank.
- **Anonymous endings:** additionally, equality and unlabeled frequency/rank of encrypted ending classes. No Latin suffix spelling is supplied.
- **Revealed Latin endings:** additionally, the original last two characters. This is an explicit upper-bound side channel, and for short function words may reveal their whole spelling.
- **Dictionary morphology:** instead of revealed suffix spellings, supply the union of ambiguous Whitaker POS/case/number/gender/mood/voice readings, obtained from plaintext before encryption. No roots or lemmas enter features. This is an explicit oracle side channel, not morphology recovered from the cipher.

The latter two arms also retain repetition and anonymous-ending statistics. Frequency/rank features use the entire unlabeled split, including the test split: this is transductive adaptation, not sentence-by-sentence online prediction. Counts and ranks are recomputed independently per split. Equal-frequency ranks use first occurrence, not ciphertext spelling. Endings receive a new alphabet mapping under each key; the learner cannot memorize their encrypted names.

Training uses key 101, tuning key 307 and testing key 709. Rekeying tests with 710 and 711 changes token names but leaves relation feature matrices exactly unchanged. Number features are invariant too. This establishes architectural resistance to key memorization; the extra keys are not independent statistical test samples.

## Fresh relation results

Percentages below are **directed labeled edge F1**, not percentages of words restored or complete parses recovered.

| Available evidence | Jerome micro-F1 | Caesar micro-F1 | Jerome macro-F1 | Caesar macro-F1 |
|---|---:|---:|---:|---:|
| Geometry | 5.9 | 4.1 | 6.4 | 3.8 |
| Repetition | 12.1 | 10.3 | 13.9 | 10.2 |
| Anonymous endings | 17.2 | 10.7 | 18.5 | 10.9 |
| Revealed Latin endings | 26.8 | 12.5 | 27.6 | 12.4 |
| Dictionary morphology | 52.4 | 35.2 | 54.1 | 32.8 |

There are 227 reference test links in Jerome and 583 in Caesar. The head radius covers 98.7% and 95.5%, respectively. Dictionary precision/recall is 52.9%/52.0% on Jerome and 38.1%/32.8% on Caesar. Its per-family F1 on Caesar is 17.7% subject, 25.5% object, 54.2% nominal modifier, and 33.8% coordination: the aggregate does not mean strong argument recovery.

Paired sentence bootstraps (1,000 resamples, fixed models and feature statistics) estimate anonymous-ending gain over repetition as **+5.1 points [0.9, 9.2]** on Jerome, versus **+0.35 points [−1.9, 2.7]** on Caesar. Dictionary gain over anonymous endings is +35.2 points [28.7, 41.6] and +24.6 points [20.5, 28.5]. These are conditional descriptive intervals, not refitting intervals; adjacent source sentences and shared transductive statistics also limit an IID interpretation.

The decoder selects at most one target-family head per dependent and may abstain by threshold. It does not enforce acyclicity; exact ties use fixed label/candidate order. Cyclic predictions occur in 100/100 sentences for geometry in each test, 94/99 for repetition, 21/39 for anonymous endings, 10/16 for revealed endings, and 3/7 for dictionary morphology. These outputs are relation proposals, not coherent restored parse trees. Weighted training probabilities are not claimed to be calibrated.

## Withheld-feature tests

### Context-only Number probe

A separate auxiliary classifier predicts singular/plural at reference Number-bearing query positions. The entire central word's features are omitted; matching word types elsewhere in the local context are masked too. Neither its ending nor dictionary reading is available. Context spans two tokens in each direction. Unlabeled split-level frequency statistics remain conditioned on the original corpus. The query positions are annotated, but the target Number is used only as a fitting/evaluation label. This probe tests contextual predictive signal; it is not proof that the relation model explains agreement.

| Evidence | Jerome balanced accuracy | Caesar balanced accuracy |
|---|---:|---:|
| Geometry | 50.0 | 50.9 |
| Repetition | 51.6 | 52.0 |
| Anonymous endings | 51.7 | 52.2 |
| Revealed Latin endings | 52.5 | 56.8 |
| Dictionary morphology in context | 61.9 | 63.1 |

There are 554/1,324 queries. Majority singular accuracy is already 68.6%/58.0%, so ordinary accuracy would be misleading. Anonymous-ending contexts barely exceed the 50% balanced majority baseline. Dictionary context provides additional information, but this is privileged evidence.

### Do inferred links predict the missing Number?

A separate **post-hoc consequence audit** masks the query word type before recomputing its relation predictions. For a predicted subject or nominal-modifier link, use the selected context word's reference Number to predict the hidden query Number; same-word-type context heads are excluded. Context Number is oracle evidence in this diagnostic only. The gold head/relation never selects the predicted link. Abstentions and links without suitable context Number fall back to the training majority.

This is a harsh whole-word mask, removing POS/case as well as Number; the relation learner was fitted on unmasked inputs. The resulting distribution shift makes coverage part of the result. Dictionary coverage falls to 0.7%/1.4%, so its strong unmasked F1 does not establish robust missing-feature reasoning.

Crucially, prediction of Number does not validate the link: geometry reaches 61.9% balanced accuracy on Caesar with oracle context Number, while only **5.6% of its covered relations** match the source. A matched-coverage control, choosing uniformly among eligible Number-bearing context tokens, yields 54.9%. Relative position and local Number correlations help without recovering the reference dependency. Agreement accuracy must therefore be reported alongside labeled-edge recovery. The reference-edge baseline has a different coverage set and is not directly comparable by raw accuracy alone. Full query-level predictions, coverage, relation precision and random-context controls are saved separately.

## Interpretation

The fresh test supports the experiment's direction, but not a restoration claim:

1. Key-independent structural evidence exists in word repetition.
2. This simple anonymous-ending representation does not reliably transfer its extra gain to Caesar. Frequency-rank alignment and genre shift are plausible explanations, not established causes.
3. The large morphology-side-channel gap suggests that recovering useful morphological classes is a higher-value target than adding another local ownership rule.
4. Full-graph consistency and abstention remain unsolved, and masked inflection prediction can reward correlations unrelated to the intended dependency.

A useful next experiment is corpus-level **distributional signatures for word/ending classes**, learned from unlabeled neighboring types rather than frequency rank alone. Evaluate class recovery and relation transfer separately, with masks included during fitting and an explicit acyclic/abstaining decoder. These test sentences are now inspected; subsequent design choices require a newly declared evaluation slice, while keeping the reserved 200 untouched.

## Reproduction and checks

Artifacts are in `experiments/results/grammar-restoration/iteration23/`: fixed datasets and declaration audit, dictionary lattice, model checkpoints, frozen weights/thresholds, tuning scores, test predictions, bootstrap comparisons, rekey proofs, context Number probes and agreement-transfer controls. Code is `src/voynich_smt/cipher_relations.py` plus the iteration 23 runner, evaluator, transfer/control audit and validator in `benchmarks/`.

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_cipher_relations_iteration23_validate`. Validation independently checks source labels and edge counts, verifies frozen hashes, replays 1,000 sentence/arm predictions and 9,390 auxiliary Number queries, recomputes transfer/control audits, verifies thresholds and cipher invariance, and checks split/holdout disjointness. Channel-isolation tests erase privileged metadata in blind arms, poison masked own-word metadata, and change reference annotations without changing feature matrices. The relevant suite passes **254 tests**. Previous experiment artifacts remain unchanged.
