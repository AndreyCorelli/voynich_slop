# High-level goal and research priorities

The final goal is to decipher the Voynich manuscript. Latin restoration experiments are a means toward that goal, not the final objective.

## Working hypotheses

- The manuscript's language is Latin. This is a working hypothesis, not an established conclusion.
- One EVA-encoded Voynich word corresponds to one Latin word. This is likewise a working hypothesis; tokenization and segmentation mismatches must remain visible when interpreting experiments.
- Develop and validate an approach on Latin before applying it to Voynich. If the Latin route fails, investigate other languages, starting with Frühneuhochdeutsch, reusing suitable parts of the model and evaluation machinery.

## Immediate lexical objective

Find a procedure that reliably identifies a small nucleus of exact plaintext word mappings without consulting the answer during selection. A concrete desired demonstration is four Latin texts, five highest-confidence nuclei selected independently in each, with at least three of the same Latin words correctly recovered in all four selections. Four texts give four sets of five; the intended criterion is their common intersection, not merely high aggregate accuracy. This is a target demonstration, not an already achieved result or a guarantee that the same vocabulary occurs in Voynich.

If established, apply the frozen procedure to Voynich to propose corresponding mappings. Any resulting Voynich mappings remain hypotheses requiring independent checks. A trustworthy small nucleus could seed a substantially different decipherment algorithm; success need not mean extending the original algorithm to full restoration.

## Parallel objective: preserve any usable recovered information

Exact lexical nuclei are not the only valuable output. Reliable POS classes, morphology, phrase membership, dependencies, repeated-type constraints, or other recovered structure may provide inputs to another decipherment method, even when the current lexical decoder cannot exploit them. For example, meaningful POS prediction around 70% accuracy could be valuable if its baseline, coverage, transfer, and input assumptions support that interpretation. Such accuracy is not by itself a universal acceptance threshold.

Track every credible positive finding alongside its limits. Distinguish information inferred from opaque text from supplied anchors, oracle morphology, known candidate classes, synthetic error assumptions, and readable surrounding words. Preserve conditional successes without presenting their privileges as discoveries. A failed integration or an unmet precision guard does not erase a useful underlying signal.

## Status at clarification, 2026-10-24

The four-text shared Latin nucleus demonstration has not been achieved, and no trustworthy Voynich plaintext nucleus has been established. Earlier English and historical German experiments recovered small frequent-word sets, but did not establish the desired general Latin/Voynich result; see [Ravi–Knight summary](ravi_knight_failure.md).

There are potential grammatical inputs worth preserving: [conditional opaque ADP/CCONJ class inference](grammar_class_validation_iteration118.md), [its cached-author transfer](grammar_class_transfer_iteration119.md), [downstream PP utility](grammar_class_pp_utility_iteration120.md), and [selective repair of synthetically corrupted supplied anchors](grammar_jerome_context_iteration112.md). These have meaningful supplied-anchor and development-data limitations. None yet demonstrates blind grammatical recovery from Voynich or a validated improvement to a full decipherment pipeline.

The living experiment and proposal record is [grammar_algorithm_proposals.md](grammar_algorithm_proposals.md). Future experiment priorities should explicitly connect to either reliable lexical nuclei or a transferable information source for another decipherment algorithm.

## Highlighted development milestone, 2026-10-25

[Iteration 142](grammar_joint_scalars_iteration142.md) supplies a concrete candidate grammatical input: one frozen anchor-free, sentence-free model reaches **71–80% binary ADP/CCONJ type agreement across four Latin texts**, with ranking above all sixteen frequency-preserving nulls per text. This is the kind of partial restoration worth preserving independently of exact word recovery. Candidate function-word membership is still given, references and normalization have limitations, and the texts were adaptively reused; further robustness checks are required before calling the component dependable. It does not meet the shared exact-plaintext-nucleus objective or demonstrate a Voynich translation.

The frozen [additional-author replication](grammar_joint_author_replication_iteration143.md) gives **Curtius 12/15 (80%)** and **Suetonius 12/16 (75%)**, but short Apuleius fails at **6/13**. Preserve these two replications and the failure together; the same model reaches 71–80% on six of seven full development texts, with catalogue/reference limitations and no exact lexical nuclei.

The full-text binary-class milestone requires a robustness qualification: iterations148–150 found that replacing a single source siue occurrence reverses the learned role coefficient and sharply degrades transfer. The repeated coordination motif provides plausible grammatical evidence, but the present small supervised training set makes the boundary depend heavily on that motif. Preserve the positive measured full-model result as conditional development evidence while investigating this fragility; it is not yet a reliable general POS input or lexical-nucleus recovery. See [iteration150](grammar_siue_motif_iteration150.md).

Iteration155 directly tested the candidate-membership privilege: the structural ADP/CCONJ detector achieved only2.85%precision among771eligible source types, with no correct top10 candidate. Thus the earlier conditional binary-class signal is not yet an unaided candidate-discovery input. Broader grammatical class recovery remains worth testing under explicit held-out-type evaluation, with frequency baselines and no claim of exact nuclei. See [iteration155](grammar_candidate_detection_iteration155.md).

Iteration156 found a possible coarse grammatical input worth preserving: source held-out-type top10 lists contain8members of an explicitly defined seven-POS union. Frequency alone matches the combined model, so this is primarily frequency-led enrichment, not exact nuclei or general POS recovery. It is not yet cross-text validated, and its benchmark currently filters types using known modal purity; remove that inference privilege and replicate before treating it as reliable deciphering input. See [iteration156](grammar_broad_classes_iteration156.md).

Iteration157 removes the purity-at-inference qualification from the coarse shortlist result: all supported source types are scored, and frequency/combined top10 still contains8members of the defined seven-tag union. Source purity is used only for training label quality. This is a more applicable possible grammatical cue, still frequency-led and awaiting cross-author replication; its42.7% overall threshold precision is not general POS restoration or nucleus recovery. See [iteration157](grammar_no_purity_iteration157.md).

Iteration158 extends the coarse frequency shortlist to cached Caesar/Jerome author sets: frequency top10 scores9/10 and8–9/10 with arbitrary boundary-tie resolution. All supported types are eligible and complete cached POS references are available, but the texts are short reused development sets with already high broad-class prevalence. This is a possible frequency-led grammatical input, not exact POS/Latin-word identities; the combined structural model does not consistently improve it. See [iteration158](grammar_broad_author_iteration158.md).

Iteration159 preserves a four-dataset coarse grammatical result: the frozen frequency top10 lists score9/10 Caesar,8–9/10 Jerome,8/10 Cicero and9/10 Palladius, with arbitrary tie resolution accounted for. All supported types are eligible without known POS purity or candidate membership. Cicero/Palladius are seen-author sentence checks, all datasets are reused development material, and treebank segmentation still needs challenge under the one-EVA-word/one-Latin-word assumption. This is a plausible grammatical input worth retaining independently of nuclei, but no exact POS or Latin identities are recovered; see [four-dataset report](grammar_broad_source_authors_iteration159.md).

Iteration160 preserves the coarse frequency shortlist under fixed enclitic joins: Caesar10/10,Jerome8–9/10,Cicero9/10,Palladius9–10/10 with arbitrary ties and both projected reference policies. Original orthographic boundaries remain unavailable, so this is a stress result rather than verified retokenization. The next practical question is whether such a coarse cue improves candidate ranking beyond unigram frequency, not whether these class-enriched lists already constitute recovered nuclei. See [iteration160](grammar_enclitic_stress_iteration160.md).

Iteration166 adds a distinct possible grammatical input: shared two-sided frames show72.22% conditional case agreement in Cicero under fixed macro weighting, versus a50% maximum across16 shuffles. It covers only18 case-comparable edges/21 supported types and uses gold case availability for evaluation; it does not identify case-bearing positions or name cases. A future decoder could test case compatibility when candidate words carry morphology, independently of exact nuclei, but broader coverage and replication remain required. See [iteration166](grammar_case_frames_iteration166.md).

Iteration168 replicates conditional case compatibility in another nonoverlapping Cicero passage:70.41% macro agreement on36 case-comparable edges involving33 supported types, versus55.56% maximum over16 shuffles. The earlier passage scored72.22% on18 edges. This is worth preserving as a possible morphological input independently of nuclei, with same-author/development exposure, narrow conditional coverage and absent case-bearing detection explicit; other cached author pools remain sparse. See [replication report](grammar_case_replication_iteration168.md).

Iteration169 strengthens the conditional case finding: all466 single endpoint/frame removals in the two Cicero graphs remain above their matched shuffle maxima, with no empty actual case set. Agreement ranges66.71–77.27% across all interventions, so no universal70% rate is implied. This is concentration robustness of a possible morphological input, not new cases/word identities or automatic applicability detection; common context-word and group-level dependence remain to test. See [concentration audit](grammar_case_concentration_iteration169.md).

Iteration170 preserves the conditional morphological finding under every single context-word removal, with agreement at least63.46%; the larger Cicero passage always exceeds matched null maxima, while two of74 primary removals in the smaller passage do not. This is evidence against a single context-word explanation, with narrow gold-case-conditioned applicability and same-author development limits intact. No new lexical nuclei or named-case/POS predictions result. See [context-word audit](grammar_context_concentration_iteration170.md).

**Iteration171 scope correction:** the measured case relation is almost exclusively on pairs involving a pronoun/determiner (73/73 and116/118 case comparisons). The fixed family stratum still exceeds all sixteen controls at72.22%/69.56%, while the remaining evidence is one edge/two comparisons with no null separation. Preserve this possible narrower morphological input, without claiming restored PRON/DET labels or general nominal agreement; [report](grammar_case_families_iteration171.md).

Iteration172 localizes most case comparisons further to both-PRON/DET endpoints (69/73 and85/118), with71.88%/67.01% macro agreement above existing word-shuffle maxima. Cross-family pairs give a limited replication lead (31 comparisons,75.13%) but no earlier control separation (only4 comparisons). Preserve shared-context substitution compatibility as the candidate input, not links between co-occurring words; testing POS-specific case marginals remains necessary. [Breakdown](grammar_case_subfamilies_iteration172.md).

**Iteration173 positive diagnostic:** the fixed-graph both-PRON/DET association clears199 within-POS case-label permutations in both passages (actual71.88%/67.01%, null maxima50.47%/43.08%). POS-specific marginal case frequencies alone do not reproduce it. Preserve this evidence for narrow morphological grouping while separating word-specific morphology from occurrence-context disambiguation; gold labels, same-author development reuse and absent lexical/named-case restoration remain explicit. [Report](grammar_case_marginals_iteration173.md).

**Highlight iteration174:** both-PRON/DET case association exceeds all199 permutations preserving each opaque word/exact-POS case profile in both passages (actual71.88%/67.01%; null maxima67.19%/58.68%). Controls genuinely change14–37 and29–53 relevant positions per run, strengthening occurrence-context association beyond empirical word morphology as a candidate decipherment input. This remains gold-reference-conditioned, same-author development evidence, without automatic POS/case/lexical restoration; cross-family compatibility does not replicate. [Report](grammar_case_word_profiles_iteration174.md).

Iteration175 limits use of174's positive relation: closing the word graph transitively gives large37/81-type components and only27.14%/27.52% both-PRON/DET agreement on transitive-only pairs, without separation from profile-preserving nulls. Preserve exact-frame pairwise compatibility as a possible soft input, but do not claim coherent word-level case classes; next test retains frame identity. [Report](grammar_case_components_iteration175.md).

Iteration176 preserves context-specific composition: separate(word,frame) groups score72.50%/72.22% conditional both-PRON/DET case consistency, above all199 profile controls in both passages. Larger groups exist but most groups are pairs, novel transitive primary evidence is limited to replication, and family selection still requires evaluation labels. Preserve this possible soft morphological input without global/named case classes or lexical identities; next check label-free selection and unconditional applicability. [Report](grammar_case_frame_components_iteration176.md).

Iteration177 tests label-free selection: primary combined20 case consistency is100% conditionally, but applicability is only6/22 and5/20 groups, each passage's evidence concentrated on one word pair. The primary joint yield does not consistently beat the unfiltered groups; no reliable diverse case-group detector or new nuclei are established. Preserve176's relation and the support-only leads with these limits; next remove duplicate frame slots by ranking unique word-pair bundles. [Report](grammar_case_group_selection_iteration177.md).

**Iteration178 lead to preserve:** a fixed support-only top10 unique-pair control finds four/three case-comparable relations spanning six types per passage, at75%/94.44% conditional agreement above all199 profile-preserving controls. Its joint yield30%/28.33% improves the full-graph25%/20.12%, but primary combined20 fails applicability and support-ranking enrichment over random same-graph lists remains untested. Preserve this control-derived hypothesis without nuclei/named-case/detector claims or adoption; [report](grammar_case_pair_selection_iteration178.md).

**Iteration179 qualification:** support10's apparent178 gain is not unusual among random ten-pair subsets of the same graphs (398/999 and278/999 match/exceed joint yield). No ranking enrichment, case-bearing detector or new nuclei is established;174/176's context-conditioned relation remains worth preserving independently. Next consider source-only case-applicability prediction with anonymous contextual features, explicit supervised training and unchanged transfer, rather than infer confidence from frequency/support. [Report](grammar_case_same_graph_iteration179.md).

**Highlight iteration180:** an explicit source-supervised, anonymous-context case-applicability model transfers unchanged from52 earlier pairs to126 replication pairs:9/10 target shortlist pairs have comparable cases, involving11 types, with82.87% conditional case agreement (AUC.8417; Brier.1416 versus frequency/support.2043). This is a potential grammatical interface without target POS/case inputs or word identities, not general case tagging or lexical nuclei. Preserve the positive result separately from179's ranking failure, with source supervision, same-author development reuse, limited calibration and small-source limits; source-label permutations are next. [Report](grammar_case_applicability_iteration180.md).

**Iteration181 strengthens180:** actual-source rich-context fit beats all199 source-label-permuted fits on targetNLL/Brier/AUC/top10 jointyield; one null ties9/10 applicability. Paired loss gains over frequency/support also clear all null gains, but shortlist applicability/diversity gains separate less strongly. Preserve the potential supervised grammatical input while avoiding calibrated significance or fresh-author/Voynich claims; next measure source/target exact-pair/endpoint overlap using cached references, never identity features. [Report](grammar_case_source_labels_iteration181.md).

**Iteration182 overlap qualification:** actual frozen applicability model retainsAUC.8283 on114 unseen supervised word pairs, and8/9 applicable original-top10 relations are unseen pairs. This supports transfer beyond repeated labeled-pair identities, while125/126 target pairs share both words with source-passage vocabulary and both passages remain reused Cicero data. Preserve this partial grammatical interface without novel-vocabulary/author or named-case/nucleus claims; next source-endpoint omission sensitivity. [Report](grammar_case_overlap_iteration182.md).

Iteration183 preserves the applicability model's loss advantage under all53 source-endpoint training-neighborhood omissions (AUC.7762–.8540), while two omissions reduce top10 applicability to5/10 by deleting the same single negative example. This supports a broad source-context relationship but limits precise shortlist confidence; only47 distinct correlated masks, features still projected from full corpus. Next isolate rescaling with frozen full-source scales; no new-author, namedcase or nucleus claim. [Report](grammar_case_endpoint_sensitivity_iteration183.md).

Iteration184 rules out rescaling as the main shortlist-sensitivity explanation: fixed-source scales preserve the same9/8/5-applicable top10 counts across all53 endpoint omissions, with the two5/10 cases still deleting source negativepair21. Broad loss advantage survives; no preprocessing robustness fix adopted. Next trace that example's coefficient/ranking influence without selecting a target-favorable weight. [Report](grammar_case_fixed_scaling_iteration184.md).

Iteration185 explains the shortlist leverage through a frozen source-example weight path: applicability recovers5→6→7→8→9, with the original list stable at tested weights.5–1. Left-context entropy mean/asymmetry directions account for large demotions of four non-case candidates; this is algebraic influence, not causal feature importance or a selected robustness repair. Preserve the grammatical interface with source-regime coverage still to audit; no named cases/nuclei/Voynich claims. [Report](grammar_case_weight_path_iteration185.md).

Iteration186 supports a source-coverage explanation for the ranking weakness: all four unstable non-case candidates are outside retained-source left-entropy ranges withoutpair21, while useful replacements are inside. That geometry also flags2 useful target pairs, so no confidence rejection or robustness repair is established. Preserve this mechanism with the grammatical interface, next audit abstention/coverage across all53 omissions. [Report](grammar_case_feature_ranges_iteration186.md).

**Iteration187 optional robustness lead:** two-entropy source-range abstention+refill repairs the known5/10 ranking failure to9/10 and retains8–9/10 applicability across53 single-endpoint omissions, while rejecting0–2 useful candidate pairs. Preserve as an experimental interface robustness option with developmental target-error exposure, correlated omissions and no named cases/nuclei explicit; do not adopt as default confidence. Next double-endpoint perturbations keep the rule fixed. [Report](grammar_case_abstention_iteration187.md).

Iteration188 extends the robustness challenge: entropy screening helps103/1378 double omissions without decreasing applicable-pair counts, but worst shortlist remains3/10 and21 cases arebelow8/10. Rich loss still beats matched controls inall cases; preserve the partial grammatical interface/optional repair, not a general confidence guarantee or new nuclei. Next inspect positive-source coverage and residual in-range errors across all masks. [Report](grammar_case_double_omission_iteration188.md).

Iteration189 identifies a second limitation: residual weak lists occur after losing much positive source evidence, yet positive-count thresholds and range/distance geometry do not provide a reliable confidence rule. Preserve the source-trained grammatical interface without promising a universal shortlist; next test fixed original class contributions across omissions, with no target-tuned weights. No new namedcase/POS/nuclei claims. [Report](grammar_case_training_evidence_iteration189.md).

Iteration190 preserves source class mass across all omissions and finds only small mixed changes, leaving poor shortlists (worst4/10 after entropy screening). This narrows the missing-source-evidence limitation without a weighting fix; no new grammar labels/nuclei or confidence claim. Next individual source-positive addbacks fix class totals/scales/base masks, with no target-selected model. [Report](grammar_case_class_mass_iteration190.md).

Iteration191 supports source-example coverage as a bottleneck: positive addbacks help99/159 trials with fixed class totals/scales/screening, but oracle selection is not deployable and one worst mask remainsbelow8/10. All historical weak masks share a removed source endpoint containing7/18 positive training pairs. Next broaden cached source training relations only, keeping target candidate graph/features/model settings fixed; no new grammatical labels/nuclei claimed. [Report](grammar_case_positive_addback_iteration191.md).

**2026-10-26 collection milestone:** four additional annotated UD treebanks add773,380 integer token rows, addressing narrow source evidence with classical/medieval/charter diversity. Seneca/Dante annotations are newly reserved for current-model evaluation, not claimed globally unseen raw authors; attribution/role/license issues are explicit. Collection alone restores nothing and does not open old reserves or prove transfer; freeze multi-author admission and label-blind deduplication before modeling. [Report](latin_source_expansion_20261026.md).

### 2026-10-26 — partial development-author transfer

Fixed-feature multi-author training now produces case-comparable top-ten pairs at8/10 Caesar,9/10 Cicero and9/10 Jerome when each is excluded from its fitting. This is a potential grammatical input, qualified by Aquinas5/10 versus a simpler control9/10, poor Jerome calibration and sparse Palladius/Tacitus; no exact words or named cases recovered. Reserved Seneca/Dante evaluation remains unopened. [Evidence and next audit](grammar_multi_author_iterations192_193.md).

### 2026-10-26 — source-author stability strengthens partial grammar evidence

[Iteration194](grammar_source_author_influence_iteration194.md) preserves rich top-ten case applicability at7–8/10 Caesar,8–9/10 Cicero and8–9/10 Jerome under every single training-author omission. This reduces dependence on one source author, while Aquinas4–6/10, poor Jerome calibration and sparse other targets prevent a universal restoration claim. Next test whether label-free consensus yields smaller useful grammatical constraint sets; no exact word/named-case recovery or reserved evaluation yet.

### 2026-10-26 — consensus does not establish trustworthy cores

[Iteration195](grammar_consensus_core_iteration195.md) finds joint stable cores Cicero3/3 and Jerome3/3 case-applicable, but Caesar1/3 and Aquinasempty. These are grammatical pair candidates, not the requested shared exact word nuclei; stable errors rule out a general consensus-confidence claim. The partial194 shortlist robustness remains preserved; next compare within-author ranking with matched-source probability fitting before reserved evaluation.

### 2026-10-26 — ranking objective is a modest candidate improvement

[Iteration196](grammar_within_author_ranking_iteration196.md) raises rich matched-source top-ten applicability to7/10 Aquinas,8/10 Caesar,9/10 Cicero and9/10 Jerome. The loss change contributes one extra applicable pair in Aquinas/Jerome versus matched pointwise training; the simpler control still wins Aquinas, so no universal model adoption is claimed. Next check reserved Seneca's label-blind coverage/overlap before a frozen later evaluation, preserving the distinction between grammatical candidates and exact nuclei.

### 2026-10-26 — reserved Seneca exposes a coverage limit

[Iteration197](grammar_seneca_coverage_iteration197.md) admits10,276 normalized Seneca words but finds zero pairs satisfying the fixed two-context rule; its grammatical labels remain sealed. The earlier partial grammatical ranking is preserved, qualified by a method that may provide no constraints on some samples; this is not a model-accuracy test or evidence against Latin. Next check allowed Dante prose coverage with the same label-blind rules before proposing a reserved-label evaluation.

### 2026-10-26 — a usable reserved-author graph, accuracy still unknown

[Iteration198](grammar_dante_coverage_iteration198.md) produces76 eligible pairs from26,083 allowed Dante-prose words after label-blind overlap/admission filtering; all grammatical labels remain sealed. This supplies a viable single-author test graph, not restored grammar or words. Next freeze the four196 model outputs and evaluate Case applicability once, preserving the reserve's prior raw-exposure/provenance caveats.

### 2026-10-26 — reserved-author grammar signal survives word-profile controls

**Preserve [iteration199](grammar_dante_case_transfer_iteration199.md):** full Dante graph has92.98% conditional Case equality versus a maximum75.46% across199within-word profile shuffles, on19applicable/76totalpairs. The frozen primary model selects6/10 applicable pairs with AUC.781, while simpler ranking control AUC.799; useful ordering is supported, reliable hard constraints and exact nuclei are not. Selectedtop10 equality does not beatprofiles, so the graph's contextual signal is not yet selectively captured. AdmittedDante Case labels are now consumed for evaluation; POS remains sealed until a separately frozen stricter word×POS/control composition follow-up.

### 2026-10-26 — stricter contextual evidence, selection still unresolved

**Preserve [iteration200](grammar_dante_pos_profile_iteration200.md):** Dante conditional Case equality92.98% beats all199word×POS-profile controls (max78.51%); bothpronoun/determiner comparisons97.62% over14pairs beatmax82.74%. This is a contextual Case-compatibility association, not predicted POS/named cases or exact nuclei. The fixed selector retains onlythreeofthose14pairs and these are profile-trivial, motivating a development-only contextual-surplus training target with the same anonymous inputs. Dante POS is now consumed reference and no longer sealed for fresh follow-up claims.

### 2026-10-26 — selective extraction remains unresolved after two development changes

[201](grammar_contextual_surplus_iteration201.md) changes supervision to profile-adjusted agreement; [202](grammar_slot_features_iteration202.md) adds anonymous queried-slot structure in a two-objective factorial check. Neither gives a common useful selector across four authors, so no new algorithm is adopted; the strict200 contextual signal remains preserved. Next audit whether individual-pair evidence can be localized above profile-preserving noise before pursuing more scoring changes; no exact nucleus or broad POS milestone is claimed.

### 2026-10-26 — localization is an additional bottleneck

[Iteration203](grammar_pair_detectability_iteration203.md) retains pooled development contextual evidence but finds only1/1/0/2pairs under fixed per-author max-statistic correction, with most predicted lists missing them. This is conditional oracle evidence about Case/POS, not a deployable detector or exact nuclei; conservative non-detections do not prove absence. Next test annotation-free structural bundles as evidence units, avoiding transitive word-level Case assumptions and preserving the distinction between pooled association and reliably selected constraints.

### 2026-10-26 — promising evidence unit: word-centered comparison bundles

**Preserve [iteration204](grammar_ego_bundle_iteration204.md):** strongest-edge-deletion bundle statistics find5/0/3/2supported centers in Aquinas/Caesar/Cicero/Jerome, including eight centers beyond individually supported-edge endpoints. Group definitions are anonymous; their evidence tests still require gold Case/POS, so this is not restored exact words or a working grammar selector. Next test central-occurrence deletion before treating pooled support as robust enough to motivate bundle-level prediction.

### 2026-10-26 — pooled localization survives single-pivot influence removal

**Preserve [iteration205](grammar_pivot_deletion_iteration205.md):** allten previously supported204bundles survive the strongest central-occurrence removal; combined edge-or-pivot statistics detect7/0/3/3centers in Aquinas/Caesar/Cicero/Jerome. This strengthens the evidence-unit hypothesis, not exact-word restoration or anonymous selection; new detections partly reflect null recalibration and Caesar remains uncovered. Next development-only graph expansion asks whether one-context observations can support robust bundles, without promoting them to hard pair constraints or reusing reserves.

### 2026-10-26 — graph expansion is mixed; close the oracle-to-prediction gap next

[Iteration206](grammar_single_frame_bundles_iteration206.md) expands one-context observations inside robust bundles, increasing Aquinas7→12 detections but leaving Caesar0 and reducing Cicero3→2/Jerome3→1. Preserve this limited result without choosing graphs by gold outcomes. Next fixed source-supervised bundle selection on the conservative graph must use only anonymous counts/topology/context distributions at inference; teacher evidence localization is not restored grammar/nuclei by itself.

### 2026-10-26 — anonymous bundle ranking does not yet extract reliable anchors

[Iteration207](grammar_bundle_selector_iteration207.md) trains without target annotations but finds zero teacher-supported centers in every full-model top3 and only one per top5 for Aquinas/Cicero/Jerome. Broad ranking AUC can be high while precision at the head fails; simple degree ranking is comparable. Preserve the robust gold-reference bundle evidence separately from this failed extraction pilot; no exact nuclei, named cases or POS restored here. Next audit supported-center ranks and the unsupported hubs above them before more predictor changes.

### 2026-10-26 — extraction favors size, teacher negatives need interpretation

[Iteration208](grammar_bundle_rank_audit_iteration208.md) finds that count features largely explain why unsupported large/frequent hubs outrank supported bundles. Some supported centers also rank near30, so a few hub removals cannot solve extraction. Failure to pass a conditional grammar-support test does not mean a bundle lacks grammatical information; next inspect Case coverage and profile variability before treating these teacher labels as decoding targets. No new recovered grammar or exact words are claimed.

### 2026-10-26 — preserve an actionable Case-applicability diagnosis

[Iteration209](grammar_bundle_teacher_audit_iteration209.md) finds11of12unsupported full-model head centers in Aquinas/Cicero/Jerome have no recognized Case at any occurrence; Caesar adds3of5. They are outside the Case-support teacher's scope, rather than examples of failed agreement. This suggests separating anonymous Case-bearing-word identification from contextual support ranking, while preserving non-Case grammatical structure as potentially valuable for decipherment. Next an explicit oracle applicability diagnostic tests this proposal's ceiling; no new grammar/word recovery is claimed.

### 2026-10-26 — preserve the oracle applicability ceiling

[Iteration210](grammar_bundle_oracle_gate_iteration210.md) shows perfect Case-bearing admissibility improves Aquinas's unchanged full/count/degree rankings to5/5 supported centers; full12 was1/5. Full12 Cicero improves to2/5, Jerome stays1/5, Caesar0; applicability alone is not a four-text solution. This is target-gold filtering, not inferred grammar or five restored words. Next remove that oracle by training anonymous applicability on other authors and measuring whether any supported-center yield survives.

### 2026-10-26 — anonymous applicability and support remain separate bottlenecks

[Iteration211](grammar_bundle_applicability_iteration211.md) does not reproduce Aquinas's oracle gain: applicability×support gives1/5 supported there,2/5 Cicero,0/5 Jerome andCaesar. Applicability-only selects0supported in every top5, even when allfive centers are trulyCase-bearing. Some binary applicability discrimination transfers (AUC.8561Caesar/.8807Cicero), but no stable grammar selector or namedPOS/word recovery follows. Next fixed.5hardgate on unchangedpredictions separates composition choice from applicability errors.

### 2026-10-26 — applicability filtering loses the supported subpopulation

[Iteration212](grammar_bundle_hard_gate_iteration212.md) finds both fixed.5 gates rejectall7supportedAquinascenters;full12rejectsall3Cicero too. ManyCase-bearingcenters survive, so broad applicability accuracy does not guarantee preserving contextual evidence. Jeromecount4improves to2/5supported, a limitedresult without universalrouting. Next inspect cachedreference POS/subpopulation differences, not another target-tuned threshold; no newlyrestoredPOS/nuclei.

### 2026-10-26 — applicability failure is not one missing POS class

[Iteration213](grammar_bundle_subpopulation_iteration213.md) finds rejected supported centers mostlynouns inAquinas andpronouns inCicero, whileacceptedcenters includeboth. Fixedmodel logitcontrasts implicatefrequencypenalties acrossallfive comparisons andoccurrencereuse especiallyAquinas, without causalproof. Next a frozen targetedfrequency/reuseablation tests this mechanism before morecomplexlearning; inspectingcachedgoldPOSisnotPOSrestoration.

### 2026-10-26 — frequency/reuse removal does not restore evidence retention

[Iteration214](grammar_bundle_ablation_iteration214.md) leavesall7Aq/all3Cisupportedcenters rejectedbyeveryfixed.5ablation; noreuseAqproductimproves1→2/5butJe0andCa0remain. Cicerono-frequencyappAUC.9263stillretains0supported: discriminationisnotconfidenceintheusefulsubpopulation. No targetedablationadopted. Nextsourcein-sampleaudit separatesfailuretofitrelevanttrainingcenters fromfailuretotransfer, without claimingnewgrammar/nuclei.

### 2026-10-26 — source objective neglect precedes transfer failure

[Iteration215](grammar_bundle_source_fit_iteration215.md) finds only10/39supportedsourceevaluationinstancesretainedbyeachvariant (13centersrepeatedthreefold), versus2or3/13heldout. Thustransferisnotthesolebottleneck; currentapplicabilitymodelsalreadyneglecttheusefulsubpopulationduringtraining. Nexttestsource-onlyrelevancebalancingwithunchangedanonymousfeatures,measuringsourceandtargetyieldseparately; noPOS/namedcase/nucleirecoveryclaimed.

### 2026-10-26 — preserve source relevance weighting's retention gain

[Iteration216](grammar_bundle_reweight_iteration216.md) raises supported-center retention10/39→38/39sourceinstances and3/13→11/13heldout, under unchangedanonymousfeatures/logisticfamily. This shows objective weighting can repairmuchoftheneglect; howevergatesexpand151→231/305centers,appAUCfallsallauthorsandhardtop5only1/0/2/1. Preserveasconditionalcomponentfinding, notrestoredgrammar/wordsorreliableconfidence. Nextmatchedadmission/sourcepriorcontrolsseparaterelevancefrompermissiveness.

### 2026-10-26 — relevance gain survives equal-admission control

[Iteration217](grammar_bundle_permissiveness_iteration217.md) retains11/13supportedcenters at231admissions versus6/13forbaselineatthesamecounts; source-prior-onlycontrolretains4/13. Thispreservesacomponentgainbeyondpermissiveness,butnonCaseadmissionsincrease91vs81andtop5precisionremainsweak(1/0/2/1). No exactnuclei/namedgrammar restored. Nextauditsupportmodelsourceheadswithoriginal/oracleCaseuniverses, ratherthanclaimingretentionequalsreliableextraction.

### 2026-10-26 — support fit and teacher coverage constrain extraction

[Iteration218](grammar_bundle_support_fit_iteration218.md) finds sourceheadweaknessalreadybeforetransfer; oracleCasegating givesfull12top5precision41.7%source/40%held, count45%both. Teachercoverageboundsfive-per-authorpooledhitsat11/20held; nofiveexactwords/commonnuclei demonstration. UsefulAquinasconditionalrankingpersists,butinferredadmissibilityandresidualrankingremainunresolved. NextsourceCase-onlysupporttrainingwithfixedanonymous targetgate testsirrelevantnegativeswithouttargetgoldinference.

### 2026-10-26 — source conditioning does not close extraction gap

[Iteration219](grammar_bundle_conditional_iteration219.md) keepsAq1/5andCi2/5fullmodelanonymousyieldbutdropsJe1→0/5afterCase-onlysource supporttraining. OracleCasefilterstillhelps, conditionalgainsdonottranslateintoreliableinference. Preserveearliercontextualevidence/controlledretention, stopassumingindependentcounts/entropieswillproduceconfidentanchors. Nextauditreplacementgraphrelationsforcontrolledapplicabilityhomophilybeforeagraph-basedmethod; nonewnamedgrammar/nuclei.

### 2026-10-26 — preserve relationship-level applicability information

[Iteration220](grammar_graph_homophily_iteration220.md) finds connectedwordCaseapplicabilityagreement64–78%,aboveall199frequency-stratifiedshufflesineachauthor. Thisgoldreferencegraphsignaljustifiestestinganonymoussoftpropagation,notnamedgrammar/nuclei. Mixededges22–36%andlarge mixedcomponentsruleouthardgrammaticalequality; correlatedclassifiererrorscanpersistthroughsmoothing. Nextonefixedhalfself/halfneighborstepwithunchangedsource-trainedscores, measuringactualrecovery/precision.

### 2026-10-26 — soft graph refinement helps some applicability metrics

[Iteration221](grammar_graph_propagation_iteration221.md) usesanonymousedges/unchangedsourcepredictionswithonefixedhalfself/halfneighborstep. BalancedappAUC/NLLimproveon305centersall4authorsandsupportedretention11→12/13,butadmissions231→246, allnodeAqAUCfallsandtop5yielddoesnotimprove. Preserveasconditionalcomponentfinding,noreliableextraction/wordrestoration. Nextglobalmeananddegreerewiringcontrolscheckrelationship-specificbenefitbeforeadoption.

### 2026-10-26 — propagation controls preserve conditional relationship value

[Iteration222](grammar_graph_controls_iteration222.md) findsrealgraphCiceroAUCbetterthanmostdegreerewires(.010balancedtail)andCaesar/CiceroNLLbetterthanall199, butJeromeNLLworsethanglobalaveraging/allrewires. Supportedtop5yieldstilldoesnotimprove; nouniversalpropagationadopted. NexttestsoftPOScompatibilityrelationsincludingnonCasewordsasapotentialdifferentgrammaticaloutput, keepingreferenceevidenceseparatefrominferredPOS/wordnuclei.

### 2026-10-26 — investigate non-Case grammatical relationships

[Iteration223](grammar_graph_pos_iteration223.md) findsPOS-profilecompatibility21–55%abovefrequency-onlynullsallauthors,including31–72%amongneither-Caseedges. ThispreservesnonCasewordsaspotentialgrammaticalinputs; itisgoldreferenceinformation,notPOSrestoration. Case/POSconfoundingremainsbecauseprofileshufflescrossCasestatus. NextCase-conditionednulltestswhatsurvivesbeyondthecoarseCasesplitbeforepairwisePOSconstraintsareclaimed.

### 2026-10-26 — preserve POS relationship signal beyond coarse Case

[Iteration224](grammar_graph_pos_case_control_iteration224.md) retainswholegraphandneither-CasePOScompatibilityaboveall199frequency×Case-statusprofile shufflesineachauthor. Strongercontrolweakensboth-CaseAquinas/Cicero, whicharenotclaimedassurviving. ThisisusefulreferenceevidencefornonCasegrammaticalrelationships,notnamedPOSrestoration. Nextsource-trainedanonymousedgecompatibilityrankingtestswhetherthatinformationcanbeextractedwithouttargetlabels.

### 2026-10-26 — HIGHLIGHT anonymous selection of POS-compatible relations

[Iteration225](grammar_pos_edge_rank_iteration225.md) selects10anonymouspairs/authorwithsource-trainedrichmodel, gold-referencecompatibility69.47/71.20/78.91/88.67% acrossAquinas/Caesar/Cicero/Jerome. TargetPOSdoesnotenterselection; thisisaninferredrelationaloutputpotentiallyusefulasdecoderconstraints,notnamedPOSaccuracy/wordrestoration. Countcontrolcompetitiveandtop20mixed; authorsreuseddevelopment, nofreshVoynichsuccess. Preservefindingandnextchallengewithsource-labelpermutations/endpoint-disjointlistsbeforereliabilityclaims.

### 2026-10-26 — pairwise output persists, learning attribution narrows

[Iteration226](grammar_pos_edge_robustness_iteration226.md) retainsrichdisjoint10compatibility79.18/67.97/78.91/88.67%over20opaquewordtypesperauthor. Source-labelpermutationsupportsrichheadAq/CibutnotCa/Jeatfixed.05;additionalfeatures'gainnotrobustagainstpairednull. PreservepotentialpairwiseconstraintoutputwithoutclaiminguniversallearnedPOSrestoration. Nextfixeduntrainedstructuralrankingscheckwhetherthisgrammaticalinputcanbeobtainedwithoutsourceannotations.

### 2026-10-26 — untrained pairwise selection is a potential grammatical input

[Iteration227](grammar_pos_untrained_iteration227.md) selectssupport-rankedtenendpoint-disjointpairswith59.14/54.56/88.10/66.94%referencePOScompatibility, withoutsourceannotations. Richlearnedselectionstronger3authors, rawsupportstrongerCi; no author-specificwinneroruniversalbestmethod. Discrete-scoreties/greedyedgeindexcanmatter, sonexttesttievaryingselectionversusuniformdisjointcontrols. Thisissoftanonymousrelationshipoutput,notnamedPOS/nuclei.

### 2026-10-26 — structural relation quality is author-dependent

[Iteration228](grammar_pos_tie_audit_iteration228.md) retains tie-robustsupportdisjointpairenrichmentinAq/Ci,moderateJe,butCaesarnearrandom10/worsethanrandom20. No consistentfourtextgrammaticalselector,namedPOSornucleidemonstrated. Preserveconditionalanonymousrelationinputsandtheirlimits. NextunchangedfamilyonadditionalalreadyconsumedDante, explicitlydevelopmenttransfernotfreshholdout,Senecagoldsealed.

### 2026-10-26 — additional Dante pair transfer remains moderate

[Iteration229](grammar_pos_dante_iteration229.md) obtainsrich10globalprofilecompat58.33%(graph34.73), disjoint55.48; untrainedsupporttieaverage55.82vsuniform34.98. Preserverelationalenrichmentwithoutuniversal/highprecisionPOSclaim; Dantealreadyconsumed/notfresh. Nextfixedselected-pairqueryslotPOSauditdistinguisheslocalgrammaticalcompatibilityfromglobalword-profileagreement, withoutchangingselectionorclaimingnuclei.

### 2026-10-26 — contextual relation agreement is not named POS restoration

[Iteration230](grammar_pos_context_iteration230.md) measuresrichdisjoint10actualslotPOSagreement80/65/87/90/60%, butonlyCicero'slistseparatesfromwithinwordprofilecontrolatfixed.05. Aggregatecontextualsignalexistsfourauthors,yetselectiondoesnotyielduniversalrestoration. Nexttestwhetherfixedanonymouspairconstraintsimproveasource-trainednamedPOSprofilepredictoragainstnode/priorbaselines, withgraphcoverageandDantenonfreshstatus explicit. Thisconnectsrelationalfindingstoaconcretedecoderinputtaskwithoutclaimingwords/nuclei.

### 2026-10-26 — direct named-POS downstream test remains weak

[Iteration231](grammar_pos_prediction_iteration231.md) predictsnamedPOSprofileswithonly12.85–33.08%type-macroexpectedtop1masson622graphnodes;pairrefinementmixedandcoveragepartial. ThisbranchhasnotdeliveredreliablePOSrestoration,despiteusefulpairwisecompatibilitysignals. Nextoraclelabelalignmentdiagnoseswhetheranonymousgrammaticalgroupingssurvivefailednames, withoutdeployinggoldmappingorclaimingnuclei.

### 2026-10-26 — oracle naming confirms weak POS grouping

[Iteration232](grammar_pos_alignment_iteration232.md) yieldsnodeoraclealignedtype26/22/29/33/35%,only4–5occupiedgroups;stronglatentPOSpartitionisnotmerelymisnamed. Dantehaslargernaminggainbutstillmoderateceiling. Preservepairwisegraphsignalwithoutforcingnamedclasses; nextgraph-onlygroupingwithfixedcapacityandconditionalprofile-nullcontrolstestsanewrepresentation. No reliablePOS/nucleirecoveryclaimed.

### 2026-10-26 — graph-only groups preserve latent POS information

[Iteration233](grammar_pos_spectral_iteration233.md) improvesoracleclusterpurityto39–61%type-macro, abovefrequency×Caseprofile-nullcontrolsall5authors, buttargetgoldnamesremainoracleandtokenJeromefails. Jerome'sembeddingconsistsonlyof20componentzeromodes, so withincomponentgeometryisabsent. Nextfixedallzero+17positive-modeembeddingteststhisrepresentationlimitwithouttargettuning. No namedPOS/nuclei/wholetextrestorationclaimed.

### 2026-10-26 — representation correction repairs a specific grouping failure

[Iteration234](grammar_pos_spectral_iteration234.md) addswithincomponentdirectionsandimprovesJeromeoraclepuritytype38.71→46.92/token25.94→54.83%, withmixedotherauthors. Conditionalpuritysignalpersistsall5, butone-to-onePOSceilingsremainweakandnamesstilloracle. Nextfixedinitializationstabilityauditseekspersistentanonymousgroupsbeforeclaimingdeciphermentinput; no reliablePOS/exactnuclei.

### 2026-10-26 — stable signal does not imply stable partitions

[Iteration235](grammar_pos_stability_iteration235.md) retainslatenttypePOSsignalacrossmost31starts,butmeanpartitionARI.25–.64andJerometokenexcessonly9/31. Do notpromoteone favorablepartitiontorestoredgrammar. Nextunanimousco-membershipcoresextractannotation-freelocalstability,thencheckcompatibility/coverageagainstconditionalcontrols. No namedPOS/exactnucleidemonstration.

### 2026-10-26 — stable local cores retain limited grammatical affinity

[Iteration236](grammar_pos_cores_iteration236.md) extractsannotation-freeunanimouscoreswithabove-controlPOScompatibilityall5authors,butcoremacro32–62%andtokencoverage3.75–40.56%ruleoutconfidentPOSclasses. Oraclepurityisnotinferredaccuracyandlargercoresmixed. Nextcachedsentence-deletiontestchecksdatastabilitybeforestablelocalrelationsaretreatedasdecoderconstraints. NamedPOS/exactnucleiremainsunresolved.

### 2026-10-26 — text perturbation exposes a coverage bottleneck

[Iteration237](grammar_pos_text_robustness_iteration237.md) retains49–72%originalunanimouspairsafter10%sentence deletion, versus68–95%conditionedonsurvivingendpoints. Missinggrapheligibilityandmembershipchangesbothmatter; nogrammaticalaccuracyfollowsfromretention. Nextstrictjointinitialization/deletioncoresreportallcoveragecostsbeforePOScontrols,withoutrelaxingemptyoutputs. NamedPOS/nucleiunresolved.

### 2026-10-26 — HIGHLIGHT a small stable anonymous grammatical core

[Iteration238](grammar_pos_joint_cores_iteration238.md) retainsoneJeromesix-wordcoreafterinitialization/deletionintersection;all6arepureVERBingold,337tokens/1.12%text. Label/spellingsnotinferred; thisisananonymousco-membershipinput,notexactnuclei. Aqfivecores79.31%compatbutonefalsePRON/NOUNpair,Ca/Ciweak,Danteempty: nouniversalconfidence/fourtextclaim. Nextallfixedcoresonunused10%/20%deletionseedswithoutreselection.

### 2026-10-26 — HIGHLIGHT small Jerome group survives unused perturbations

[Iteration239](grammar_pos_core_validation_iteration239.md) keepsfixedsix-wordJeromecoreintact30/31new10%deletionsand24/31at20%,withoutreselection;pairretention98.92/89.03%. Anonymousgroupingrobustnessisuseful,butlabelpuritycomesfrom238referenceandcoverage1.12%;wrongAqpairalsostable,Ca20%weak,Danteempty. No exactnuclei/universalPOSclaim. Nextwithin-sentenceword-ordernegativecontrolpreservesfrequency/bagsandtestsgraph/pipelineavailability.

### 2026-10-26 — word-order controls expose a specificity requirement

[Iteration240](grammar_word_order_control_iteration240.md) findsall995sentencebag-preservingshufflesclusterableandoftenmoreedgesthanreal;graphavailability/oraclepurityalonecannotvalidategrammar. Jeromepure-coreandperturbationfactsremain,butfullselectionfalse-outputrateuntested. Nextmatchedfullconsensuspipelineon19fixedJeromecontrolscompareslargestpurecore(real6),withoutgoldcontrolselectionorclaimingnames/nuclei.

### 2026-10-26 — HIGHLIGHT matched negative-control pilot supports the small core

[Iteration241](grammar_full_core_null_iteration241.md) reproduces the six-word Jerome core and finds no equally large fully POS-pure core in 19 full-pipeline sentence-order controls (maximum3; finite tail.05). This strengthens the anonymous grouping finding beyond perturbation stability, with only1.12% token coverage and no inferred POS name or exact nuclei. Next extend unchanged to all199 fixed shuffles; same-corpus evidence remains distinct from author transfer.

### 2026-10-26 — HIGHLIGHT full order-control set supports the Jerome core

[Iteration242](grammar_full_core_null_iteration242.md) confirms six pure words in the real Jerome core versus at most three in199 matched full-selector shuffles (0/199 exceed; finite tail.005). This is stronger same-corpus evidence for anonymous grammatical co-membership covering1.12% of tokens; no namedPOS or exact nuclei are inferred. Preserve as a potential decoder input while checking all remaining admitted authors with the unchanged control pilot; transfer remains unresolved.

### 2026-10-26 — second selective pure-class finding, limited generality

[Iteration243](grammar_full_core_authors_iteration243.md) finds two pure reference-VERB pairs in real Aquinas and none in19 matched full-pipeline controls (largestpure2vs0;tail.05). Together with Jerome this is a second potential anonymous grammatical input, not shared lexical nuclei or inferred verb naming. Caesar/Cicero retain mixed pairs and Dante is empty; Aquinas also retains a wrong pair, so reliable gold-free confidence and transfer remain unresolved. Next unchanged full199Aquinas controls is a selected-positive follow-up, not fresh confirmation.

### 2026-10-26 — Aquinas full controls preserve a smaller signal with ties

[Iteration244](grammar_full_core_null_iteration244.md) retains real largest pure core2 against199 controls:197zero and2pureAUXpairs, finite tail.015. Real two reference-VERB pairs cover.92%tokens, but the extractor also retains a wrong pair; gold-free selection/naming is unresolved. Preserve alongside the stronger Jerome finding without claiming universal POS or exact nuclei. Next unchanged extraction on disjoint sentence halves of all5datasets tests support beyond overlapping deletions.

### 2026-10-26 — HIGHLIGHT disjoint-half reproducibility remains absent

[Iteration245](grammar_disjoint_cores_iteration245.md) recovers no shared non-singleton strict core across sentence halves in any of5datasets; all24originalpairs fail joint recovery. Earlier full-data Jerome/Aquinas control signals remain valid at their original scope, but small-deletion robustness does not establish independent passage recovery. Half-volume support loss and passage composition are confounded; next fixed random balanced sentence splits diagnose this before algorithm changes. No naming/nuclei milestone is reached.

### 2026-10-26 — HIGHLIGHT random halves confirm the reproducibility bottleneck

[Iteration246](grammar_random_halves_iteration246.md) finds zero shared strict cores in95fixedrandomsentencebipartitions/all5datasets, with0/456originalpair-splitopportunities recoveredbothhalves. Jerome's38initialhalfgraphs are all clusterable but none yields a strict non-singleton, so passagecomposition or initialavailability alone does not explain failure. Full-text signals remain potential inputs at their original scope; no namedPOS/nuclei or independent passage recovery. Next trace frozen pair attrition through graph presence, initialization unanimity and deletion survival/co-membership before changing the algorithm.

### 2026-10-26 — half-text failure localizes to support and partition instability

[Iteration247](grammar_pair_attrition_iteration247.md) attributes Aquinas losses largely to endpoint survival (117initial-unanimouspair-halfcases→26survivealldeletions→17strict), whereas Jerome has only20/388initial-unanimouscases and no deletion-unanimouspair. Even80Jeromecaseswithstableendpoints haveonly1–18/31deletioncoassignments: smallunanimityrelaxationisnottheresolution. No labels/nuclei recovered; next inspect continuousgraphproximitybeforek-means tolocaterepresentationversuspartitionfailure.

### 2026-10-26 — HIGHLIGHT a concrete spectral representation defect

[Iteration248](grammar_pair_proximity_iteration248.md) finds70/145eligiblehalfgraphs useafullequal-weightorthobasis, makingallnodedistancesequal; all eligibleCa/Ci/Dantehalvesareaffected. Aqconditionalpairproximitymostlysurvivesbutcoveragefails;Jeromelosessubstantialproximityaswellaspartitionstability. Distanceranksarenotgrammaticalaccuracyandnorecoverednames/nucleiresult. Next fixedtime1diffusionweightingtestsrepresentationwithouttime/authorselection; matchedextractioncontrolsremainrequired.

### 2026-10-26 — HIGHLIGHT fixed diffusion repairs selected-pair geometry

[Iteration249](grammar_diffusion_proximity_iteration249.md) removes all70equal-distancehalfgraphcollapses;Jeromeoriginalpairconditionalcloseness55.67→95.31%,missing-as-zero37.89→64.88%,withunchangedcoverage. This is a promising representation component, not POS accuracy: mixed/wrongoriginalpairsalsoobtainhighranks. Next fullunchangedstrictcoreextractionwithonlyfixedtime1diffusionreplacementtestsrecurrencebeforematchedcontrols/decoderuse. No exact nuclei or namedPOS recovered.

### 2026-10-26 — HIGHLIGHT diffusion yields a small recurring grammatical input

[Iteration250](grammar_diffusion_cores_iteration250.md) recovers sharedAqstrictcoresin3/19randomsplits(vs0):samepure-referenceAUXpairintwosplits(1252tokens/4.17%)andadifferentnear-pureADPtripleinthethird. Names/spellingsarenotinferred,andother4datasetsstillnorecurrence;falsefulltextgroupsremain. Preserveasapromisingrepresentation/extractiongain,notvalidateddecoderconfidence. Nextmatchedordercontrolsreplayallsplit-selectionopportunitiesbeforeusingthegroup.

### 2026-10-26 — HIGHLIGHT matched controls support a potential selective grammatical input

[Iteration251](grammar_diffusion_controls_iteration251.md) finds realAqmaxpure sharedcore2 against0inall19full-selectionordercontrols,eachreplayingall19splits (tail.05). Realoutputsaretwoanonymousgroups/5wordtypes/8.39%globaltokencoverage:onepure-referenceAUXpairandone99.49%-compatibleADPtriple;noPOSnames/spellingsinferred. Preserveaspotentialdecoderinputwithrareselectionseedrecurrenceandnootherauthorgain. NextfreezeBOTHgroupsandvalidaterecoveryon19unusedsplitswithoutgoldfilter/membershipupdate;newresamplingnotfreshtext.

### 2026-10-26 — fixed-group validation shows rare recurrence, not dependable recovery

[Iteration252](grammar_fixed_groups_iteration252.md) recovers the frozen reference-AUXpairin1/19unusedsplits;thefrozenADPtriplein0/19,withonesubsetpairtwice(notcountedasfullsuccess). G1initialendpointsboth19/19andstrictendpoints18/19,so partitionco-membershiplimitsrecovery. Newanonymousoutputsremain3/19withreferencecompatibility>=99.77%,butsamecorpus/labelsandno inferrednames/nuclei. Nextlocalmutual-neighborrelationsreplacewholepartitionwhilekeepingdiffusion/graph/stabilitycriteriafixed.

### 2026-10-26 — HIGHLIGHT local relations add a second author's cross-half signal

[Iteration253](grammar_mutual_neighbors_iteration253.md) findsoneanonymousJepairinpure-referenceADVclassintwo/19splits,747tokens/2.49%,wherediffusionclusteringhadnone. AqAUXpairretains2/19oldand1/19reusednew,noreliabilitygain;Ca/Ci/Dantesharedemptyandfulltextfalsepairspersist. No names/spellingsinferred;preservepotentialgrammaticalinputpendingmatchedordercontrolsforthechangedruleonbothAq/Je.
