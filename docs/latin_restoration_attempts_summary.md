# Latin restoration: summary of improvement attempts

This summarizes the Latin experiments in the scalable whole-word decipherment project, through the learned reconstruction scorer. The goal is a reliable nucleus of frequent words, eventually supporting a Voynich → Latin attempt. These synthetic tests assume **injective whole-word substitution with word boundaries and order preserved**. Latin is assumed known; topic, target vocabulary, sentence boundaries and guessed translations are not supplied. Whether this cipher model fits Voynich remains unestablished.

“Recovery” below means **exact surface-word token accuracy**, not grammatical or semantic recovery. Mean recovery averages search restarts; choosing the highest-scoring output can give a different result. Top-50 precision counts correct word types, rather than tokens.

## Starting point

English reached approximately 35% literal recovery in its own experiments. The first Latin/Caesar benchmark reached only **4.21% mean recovery with random starts and 5.49% with frequency starts**, using 169,100 training tokens and a 2.56-million-form inventory. Its frequency-start top-50 shortlist contained **3 correct mappings**. The useful frequent words were principally `et` and `in`; agreement across runs also produced confidently repeated errors. English and Latin percentages are not controlled language-only comparisons.

## Attempts and outcomes

| Attempt | What changed | Result and lesson |
|---|---|---|
| **More search** | Increased Caesar search from 4,000 to 20,000 proposals, with a longer annealing horizon. | Means **4.26% random / 5.48% frequency**: essentially unchanged. More correct candidates were encountered without improving frequent-word recovery. |
| **Favor training-attested proposals** | Mixed proposals from observed words with proposals from the full inventory; all forms remained eligible. | **1.19% / 5.50%**. Random starts regressed; no better nucleus. |
| **Coordinated moves** | Added three-word dictionary cycles to escape single-move barriers. | **4.11% / 5.68%**. Tiny mean change, more false unanimous anchors; no reliable improvement. |
| **Context-profile initialization** | Matched words using frequency, neighbor diversity and contextual statistics before ordinary search. | **3.72% mean**, **2/50** correct shortlist mappings. Shared initialization errors remained highly repeatable. |
| **Association-graph alignment** | Matched directional associations at distances 1, 2 and 4 instead of ordinary likelihood. | About **0.02% recovery**, **0/50**. An uninformative dictionary could outscore the near-correct reference: the objective itself failed a basic control. |
| **Learned contextual classes / coarse decoding** | Learned 32 source word classes; tested class-based language models and a class-first decoder. | Rejected before full decoding: random or collapsed class assignments could beat reference classes, and the word-class model preferred a wrong frequency dictionary. |
| **Word-confidence calibration** | Learned a mapping-quality filter on separate Latin works, using agreement, stability, frequency and context features. | A modest cutoff retained correct `in` and `et` on Caesar, covering **4.82% of tokens**, but the independent high-trust validation failed. Top-50 stayed **3/50**; no validated 50-word nucleus. |
| **Much larger corpus + morphology** | Expanded to **5.94 million tokens, 30 authors**, a **2.67-million-form inventory**, and lemma/grammatical analyses; tested nested corpus sizes and surface/lemma/grammar mixtures. | All **15 configurations** failed the reference-versus-frequency development gate. Full factor-model decipherment was therefore not run. Useful resources were retained; this does not establish that more data or morphology cannot help. |
| **Shuffle-contrast scoring** | Subtracted scores of fixed shuffled copies to cancel unigram pressure; also tested partial unigram regularization. | On Gellius, means **7.12% baseline → 5.36% pure contrast / 6.37% regularized**; top-50 **3 → 1 / 2**. Simple development controls passed, but search found other high-scoring wrong dictionaries. |
| **Trigrams** | Added adjacent three-word context using the larger corpus. | Gellius improved **7.12% → 8.98% mean**, but fresh Livy confirmation regressed **0.80% → 0.25%**. Neither method recovered a correct unanimous frequent anchor on Livy. The gain did not generalize. |
| **Learned reconstruction scorer** | Trained on correct passages, synthetic dictionary corruptions and actual solver negatives; added word sequences and suffix relationships up to eight positions apart. | On Gellius and Livy, intact references beat **all 12 optimized wrong outputs**, versus **4/12** for a unigram-only control. However, those wrong outputs still beat every roughly 50%-correct reconstruction. Reranking selected **7.48% / 0%** recovery. Better intact-text discrimination, not better restoration. |

## What we learned

The obstacle is broader than dictionary size or iteration count. Correct frequent-word candidates are often considered and then rejected or displaced by the score. Some objectives prefer wrong dictionaries even to near-correct references; others pass that comparison but are still exploitable by search. Agreement is not calibrated confidence, and filtering cannot manufacture correct mappings absent from the candidate pool.

**No tested change has established a general Latin recovery improvement or a substantial trustworthy frequent-word nucleus.** The isolated Gellius trigram gain failed fresh confirmation. Results from different texts and resource versions must not be interpreted as one continuous improvement curve. The low Livy results also show that the original Caesar percentages are not dependable real-world expectations.

The most direct remaining scorer experiment is to train on more diverse optimized wrong dictionaries **against partially correct dictionaries**, then require correct ordering on excluded authors before integration into search. Finally, optimize against the scorer itself to check for new loopholes. These follow-ups are proposed, not completed. Decoder defaults remain unchanged; Ammianus and Quintilian remain sealed.

## Detailed reports

- [Original Caesar benchmark](scalable_latin_caesar.md)
- [More search, proposal mixture and coordinated moves](scalable_latin_target_independent.md)
- [Context profiles and association graphs](scalable_latin_profiles_association.md)
- [Learned classes and confidence calibration](scalable_latin_classes_confidence.md)
- [Larger corpus and morphology](scalable_latin_corpus_morphology.md)
- [Shuffle contrast](scalable_latin_shuffle_contrast.md)
- [Trigrams and fresh confirmation](scalable_latin_trigram.md)
- [Learned reconstruction scorer](scalable_latin_reconstruction_scorer.md)
