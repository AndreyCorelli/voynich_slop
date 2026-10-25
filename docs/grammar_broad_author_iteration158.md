# Iteration 158: frequency-led broad-class shortlist transfers to two cached authors

**Preserve the measured transfer result:** the frozen frequency model's top10 contains9 members of the seven-tag grammatical union in Caesar and8–9 in Jerome, depending on a boundary tie. This extends the source-only shortlist finding to two authors absent from the source training partition. It remains a coarse, frequency-led grammatical cue, not exact POS or word-identity recovery.

Available complete cached references cover the original100 sentences per author:1,514 Caesar tokens and913 Jerome tokens. Expanded streams lack cached full POS references and were not newly annotated. The author sentence IDs have zero overlap with all source partition IDs and the200 reserved IDs. These are already reused development sets, not fresh confirmation, and their short lengths limit the claim.

The frozen iteration157 structural, frequency and combined models were applied without fitting or threshold selection. Every author word type with>=5 occurrences was eligible, regardless of purity, source vocabulary membership or historical16-type catalogue. Inference uses flat opaque ID equality/order and counts; no anchors, sentence boundaries or POS are supplied. References are modal POS computed only after predictions, using cached author annotations; ties are resolved lexically as before. The positive union remains ADP/AUX/CCONJ/DET/PART/PRON/SCONJ, with ADV and all other tags negative.

| Raw-count model | Caesar top5 | Caesar top10 | Caesar top20 | Jerome top5 | Jerome top10 | Jerome top20 |
|---|---|---|---|---|---|---|
| Structural | 5/5 | 10/10 | 18/20 | 4/5 | 7/10 | 15/20 |
| Frequency | 5/5 | 9/10 | 17/20 | 4/5 | 9/10* | 14/20 |
| Combined | 5/5 | 9/10 | 17/20 | 4/5 | 7/10 | 15/20 |

*The displayed inherited lexical tie-break selects9/10 for Jerome frequency. A tie among cum/eius/enim at the cutoff permits8–9 correct depending on anonymous tie resolution. Thus the defensible identity-independent result is8–9/10, not a guaranteed90%. The audit records minimum/maximum correct counts under every boundary tie for all predeclared shortlist sizes. Caesar frequency top10 is9/10 under every tie resolution. All top5/10/20/50 budgets are retained; where fewer than50 candidates exist the actual pool size is reported, not a fabricated50-item list.

Candidate pools are already enriched:28/41 Caesar types (68.29%) and17/27 Jerome types (62.96%) are modal positive. Top10 precision therefore exceeds these pool prevalences, but only two small author sets are available. The source evaluation had211/866 positive types and frequency/combined8/10. These are three datasets, not proof of universal80% precision or the user's four-text lexical-identity objective.

Frequency top10 Caesar: que, in, ad, et, atque, cum, ne, se, qui, eorum. Jerome: et, in, est, non, eum, de, illis, ut, cum, eius under the inherited tie-break. These names are evaluation outputs; the algorithm does not infer them from opaque IDs. Repeated class membership across texts is not recovery of shared Latin words.

Structural results are inconsistent:10/10 in Caesar but7/10 in Jerome, after2/10 in the source all-supported test. Do not choose the structural arm just for Caesar. The combined model does not consistently outperform frequency, so the transferable positive is primarily a frequency baseline, not an established structural addition.

The design also froze a length-normalized frequency control, replacing log1p(n) by log1p(n*31884/Nauthor) while retaining model weights. Top10 lists/counts are unchanged in both authors. Threshold behavior is not: normalization labels every eligible type positive for frequency and combined models, giving precision equal to pool prevalence and100% recall. Raw frequency calls have88.89%precision/28.57%recall Caesar and75%/17.65% Jerome; raw combined90%/32.14% and80%/23.53%. Neither normalization nor raw thresholds were selected per author. This reinforces the distinction between useful small rankings and reliable calibrated classification.

Next proposed extension: add the existing source-author calibration+test sentence sets grouped into Cicero and Palladius, excluding all training-fit and reserved IDs. Freeze the two streams and the same models/support/shortlist budgets before predictions. This supplies two more text datasets without new annotations, but source authors were seen in training and the sets have prior development use, so report them separately from Caesar/Jerome author transfer. Preserve frequency as an independent comparator; no author-specific model selection or claim that four coarse lists establish exact nuclei.

Independent verification reconstructed author word-only streams and complete supported-type coverage, recomputed68 feature vectors using combinatorial overlap/dictionary roles, replayed408 probabilities and12 metric groups, and recorded all shortlist tie bounds. No fitting or production model changes occurred; the dedicated audit validates this inference experiment without repeating the preceding18-test suite. Artifacts and manifest: `experiments/results/grammar-restoration/iteration158/`.
