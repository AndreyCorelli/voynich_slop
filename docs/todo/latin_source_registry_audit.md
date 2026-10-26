# Follow-up: Latin corpus admission and legacy source IDs

Collection evidence: [2026-10-26 source report](../latin_source_expansion_20261026.md).

- Preserve historical frozen manifests/code; audit the impact of legacy phi1221.phi007→Petronius and phi0972.phi001→Gellius labels before reusing author-level splits. Correct identities are Augustus/Res Gestae and Petronius/Satyricon; the new collection inventory uses these, without silently rewriting old results.
- Resolve UDante's pinned README/license declaration conflict before asserting redistribution terms; keep both originals and the current reserve status.
- Freeze a model-admission protocol covering source-author/work budgets, tokenization/MWT/enclitics, annotation harmonization and label-blind text deduplication. No graph projection or reserved label scoring has run.
- Use explicit role/sentence allowlists; upstream train filenames include authors now reserved from model development. Prior200-sentence reserves and sealed Ammianus/Quintilian remain protected.

These are data-quality/admission follow-ups, not a request to alter the decipherment goal or automatically open the reserves.

- Development admission/tokenization/dedup and LOAO now frozen/tested in iterations192–193; reserved FORM overlap and author evaluation remain pending, not implied completed. See [transfer report](../grammar_multi_author_iterations192_193.md).

- Iteration197 completes Seneca-only FORM admission/overlap/coverage against193 admitted development: no overlaps detected, zero eligible two-context pairs; labels remain sealed. Dante reserve FORM coverage/overlap is still pending, with its declaration conflict/quarantines unchanged. [Seneca report](../grammar_seneca_coverage_iteration197.md).

- Iteration198 completes secure Dante DVE+Mon FORM admission/overlap: one Cicero12word-overlap sentence removed, primary76pairs; no Case/POS labels opened. Attributed letters and quarantines stay unprojected; UDante declaration conflict remains preserved, not resolved. [Dante coverage report](../grammar_dante_coverage_iteration198.md).

- Iteration199 consumes Case annotations of the198 admitted Dante DVE+Mon sentences after frozen model outputs, with no POS fields used. They are no longer a fresh Case reserve for subsequent work; excluded sentences/attributed letters/quarantines and Seneca gold stay unprojected. Future within-word×POS audit must explicitly freeze its POS decoding scope; source/licensing records unchanged. [Case transfer report](../grammar_dante_case_transfer_iteration199.md).

- Iteration200 consumes UPOS of198 admitted Dante sentences for reference-only composition/strict Case nulls; Case/POS now both known follow-up data, with models/outputs unchanged. Attributed letters, excluded/quarantined material and Seneca gold remain unprojected. [Strict-control report](../grammar_dante_pos_profile_iteration200.md).
