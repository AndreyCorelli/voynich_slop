# Experiment configurations

`staged-recovery.json` is a validated, runnable specification for hidden-plaintext
synthetic validation. Run `uv run python benchmarks/staged_recovery.py` from the
repository root. Stage names, alphabets, vocabulary widths, cipher bounds, seeds,
sample sizes, representation, and timeout are explicit. The vocabulary is the
versioned hand-authored Latin fixture, not a downloaded corpus.

`nulls-demo.json` is a synthetic-generation template with a four-symbol plaintext
alphabet, five dictionary entries, verbose homophones, and bounded boundary
nulls. Its empty ciphertext is filled by `voynich-smt synthetic generate`.
Optional `nulls` and `optimization` objects are validated on public requests;
missing objects preserve the earlier feasibility defaults. See
[the CLI examples](../../docs/nulls_optimization.md).

`latin-frontier.json` widens the acquired Caesar vocabulary from 32 to 128 to 512
to all entries, then increases homophones and code length separately. Each stage
compares free and text-wide cyclic selection on identical inputs, with three
synthetic seeds and two controls. `latin-frontier-lexical.json` starts at 512 and
whitelists single-letter a/e/i/o. Run `benchmarks/latin_frontier.py`; these are
runner configurations, which produce separate public solver requests.

`sample-scaling.json` fixes the full filtered vocabulary, alphabet, cipher bounds,
cyclic selection, and timeout while increasing uninterrupted sample prefixes to
5/10/25/50 words. Run `benchmarks/sample_scaling.py`; it selects the earliest
sufficiently long clean paragraph-text span and saves individual solver requests.

`l3-conflict.json` reuses the saved UNSAT boundary. It specifies three synthetic
seeds, a 30-second gate budget and flat/trie attempts at 30/120 seconds. Scientific
parameters are inherited from the original request with only maximum code length
raised to three. Run `benchmarks/l3_conflict.py`; it checkpoints synthetic
validation, the conflicting suffix and conditional progression to the full prefix.

`guided-extension.json` selects the verified L3 report, a 30-second per-stage
budget and trie dictionary encoding. The runner holds scientific parameters
fixed while freeing candidate-key mappings. Full-text cycling persists through
all 23 words. Key pin restrictions and rotations are recorded separately from
ordinary hidden requests, with source witness identity and optional core settings.

`learned-search.json` fixes the L3 model and limits the alternative-key search to
five candidates, with 30-second solve budgets and the trie dictionary formula.

`learned-prefix.json` applies the learned-search exclusions to the entire unchanged
prefix with no mapping pins and a 120-second solver budget.

`cycle-performance.json` calibrates equivalent cycle formulas on saved synthetic
seeds 7/17/1729, with declared smaller vocabulary controls and a full-prefix retry.

`dictionary-selection.json` compares the entry formula on exact seed-7 calibration
requests, using 30-second paired budgets and a 120-second full-vocabulary retry.

`synthetic-prefix.json` fixes seed 7, full vocabulary and H2/L3/text cycles;
only the observed prefix grows through 1/2/4/6/8/11 words, at 30 seconds per solve.

`synthetic-prefix-gap.json` tests the three-word prefix to fill the initial
calibration gap between two-word SAT and four-word UNKNOWN. Use a separate
`--output` and `--artifacts` path as shown in the synthetic-prefix documentation.

`segmentation-diagnostic.json` selects the saved four-word control and gives both
hidden and boundary-oracle diagnostics a fresh 30-second solve budget.

`word-length-diagnostic.json` enables the length-only case alongside fresh boundary
and hidden runs. Pass its dedicated output and artifact paths when invoking the
segmentation-diagnostic runner to preserve the earlier report.

`length-search.json` reads only public seed-7 control inputs, tries shorter
admissible length vectors first, and limits each case to twelve ten-second solves.

`length-search-intermediate.json` calibrates six- and eight-word public controls,
allowing four shortest-first branches with 30-second budgets in each case.

`solver-engines.json` selects one public six-word length-search branch that stalled
at 30 seconds, retaining identical formula/lengths and comparing only the engine.

`length-search-diverse.json` compares balanced diagonal and candidate-rich ordering
on the six/eight-word public controls, with the same four-branch/30-second budgets.

`observed-codes.json` tests the optional codeword-domain formula on saved 4/6/8/11
word hidden controls, with the same 30-second budgets as their recorded baselines.
