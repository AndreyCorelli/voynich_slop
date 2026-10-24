# Generated datasets

Store synthetic ciphertext and controls here with seed, generator configuration,
and source identity. Keep hidden ground truth separate from solver inputs.

Corpus samples record exact indices, source locations, normalization, and checksums.
The corpus pilot keeps synthetic ground truth here, separate from public requests.

`l3-conflict/inputs/` stores hidden public requests for L3 synthetic controls,
the 11-word conflict and the 23-word prefix. Known-plaintext calibration inputs
use an explicit `mode: known` wrapper; they contain public plaintext, while keys
and synthetic choices remain in the separate `l3-conflict/truth/` directory.

`guided-extension-certified/inputs/` contains wrappers pairing the complete
23-word public request with recovered-key pins, optional rotations and heuristic
suffix hints. Ordinary `solve` rejects these wrappers; replay them with
`benchmarks/guided_extension.py --replay`. Earlier schedules retain separate
`guided-extension/` and `guided-refinement/` folders, preserving input checksums.

`learned-search-certified/inputs/` contains replayable alternative-suffix wrappers
with their full proof context and guided extension inputs. Use the learned-search
runner for candidate replay and guided-extension runner for extension replay.
`learned-search/` preserves the initial analytic-only probe.

`learned-prefix/inputs/full-prefix.json` is the complete prefix request plus the
original proof context and all proved exclusions. Replay with the learned-search
runner; it validates the proofs again before solving.

`cycle-performance/inputs/` contains public recovery requests and explicit cycle
formula choices. Calibration vocabularies are declared in the report; synthetic
truth stays in `l3-conflict/truth/` and is never passed into hidden recovery.

`dictionary-selection/inputs/` holds standard public requests with optional entry
membership and state cycles. Replay using the cycle-performance runner.

`synthetic-prefix/inputs/` holds public prefix wrappers. `synthetic-prefix/truth/`
holds separate validated generation witnesses with choices truncated at word
boundaries. Ground truth is never passed to the hidden solver.

`synthetic-prefix-gap/` contains the independently replayable three-word follow-up
and its separate generation witness; it uses the same full vocabulary and model.

`segmentation-diagnostic/inputs/` stores explicit diagnostic wrappers. Replay with
`benchmarks.segmentation_diagnostic` to preserve the oracle-boundary restriction;
the hidden wrapper supplies `segmentation: null` and leaves boundaries unknown.

`word-length-diagnostic/inputs/` contains separate `lengths.json`, `boundaries.json`
and `hidden.json` wrappers. Only the first carries word-length counts, with no
boundary positions, plaintext or key. Replay with the segmentation-diagnostic runner.

`length-search/inputs/` contains branch wrappers with length vectors chosen only
from public bounds and vocabulary. No truth is used in their selection. Replay
with the segmentation-diagnostic runner to preserve the recorded branch.

`length-search-intermediate/inputs/` holds public branches for six/eight-word
controls; each branch's chosen lengths derive only from public candidate domains.

`solver-engines/inputs/` holds explicit engine wrappers. Replay with the dedicated
solver-engines runner to preserve the engine and chosen public length vector.

`solver-engines-certified/inputs/` preserves the rerun with pre-check formula
fingerprints. `solver-engines/inputs/` belongs to the initial comparison, whose
constraint counts were read after solver preprocessing.

`length-search-diverse/inputs/` holds public length branches chosen by the two
alternative orderings. Case/strategy identities are in the main experiment report.

`observed-codes/inputs/` contains explicit public substring-domain wrappers.
Use the observed-codes runner for replay; inputs contain no oracle lengths,
boundaries, plaintext or key.

`observed-codes-voynich/inputs/words-23.json` preserves the original complete
23-word H2/L3 prefix with optional observed domains and a 30-minute budget.
It supplies no key/length/segmentation hints or learned clauses. See observed-code
documentation for the user-initiated console command.
