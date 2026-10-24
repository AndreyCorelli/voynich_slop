# Iteration 69: can the discovered structure score lexical mappings?

**The first bridge fails. No larger nucleus is established.** A truth-free score based on iteration-68 structured carrier utility prefers the intact dictionary in only **5/10** saved first-corruption tests, prefers corruption in four and ties once. The matched shuffled-query control prefers intact in four. The predeclared gate required at least eight intact preferences and at least two more than the shuffled control, so dictionary search was not run under this score.

This does not invalidate the source-side precision/F1 gains of65/68. It shows that their attachment objective, even after an order-sensitive normalization, is not yet a useful lexical-decipherment objective. A discriminative attachment model does not automatically provide a likelihood of the proposed words.

## Frozen bridge score and access

Use source fold0's fixed morphology49, carrier56, primary competition65 and contextual relative-evidence68 models/policies, with no target-selected model, coefficient or threshold. Derive candidate POS from the fold0 source-fit word/POS counts; for unseen forms, map candidate dictionary POS possibilities to UD and choose the source-prior MAP alternative. Forms with no source/dictionary support remain X. These are estimates from proposed word spellings, not true target token tags. Source fit contains no Caesar. The previously cached morphology responses are queried by candidate word; they are not a plaintext-to-cipher lookup in the scorer.

For a proposed translated flat window, generate the same predicted morphology/candidate lattice, infer optional subject/carrier assignments, and calculate:

`F = [sum(selected edge score − frozen NONE cutoff) − λ × extra-subject count] / token count`.

The primary uses68 relative contestant evidence;65 supplies the attachment-only control. This is a new scoring hypothesis, **not** a normalized word-language likelihood. No reference edge, F1, target POS, true sentence boundary, lemma, morphology or grammatical label enters inference. The scorer's API receives only candidate word strings and fixed source resources.

The primary grammatical lift is `F(ordered words) − mean F(five fixed permutations)`. Each permutation preserves exactly the word multiset and uses the same positional permutation for intact/corrupted versions. A sixth permutation supplies a shuffled-query control with the same five background references. A separate source-fit unigram mean log-frequency is reported but never combined with grammar or tuned after results.

The diagnostic uses every historical first-corruption move saved in iteration1: ten moves at target lengths500–32,000, twelve flat64-token crops in total. One move has three crops, combined by token-weighted mean. These are proposed correct versus corrupted dictionaries in correct surrounding context: an easier **perfect-start local diagnostic**, not blind recovery from a poor dictionary or a full-document score. Candidate originals are explicitly available to the pairwise scorer even when missing from a bounded retrieval inventory. No supplied function anchors are needed for these candidate-translation scores.

The frozen gate requires primary ordered lift to strictly prefer intact in at least8/10 moves and exceed shuffled-query wins by at least two. Ties fail. It is an engineering falsification gate on reused development errors, not a population significance test. Failure stops dictionary search/nucleus selection under this objective.

## First-corruption result

| Score | Intact preferred | Corruption preferred | Tied |
|---|---:|---:|---:|
| Primary68 grammatical lift | 5 | 4 | 1 |
|68 shuffled-query lift | 4 | 5 | 1 |
|65 grammatical lift | 6 | 3 | 1 |
|65 shuffled-query lift | 4 | 5 | 1 |
| Raw68 carrier utility | 2 | 2 | 6 |
| Raw65 carrier utility | 2 | 2 | 6 |
| Source-fit word frequency | 3 | 0 | 7 |

Do not interpret five versus four as evidence of useful grammar beyond frequency/context chance. Neither grammar variant passes. The old iteration1 independent-obligation score rejected0/10, but the present5/10 does not establish successful restoration: four corruptions are still strictly rewarded and most raw comparisons tie. No post-result mixture with unigram or old language-model scores was tested.

## Separate candidate/privileged-morphology audit

Replayed the earlier, previously explored **22 known lexical types in the2,022-token Caesar excerpt**, using its original100,000-form dictionary, supplied function-word mappings and disjoint Caesar-book frequency counts. These resources/frequencies are distinct from the non-Caesar source-fit statistics used by the structural scorer above. This audit is an explicitly privileged resource ceiling, not the realistic grammar-inference arm.

All22 originals are available. The unfiltered content pool contains96,823 forms. Frequency gives0/22 exact top-one and3/22 top-ten; filtering by a shared complete dictionary analysis gives4/22 top-one and17/22 top-ten. All22 saved oracle pool sizes/ranks reproduce exactly. Full analyses here are possibilities of the original word, not inferred token analyses or recovered dependency links. This confirms useful information content when supplied, while leaving the inference gap intact.

Membership checks for the ten different historical first-corruption originals reveal a separate coverage issue: only3/10 are present in that bounded100k inventory. A post hoc read-only check finds8/10 in the separate2,557,237-form old Latin inventory; `pisone` and `perpendiculum` are absent there. These inventories are different resources, not nested sets: `onerariam`, for example, is in the100k resource but absent in the larger one. No inventory was expanded or silently substituted. The scoring gate already supplied all ten original proposals, so missing retrieval candidates cannot explain its failure.

## Why the bridge fails

The replacements are incorrect under the known synthetic word mapping; they have not been independently certified as ungrammatical Latin. Grammatical alternatives can differ in lexical identity. This experiment tests usefulness for exact dictionary recovery, not whether a grammar checker should reject every alternative wording.

Post hoc traces preserve candidate POS, candidate edges and selected endpoint participation for each changed position. The graphs do react to changes, but a reaction need not affect the selected utility. Six of ten raw-utility comparisons tie. Cases such as `pisonem→indiligentiae` and `pisone→indiligentiae` have no selected subject/carrier role for the changed position in either version. Their object/oblique lexical identity is outside this score's modeled evidence. Some grammatical-lift differences then arise solely from changes in the shuffled reference background, rather than changes in the ordered text's utility.

More seriously, `celtae→exceptans` and `caedere→admittitur` create newly selected carrier attachments and improve raw utility. The source-derived analysis channel projects `celtae` to ADJ and `exceptans` to VERB; it does not possess the true token readings. Broad predicted finiteness/attachment possibilities can reward the new, wrong carrier. This is positive support for a spurious analysis, not merely absence of evidence.

The current mechanism therefore has two gaps: candidate-derived POS/morphology and structural coverage, and an objective rewarding favorable attachment opportunities instead of explaining all observed words. Correct spelling, especially between candidates with similar grammatical readings, remains a separate lexical problem. These cases do not prove grammar cannot improve recovery, but they rule out treating the present parser utility as that improvement.

## Verification, decision and next proposal

Artifacts are in `experiments/results/grammar-restoration/iteration69/`. Design/source-model inputs and all predictions were separately frozen. The independent audit replays48 aggregate score queries comprising336 raw structured solves, all22 oracle retrieval ranks, candidate POS statistics and the gate decision. Read-only larger-inventory membership has its own post hoc input hashes. **125 relevant tests pass**, covering source-only POS projection, unknown handling, cipher renaming invariance, objective accounting and shuffle preservation, alongside the earlier structural suites. Older frozen inputs remain unchanged.

Preserve65/68 as source-side structural findings. Do not start a long dictionary search or claim additional nuclei under this failed score. The next lexical-score proposal should distinguish **word/analysis compatibility with contextual roles** from the utility of whichever attachments happen to be easiest to select; it needs an explicit treatment of non-subject tokens and missing analyses. An oracle role/analysis ceiling on already declared annotated material can separate missing grammatical information from scoring failure before fitting a new lexical model. Both exact mapping count and nucleus precision/coverage must be evaluated after a score passes the falsification gates; parser F1 remains evaluation, not a decipherment objective.

No dictionary recovery or nucleus was selected, no true target POS/parse was supplied to the realistic scorer, and no recovery percentage is claimed. The200-sentence grammar reserve and sealed lexical final test remain unscored. No new Caesar/Jerome grammar queries were scored; only already saved historical candidate texts and the older oracle retrieval cases were reused. No plaintext or Voynich restoration result follows from these diagnostics.
