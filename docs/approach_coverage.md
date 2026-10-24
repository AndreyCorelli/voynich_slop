# Coverage of tried approaches

Research snapshot: **11 October 2026**. This is a structural map of the recorded
experiment families, not a chronological log or an exhaustive Cartesian grid.
Detailed reports remain the evidence; links below lead to them. Branch decisions
are recommendations, not claims that an entire historical hypothesis is false.

**We have explored some narrow branches deeply.** Latin dictionary construction,
solver formulation and local-statistical prediction have much more coverage than
alternative spacing or cipher structure. Most cipher fits still preserve spaces
and use a globally prefix-free, reversible unit-to-code mapping. No tested
family has established grammatical plaintext and reliable manuscript-wide
prediction against matched controls.

Recent A/B work adds necessary constraints, shared-parameter predictions and
section/position matching, rather than a recovered cipher. The main implication
is that **the pooled length gap is not a stable target independent of corpus
composition and glyph counting**. The matched findings below qualify its use in
model selection. Statistical classifiers remain parked after failed transfer.

## Read the evidence labels first

| Label | What was actually tested | What it does not establish |
| --- | --- | --- |
| **FIT** | Shared-key SAT/UNSAT on an identified manuscript block | Language identification or readable prose; SAT is usually dictionary membership |
| **RECOVERY** | Known synthetic encryptions with hidden parameters, sometimes assisted | That the mechanism describes Voynich; oracle assistance must stay visible |
| **CAPACITY** | Length, repetition, normalization or inventory feasibility | A common key, grammatical text or successful hidden recovery |
| **STATISTICS** | Distributions/predictors, including full-transcription measurements | A reversible mechanism or exclusive historical explanation |
| **PROPOSED** | A specified next experiment | Implementation or completed results |

**UNKNOWN is unresolved.** A model-specific UNSAT excludes only its precise
vocabulary, sample and assumptions. **Park** means further similar runs currently
have low expected information; it is separate from scientific rejection.

## Currier A/B findings and their limits

The [structural census](currier_structural_constraints.md) measures A/B separately
under two filtering cohorts and atomic versus existing reversible grouped EVA.
The [shared-parameter audit](currier_shared_parameters.md) asks whether a fixed
key predicts the contrast. The [section/line-position audit](currier_section_position.md)
then checks whether the pooled contrast survives on comparable pages.

| Finding | Recorded result | Consequence for model choice |
| --- | --- | --- |
| Fixed-two output per plaintext unit | No eligible 22-word window passes divisibility in either class, cohort or counting convention | **CAPACITY:** excludes this precise preserved-space, no-null model; not H2 generally or a language |
| Pooled mean lengths | Clean-word atomic means A 5.009, B 5.333; grouped A 4.302, B 4.835 | **STATISTICS:** B is longer in this filtered census; the size depends on counting convention |
| Comparable section coverage | Only herbal H meets the five-folios-per-class threshold; fully matched primary analysis has 95 A and 32 B folios | Other sections lack adequate overlap; no manuscript-wide adjusted estimate is supported |
| Atomic gap after section, paragraph-line-role and original word-position matching | B−A **+.128**, folio-resampling interval **−.022 to +.305**, versus pooled +.324 | Zero is compatible on matched herbal pages; pooled length differences alone do not establish different cipher parameters |
| Grouped gap under the same matching | B−A **+.386**, interval **+.253 to +.548**, versus pooled +.532 | A residual remains in this convention and is a constraint on models that use these units; not language or key identification |
| Why the conventions differ | Grouping saves .764 units per matched A word versus .505 per B word; difference .258, mainly `cth` and `ch` | Output structure differs on comparable pages; these groupings are not established historical cipher symbols |
| Filtering sensitivity | Whole-clean-line adjusted gaps: atomic +.083 (−.082 to +.258), grouped +.331 (+.181 to +.474) | The counting-convention dependence persists under stricter filtering |
| Exact repeats | A has a higher observed within-folio repeat rate, but A/B folio intervals overlap; grouping leaves repeats unchanged | Repetition remains an exact candidate constraint; the observed class difference is less secure than the pooled length difference |
| Shared-parameter moment prediction | None of 63 tested configurations matches both absolute mean lengths and the A/B contrast; closest A candidate predicts the wrong direction | This finite generator/source-assumption shortlist fails; it does not exclude shared keys with differing plaintext composition or state |

**Coverage matters:** the primary matched comparison retains 4,634 A tokens
(75.7% of clean A) but only 1,722 B tokens (15.2% of clean B). Section restriction
and reweighting change the target population; the smaller atomic gap is not a
causal estimate of how much section “explains.” Intervals assume exchangeable
folios and omit transcription and glyph-interpretation uncertainty. Zero inside
an interval does not prove identical distributions or successful shared-key
prediction.

The shared-parameter audit's original full-cohort result remains valid for that
cohort. Matching qualifies its interpretation: **different keys or languages are
not required by the pooled atomic length gap alone**. Its seven-contraction
extension was added after the letter-stage results, not as a fresh blinded
replication; the broader contraction inventory was not tested there. Some Caesar
configurations match the contrast while predicting means around nine glyphs,
which is not successful absolute prediction.

The new [paired mechanism screen](currier_mechanism_comparison.md) and
[one-glyph follow-up](currier_selection_comparison.md) also show that null effects
depend on expansion cost. The latter uses a 52-symbol diagnostic alphabet.
The [25-label comparison](currier_alphabet_comparison.md) finds no consistent
sparse-homophony advantage. [Same-source discrimination](currier_mechanism_discrimination.md)
has some success, but [cross-source transfer](currier_mechanism_transfer.md)
rejects most genuine cases and makes accepted sparse-selection errors. These
scores are **parked for manuscript ranking**, rather than used to choose a
“best” deciphering hypothesis.

## Dimensions that must stay separate

| Dimension | Variants explored | Coverage gap / distinction |
| --- | --- | --- |
| Manuscript sampling / counting | Currier A/B; whole-clean-line versus clean-word cohorts; atomic versus reversible grouped EVA; herbal section/position matching | Matched support covers only 15.2% of clean B; glyph convention changes the residual contrast; no matched language inference |
| Language / source | Classical and medieval Latin; nine regional German sources; Italian and Czech length comparanda | Latin/German have cipher fits; Italian/Czech do not have comparable cipher-recovery campaigns |
| Source normalization | Historical spellings, canonical Latin forms, German corrected versus legacy parsing | Source editions and normalizers change the experiment; German abbreviation expansion during ingestion is not a contraction cipher |
| Plaintext units | Ordinary letters; `ae`; seven macros; documented27-rule core; nasal/macro cost envelopes | Envelopes are capacity calculations; ambiguous nasal marks are not calibrated reversible encoders |
| **Word boundaries (spaces)** | Mainly preserved one-to-one; exhaustive ≤2-cut-edit exact-passage screen; synthetic renewal-generated boundaries | General unknown/recovered word boundaries remain largely untested |
| **Internal code boundaries** | Public fixed-width codes, oracle offsets/lengths, hidden mixed widths | Hidden code segmentation does **not** mean hidden word spacing |
| Output width | Fixed1/2; mixed1–2/1–3; other widths in arithmetic screens | Width2 is not H2; one-glyph diagnostic alphabets can be much larger than EVA |
| Homophone count | H1 and H<=2 extensively; broader framework bounds configurable | Increasing H is a different change from contractions or output width |
| Homophone selection | Free choices; text-wide/per-word cycles; independent and deterministic whole-word synthetic selection | Observed code coverage does not reveal which codes belong together |
| Language constraint | Finite attested vocabularies, generated morphology, word-pair experiments, frequency/context reranking | A dictionary or soft bigram score is not a Latin/German syntax model |
| Extra mechanism | Bounded nulls/complexity minimization; known contextual-marker encoder; copy/state/template generators | Implementation/synthetic evidence is not a calibrated manuscript fit for each mechanism |
| Evaluation / assistance | Training fit, frozen continuation, shuffled controls; known plaintext/lengths/boundaries, training-assisted vocabulary, engineered coverage, injected truth | Assisted diagnostics and hidden recovery must never share a single success label |

A contraction maps several expanded letters to fewer plaintext units. An
expansion emits multiple output glyphs for a plaintext unit. They can coexist:
`per` → one macro → a two-glyph code still contracts three original letters to
two glyphs. Neither parameter changes word spacing automatically.

## Structural model coverage

Each row groups a family of reports. Rows are **not** matched likelihood
comparisons: their samples, dictionaries, alphabets and assistance differ.

| Family | Language / units | Spaces | Codes / choices | Evidence and outcome | Branch decision |
| --- | --- | --- | --- | --- | --- |
| Small and expanded dictionary fits | Latin letters, progressively corrected Caesar vocabulary | Preserved | H<=2, mixed up to3, free/cyclic | **FIT:** initial narrow UNSATs changed with vocabulary; free and cyclic outcomes differ. [Frontier](latin_frontier.md), [selection comparison](german_selection.md) | **Park** arbitrary dictionary enlargement as evidence of prose |
| Regional German fits and audits | Nine dated regional vocabularies, letters | Preserved | H<=2, mixed1–3; free/text cycles | **FIT:** several short-block SATs; corrected Swabian/Alsatian30-word SATs, corrected Ripuarian UNSAT. [Regional cycles](german_regional_cycles.md), [audit](german_regional_audit.md) | **Park** more dictionary SATs until predictive comparison is calibrated |
| Conflict localization | Latin and German fixed dictionaries | Preserved | Original model held fixed per search | **FIT:** minimal prefix/suffix and deletion obstructions localized. [Latin prefix](clean_latin_prefix.md), [German prefix](german_free_prefix.md), [deletions](german_word_deletions.md) | **Completed** for those inputs; not a broad mechanism comparison |
| Particular keys on next text | Latin/Swabian/Alsatian letters | Preserved | Saved free-selection mixed-width keys frozen | **FIT/prediction:** keys fail complete next-block coverage; novel dictionary hits weak. [Frozen continuation](frozen_key_holdout.md) | **Completed:** those keys failed; their families remain open |
| Latin contractions plus expansion | Caesar letters, `ae`, seven macros | Preserved | H<=2, mixed1–3, free | **FIT + RECOVERY:**23-word SAT with macros and without; contractions unnecessary for that fit. [Mixed comparison](latin_mixed_comparison.md) | **Completed** narrow necessity comparison; no grammatical interpretation |
| Historical word/window lengths | Latin/German/Italian/Czech letters; specified normalization | Source spacing retained | Necessary emission bounds only | **CAPACITY:** German/vernacular samples often shorter; no language likelihood. [Historical lengths](historical_word_lengths.md), [grouped EVA](eva_tokenization.md) | **Completed screen**, useful prior constraints |
| Contraction shortening and tails | Seven Latin works; seven/core27/37-rule envelopes | Preserved | Minimum unit counts, no common key | **CAPACITY:** core improves shortening; optimistic nasal profiles can pass some means but fail exact distribution capacity. [Seven-unit audit](contraction_distribution_audit.md), [broader audit](broader_contraction_capacity.md) | **Park** further inventory growth without a new mechanism question |
| Bounded space edits | Six medieval Latin works; letters/seven macros | ≤2 inserted/deleted cuts | Positionwise1–3 bounds and exact word repetition; no solve | **CAPACITY:** no surviving exact source alignment; all83 seven-unit length fits contradict repetition. [Boundary edits](word_boundary_edits.md) | **Completed narrow screen**; general unknown spacing still open |
| Natural Latin fixed-two recovery | Attested/generated Latin letters, several vocabulary/solver formulations | Preserved; code boundaries public | H1/H2, fixed2; free/cyclic synthetic choices | **RECOVERY:** useful controls exist, but the fixed-two convention fails divisibility in every scanned22-word EVA window. [Natural H2](latin_h2_random_context_loop.md), [width audit](manuscript_width_audit.md) | **Park** as manuscript model; retain as implementation benchmark |
| Hidden contraction recovery | Core27, Latin natural excerpts | Preserved; mixed code boundaries hidden | H<=2, fixed1 or mixed1–2, free | **RECOVERY:** ordinary training11/24 on three H2single cases; engineered coverage21/24; fresh covered mixed Caroli7/8. Grouping/meaning ambiguity remains. [Hidden calibration](contraction_hidden_calibration.md), [coverage calibration](contraction_coverage_calibration.md) | **Blocked on calibration**, not historically rejected |
| Frequency / context selection | External Latin unigram/adjacent-word priors | Preserved | Rerank existing verified keys; no new grouping search | **RECOVERY/ranking:** no held-out improvement in saved pools; owner swaps cannot fix split groups. [Frequency](latin_frequency_ranking.md), [context](contraction_context_ranking.md) | **Park** rescoring the same owner-swap pools |
| Full morphological inventories / solver engineering | Latin attested plus independently generated forms | Preserved; many public/oracle diagnostics | Membership encodings, shared keys, construction profiling | **RECOVERY/CAPACITY:** millions of forms supported, but availability and SAT do not guarantee true plaintext. [Form inventory](latin_form_inventory.md), [layered cipher](latin_layered_cipher.md), [profiling](recovery_construction_profile.md) | **Maintenance only** unless required by a specific calibrated test |
| Nulls / complexity minimization | Framework vocabularies; Latin/Middle Bavarian real-passage generators | Preserved | Dedicated null glyphs, bounded objectives; matched independent/positional insertion | **RECOVERY + STATISTICS:** implemented; null length compatibility depends on expansion cost, with no overall mechanism match. [Null milestone](nulls_optimization.md), [paired screen](currier_mechanism_comparison.md), [width sensitivity](currier_selection_comparison.md) | **Open calibrated-fit gap**; neither all null models rejected nor a manuscript decoder established |
| Currier length/repetition constraints | Filtered A/B census, atomic/grouped EVA | Supplied transcription boundaries | Necessary width reachability and inverse-decoding repeat invariants | **CAPACITY/STATISTICS:** fixed-two fails; deterministic mappings preserve frequency spectra. [Census](currier_structural_constraints.md) | **Retain as constraints**, not language scores |
| Shared A/B parameter predictions | Caesar/Aquinas/Middle Bavarian letters; seven Latin contractions | Preserved | Shared mono/sparse/mixed-width keys; stationary or source-half plaintext assumptions | **STATISTICS/prediction:** no joint absolute-mean/contrast match among 63 configurations. [Shared parameters](currier_shared_parameters.md) | **Completed finite screen**; no class-specific parameter tuning justified |
| Currier section/position matching | A/B paragraph census; two cohorts and unit conventions | Original positions retained before filtering | Same section/line-role/word-position weights; folio resampling | **STATISTICS:** herbal atomic gap includes zero; grouped gap remains positive; B coverage limited. [Matching](currier_section_position.md) | **Qualify pooled contrasts**; preserve both counting conventions |
| Synthetic mechanism classification | Real Latin/Middle Bavarian passages, fresh keys and held-out passages | Preserved or specified renewal cuts | Mono/sparse selection/renewal; training-only centroids and rejection | **STATISTICS/calibration:** same-source success fails to transfer reliably; control rejection accompanies genuine-case rejection. [Discrimination](currier_mechanism_discrimination.md), [transfer](currier_mechanism_transfer.md) | **Park** classifier-based manuscript ranking |
| Local/long-range feature families | EVA; Latin/German controls; copying, state, template generators | Supplied word/line/block layout | Statistical predictors; some known reversible marker encoders | **STATISTICS:** associations replicate; different generators imitate them, defeating mechanism specificity. [Boundary mechanisms](boundary_mechanisms.md), [joint ordering](joint_order_constraints.md), [cross-family failure](long_range_families.md) | **Park** mechanism attribution through more feature tuning |

## Language and regional coverage

**Latin:** Caesar is the main cipher-dictionary source. Aquinas, *Vita Caroli IV*,
Einhard, *Gesta Francorum*, Bury and Dante extend historical passage/capacity
coverage. Recent core-contraction recovery uses Caesar/Aquinas/Einhard and one
fresh Caroli case. All seven having length measurements does not mean all seven
have comparable cipher-recovery tests. Mechanically generated Latin forms are
another inventory, not seven additional natural corpora.

**German:** these are individual source witnesses, not complete dialect models.
The first outcome column below uses the original22-word text-cycle experiment;
the second uses separately audited full30-word models, usually free selection.
Different columns must not be read as repeats of identical inputs.

| Source | Regional label | Original22-word cycle result | Later corrected30-word evidence |
| --- | --- | --- | --- |
| 113, Kottanerin | Middle Bavarian, Vienna | UNSAT; free selection SAT on22 | Original dictionary extension hits one-letter length obstruction at23; no comparable corrected30-word SAT |
| 123, Neidhart | Swabian, Ulm | SAT, legacy vocabulary | Corrected free-selection SAT; frozen continuation inadequate; long shuffle discrimination unresolved |
| 133, Pillenreuth | East Franconian, Nuremberg | SAT, legacy vocabulary | Original full-block SAT relies on `k/x`; excluding those forms gives UNSAT |
| 143, Tauler edition | Upper Saxon, Leipzig | SAT, legacy vocabulary | Other extension/free-model conflict tests; no surviving corrected30-word result comparable to123/233 |
| 153, Koelhoff | Ripuarian, Cologne | SAT, legacy vocabulary | Corrected full-block UNSAT |
| 223, Burlaeus edition | East Swabian, Augsburg | UNSAT | No comparable corrected30-word result recorded here |
| 233, Brunschwig | Alsatian, Strasbourg | SAT, legacy vocabulary | Corrected free-selection SAT; frozen continuation inadequate; controls incomplete |
| 243, Wonnecke | Hessian, Mainz | UNSAT | No comparable corrected30-word result recorded here |
| 253, Rothe witness | Thuringian, Eisenach | UNSAT | No comparable corrected30-word result recorded here |

Evidence: [regional table](german_regional_cycles.md),
[Middle Bavarian](german_selection.md), [source113 extension](german_scaling.md),
[source133 sensitivity](german_short_form_audit.md),
[corrected regional audit](german_regional_audit.md),
[shuffle limits](german_shuffle_controls.md). Earlier length artifacts retain
legacy German bracket handling; they were not silently replaced by the corrected
solver vocabularies.

**Italian and Czech:** historical length/normalization and EVA-grouping screens,
not a Latin/German-comparable Z3 search or calibrated recovery campaign.
**Other comparanda:** Greek and additional historical texts in
[frequency notes](research/word_frequences.md) are reference distributions,
not tested plaintext-language hypotheses. The quarantined mixed Latin/English
Turba extraction must not become a Latin prior.

## Coverage by shortening mechanism and boundaries

This small matrix prevents a familiar result in one cell being mistaken for
coverage of another. “Not recorded” describes this campaign, not impossibility.

| Plaintext / emission | Preserved spaces | ≤2 space edits | General unknown spaces |
| --- | --- | --- | --- |
| Ordinary letters → mixed1–3 outputs | Latin/German manuscript fits; synthetic calibration | Latin exact-source necessary-condition screen | Not recorded as a general hidden recovery campaign |
| Seven Latin macros → mixed1–3 outputs | Short manuscript fit and capacity screens | Latin exact-source necessary-condition screen | Not recorded |
| Core27 macros → fixed1 / mixed1–2 outputs | Synthetic recovery and ownership calibration; manuscript distribution screen | Not recorded with core27 | Not recorded |
| Nasal disambiguation envelopes | Capacity only; not an implemented historical decoder | Not recorded | Not recorded |
| German contractions as cipher units | Not recorded; ingestion normalization is different | Not recorded | Not recorded |
| Bounded nulls | Framework calibration; matched insertion statistics on real-passage generators | Not recorded | Not recorded |

Internal mixed-width segmentation has been explored inside the preserved-spaces
column. None of those successes establishes the general unknown-spaces column.
Renewal-generated spaces have synthetic statistics/classification coverage, not
general hidden-boundary recovery. Likewise a known state/template generator producing EVA-like statistics does
not fill an untested stateful cipher-fit cell.

## Where the campaign is deep, and where it is thin

| Area | Depth of existing work | Practical interpretation |
| --- | --- | --- |
| Latin vocabularies, membership and solver performance | Extensive, many successive diagnostics | Often instrument development rather than new historical hypotheses |
| German regional dictionaries | Broad short-block FIT coverage; some serious normalization audits | Worth retaining, but calibrated language comparison remains absent |
| Contractions | Extensive capacity work; limited natural recovery, then engineered coverage | No need for more signs until grouping/meaning ambiguity is addressed |
| Word-boundary correspondence | One very narrow edited-passage screen | Major untested structural assumption; a full search is expensive |
| Independent language/genre comparison under one mechanism | Thin | Latin versus German is confounded by inventory and protocol differences |
| Currier A/B composition and counting sensitivity | Census, folio uncertainty, shared-parameter screens and herbal matching | Pooled contrasts do not establish distinct keys; limited overlap and unit interpretation remain central |
| Full-manuscript common-key recovery | Not established | Full-text statistics are not full-text cipher fits |
| Mechanism-specific statistical discrimination | Extensive negative calibration | This branch should remain parked rather than accumulate similar plots |

The recurring “dead horse” is **rerunning a branch without changing the question**:
more dictionary SATs, larger inventories, rescoring owner-only swaps, or more
feature gains do not by themselves address the missing evidence. The map gives
us a reason to stop those loops without declaring Latin, German or contractions
false.

## Decisions for the next work

1. **Park** feature/classifier tuning, arbitrary vocabulary enlargement and
   same-pool frequency/context loops. There is no established leading deciphering
   model, and better agreement on averages is not reliable mechanism selection.
2. **Audit existing synthetic recovery before new manuscript fitting.** Identify
   whether any recorded solver recovers a hidden key and decodes unseen words
   under the exact intended assumptions. Reuse results; do not start another
   open-ended calibration or timeout ladder if none qualifies.
3. **If that gate passes, run one bounded frozen-key prediction test.** Prioritize
   preserved spaces with the documented reversible contractions; select blocks
   in advance, fit the first, freeze the key and test the second against shuffled
   controls. Add no homophones, vocabulary exceptions or parameter adjustments
   after seeing continuation text. Report ambiguity and coverage; a readable
   interpretation chosen from many alternatives is not the success criterion.
4. **Keep A/B as a conditional structural check.** Require the selected model to
   state its glyph convention and explain differing plaintext composition or
   state before predicting the class contrast. Match comparable sections where
   possible; do not introduce Currier-specific length parameters solely to fit
   the pooled gap. Boundary regeneration remains a separate alternative.

The earlier oracle-grouping instrument diagnostic remains **PROPOSED, not run**,
but is no longer the default next branch. A failure to pass the bounded recovery/
prediction gates is a reason to park that family and change the mechanism
substantially, not begin another round of distribution-score refinement.

Before any new loop, identify its cell in this map, the hypothesis it separates,
the changed dimension, the held-out success criterion and the stopping rule.
A rerun of an already answered question needs an explicit new reason. These are
research discipline recommendations, not permission gates.

## Scope of the page

This page groups recorded experiment families rather than indexing every seed,
worker encoding or result file. It deliberately gives no “percent of all models
covered”: parameter families are open-ended, and unequal experiments cannot be
counted as equal coverage. Keep detailed frozen reports intact. Update this map
when a structural family, assistance level or branch decision changes; do not
prepend another chronological milestone to replace the overview.
