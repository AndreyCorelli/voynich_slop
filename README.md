# Voynich decipherment research

## Earlier approach: Z3 constraints

The original approach used the Z3 solver to search for reversible encodings that could explain Voynich text under explicit language and dictionary constraints.
It tested monoalphabetic, homophonic, and bounded variable-length codes, including variants with nulls, contractions, and alternative word boundaries.
Synthetic ciphertext with known plaintext provided recovery controls, and discovered encoding/decoding witnesses were independently checked.
Short Voynich samples sometimes admitted dictionary fits, but those fits did not establish grammatical plaintext, a manuscript-wide key, or its language.
The work produced useful model-specific exclusions and structural diagnostics, documented in the [coverage map](docs/approach_coverage.md), without deciphering the manuscript.

## Newer approach: recover reliable information first

The final goal remains deciphering Voynich, initially under the working hypotheses that its language is Latin and one EVA word corresponds to one plaintext word.
We first test recovery methods on known Latin texts, aiming to identify small, trustworthy sets of exact word mappings that could seed another decipherment algorithm.
A target demonstration is five confidently selected words in each of four Latin texts, with at least three correctly recovered Latin words common to all four sets.
Reliable grammatical information—such as word classes, morphology, or phrase membership—is also a valuable output, even if it does not immediately recover words.
A successful method would then be tried on Voynich; if the Latin route fails, other languages follow, starting with Frühneuhochdeutsch and reusing suitable model components, as described in the [high-level goal](docs/high_level_goal.md).

### First iteration: statistical word restoration

The initial Ravi–Knight-inspired implementation searched whole-word substitution dictionaries using language-model scores, contextual candidates, and multiple search restarts.
It recovered small frequent-word nuclei in English, but transfer to Latin did not establish a substantial reliable nucleus.
Larger corpora, morphology, alternative objectives, and more search exposed weaknesses in scoring and confidence rather than delivering dependable Latin restoration.
Historical German trials also yielded partial frequent-word recovery without a trusted Voynich translation; see the [approach and outcomes](docs/ravi_knight_failure.md).

### Current iteration: grammatical recovery

The current work isolates grammatical information that can be inferred for opaque repeated word types and used as constraints in a later decoder.
Unlike the initial search for a complete word dictionary, it separately tests function-word classification, prepositional-phrase membership, and selective repair of mistaken grammatical anchors.
Experiments compare frozen models with baselines and controls, recording both useful signals and failures of precision, coverage, or transfer.
Conditional word-class signals, coarse grammatical shortlists, and source-trained case-applicability ranking provide measured inputs, with explicit limits on supervision, coverage, and transfer reliability.
The [experiment tracker](docs/grammar_algorithm_proposals.md) preserves successes, limitations, and proposed checks before any Voynich application.

## Progress

### 2026-10-26: selective grammatical relations, limited reproducibility

The strongest potential input is a shortlist of anonymous grammatical relations, with trained pair-ranking compatibility of **68–89%** across four author datasets and uneven gains beyond simple controls.
Fixed diffusion repairs collapsed graph geometry, while local relations recover rare reference-pure Aquinas/Jerome pairs whose reliable recurrence and new-rule control validation remain unresolved.
No exact nuclei or dependable named-POS restoration is established.
See the [daily report](docs/progress/20261026.md#daily-summary) and separate [best shot today](docs/progress/20261026.md#best-shot-today).

### 2026-10-25: promising grammatical inputs

A source-trained model selects **9/10 case-comparable pairs** in another Cicero passage, spanning 11 word types with 82.87% conditional case agreement, without target POS/case labels at inference.
Target AUC is **0.842**; [audits](docs/grammar_case_endpoint_sensitivity_iteration183.md) preserve the gain under source-label permutations, unseen training pairs, and all 53 endpoint omissions.
Other preserved findings include context-specific case compatibility and [80–90% coarse grammatical membership in top-ten word lists across four datasets](docs/grammar_broad_source_authors_iteration159.md).
One negative training pair influences the shortlist (dropping it gives 5/10 even with [fixed scaling](docs/grammar_case_fixed_scaling_iteration184.md)); evidence remains same-author with shared vocabulary and **no named cases or lexical nuclei restored**.

### 2026-10-24: three potential grammatical inputs preserved

Opaque preposition/conjunction classification reaches **12/16 correct types** on source-test text, **11/16 on Jerome**, and **13/15 on Caesar** with a frozen model.
Using inferred classes increases correct prepositional-phrase selections from **23 to 235**, with **34 errors (87.36% precision)**.
A selective repair policy achieves **25 correct repairs and zero wrong repairs** on synthetic Jerome anchor corruptions, although later challenges expose limits to its reliability.
These are conditional successes with supplied anchors, not recovered plaintext nuclei; their evidence, possible decipherment uses, and limitations are captured in the [milestone record](docs/progress/20261024.md).
