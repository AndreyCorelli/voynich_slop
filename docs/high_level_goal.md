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
