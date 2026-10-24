# One out-of-dictionary training occurrence

Three of eight genuine-encryption fixtures return verified SAT, recovering all
24 training words and predicting all six held-out words each (18/18, all novel).
The other five positives are UNKNOWN. Controls yield three UNSAT and five
UNKNOWN; no SAT control appears. Four tests and sixteen-case validation pass.

| Case | Genuine fixture | Paired shuffle |
|---|---|---|
| Latin 1, fixed two | SAT; 6/6 exact | UNSAT |
| Latin 1, mixed 1/2/3 | SAT; 6/6 exact | UNSAT |
| Latin 2, fixed two | UNKNOWN | UNKNOWN |
| Latin 2, mixed 1/2/3 | SAT; 6/6 exact | UNSAT |
| Swabian 1, fixed two | UNKNOWN | UNKNOWN |
| Swabian 1, mixed 1/2/3 | UNKNOWN | UNKNOWN |
| Swabian 2, fixed two | UNKNOWN | UNKNOWN |
| Swabian 2, mixed 1/2/3 | UNKNOWN | UNKNOWN |

Each recovered SAT key places its single OOV occurrence at the deleted first
training word and recovers that word correctly. Generating witnesses verify for
all eight relaxed positives, including the timed-out cases. The model now admits
the correct explanations, but search becomes harder: a five-second timeout cannot
recover most cases or exclude most controls. Conditional SAT accuracy is 18/18;
unresolved cases receive no accuracy score. This is not a demonstrated false-fit
rate or a reason to interpret UNKNOWN as incompatibility.

This calibration uses the exact sixteen frozen one-type deletion requests from
[training vocabulary ablation](training_vocabulary_ablation.md): eight genuine
encryption fixtures and eight paired shuffles. It relaxes training membership to
allow at most one actual out-of-dictionary word occurrence. The solver chooses
the occurrence, letters and length jointly; no missing word or position is given.
All deleted true types occur once, so each generating explanation is again legal.

The allowance counts occurrences, not distinct types or free exemption flags.
Each flag is equivalent to failure of dictionary membership. Unknown words may
use every plaintext alphabet symbol, within the unchanged public minimum/maximum
word lengths and ciphertext/code-length bounds. Repeated unknown occurrences
consume the budget separately. Prefix-free encoding, ciphertext reproduction,
H1 L1–3 code bounds, free selection and five-second solver timeouts remain fixed.
Construction time is additional. Dictionary size stays 255; no new words are added.

Strict pairwise dictionary candidate pruning and dictionary-derived symbol
restrictions would be unsound with unknown words. The experimental solver uses
unpruned individual length candidates, no dictionary-only prefix relations, and
all plaintext letters at symbolic slots. Padding is constrained separately.
Original strict solver files and frozen results remain unchanged. The isolated
`oov_recovery.py` prototype derives its feasibility builder from `recovery.py`;
this duplication preserves baseline hashes but needs consolidation before broader
use. It is not a change to the default request/replay semantics.

All sixteen inputs were frozen before fitting; completed cases checkpoint and
skip on resume. SAT explanations are independently checked for their actual OOV
count, cipher reproduction, unique decoding, code bounds, language length bounds
and selection rules. First keys are frozen-scored using unchanged holdouts;
positive exact/novel accuracy and shuffled dictionary compatibility stay separate.
UNKNOWN is unresolved; UNSAT is solver-reported without independent certificates.
No manuscript-language conclusion follows. Retained training vocabulary remains
assisted, and the passages/profiles remain correlated.

```sh
.venv/bin/python -m benchmarks.one_oov_calibration --run
.venv/bin/python -m benchmarks.one_oov_calibration --validate
```

Artifacts in `experiments/results/one-oov-calibration/` save protocol, hashes,
public requests, strict paired rows, recovered witnesses, OOV positions and frozen
scores. Four integration tests cover empty candidate domains, actual occurrence
budgets including repetitions, solver input/resume isolation and rejection of
excess-OOV witnesses. Validation reconstructs matched inputs and recomputes scores.
