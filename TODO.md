# TODO.md — SMT Exploration of Voynich-Compatible Cipher Models

## 1. Goal

Build an experimental Python framework using **Z3** to investigate whether text with the structural properties of the Voynich Manuscript can plausibly be produced by relatively simple, historically plausible encryption/encoding mechanisms.

The primary research question is **not**:

> "Can we decipher the Voynich Manuscript?"

Instead:

> "What is the simplest reversible encoding mechanism, within a clearly defined family, capable of mapping plausible natural-language plaintext to observed Voynichese?"

The framework should support:

1. Synthetic experiments where plaintext and cipher mechanism are known.
2. Recovery of hidden cipher parameters from synthetic ciphertext.
3. Testing whether Voynich samples are SAT/UNSAT under specified cipher families.
4. Optimization/minimization of cipher complexity.
5. Comparison of Voynich against appropriate controls.
6. Incremental addition of richer cipher mechanisms without redesigning the system.

The implementation should prioritize **scientific falsifiability and inspectability** over raw decipherment attempts.


# 2. Technology

Primary language:

- Python 3.12+

Core solver:

- `z3-solver`

Supporting libraries may be selected as appropriate.

Likely useful:

- `pytest`
- `pydantic`
- `numpy`
- `pandas`
- `matplotlib`
- `rich`
- `typer`

Use Poetry, uv, or another modern Python dependency manager.

Codex may:

- install/download missing Python dependencies;
- download public Voynich transcriptions;
- download public-domain Latin texts;
- download other public datasets useful as controls.

Do NOT introduce large ML frameworks unless a later experiment genuinely requires them.


# 3. Important conceptual constraint

Do not encode vague assertions such as:

    Language = Latin

directly.

Every hypothesis must be translated into explicit machine-testable constraints.

For example, "Latin" may eventually mean some combination of:

- alphabet restrictions;
- dictionary membership;
- character n-gram constraints;
- word-length distributions;
- morphological constraints;
- finite-state grammar;
- frequency constraints;
- corpus-derived language model.

Keep these definitions explicit and replaceable.


# 4. Architecture

Design around interchangeable components.

Suggested structure:

    src/
        data/
            voynich.py
            latin.py
            controls.py

        models/
            alphabet.py
            plaintext.py
            ciphertext.py
            segmentation.py

        cipher/
            base.py
            substitution.py
            homophonic.py
            verbose.py
            nulls.py
            contextual.py
            table_driven.py

        language/
            base.py
            alphabet.py
            dictionary.py
            ngram.py
            morphology.py

        solver/
            model.py
            constraints.py
            optimization.py
            unsat.py

        experiments/
            synthetic.py
            recovery.py
            voynich.py
            controls.py
            comparison.py

        metrics/
            entropy.py
            distributions.py
            complexity.py

        cli.py

    tests/

    data/
        raw/
        processed/
        generated/

    experiments/
        configs/
        results/

    README.md
    TODO.md


# 5. Configuration model

Cipher experiments must be configuration-driven.

Example:

    language: latin

    plaintext:
      alphabet_size: 23
      preserve_word_boundaries: true

    cipher:
      type: verbose_homophonic

      max_homophones_per_symbol: 4
      min_code_length: 1
      max_code_length: 3

      nulls:
        enabled: false
        max_symbols: 0

      context:
        enabled: false
        memory: 0

      table:
        enabled: false

    optimization:
      enabled: true

Configuration should eventually permit experiments such as:

    max_homophones_per_symbol = 1..8
    max_code_length = 1..4
    null_symbols = 0..5
    context_memory = 0..2
    word_boundaries_preserved = true/false


# 6. Data: Voynich transcription

Download a reputable machine-readable Voynich transcription.

Prefer established EVA-based transcription(s).

Requirements:

- preserve original source;
- record download URL/source/version/date;
- never silently modify raw data;
- normalize into an internal representation;
- distinguish uncertain/ambiguous transcription symbols;
- preserve page/folio/line information where available;
- preserve spaces separately from glyphs.

Do not assume EVA characters correspond to actual plaintext characters.

Implement something like:

    class VoynichCorpus:
        pages
        lines
        words
        glyphs

Allow selection by:

- folio;
- section;
- line;
- first N words;
- first N glyphs;
- random deterministic sample.

All experiments must record exactly which source/sample was used.


# 7. Latin control corpus

Acquire public-domain medieval/classical Latin text.

Initially normalization may:

- lowercase;
- remove punctuation;
- map `j -> i` if appropriate;
- map `v/u` according to selected historical convention;
- optionally remove spaces;
- restrict to a configurable alphabet.

Do not hardcode one normalization as "correct Latin."

Represent normalization choices explicitly.


# 8. Phase 1 — Basic Z3 sanity tests

Before Voynich work, implement very small known problems.

## 8.1 Monoalphabetic substitution

Generate:

    plaintext
        ↓
    random substitution key
        ↓
    ciphertext

Hide the key.

Ask Z3 to recover mappings consistent with:

    Encoder(plaintext) == ciphertext

Verify:

- SAT;
- recovered mapping is valid;
- recovered mapping reproduces ciphertext.


## 8.2 Homophonic substitution

Allow:

    plaintext symbol -> one of N ciphertext symbols

Example:

    E -> {Q, X, P}
    A -> {L, M}

Test recovery when plaintext is known.

Then test when portions of plaintext are symbolic.


# 9. Phase 2 — Variable-length verbose homophones

Implement codes such as:

    E -> {q, qo, che}
    A -> {da, ai}
    T -> {k, ot, chy}

Parameters:

    min_code_length
    max_code_length
    max_homophones_per_plaintext_symbol

The solver must represent:

- plaintext symbols;
- homophone choices;
- code lengths;
- generated ciphertext sequence.

Require generated ciphertext to exactly equal observed ciphertext.


# 10. Symbolic segmentation

This is essential.

Given ciphertext:

    q o k e e d y

the solver may need to consider segmentations such as:

    qo | kee | dy

or:

    q | ok | ee | dy

or eventually:

    qo | NULL | ee | dy

Do not enumerate all segmentations in Python if Z3 can reasonably represent the choice symbolically.

Benchmark alternative representations.

Document performance differences.


# 11. Phase 3 — Null symbols

Add optional ciphertext nulls.

Example:

    plaintext encoding:

        A -> qo
        B -> ee

    ciphertext:

        qo k ee

where:

        k = NULL

Support constraints:

    nulls_enabled
    max_distinct_null_symbols
    max_null_occurrences
    max_consecutive_nulls

Initially assume nulls are single glyphs.

Later allow null sequences if justified.


# 12. Phase 4 — Word boundaries

Support two models.

## Model A

Voynich spaces correspond to plaintext spaces.

    preserve_word_boundaries = true

## Model B

Voynich spaces may be introduced by the encoding mechanism.

    preserve_word_boundaries = false

Start with Model A.

Only implement Model B after earlier models are working, because unconstrained boundaries dramatically increase the search space.


# 13. Language models

Implement progressively.

## Level 0 — Known plaintext

Used for solver validation.

## Level 1 — Alphabet only

Plaintext consists of Latin alphabet symbols.

This is intentionally weak.

## Level 2 — Dictionary

Plaintext words must belong to a supplied Latin vocabulary.

Use this primarily for short experiments.

## Level 3 — N-gram constraints

Build character/bigram/trigram statistics from a Latin corpus.

Do NOT require exact corpus frequencies.

Allow configurable tolerance.

Possible constraints:

    frequency("qu") >= threshold
    frequency(illegal_bigram) == 0

and/or aggregate distance constraints.

## Level 4 — Morphological model

Potential later extension.

Represent words approximately as:

    prefix? + stem + suffix?

Do not implement a full Latin parser initially.

The language-model interface must allow other languages later:

- Italian;
- German;
- Czech;
- Greek;
- etc.


# 14. Critical validation experiment

This experiment MUST succeed before drawing conclusions from Voynich.

Generate synthetic ciphertext using our own verbose homophonic encoder:

    Latin plaintext
        ↓
    random verbose-homophonic encoder
        ↓
    ciphertext

Discard/hide:

- plaintext;
- key;
- segmentation;
- homophone choices.

Give the solver only:

- ciphertext;
- cipher-family constraints;
- Latin language constraints.

Ask it to reconstruct a valid explanation.

Success criterion is NOT necessarily recovering the exact original key.

There may be equivalent keys.

Instead verify that Z3 finds:

    some plausible Latin plaintext
    +
    some legal encoder

such that:

    Encoder(plaintext) == ciphertext

If this cannot be achieved reliably on synthetic data, do NOT interpret failure on Voynich as evidence against the cipher hypothesis.


# 15. Incremental synthetic difficulty

Run recovery experiments at increasing sizes:

    10 words
    25 words
    50 words
    100 words
    250 words

Record:

- SAT/UNSAT/UNKNOWN;
- runtime;
- Z3 statistics;
- number of symbolic variables;
- number of constraints;
- recovered plaintext;
- recovered key;
- ambiguity where measurable.

Find practical scaling limits.


# 16. Complexity model

Define an explicit complexity score for candidate encoders.

Initial proposal:

    base mapping                   +1 per mapping
    additional homophone           +1
    2-glyph encoding               +1
    3-glyph encoding               +2
    distinct null symbol           +2
    null occurrence                +small penalty
    context dependency             +5
    special-case rule              +10

These weights are arbitrary starting values.

Therefore:

- keep them configurable;
- report raw structural measurements as well as weighted score;
- never present the weighted score as objectively meaningful.


# 17. Z3 Optimize

Use `Optimize` where practical to find low-complexity explanations.

Objective conceptually:

    minimize(
        encoder_complexity
    )

subject to:

    encode(plaintext, encoder) == observed_ciphertext

and:

    plaintext satisfies language constraints

Prefer lexicographic optimization initially:

1. minimize context dependence;
2. minimize null machinery;
3. minimize number of homophones;
4. minimize total codebook size;
5. minimize average code length.

This may be more interpretable than one arbitrary weighted sum.


# 18. SAT / UNSAT experiments

For each cipher family, run a bounded search.

Example:

    Latin
    alphabet = 23
    max homophones = 4
    max code length = 3
    nulls = 0
    context memory = 0
    boundaries preserved

Question:

    SAT?

If UNSAT, relax ONE dimension.

Example sequence:

    H <= 1
    H <= 2
    H <= 3
    H <= 4

then:

    nulls <= 1

then:

    nulls <= 2

etc.

Record the exact point where the model changes from:

    UNSAT -> SAT

This "complexity frontier" is one of the primary outputs of the project.


# 19. UNSAT cores

Where possible, structure constraints using named assumptions.

If a model is UNSAT, obtain an UNSAT core.

Goal:

identify which observed properties or linguistic assumptions conflict.

Example output:

    UNSAT

    conflicting assumptions:

        latin_bigram_rule_17
        preserve_spaces
        homophone_limit_4
        voynich_positional_rule_8

This is potentially more scientifically useful than simply reporting failure.


# 20. Voynich structural constraints

Implement measurable properties independently of cipher hypotheses.

Candidates:

- glyph frequencies;
- word-length distribution;
- glyph positional preferences;
- prefix frequencies;
- suffix frequencies;
- repeated-word behavior;
- repeated-substring behavior;
- character conditional entropy;
- bigram/trigram distributions;
- vocabulary growth;
- line-position effects;
- page/section effects.

Do NOT encode all of these into Z3 immediately.

First implement them as ordinary Python metrics.

Use them to compare:

    Voynich
    Latin
    synthetic ciphertext
    pseudo-Voynich controls
    randomized controls


# 21. Control datasets

At minimum compare four categories.

## A. Known natural language

Latin.

## B. Known synthetic ciphertext

Latin encrypted using mechanisms implemented by this project.

## C. Generated pseudo-language

Create text using a simple Voynich-like generative process.

For example:

    prefix + stem + suffix

with constrained component sets.

Potentially later reproduce published pseudo-Voynich generation methods if licensing/data permits.

## D. Randomized controls

Generate:

- random glyph sequences;
- frequency-preserving shuffled Voynich;
- word-shuffled Voynich;
- within-word shuffled Voynich.

These controls are essential.


# 22. Main comparative experiment

For equivalent sample sizes, estimate minimum encoder complexity required for:

    known encrypted Latin
    Voynich
    pseudo-Voynich
    randomized text

Conceptual output:

    Dataset                     Min complexity
    ------------------------------------------
    synthetic Latin cipher          18
    synthetic verbose cipher        24
    Voynich                         31
    pseudo-Voynich                  90
    randomized control             170

DO NOT assume the result will look like this.

The reverse would be equally interesting.

The goal is measurement.


# 23. Avoid overfitting

A sufficiently flexible encoder can explain ANY finite ciphertext.

Therefore every experiment must report model capacity.

Track at minimum:

    number of mappings
    number of free variables
    number of homophones
    number of null symbols
    number of context-dependent rules
    code lengths
    number of exceptions

Prefer models that generalize.


# 24. Train/test approach

Do not merely fit one Voynich sample.

Eventually:

1. Fit/infer encoder constraints using sample A.
2. Freeze as much of the inferred mechanism as possible.
3. Test whether the mechanism can explain sample B.

Possible split:

    folios 1..N -> training
    later folios -> validation

Also test across manuscript sections.

An encoder that explains 200 words by constructing 200 special cases is worthless.


# 25. Historically plausible mode

Add metadata describing historical plausibility separately from mathematical complexity.

Example mechanisms:

    monoalphabetic substitution
        known historically: yes

    homophonic substitution
        known around target period: investigate

    null symbols
        known around target period: investigate

    nomenclator
        known around target period: investigate

    context-dependent state machine
        known around target period: uncertain

    Cardan grille
        known around target period: NO / anachronistic

Do not equate:

    mathematically possible

with:

    historically plausible.

Create:

    docs/historical_cipher_context.md

with sources for historical claims.

The Voynich vellum dates approximately to the early 15th century, so chronology matters.


# 26. Table-driven mechanism

Only after verbose homophones/nulls work, introduce a generic table-driven encoder.

Do NOT call this a "Cardan grille" unless implementing that specific historical mechanism.

Generic model:

    table[row][column] -> ciphertext chunk

Plaintext and/or state determine:

    row
    column

Possible parameters:

    rows
    columns
    state_count
    previous_symbol_dependency

Start extremely small:

    rows <= 4
    columns <= 4
    state_count <= 2

Otherwise the model will trivially overfit.


# 27. Context-dependent encoding

Later support:

    encoding(P_i) =
        f(
            P_i,
            plaintext_position,
            previous_plaintext_symbol?,
            previous_cipher_symbol?,
            word_position?
        )

Every additional context source increases complexity.

Do NOT introduce arbitrary Python callbacks.

Context mechanisms must themselves have bounded symbolic representations.


# 28. Reverse verification

Every SAT model must be independently verified outside Z3.

After Z3 produces:

    plaintext
    encoder parameters
    segmentation
    null positions

construct a normal Python encoder.

Run:

    generated = encoder.encode(recovered_plaintext)

and require:

    generated == observed_ciphertext

Never trust model interpretation code alone.


# 29. Result serialization

Every experiment should produce machine-readable output.

Example:

    {
        "dataset": "...",
        "sample": "...",
        "cipher_model": {...},
        "language_model": {...},
        "solver_result": "SAT",
        "runtime_seconds": 12.4,
        "complexity": {...},
        "plaintext": "...",
        "mapping": {...},
        "segmentation": [...],
        "nulls": [...],
        "solver_statistics": {...}
    }

Use JSON.

Include random seeds and dataset versions so experiments are reproducible.


# 30. CLI

Provide commands roughly like:

    voynich-smt corpus info

    voynich-smt synthetic generate \
        --language latin \
        --cipher verbose-homophonic \
        --words 50

    voynich-smt solve \
        experiments/configs/basic.yaml

    voynich-smt sweep \
        experiments/configs/homophone-sweep.yaml

    voynich-smt compare \
        experiments/results/

Exact CLI design may differ.


# 31. Performance

Do not start with the entire manuscript.

Start tiny.

Suggested progression:

    5 words
    10 words
    25 words
    50 words
    100 words
    ...

Measure solver performance continuously.

Potential optimizations:

- symmetry breaking;
- canonical ordering of homophones;
- restrict unused codebook entries;
- constrain alphabets from observed symbols;
- incremental solving;
- push/pop;
- assumptions;
- precomputed candidate segmentations where superior;
- finite-domain integer representations;
- bit-vectors where genuinely advantageous.

Document optimizations and why they are valid.


# 32. Symmetry breaking

This will probably matter considerably.

Example:

If plaintext E has three homophones:

    H0
    H1
    H2

then permuting their identities creates equivalent models.

Add canonical constraints where possible, e.g.:

    lexical(H0) < lexical(H1) < lexical(H2)

Likewise canonicalize:

- null IDs;
- table rows/columns where equivalent;
- state IDs.

Avoid making Z3 rediscover millions of isomorphic solutions.


# 33. Tests

Unit-test every constraint family.

Important test categories:

### SAT test

Construct known-valid tiny example.

Expect:

    SAT

### UNSAT test

Construct deliberately impossible example.

Expect:

    UNSAT

### Round-trip

    plaintext
        -> encoder
        -> ciphertext
        -> solver

Verify recovered model reproduces ciphertext.

### Boundary cases

Test:

    zero nulls
    one homophone
    maximum code length
    one-character plaintext
    repeated characters
    repeated words

### Regression tests

Whenever a solver bug is discovered, preserve the minimal failing example.


# 34. First milestone

Do NOT attempt real Voynich decipherment yet.

Deliver:

1. Python project skeleton.
2. Z3 dependency.
3. Basic alphabet abstraction.
4. Monoalphabetic substitution solver.
5. Homophonic substitution solver.
6. Variable-length verbose homophonic solver.
7. Synthetic encoder.
8. Round-trip recovery tests.
9. Benchmark for 10/25/50-word synthetic examples.
10. README explaining the model.

Stop and evaluate solver performance.


# 35. Second milestone

Add:

1. symbolic segmentation;
2. null glyphs;
3. word boundaries;
4. simple Latin dictionary model;
5. basic Optimize complexity minimization;
6. experiment serialization;
7. CLI;
8. reproducible experiment configs.

Again benchmark before proceeding.


# 36. Third milestone

Acquire and normalize:

1. Voynich EVA transcription;
2. Latin corpus.

Implement:

1. corpus statistics;
2. Voynich sample extraction;
3. equivalent-size controls;
4. initial Voynich SAT experiments.

Initial real-Voynich experiment should be deliberately restrictive:

    language = Latin
    boundaries preserved = true
    max homophones = small
    max code length = small
    nulls = disabled
    context = disabled

Then relax constraints systematically.


# 37. Fourth milestone

Implement experiment sweeps.

Example matrix:

    max_homophones = [1, 2, 3, 4, 5]
    max_code_length = [1, 2, 3]
    null_count = [0, 1, 2, 3]

Produce a table:

    H   L   N   result   runtime   complexity
    -----------------------------------------
    1   1   0   UNSAT     ...
    2   1   0   UNSAT     ...
    2   2   0   UNSAT     ...
    3   2   0   SAT       ...

This boundary is a primary research result.


# 38. Fifth milestone

Only after earlier milestones are robust:

- context-dependent encoding;
- generic table-driven mechanisms;
- morphological Latin models;
- alternative candidate languages;
- cross-folio validation;
- UNSAT-core analysis;
- stronger statistical controls.


# 39. Scientific interpretation rules

The program must NEVER report:

    "Voynich is Latin"

merely because a SAT solution exists.

SAT means only:

> At least one model satisfying the encoded assumptions exists.

Likewise, UNSAT means only:

> No solution exists within the precisely specified bounded model.

UNSAT does NOT mean:

> Voynich is not encrypted.

Distinguish:

    solver result
    model assumptions
    historical plausibility
    linguistic plausibility
    statistical plausibility

throughout reports and documentation.


# 40. Particularly interesting questions

Once infrastructure exists, investigate:

### Q1

How complicated must a verbose homophonic cipher become before it can explain a Voynich sample?

### Q2

Does allowing nulls dramatically reduce required complexity?

### Q3

Does preserving spaces make the model impossible?

### Q4

Does variable-length encoding matter substantially more than homophony?

### Q5

Does context dependence suddenly make Voynich easy to fit?

If so, how much context is required?

### Q6

How does minimum complexity compare with known encrypted Latin?

### Q7

How does it compare with pseudo-language generated without underlying plaintext?

### Q8

Can a model inferred from one Voynich section explain another without adding many new rules?

Q8 is especially important.


# 41. Negative results are valuable

Treat:

    UNSAT

as a useful result.

Treat:

    timeout

as different from UNSAT.

Treat:

    SAT only after adding enormous flexibility

as potentially evidence against the model rather than success.

Do not optimize the project toward obtaining readable plaintext at all costs.


# 42. README visualization

Eventually include a conceptual diagram:

    LATIN PLAINTEXT
          |
          v
    +-------------------+
    | plaintext model   |
    +-------------------+
          |
          v
    +-------------------+
    | verbose/homophone |
    | encoder           |
    +-------------------+
          |
          +---- optional nulls
          |
          +---- optional context
          |
          +---- optional table selection
          |
          v
    VOYNICH GLYPHS
          ^
          |
       observed

Z3 searches the unknown parts while the observed ciphertext remains fixed.


# 43. Guiding principle

The purpose of the project is not to construct an arbitrarily complicated mechanism that "deciphers" Voynich.

Given enough degrees of freedom, that is trivial and meaningless.

The interesting problem is:

> How little machinery is sufficient?

More formally:

    Find minimal M and plausible plaintext P

such that:

    M(P) = V

where:

    V = observed Voynich text

and compare:

    complexity(M_voynich)

against:

    complexity(M_known_cipher)
    complexity(M_generated_text)
    complexity(M_random_control)

That comparison—not an isolated SAT solution—is the central experiment.