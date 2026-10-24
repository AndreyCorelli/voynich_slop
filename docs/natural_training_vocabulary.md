# Natural calibration without reserved held-out vocabulary

All eight positives are verified SAT, recover 24/24 training words and predict
48/48 held-out occurrences exactly, including 38/38 novel occurrences. This
includes 22/22 excluded occurrences and 26/26 included occurrences (16/16 novel
included). All eight paired shuffles are UNSAT; no fits time out. Positive solver
times are 1.503–2.746 seconds and shuffle times 1.432–4.200 seconds.

Explicitly reserving held-out entries was not necessary for these successful
first-key predictions. This remains small-scale, training-assisted calibration;
it does not establish blind language identification or manuscript compatibility.
The changed dictionary also resolves the previously timed-out Swabian shuffle;
that is a different request, not a resolution of the original UNKNOWN.

The four frozen natural passages, eight generating keys and eight paired shuffles
are unchanged. Each 256-word dictionary is rebuilt from the sorted distinct
training plaintext words, then filled with first distinct eligible corpus words
under the unchanged passage alphabet. Held-out words are neither reserved nor
forbidden. Their membership is audited only after construction and never supplied
as a recovery constraint. No solver outcome changes vocabulary construction.

| Passage | Novel held-out occurrences | Included naturally | Excluded |
|---|---:|---:|---:|
| Latin 1 | 6 | 2 | 4 |
| Latin 2 | 6 | 1 | 5 |
| Swabian 1 | 4 | 3 | 1 |
| Swabian 2 | 3 | 2 | 1 |

The same passage is used under two key profiles. Eleven of nineteen novel
occurrences per profile are excluded. Exact decoding of excluded words is
possible: dictionary membership constrains training recovery, not frozen-key
continuation decoding. Dictionary coverage and exact prediction therefore need
separate reporting.

This removes explicit held-out vocabulary reservation, not all assistance.
True training words remain guaranteed present. Original passage selection saw
held-out plaintext for novelty and letter coverage, and additions use the full
cached source stream rather than a separate corpus. All held letters already
occur in training. This is not fully blind or out-of-source evaluation.

Only dictionary fields change from the paired 64-word requests; training and
held-out ciphertext, alphabets, H1 L1–3 bounds, free selection, flat observed
encoding and five-second solver timeout remain fixed. Construction time is extra.
All sixteen requests and their coverage audits were frozen before fitting.
Known-word fits are not repeated. First SAT keys are frozen-scored for exact
included/excluded predictions, separately for novel occurrences; controls receive
dictionary compatibility scores without plaintext accuracy claims. UNKNOWN is
unresolved and unscored; UNSAT is solver-reported without independent proof
certificates. Same-source/profile cases remain correlated.

```sh
.venv/bin/python -m benchmarks.natural_training_vocabulary --run
.venv/bin/python -m benchmarks.natural_training_vocabulary --validate
```

Artifacts in `experiments/results/natural-training-vocabulary/` contain protocol,
source/code hashes, dictionaries/provenance, coverage audits, paired 64-word rows,
checkpointed results and validation. Completed fits skip on resume. Validation
reconstructs dictionaries and coverage, checks unchanged public inputs and paired
results, independently verifies generating/recovered witnesses and recomputes
frozen scores. Three integration tests cover input isolation, training-only seeds,
resume, UNKNOWN handling, baseline mismatch rejection and dictionary construction
independence from held-out inventories.
