# Length/frequency prediction baseline

Saved recovered keys outperform the frozen superficial predictor on all three
SAT-matched groups. No new solver fits are run. Two tests and 44-case artifact
validation pass.

| Group | Positive status | Matched held-out words | Baseline exact | Key exact | Novel baseline / key |
|---|---|---:|---:|---:|---|
| Natural, strict vocabulary | 8 SAT | 48 | 2 | 48 | 0/38 versus 38/38 |
| Natural, one unknown occurrence | 3 SAT, 5 UNKNOWN | 18 | 0 | 18 | 0/18 versus 18/18 |
| Synthetic, one unknown type | 6 SAT | 18 | 6 | 14 | 6/18 versus 14/18 |

Across all eight natural one-occurrence cases, the baseline scores 2/48, but key
accuracy is available only for the three SAT cases. UNKNOWN cases are not silently
excluded from status reporting or counted as wrong decoded keys. These natural
cases reuse the strict group's text; their totals must not be pooled as independent
observations. Synthetic profiles/seeds also reuse the same underlying text.

Controls retain their saved statuses: natural strict eight UNSAT; natural
one-occurrence three UNSAT/five UNKNOWN; synthetic one-type six UNSAT. None has a
SAT key to score. No plaintext accuracy is assigned to shuffles. The baseline
always emits an inventory word, so control vocabulary membership is a descriptive
output, not a test of successful encryption recovery or a comparable exact score.

## Fixed predictor and assistance

Before scoring, the rule and predictions are frozen. The predictor learns the
ratio of total training ciphertext glyphs to total true training plaintext letters.
For each held-out ciphertext word, it chooses a candidate minimizing the absolute
scaled length error. Ties prefer higher true training word frequency, then lexical
tuple order. Integer arithmetic fixes ties reproducibly. The candidate pool is
the supplied dictionary union true training words. Cipher glyph identities, keys,
generating profiles and held-out plaintext never enter the predictor. No tuning,
reranking or alternative predictors are added after observing scores.

This is an oracle-supervised training baseline: it receives true training word
identities, frequencies and paired lengths, which hidden recovery does not.
However, it emits only existing inventory entries. It cannot predict a novel
spelling absent from that inventory, whereas a recovered key can decode such a
word. In the strict natural cases 22/48 held-out occurrences are absent from the
pool. Therefore the 48-versus-2 comparison combines structural prediction and
open-vocabulary capability; it does not isolate one source of improvement.
The length/frequency baseline is simple, not a claim to the strongest noncipher
language model or a fitted likelihood test.

The results demonstrate useful predictive structure in recovered keys on these
assisted fixtures, despite errors in relaxed synthetic cases. They do not validate
a manuscript hypothesis, eliminate the observed key ambiguity, or establish that
cipher recovery outperforms every statistical alternative.

## Reproduction

```sh
.venv/bin/python -m benchmarks.length_frequency_baseline --run
.venv/bin/python -m benchmarks.length_frequency_baseline --validate
```

`experiments/results/length-frequency-baseline/` saves source/report/code hashes,
protocol, precomputed baseline guesses, training assistance, paired saved solver
rows, exact/novel scores and separate group summaries. Source prepare functions
check frozen dependencies; completed report hashes and requests are matched.
Validation reconstructs predictions and deterministic scoring without solver calls.
Tests exercise ratio/frequency/lexical ranking, glyph-identity invariance,
unresolved handling and absence of control accuracy claims.
