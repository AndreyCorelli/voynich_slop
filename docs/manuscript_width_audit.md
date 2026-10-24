# Manuscript compatibility of calibrated code widths

The recent natural Latin H2 checks calibrate recovery when every plaintext unit emits exactly two ciphertext units and code boundaries are public. This arithmetic audit asks whether those assumptions can describe the cached manuscript transcription before another solver run. It uses no Z3 calls, downloads, new grouping inventories or corpus normalization changes.

## Full transcription result

The audit includes 37,608 clean lowercase word occurrences and treats 1,418 excluded/invalid records as barriers. It counts 17,251 contiguous 22-word windows within folios; windows may cross lines but cannot cross excluded records or folio boundaries. Counts are descriptive, not independent statistical trials. The existing EVA grouping is unchanged: ch/sh and the four benched-gallows combinations, with longest matching. Neither convention is established as the true manuscript glyph inventory.

| Metric | Atomic EVA | Existing grouped units |
|---|---:|---:|
| Mean word length | 4.971 | 4.464 |
| Median word length | 5 | 4 |
| Words compatible with fixed width 2 | 18,479 | 18,306 |
| 22-word windows compatible with fixed width 2 | **0** | **0** |
| 22-word windows compatible with fixed width 3 | **0** | **0** |
| 22-word windows compatible with widths 1–2 | 17,251 | 17,251 |
| 22-word windows compatible with widths 1–3 | 17,251 | 17,251 |
| 22-word windows compatible with widths 2–3 | 9,380 | 9,315 |

Fixed width 2 requires every word's ciphertext length to be divisible by two. One odd word suffices to exclude an entire window under preserved word boundaries, no nulls and no unencoded characters. This is an arithmetic contradiction, not a solver timeout. Plaintext contractions do not repair output divisibility when each contracted unit still emits exactly two output units.

**Two homophones per letter does not imply code width two.** H2 limits how many alternative codes represent a letter; width specifies the length of each alternative. The recent calibration tests used both H2 and fixed width two. This audit excludes that width convention on the scanned windows, not homophonic substitution in general.

Mixed 1–2 and 1–3 widths admit all positive word lengths by arithmetic because width one is allowed. Passing does not imply a common key exists, that a dictionary fit is grammatical, or that natural Latin is plausible. Widths 2–3 reject one-unit words and impose a stronger plaintext-unit ceiling. Fixed width one likewise passes divisibility alone and leaves its key and language questions open.

## Original pilot and earlier checks

The original 22-word block has 104 atomic EVA units, or 85 under the existing grouping. Twelve words have odd atomic lengths; fifteen have odd grouped lengths. Fixed width two therefore fails before fitting.

The original noncontracting mixed 1–3 ceiling remains **104/22 = 4.727 plaintext letters per word** in atomic EVA, or **85/22 = 3.864 units** when grouped. These are ceilings for that block, not a manuscript-wide constant. Under widths 2–3 the respective ceilings drop to 46/22 = 2.091 and 35/22 = 1.591 input units. With contractions, input-unit counts need not equal expanded Latin-letter counts.

The [earlier word-length plausibility analysis](word_length_plausibility.md) already showed that no scanned Caesar 22-word passage fits the original positionwise 1–3 lengths. The [existing EVA grouping sensitivity](eva_tokenization.md) screened cached historical Latin, German, Italian and Czech streams; no grouped positionwise survivors were found under its stated profiles. Those results remain unchanged, with their historical-normalization caveats. This audit hashes their saved artifacts rather than repeating those corpus searches or claiming a new language ranking.

The seven recent natural-control training passages would have mean ciphertext lengths **10.458–14.250 units per word** under fixed width two. Their recovery success therefore does not reproduce the manuscript's mean 4.971 atomic EVA units. It validates a solver component under easier boundary/width assumptions, not manuscript feasibility.

## Recommended next experiment

Stop extending the fixed-two natural-control branch. The next useful calibration is **H2 with widths 1–2 and hidden code boundaries**, using a frozen prefix-free variable-width generator, natural positive controls, shuffled controls and first-key holdout scoring. A separately labeled known-segmentation arm can diagnose whether segmentation is the new bottleneck. It must not leak generating boundaries into the hidden-boundary arm.

This is not a claim that 1–2 is the true manuscript code convention. It is a smaller length-compatible expansion family than 1–3. Earlier [H1 public length calibration](public_length_calibration.md) already produced SAT fits with poor heldout recovery, so merely obtaining variable-width SAT would repeat an inadequate success criterion. Preserve missing vocabulary and unseen-code reporting, and calibrate prediction before manuscript discrimination. The older mixed-contraction pilot establishes functional support for its different model, not this recovery gate; no contraction inventory is expanded here.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.manuscript_width_audit
.venv/bin/python -m benchmarks.manuscript_width_validation
.venv/bin/python -m pytest tests/integration/test_manuscript_width_audit.py -q
```

Frozen report and validation: `experiments/results/manuscript-width-audit/`. Three focused tests pass. Independent validation rebuilds grouping, word-length histograms, exclusion/folio barriers, fixed-width divisibility and mixed-width counts without using the audit's reachability helper. Source and prior artifact hashes are checked. Existing research artifacts are preserved; zero solver calls.
