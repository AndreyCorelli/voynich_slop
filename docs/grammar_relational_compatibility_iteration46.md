# Iteration 46: role alternatives and genuinely coupled agreement

**This is a positive local constraint result under oracle morphology.** Explicit genitive-dependent alternatives preserve all879 PP references, with only a5.1% increase in compatible tuples. Finite subject–verb agreement uniquely identifies28 of270 previously ambiguous links without any additional revealed fact. Unlike the PP predicate variable, subject and verb can constrain each other.

This is still a diagnostic on reused source data with privileged morphology, POS, eligibility and sentence boundaries. It is not blind parsing or restoration from ciphertext.

## 1. Restore genitive alternatives without discarding agreement

Keep iteration45's879 PP examples, exact candidate domains and same-source word-type morphology dictionary. Change only the internal-role compatibility rule: an ADJ/DET may be an **agreeing modifier** or a **genitive dependent** when an explicit Gen reading exists. The latter has its own number/gender and need not agree with the PP head. This also admits substantivized genitive adjectives; “possessor” alone would be too narrow a label.

Unknown case does not automatically license this new branch. A non-genitive adjective that disagrees with its head remains incompatible. Roles are existential witnesses, not separately recovered attachment analyses.

| Result | Original agreement rule | With genitive-dependent alternative |
|---|---:|---:|
| Reference constructions retained | 875/879 | **879/879** |
| Compatible tuples | 11,816 | **12,413** |
| Unique correct tuples without facts revealed | 6 | 6 |

The597 added tuples are a5.1% expansion; all previously compatible tuples remain. The rule restores all four iteration45 counterexamples, including the genitive determiners in *in illius potestate*, *in istius potestate*, *in istorum sella curuli*, and the genitive adjective in *in turma inauratarum*. This is a correction motivated by those inspected failures, **not independent validation** of the broader role grammar.

Replay exactly the earlier wrong-fact values on the common reference-surviving cohort:

| Wrong fact | Probes | Original nonempty | Role-aware nonempty |
|---|---:|---:|---:|
| Boundary | 875 | 47 | 50 |
| Nominal head | 846 | 115 | 117 |
| Case | 875 | 183 | 184 |
| Predicate | 855 | 855 | 855 |

The added role does not make everything compatible. It modestly increases acceptance of incorrect treebank facts, as expected from a relaxation. It does not solve the disconnected PP-governor problem: all wrong predicates remain feasible. The full16-fact-subset comparison is saved.

## 2. Test finite subject–predicate agreement

Use the same4070 Cicero/Palladius source sentences. No prior Jerome/Caesar queries or reserved sentences are evaluated. There are1513 eligible reference constructions:1437 Cicero,76 Palladius.

Eligibility requires an overt direct `nsubj` nominal/pronoun with nominative case and known singular/plural number, attached to an actual finite VERB/AUX with known number and person. NOUN/PROPN count as grammatical third person; PRON requires an explicit known person. Exclude coordinated subjects. Do **not** exclude actual subject–verb feature mismatches.

Nonverbal/copular heads, nonfinite heads, clausal/non-nominative subjects, missing/non-atomic features and coordination are outside this experiment. Their exclusion counts are saved. There is no null-subject candidate: the test conditions on the existence of an eligible overt reference subject, so it is not a subject-detection benchmark.

Before enumeration, fix a sample of at most250 constructions per author, selected by SHA256 of sentence/subject/predicate IDs. The resulting sample has **326 constructions:250 Cicero and76 Palladius**. Multiple constructions can share a sentence; counts are descriptive under this selection, not326 independent texts.

### Candidate lattice and controls

Build an oracle word-type dictionary from all4070 source sentences, including analyzed sentences, using Case/Number/Person/VerbForm. Candidate subjects are all nominal tokens with a nominative or unknown-case dictionary reading; predicates are all VERB/AUX tokens with a finite dictionary reading anywhere in the sentence. Unknown number/person expand to their possible values. No reference clause boundaries, dependency edges, distance prior or lexical score enters filtering.

Each hypothesis records subject token, predicate token, subject(number,person), and predicate(number,person). Distinguish correct **links** from exact reading tuples: a link can remain available under an alternative morphology reading even when the annotated reading combination is eliminated.

Four fixed arms:

- **No agreement:** same morphology, no cross-token equality.
- **Number only:** require equal subject/verb number.
- **Number + person:** require both equalities.
- **Hidden features:** mask dictionary number/person, retain the nominal third-person rule, then enforce agreement. This removes the observed agreement information rather than merely dropping the rule.

All reference tuples are available in the raw dictionary-based lattice; no reference candidate is injected. All16 subsets of the four facts are tested. Fitting and objective optimization are absent.

## Unique link identification without revealed facts

| Arm | Correct unique links /326 | Correct unique links among270 common ambiguous examples | Mean candidate links, common cohort |
|---|---:|---:|---:|
| No agreement | 55 | 0 | 11.80 |
| Number only | 71 | **16** | 9.08 |
| Number + person | **83** | **28** | **7.75** |
| Features hidden | 55 | 0 | 11.80 |

The common cohort retains the exact reference in both the raw and full-agreement arms and has more than one raw link. The28 recovered links are **10.4% of that cohort**. Across the whole sample, unique correct links rise from16.9% to25.5%. There are no uniquely incorrect links with no facts revealed in this selected sample.

Both source authors contribute: Cicero37→62 unique links and Palladius18→21. This is a within-source constraint check, not independent author generalization: the oracle dictionary uses both authors.

Number accounts for16 of the28 additional links; person contributes12 more. Hiding the agreement features removes all28 gains. This isolates useful cross-token morphological information rather than a frequency preference.

## Fact propagation

On the same270 initially ambiguous examples:

| Correct fact revealed | Unique correct links without agreement | With number + person agreement | Newly resolved opposite-token choices within agreement arm |
|---|---:|---:|---:|
| Subject token | 23 | **109** | **61 predicates** |
| Predicate token | 32 | **82** | **35 subjects** |
| Subject(number,person) | 8 | **55** | **64 predicates** |
| Predicate(number,person) | 19 | **55** | **35 subjects** |

“Newly resolved” excludes choices already uniquely fixed before the intervention. Directly supplying a token can also complete a link whose other endpoint was already fixed, so differences in complete-link counts are not identical to propagation counts.

Without agreement, subject revelation resolves **zero** additional predicate choices and predicate revelation resolves **zero** additional subjects. With agreement, information crosses that relation. This is the structural coupling missing from the preceding PP test.

Features are a composite fact and token identities imply some dictionary features; fact costs differ. These comparisons do not establish an optimal acquisition policy.

## Wrong anchors and the limit of consistency

Choose one alternate subject and one alternate predicate where possible from the common raw token domains, seed46001. Reuse the same choices across arms. There are239 wrong-subject and248 wrong-predicate probes. “Wrong” means different from the reference link; an alternative can be grammatical elsewhere in the sentence.

| Wrong fact, with opposite reference token supplied | No agreement: feasible | Number only | Number + person | Features hidden |
|---|---:|---:|---:|---:|
| Subject, correct predicate supplied | 239/239 | 179/239 | **157/239** | 239/239 |
| Predicate, correct subject supplied | 248/248 | 180/248 | **105/248** | 248/248 |

Full agreement rejects82 wrong subjects (34.3%) and143 wrong predicates (57.7%) under these anchored tests. This is genuine compatibility information; the PP test rejected no wrong predicates.

It is not a correctness guarantee. With only the wrong token supplied, agreement still permits207/239 wrong-subject probes and207/248 wrong-predicate probes. It yields unique wrong links in53 and72 respectively, versus23 and32 without agreement. Stronger constraints can make a wrong premise produce more confident wrong conclusions. With both token identities supplied, link uniqueness is tautological whenever the pair survives and must not be counted as recovery.

## One reference feature mismatch remains visible

Full agreement retains **all326 reference links**, but only325 exact reference reading tuples. Sentence86713 records *appetitus* as plural and its finite predicate *pareat* as singular. The dictionary permits an alternative subject reading that preserves the link, while strict number equality excludes the recorded plural/singular tuple.

The audit retains this example. It may require annotation or construction review; the experiment does not silently relabel it or declare the treebank reading ungrammatical. Exact morphology survival and link survival therefore remain separate metrics.

## What this supports next

Keep the genitive-dependent alternative as an explicitly tested compatibility branch. More importantly, **agreement-supported subject–predicate links are a better unit for further work than a free PP predicate label**: there is now measurable propagation and rejection of incompatible alternatives.

The next test should stress the morphology channel. Measure how the28 additional unique links and the wrong-anchor rejection rates change as readings become ambiguous, missing or noisy. Include reference survival and false unique links, not merely candidate-count reduction. Only after demonstrating tolerance to a recoverable morphology lattice would joint sentence decoding be justified.

The present result assumes oracle POS, a known eligible construction and a same-source morphology dictionary. It does not yet restore grammatical structure from anonymous words.

## Verification and artifacts

371 regression tests pass. The validator replays48,992 PP/SV intervention summaries and1948 paired wrong-token probes, reconstructs the dictionary and deterministic sample, verifies PP candidate-set monotonicity, checks actual agreement exceptions remain in the sample, and confirms326 word-type candidate extractions ignore altered reference edges and token-specific morphology. All14 frozen-input hash checks pass; the reserved200 remain unscored.

Run `python -m benchmarks.grammar_relational_compatibility_iteration46` (refuses overwrite), then `python -m benchmarks.grammar_relational_compatibility_iteration46_validate` and `python -m benchmarks.grammar_relational_compatibility_iteration46_audit`. Core code is `src/voynich_smt/relational_compatibility.py`. Artifacts under `experiments/results/grammar-restoration/iteration46/` contain the declaration, role-aware PP candidates and witnesses, SV oracle dictionary/candidates, eligibility audit, interventions, paired wrong-fact controls, author breakdown, restored/pruned-reference audits and validation. Previous artifacts and the shared todo remain unchanged.
