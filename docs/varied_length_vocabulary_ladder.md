# Vocabulary-only scaling of varied-length controls

With keys, alphabets and ciphertext fixed, expanding the dictionary to 64 words
retains six verified SAT fits and 17/18 exact novel predictions. Expanding to
256 words produces four SAT fits, two UNKNOWN timeouts, and only 4/12 correct
predictions among the successful fits. The same four cases scored 12/12 at 64
words. Dictionary expansion alone can therefore make the returned first key much
less predictive on these controls.

| Generating profile / seed | 12-word exact holdout (reused) | 64-word status / exact holdout | 256-word status / exact holdout |
|---|---:|---|---|
| Length two / 4301 | 3/3 | SAT, 3/3 | UNKNOWN, unscored |
| Length two / 4302 | 3/3 | SAT, 3/3 | SAT, 0/3 |
| Lengths one/two / 4301 | 3/3 | SAT, 3/3 | SAT, 3/3 |
| Lengths one/two / 4302 | 3/3 | SAT, 3/3 | SAT, 0/3 |
| Lengths one/two/three / 4301 | 2/3 | SAT, 2/3 | UNKNOWN, unscored |
| Lengths one/two/three / 4302 | 3/3 | SAT, 3/3 | SAT, 1/3 |

All 64-word checks take 0.65–0.75 solver seconds. At 256 words, SAT checks take
1.08–4.60 seconds and UNKNOWN checks take approximately five seconds. Construction
is 0.29–0.47 seconds per new fit, so model building is not the limiting cost on
this small ladder. Successful 256-word keys match only 6–10 of 18 training
occurrences, even though every generating training word remains in the dictionary.
Correct predictive explanations remain constructively verified at every size.

## Frozen one-variable protocol

The six keys and training/held-out observations are copied unchanged from
[small varied-length controls](small_varied_length_controls.md). The same
14-letter plaintext alphabet, six ciphertext glyphs, H1 prefix-free L1–3 bounds,
free selection, flat membership with equality reuse and observed domains are
retained. Training identities, lengths and the key remain hidden. Each fit receives
the same configured five-second solver timeout. Only the dictionary field changes.

The ladder preserves the original twelve entries and their order, then appends
the first distinct eligible normalized Caesar words in corpus record order.
Candidates must use only the existing 14-letter alphabet and must not have an
excluded normalization reason. No frequency, word-length or solver-outcome
filter is used. The 64-word dictionary is an exact prefix of the 256-word
dictionary. Added words carry corpus record indices. This corpus has sufficient
eligible words, so no alphabet expansion or fallback was needed.

All dictionaries and twelve new requests were frozen before solving. Source,
corpus, baseline and model code hashes are recorded. Six 12-word hidden results
are reused exactly after request/hash checks; no known-word arms or new keys are
rerun. Independently checked generating witnesses satisfy every expanded request.
Completed fits checkpoint and skip on resume, without retries or extra timeouts.

First verified keys are frozen before scoring the same three novel, code-covered
held-out words. Exact correctness is compared against unchanged generating truth.
Dictionary-member counts use the current arm's dictionary and are not a stable
cross-size metric. UNKNOWN remains unscored; its missing predictions do not count
as incorrect or as evidence of impossibility. The 4/12 figure is conditional on
SAT; six held-out occurrences from UNKNOWN fits remain unevaluated.

## Prior-work review and limits

The earlier 64/128/256 reduced-vocabulary experiment used another H2 fixture,
truth-required dictionary subsets and ten-second timeouts. This ladder fixes
H1 varied generating lengths, the smaller alphabet, identical observations and
five-second budgets. The old experiment is preserved, not repeated.

These outcomes concern the first returned witness under one frozen expansion
rule. They do not prove all keys at 256 words predict poorly, a universal vocabulary
threshold, or any manuscript-language conclusion. Added words change candidate
identities and lengths together; that is the intended dictionary-only intervention.
No randomized negative controls were included, so this measures positive recovery
and ambiguity rather than discrimination against accidental fits.

Nine focused tests pass, checking deterministic corpus order, nesting, fixed
alphabet/exclusion filters, insufficient input rejection, unchanged public
requests except dictionary, matched budgets, exact baseline reuse, unscored
UNKNOWN and checkpoint resume. Actual artifact validation passed for twelve new
fits and six saved baselines, including reconstructed selection, full witnesses,
absence of oracle lengths and independently recomputed frozen scores.

Artifacts: `experiments/results/varied-length-vocabulary-ladder/`.

```sh
.venv/bin/python -m benchmarks.varied_length_vocabulary_ladder --validate
```

Next priority: measure discrimination by pairing the tractable 64-word positives
with fixed randomized ciphertext controls. Preserve word lengths, repeated-word
identity patterns and per-word glyph counts where possible. Such controls are
not automatically impossible under the model: their SAT rate is exactly what
needs measuring. Freeze control seeds before fitting, avoid selecting controls
by solver rejection, and compare outcomes under the same budgets. This addresses
accidental fits before introducing another language prior or expanding vocabulary
again.
