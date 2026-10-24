# Iteration 22: challenge the selection bottleneck

The previous diagnosis was too broad. Some ambiguity is removable by simple preferences already available from the construction model; some reflects annotation conventions; and the remaining coordinated-object choice is invisible to the tested structural/frame features. This is a small diagnostic on inspected examples, not evidence for a validated selector or an impossibility result for Latin parsing.

## Frozen inputs and counting

We reuse iteration 21's candidates unchanged, with original dictionary morphology and, separately, the five oracle missing readings. No dependency labels enter feature extraction or selection. The primary condition supplies the same reference finite predicates and marker scopes as earlier experiments, with sentence boundaries hidden; the overall candidate-generation pipeline is therefore not annotation-free. This experiment tests selection conditional on those frozen inputs.

There are 48 supported unit records across both morphology arms. Twelve duplicate lexical-unit readings collapse under the same span, governor, members, feature vectors and evaluation labels, leaving 16 dictionary and 20 oracle-morphology unit examples. Among these, only **two dictionary / four oracle-morphology examples** have both multiple structures and an available strict reference match. Repeated scope settings do not create additional evidence. Ambiguous singleton `aperire → debemus` lacks a complete local reference match and is reported separately rather than counted as a selectable success.

## Preferences, without training

All policies preserve top-score ties and ignore candidate order. Distance includes NP-internal edges, so explicit participial dependencies do not acquire an artificial edge-count disadvantage. The construction preference orders marked clauses, participial clauses, declared arguments, then fewer fragments. Attachment variants add a matrix, infinitive, or frame-conditioned default. The latter prefers the infinitive for passive-reporting units and the matrix predicate for other frames. These are post-hoc debugging hypotheses on already inspected development; none is a learned or independently validated Latin rule.

On the four distinct selectable oracle-morphology examples:

| Preference | Unique strict matches | Unique mismatches | Unresolved ties | Reference retained |
|---|---:|---:|---:|---:|
| Keep all | 0 | 0 | 4 | 4 |
| Shortest dependency distance | 1 | 1 | 2 | 3 |
| Construction priority | 1 | 0 | 3 | 4 |
| Construction + matrix default | 2 | 1 | 1 | 3 |
| Construction + infinitive default | 2 | 1 | 1 | 2 |
| Construction + frame default | **3** | **0** | **1** | **4** |

The frame default uniquely matches both dictionary examples as well (2/2). These tiny denominators and inspected policy design prohibit a generalization claim. Preference rules can also select an incorrect analysis when the reference is absent: the singleton `aperire` unit remains a counterexample to treating a unique winner as reliable.

The four cases explain the result:

- **`solent hortis nocere`:** prefer the declared dative argument over a generic ablative; one strict match among three structures.
- **`creduntur enim sua praesentia fecundare`:** the frame default prefers infinitive attachment; one strict match among two structures. A matrix-only default chooses the other structure.
- **`possit defensis sedibus apricare`:** construction priority prefers the explicit participial clause, then the frame default chooses matrix attachment; one strict match among eight structures. An infinitive-only default fails.
- **Coordinated `conlocare/aperire`:** the marked clause and its matrix attachment become preferred, but three object variants remain tied: first infinitive, second infinitive, or shared. Only the first matches the strict source projection.

Thus selection is not uniformly blocked by absent information: a modest preference vocabulary resolves three inspected examples. It still cannot determine the final object assignment here.

## What information is missing?

An oracle reading filter uses source POS and nominal/participle case, gender and number, without source attachments, solely as a separate diagnostic. Candidate counts fall from **3/2/8/27 to 1/2/4/9** in the four cases. Only `hortis` becomes unique. Oracle morphology does not resolve the remaining attachment questions.

A feature-collision audit and exact linear feasibility queries sharpen this:

- Construction counts alone cannot strictly rank all reference matches above their competitors. Opposite attachments have identical vectors.
- Adding frame and attachment/sharing features resolves those collisions except first-versus-second coordinated-object attachment.
- Adding dependency distance makes an exact in-sample linear fit possible.
- That fit is **impossible with a nonpositive distance coefficient** in this feature family. The reference object belongs to the farther infinitive, while its otherwise identical competitor belongs to the nearer one. Strictly preferring the reference therefore requires rewarding greater distance for that contrast.

The feasibility weights use gold labels and are saved only as oracle witnesses, never used for label-free predictions. Rational arithmetic independently checks their margins. Colliding vectors and the required distance sign provide independently checkable obstructions to the infeasible queries. A positive distance weight could memorize this sample while damaging other attachments; successful fitting is not evidence that the objective is suitable. These conclusions apply only to the named feature families, not arbitrary lexical/contextual models.

## Challenge the measurement too

Two explicit sensitivity analyses keep their assumptions separate from strict scoring:

1. Contract an **unmarked** subject–participle clause into an agreeing nominal-adjunct attachment, and allow a shared object where the source attaches it to the first coordinated infinitive. This tests annotation granularity, not a claim that every relaxed alternative has identical meaning. The `defensis` example gains a second accepted candidate; the coordinated-object example also gains one (shared). Second-infinitive-only object attachment remains distinct. The frame policy's three-way object tie therefore remains unresolved even under this relaxation.
2. Audit `instare malum uiderint` separately. PROIEL represents `malum` as a substantivized ADJ and matrix object; the model uses an N reading as an embedded ACI subject. An explicit annotation correspondence, preserving case/number/gender and the perception frame, makes **two of six lexical-unit readings** compatible where strict scoring admitted none. This does not establish their full finite-verb morphology or semantic correctness. It shows that the strict reference projection can classify a plausible construction correspondence as absent.

The latter is outside the four-case strict selectable cohort and does not silently inflate its success count. Likewise, the first singleton `aperire` unit really omits the annotated object governor: better within-unit ranking cannot supply that missing unit context.

## Revised conclusion and next action

The bottleneck is a mixture of **missing preferences, limited feature distinctions, candidate-unit scope, and reference normalization**. It is not simply “the scorer is bad,” nor evidence that all remaining ambiguity is irreducible. The larger inventory limitation also remains: only 21 of 66 reference infinitives had their reference governor in the original pool.

Before training another scorer, define the evaluation correspondences for substantivized adjectives, ACI subjects and coordinated shared objects. Then freeze the simple frame preference and test it on a fresh contrast set from the available training material, including counterexamples to its reporting/modal defaults and first/second/shared objects. Keep absence of a compatible candidate separate from ranking failure. Do not train on these four examples and report their recovery as progress on unseen text. The reserved 200 sentences should remain untouched until this protocol is stable.

## Artifacts and validation

Artifacts: `experiments/results/grammar-restoration/iteration22/`, containing label-free feature/selection predictions and separate evaluation, collision, oracle-weight and annotation-convention audits. Run `.venv/bin/python -m benchmarks.grammar_structure_preferences_iteration22_validate`.

Validation replays all 48 unit selections, verifies deduplication, independently recomputes rankings, checks tie preservation under candidate reversal, checks linear witness margins and infeasibility obstructions, and verifies input hashes and holdout disjointness. Tests confirm annotation metadata and surface identity do not enter preference features, global attachment defaults have counterexamples, and relaxed scoring does not accept the wrong second-only object attachment. The relevant regression suite passes **231 tests**. No full restoration rerun, deployment, or scoring of the 200 reserved sentences occurred.
