# Voynich: unforced Frühneuhochdeutsch word-map probe

This experiment applies the frozen historical German model to the actual Voynich transcription. No translation, preferred word or anchors enter inference. Language and injective whole-word substitution remain experimental assumptions.

## Design

Use the existing Zandbergen–Landini EVA version 3b transcription from `data/processed/zl-eva.json`. The corpus retains **37,608 words, 7,457 types**, across **227 folio sides**. The existing transcription normalization splits uncertain spaces and excludes non-basic or annotated words. The 1,418 excluded word records and page changes break adjacency, leaving 1,527 segments. Physical lines are not treated as sentences. No section, topic or Currier filtering is applied.

The solver sees opaque integer word IDs and their sequence, without EVA spelling, lengths or manuscript metadata. Its stream compatibility tag is the frozen model's tokenization identifier; EVA characters are never interpreted as German characters.

Reuse the original ReF-trained model: **2,956,502 training tokens and 245,420 source-derived dictionary forms**. This is the parent model used for the German pilot and Abelin confirmation. Retain the English sparse bigram objective, mixed proposal scheduler, retrieval settings and archive selection. Use random starts only, seeds **3/5/7**, with **8,000 proposals per chain** and a 1,200-second allowance. All candidates remain available; `vnd` has no special treatment.

Four fixtures provide twelve chains:

- Actual full transcription.
- One fixed null control, seed 2701: shuffle interiors separately within each segment, preserving its endpoints, length and the exact overall word counts. This changes 32,968 positions (87.66%). Actual and control use identical initial assignment vectors for each paired seed.
- First half: 18,804 words, 4,560 types, 924 segments.
- Second half: 18,804 words, 4,548 types, 604 segments. The midpoint splits a segment; halves never join gaps. Both halves run independently with opaque IDs.

For each seed, select a complete archived key by the frozen source objective. Rank all predicted mappings by agreement, then observed count, then opaque ID. Primary candidates require three-run unanimity and at least 100 occurrences. These are repeatability criteria, not calibrated correctness probabilities. Inspect `vnd` only after inference and unrestricted ranking.

## Results

**`daiin → vnd` emerges without prompting in all three full-text runs**, at 847 positions (2.25% of retained words). It is the **only** full-text mapping meeting the unanimous/frequent criterion. However, exactly the same mapping is unanimous in the shuffled control.

| Fixture | `daiin` occurrences | Runs predicting `vnd` | Other prediction |
|---|---:|---:|---|
| Full actual | 847 | 3/3 | — |
| Full shuffled | 847 | 3/3 | — |
| First half | 543 | 3/3 | — |
| Second half | 304 | 2/3 | `die` in seed 7 |

In the second half, seed 7 instead assigns `ol → vnd` (278 occurrences). This is one vote, not a unanimous candidate.

All primary mappings, across every fixture:

| Fixture | EVA → guess | Count | Agreement |
|---|---|---:|---:|
| Actual | `daiin → vnd` | 847 | 3/3 |
| Shuffled | `daiin → vnd` | 847 | 3/3 |
| Shuffled | `shol → vnnd` | 184 | 3/3 |
| First half | `daiin → vnd` | 543 | 3/3 |
| Second half | `aiin → der` | 315 | 3/3 |

For perspective, the next full-text frequent guesses have only two votes: `ol → das` (556), `aiin → der` (504), `chedy → die` (502), `or → in` (386), `s → ist` (341), `al → dem` (261), and `shol → also` (184). Every third run disagrees. None is promoted to a trusted anchor.

The full-text selected-key scores for seeds 3/5/7 are −336069.58, −337500.82 and −337342.93; the paired shuffled scores are −336623.58, −337045.75 and −336938.13. The actual text wins only one of three paired comparisons. This single shuffle is a diagnostic, not a calibrated significance test.

**Interpretation:** the desired word does pop up naturally, and repeatedly attaches to the same EVA type. But it also survives substantial order disruption. Frequency, retained endpoints, residual local order and shared model preferences are not separated by this control; the result does not establish contextual recovery. Independent halves give incomplete replication. Consequently `daiin → vnd` is an exploratory hypothesis, with unknown correctness probability, and should not yet be fixed as an anchor. These results neither identify the manuscript's language nor establish the assumed cipher mechanism.

All **12 chains / 96,000 proposals** finish at the proposal cap. Search time sums to **35.80 minutes** across concurrent processes; this is not wall-clock duration. Each chain takes approximately 138–234 seconds. All initial/current/archived dictionary scores are independently recomputed, and paired initial keys match exactly. Frozen source/resource/protocol checks pass. **170 relevant tests pass**, including the three new tests for gap handling, independent half construction and deterministic count/endpoint-preserving shuffling. No production solver defaults are changed.

## Artifacts and reproduction

Local artifacts: `experiments/results/scalable-voynich-fruehneuhochdeutsch/v1/`. `design.json` records the frozen inputs, policies and reference protocol before inference. `preparation.json` records fixture identities. Each run preserves checkpoints, compressed traces, public confidence features, every word prediction, and fixed 100-word EVA/model-output excerpts at offsets 0, 1000 and 10000. These excerpts are exploratory assignments, not translations.

The cached transcription source URL is `https://www.voynich.nu/data/ZL3b-n.txt`; its provenance and original rights statement remain in the design manifest. No explicit redistribution license has been established; these are local research artifacts.

```
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch prepare
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch trial --name actual
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch trial --name shuffled
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch trial --name first-half
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch trial --name second-half
.venv/bin/python -m benchmarks.scalable_voynich_fruehneuhochdeutsch summarize
```

Preparation refuses to overwrite an existing versioned experiment. Completed inference can be inspected again with `inspect --name NAME` without repeating search.
