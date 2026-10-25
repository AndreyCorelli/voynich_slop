# Iteration 147: existing source annotations cannot expand the training set

The proposed training-type expansion adds **zero eligible types**. The fixed source fit partition contains no additional sufficiently supported ADP/CCONJ types outside the 16 excluded targets and the original 13 training types. No new model was fitted and no target predictions were generated.

Before counting eligibility, the design fixed the following rule: retain the original 13 labels and validation folds; add every other non-target word with at least five source-fit occurrences, a modal POS of ADP or CCONJ, and at least 80% modal agreement. All POS tags of a word count in the denominator. Added types would receive three deterministic class-stratified SHA-ordered folds; the original two scalar features, fitting procedure, regularization and raw decision threshold would remain unchanged. The input annotations are the existing iteration44 cache restricted to iteration49 partition0 fit. Reserved sentence IDs are excluded.

The independently checked source contains 2,471 sentences, 31,884 tokens and 8,720 word types. The original195 anchor catalogue already exhausts supported non-target binary-class types. Searching the complete fit annotations, rather than only that catalogue, finds these additional modal ADP/CCONJ forms:

| Word | Total occurrences | Modal class | Modal agreement |
|---|---|---|---|
| aduersus | 2 | ADP | 2/2 |
| circa | 4 | ADP | 3/4 |
| circiter | 1 | ADP | 1/1 |
| circum | 1 | ADP | 1/1 |
| extra | 1 | ADP | 1/1 |
| intra | 3 | ADP | 3/3 |
| iuxta | 1 | ADP | 1/1 |
| mart | 1 | ADP | 1/1 |
| secundum | 3 | ADP | 3/3 |
| seu | 1 | CCONJ | 1/1 |
| sub | 3 | ADP | 3/3 |
| uersus | 1 | ADP | 1/1 |
| xiii | 2 | ADP | 1/2 |

These are inherited modal annotations, not claims that every form is a sound grammatical exemplar; no manual repair was applied. Every additional form fails occurrence support; circa and xiii also fail modal agreement. The lone additional conjunction, seu, occurs once. Lowering support after seeing this inventory would change the experiment, and would still scarcely address the conjunction shortage. No thresholds were relaxed.

This is a data-availability result, not evidence that training expansion would fail if genuinely more annotated examples became available. It does not alter the prior full-text grammatical milestone. Under the present inputs, however, expanding the supervised type inventory is exhausted at the declared support level.

Next proposed diagnostic: leave out each of the 13 existing training types in turn, refit the unchanged two-feature classifier, and measure changes from the full-fit probabilities and decisions on all seven texts. Report all omissions, separating the three conjunction omissions from the ten preposition omissions; do not select a favorable model or treat agreement as a validated confidence gate. This tests whether the current positive result depends disproportionately on one supervised exemplar, without requiring new annotations or access to sealed material.

Verification independently reconstructed word/POS counts and integer-ratio eligibility, checked all42 candidate records, preserved the13 labels/folds, confirmed all16 target types are excluded, and verified zero reserve overlap. The20 frozen input hashes passed. No model-level tests were rerun because execution stopped at the verified no-expansion branch; production feature/model code was unchanged. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration147/`.
