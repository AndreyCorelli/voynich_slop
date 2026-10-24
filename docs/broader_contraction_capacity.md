# Broader documented contractions: frozen capacity check

The broader fixed-expansion core improves compression but still fails every tested Latin source mean. Optimistic nasal profiles pass some atomic-EVA means, while every profile/source retains short-word distribution deficits. This does not rule out contractions generally or establish a manuscript language. Stop these fixed inventories without outcome-driven additions.

## Research and rule selection

The new [versioned inventory](../experiments/configs/latin-contractions-broader-v1.json) was written before capacity scoring. It retains the previous seven rules and adds independently documented conventions, not substrings selected from Voynich or fitted plaintext. Documentation consulted on 2026-10-10:

- [HMML Humanist transcription](https://hmmlschool.org/latin-humanist-transcription/): distinct stroked-q forms, q plus a separate mark, and several whole-word contractions.
- [HMML Insular transcription](https://hmmlschool.org/latin-insular-transcription/): additional whole-word signs; these are earlier precedents, not a demonstrated fifteenth-century combined system.
- [HMML Christian Late Antiquity transcription](https://hmmlschool.org/latin-christian-antiquity-transcrip/): contracted sacred names with retained letter sequences and an after-b ending sign.
- [HMML Carolingian transcription](https://hmmlschool.org/latin-caroline-transcription/) and [Gothic transcription](https://hmmlschool.org/latin-gothic-transcription/): common omission marks with contextual expansion.
- [National Archives palaeography material](https://cdn.nationalarchives.gov.uk/documents/latin-palaeography-activities-and-documents.pdf): an above-t omission example used for one explicitly generous marked-letter rule.

The core has 27 macros, including the original seven. Additions are initial qui/qua, final que, whole-word enim/autem/eius/etiam/tamen/omnino/sed, a ter marked-letter abstraction, final us after b, and eight explicitly documented inflected sacred-name forms. Scopes and costs are recorded per rule. Initial qui/qua are conservative restrictions; any-position ter is a generous modeling extrapolation from an example. No claim of exhaustive coverage, actual manuscript use or a complete historical codebook is made.

## Count retained letters and ambiguity explicitly

Each optional macro has a retained graphic-unit cost. Stroked letters and attached tituli can be treated as single compound units, while separate retained letters/signs remain separate. For example, tamen costs two units, omnino three, sed two, que two, and the sacred-name contractions cost two or three. These are explicit abstraction choices, not known EVA glyph counts.

A path stores distinct expansion labels and its summed cost; path-label count need not equal graphic-unit cost. Such paths reverse exactly to normalized plaintext. They are **not a constructed cipher codebook**: unique expansion labels do not prove that ambiguous historical marks are physically uniquely decodable.

Four predeclared profiles are scored:

| Profile | Rules | Meaning |
|---|---:|---|
| Broader core | 27 | Fixed logical expansions, retained-unit costs |
| Final nasal envelope | 37 | Core plus vowel+m/n contraction at word end |
| Syllable nasal envelope | 37 | Core plus vowel+m/n before a consonant or word end |
| One-unit macro envelope | 27 | Core macros all cost one; deliberate optimistic cipher-unit ceiling |

The two nasal profiles supply separate logical labels for m and n expansions. Actual common marks can require context to distinguish them. A reversible cipher would need disambiguation machinery, which this capacity ceiling does not price. The internal boundary condition is a simple approximation, not a Latin syllabifier. The one-unit profile is a different macro-coding hypothesis, not a paleographic count of retained letters. Profiles are frozen sensitivities, not candidates selected after seeing a fit.

## Seven stages

1. Freeze the researched inventory, scopes, costs and source/target protocol.
2. Broader core on Caesar.
3. Broader core on six cached medieval Latin works.
4. Final-nasal envelope on all seven sources.
5. Syllable-nasal envelope on all seven sources.
6. One-unit-macro ceiling on all seven sources.
7. Compare full word and overlapping 22-word-window distributions against atomic and existing grouped EVA, then stop.

Plans precede scoring and pin preparation and preceding-result digests. Source extraction, normalization, barriers and manuscript targets are reused unchanged from the [previous distribution audit](contraction_distribution_audit.md). The existing grouped convention is not an established true glyph inventory. No new corpus acquisition, solver, homophone selection, key recovery or plaintext fit occurs.

## Results

Minimum mean input units per word under maximum permitted contraction; compare atomic EVA **4.971** and existing grouped EVA **4.464**.

| Source | Broader core | Final nasal | Syllable nasal | One-unit macros |
|---|---:|---:|---:|---:|
| caesar | 5.533 | 5.371 | 5.187 | 5.492 |
| aquinas | 5.053 | 4.886 | 4.709 | 5.032 |
| caroli | 5.294 | 5.102 | 4.933 | 5.264 |
| einhard | 5.501 | 5.327 | 5.156 | 5.463 |
| gesta | 5.356 | 5.210 | 4.998 | 5.308 |
| bury | 6.099 | 5.951 | 5.740 | 6.075 |
| dante | 5.183 | 4.994 | 4.826 | 5.150 |

The core saves **7.2–9.7%** of original letters, versus approximately 3.8–5.0% for the previous seven rules. Every core mean remains too long for the atomic target. Even the deliberately optimistic one-unit core profile fails every mean. With final nasals, only Aquinas passes the atomic mean. With the internal nasal envelope, **Aquinas, Vita Caroli and Dante** pass; Gesta Francorum at 4.998 narrowly fails. No profile/source passes the grouped mean.

The internal nasal envelope saves **12.9–15.9%** of letters. Mean-passing cases have only about **0.8–5.6%** mean expansion headroom beyond their already maximally compressed counts. Actual rule use below this envelope or longer homophonic outputs would consume that margin.

### Passing the mean is insufficient

At each length threshold t, compare the fraction of source words that can reach at most t input units with the manuscript fraction no longer than t. Output codes cannot shorten those input units further. Under exact empirical frequency matching, every scored profile/source has a positive short-tail capacity deficit. Even the generous internal-nasal envelope retains atomic deficits of **10.7–22.9 percentage points**, at source-specific thresholds. Optimistic extra unit removal remains **0.390–0.954 units per word**, even allowing arbitrary quantile matching and ignoring actual word order.

Complete word and 22-word-window histograms, threshold deficits and rational-coupling removal bounds are saved. Window removal is measured per 22-word window, not per word; overlapping windows are descriptive observations rather than independent trials. The absence of a zero short-tail deficit means the tested exact-frequency capacity gate does not pass, despite three successful mean checks.

This benchmark assumes the unknown plaintext has exactly the empirical source-frequency marginal. That is a strong comparison, not a necessary property of all Latin. Another genre, vocabulary, spelling convention or spacing model could have different marginals. No language-wide exclusion, likelihood ranking or manuscript decipherment follows.

## Assessment

Broader documented contractions make a material difference, particularly nasal omission, so the original short-word concern was worth investigating. But this fixed family does not yet match the full word-length benchmark. A shared prefix-free cipher could impose further restrictions; capacity alone would not establish its existence.

Stop this fixed inventory rather than add more rules until the histograms fit. The next useful alternative is the assumption that EVA spaces correspond one-for-one to plaintext words. A predefined corpus-level spacing sensitivity could test the length issue with the inventory fixed. This would be distinct from the earlier two-edit exact-passage screen; it must retain a bounded, inspectable rule and must not be interpreted as a reversible cipher until decoding is demonstrated. Other genre choices remain alternatives, not grounds for selecting favorable passages after scoring.

Do not start Z3 recovery merely because one mean passes. The separate hidden-boundary synthetic prediction gate remains necessary for any newly capacity-positive reversible model.

## Verification and reproduce

```sh
.venv/bin/python -m benchmarks.broader_contraction_capacity --run
.venv/bin/python -m benchmarks.broader_contraction_validation
.venv/bin/python -m pytest -q tests/integration/test_broader_contraction_capacity.py
```

Results: `experiments/results/broader-contraction-capacity/`. Inventory evidence/costs/scopes, prepared sources/targets, seven plans/results, word-level minimum paths and frequencies, full histograms, comparisons, assessment and validation are saved. Frozen prior code and artifacts are preserved.

Three tests check retained-unit versus one-unit semantics, nonoverlap/scopes, and explicit nasal boundary approximation. Independent reverse weighted dynamic programming reconstructs minima; validation checks each saved path's scopes, costs and expansion, all word/window histograms, rational quantile integrals, rule counts, digests and summaries. Historical evidence judgments and cached source parsing are reused rather than independently palaeographically certified.

Verification passed: **129,824 independent weighted minimum-word-type checks**, covering **416,968 token occurrences across profiles**, plus all three tests. Zero solver calls.
