# Iteration 159: frequency-led coarse shortlist across four text datasets

**Preserve and highlight:** the same frozen frequency model's top10 contains80–90% members of the defined grammatical group in all four text datasets, with arbitrary boundary ties accounted for. This is a concrete coarse grammatical cue worth retaining as possible input to another deciphering approach. It does not recover exact POS tags, Latin identities or the requested shared lexical nuclei, and only Caesar/Jerome are source-unseen authors.

The two added streams are all existing partition0 calibration+test sentence IDs grouped by author, retaining original order and excluding training-fit and reserved IDs. Cicero has1,541 sentences/20,136 tokens; Palladius58 sentences/737 tokens. Both authors occur in the source training partition and the sentence sets have prior development use. No new annotation, reserved material or sealed works were used. All supported word types (>=5 occurrences) enter inference with no purity, source-vocabulary or historical catalogue filter.

The frozen iteration157 structural/frequency/combined models and raw0.5 threshold are unchanged. As in158, raw log1p counts are primary and a fixed source-length-normalized control is fully reported. Inputs and selections were frozen before features, predictions before evaluation. Modal references derive only from cached annotations; the positive union remains ADP/AUX/CCONJ/DET/PART/PRON/SCONJ, with ADV negative.

| Dataset | Status | Tokens | Supported pool: positive/total | Frequency top10, any boundary tie | Combined top10 |
|---|---|---|---|---|---|
| Caesar | Source-unseen author, reused development | 1,514 | 28/41 | 9/10 | 9/10 |
| Jerome | Source-unseen author, reused development | 913 | 17/27 | 8–9/10 | 7/10 |
| Cicero | Seen author, sentences outside fit | 20,136 | 189/588 | 8/10 | 9/10 |
| Palladius | Seen author, sentences outside fit | 737 | 10/15 | 9/10 | 9/10 |

These are not four independent author-transfer confirmations, nor an estimate of universal80% precision. Candidate pool prevalence ranges32.14–68.29%; the small Palladius pool already has ten positives among fifteen types. All datasets are development material. The source nested-type evaluation separately scored frequency8/10 and combined8/10 among866 supported non-target types, but must not be pooled as an independent fifth author.

| New author, raw arm | Structural top5/top10/top20 | Frequency top5/top10/top20 | Combined top5/top10/top20 |
|---|---|---|---|
| Cicero | 2/5;3/10;7/20 | 4/5;8/10;17/20 | 4/5;9/10;17/20 |
| Palladius | 3/5;7/10;10/15 | 4/5*;9/10;10/15 | 5/5;9/10;10/15 |

*Palladius frequency top5 permits4–5 correct under anonymous tie resolution; its top10 is exactly9 regardless. All top5/10/20/50 bounds and actual list sizes are retained. Top20 in Palladius contains only fifteen supported types. Cicero frequency/combined top50 both score37/50. Top10 was fixed before scoring and no author-specific model or shortlist size was chosen.

Cicero frequency top10 is et, in, ut, non, me, est, cum, ad, que, ne. Palladius is et, uel, est, in, ne, sed, si, hoc, ad, quod under the inherited tie-break. These identities are evaluation outputs, not inferred plaintext mappings. Shared names in frequency lists are not shared recovered lexical nuclei.

Cicero frequency AP=0.5743 and AUC=0.7224, versus combined AP=0.5917 and AUC=0.7288; Palladius frequency AP=.922 and AUC=.890, combined AP=.950 and AUC=.900. Structural-only results remain poor/inconsistent, so this finding is predominantly frequency-led; do not credit the four-text success to the structural model.

Raw frequency threshold calls are52.17%precision/50.79%recall Cicero and100%/30% Palladius. Combined gives55.15%/56.61% and100%/40%. Source-length normalization changes thresholds strongly but preserves the reported top10 counts. All models/controls remain reported without selecting an author-specific winner. A useful shortlist is distinct from generally reliable calibrated classification.

Next proposed check: audit treebank versus orthographic word segmentation, especially enclitic components such as que/ue/c. The working Voynich hypothesis is one EVA word per Latin word, so a shortlist enriched by separately tokenized grammatical components may overstate applicability. Establish what original boundary metadata is already available, then predeclare a mechanically reproducible boundary comparison before scoring; do not remove errors by hand or acquire new POS annotations. This challenges the transfer assumption directly while preserving the observed coarse grammatical achievement.

Independent verification reconstructed the exact source-author sentence sets and complete modal references, confirmed zero source-fit/reserved overlap, recomputed603 anonymous feature vectors, replayed3,618 probabilities and12 metric groups, and recorded every shortlist tie bound. No fitting or production model changes occurred; the dedicated audit verifies this inference experiment. Frozen artifacts and manifest: `experiments/results/grammar-restoration/iteration159/`.
