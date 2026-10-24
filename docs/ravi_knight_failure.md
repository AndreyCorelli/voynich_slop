# Ravi–Knight adaptations and their limits

## English

We adapted the Ravi–Knight word-substitution setup from dense HMM/channel EM to a scalable search over complete injective word dictionaries, using a sparse smoothed bigram language model, bounded contextual candidate retrieval, incremental assign-or-swap scoring, annealing and multiple restarts.
The decoder received a continuous word stream with word order and boundaries preserved, without target vocabulary, sentence boundaries or plaintext hints; “restored” below means exact word-token matches, not recovered grammar or meaning.
On an independent 35,000-word Wells passage, random starts restored **27.04% on average**, while frequency-ranked starts restored **29.70% on average** and **34.91% in the model-score-selected run**, whose dictionary contained **42 correct word types out of 4,872**.
Pooled contexts, coordinated three-word cycles, trigrams, more training text and weaker unigram pressure produced small or inconsistent gains; on a second 35,000-word work, *The Hound of the Baskervilles*, the trigram improved **35.32% to 35.77%** at roughly four times the cost.
Requiring agreement across three random starts and at least 100 occurrences identified a correct four-word nucleus on each work: **the, and, of, a** on Wells, covering **19.11% of tokens**, and **the, a, his, with** on Hound, covering **9.62%**.
These were **two small nuclei of four correct mappings each**, not broad restoration: rare words remained largely unrecovered, and the objective could prefer poor decodings to nearly correct reference dictionaries.
Sources: [independent English benchmark](scalable_english_independent.md), [strategy and nucleus experiments](scalable_english_strategies.md), and [frequency-pressure experiment](scalable_english_frequency_tempering.md).

## Latin

We transferred the same whole-word substitution/search framework to Latin, initially using **169,100 training tokens** and a **2.56-million-form inventory**, without supplying the target vocabulary or translations.
The Caesar baseline restored **4.21% of word tokens on average with random starts** and **5.49% with frequency starts**, whose top-50 mapping shortlist contained only **3 correct entries**, with useful frequent-word recovery principally limited to **et** and **in**.
Increasing search from 4,000 to 20,000 proposals left recovery essentially unchanged at **4.26% / 5.48%**, while favoring training-attested candidates and adding coordinated dictionary cycles failed to establish a better nucleus.
Context-profile initialization yielded **3.72% recovery and 2/50 correct mappings**, and association-graph alignment yielded approximately **0.02% and 0/50**.
Learned contextual classes failed preliminary scoring controls, while confidence filtering retained correct **in** and **et**, covering **4.82% of Caesar tokens**, but failed independent high-trust validation.
We expanded training to **5.94 million tokens from 30 authors**, with **2.67 million forms** and lemma/grammar annotations, but all **15 tested configurations** failed a development scoring gate, so full decoding with those factor models was not run.
Shuffle-contrast scoring reduced Gellius recovery from **7.12% to 5.36%**, or **6.37%** with unigram regularization; trigrams improved Gellius to **8.98%**, but regressed on fresh Livy confirmation from **0.80% to 0.25%**, with no correct unanimous frequent anchor for either model on Livy.
A learned reconstruction scorer using word sequences and suffix relationships ranked intact references above **all 12 optimized wrong outputs**, but still ranked those outputs above every roughly half-correct reconstruction, and reranking delivered only **7.48% on Gellius and 0% on Livy**.
Overall, none of these changes established a general Latin recovery improvement or a substantial trustworthy nucleus: candidate availability, exploitable scoring and repeatable wrong mappings remained obstacles, and percentages across different texts/resources are not a single improvement curve.
Sources: [Latin attempts summary](latin_restoration_attempts_summary.md) and [learned reconstruction scorer](scalable_latin_reconstruction_scorer.md).

## Frühneuhochdeutsch

We applied the unchanged English algorithm to historical German surface forms using roughly **2.95 million training tokens**, a **245,420-form inventory**, random/frequency starts and three restarts of **8,000 proposals** per setting.
On the long Arndt and Abelin texts, random starts restored **14.07% and 13.01% of tokens on average**, respectively, while frequency starts fell to **9.89% and 7.21%**; shorter excluded-author texts varied substantially, with random-start means of **1.72–12.26%**.
The unanimous frequent-word nucleus contained **3 correct mappings out of 4 selected** on Arndt (**vnd, aber, sein**, covering **4.45% of tokens**) and **2/2** on Abelin (**vnd, in**, covering **5.19%**).
Historical spelling variants explained some literal mismatches, but a separate lemma diagnostic remained modest, and neither long text met the provisional nucleus target of **20 selected types at 80% precision**.
The result was partial frequent-word recovery without a substantial reliable nucleus or trusted Voynich restoration; see the [long-text validation report](scalable_fruehneuhochdeutsch_long.md).
