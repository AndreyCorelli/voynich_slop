# Natural Latin H2 calibration

This loop moved from generated dictionary words to seven fresh, nonoverlapping Caesar passages: 48 training words followed by six continuation holdouts. All seven were selected and frozen before fitting. Selection used source eligibility, heldout letter coverage and at least three novel heldout types; dictionary membership was audited afterwards. No passage was replaced after failing a gate.

## Protocol

Source: `data/processed/caesar-latin-v2.json`, after the previously tested natural passages. Canonical Latin spelling maps j to i and v to u using the existing morphology policy. Source records and code hashes are frozen in `experiments/results/latin-h2-natural/prepared.json`.

The broader `through-medieval-rare` inventory supplies all 6,327,182 finite generated forms, including lengths outside the previous synthetic 3–6 restriction. The default inventory is audited separately. Missing training forms prevent admission; missing heldout forms are reported without constraining predictions. No target words are added.

Each letter has two disjoint two-glyph codes. The generating process alternates between them across training and continuation. The fitted model allows free selection with at most two observed codes per letter, with public word and code boundaries. Natural words are neither duplicated nor rearranged. A heldout code unseen in training prevents admission for this first complete-key scoring test. The code was not replaced by a seen homophone.

Each admitted case gets its first positive fit, a pattern-preserving shuffled control, and a separate exclusion of the first observed key. Budgets are 30 seconds for Z3 and 60 seconds for each worker, including preprocessing. Alternative keys never replace the first scored key. UNSAT is a bounded solver result without an independently checked proof certificate.

## Coverage results

| Passage | Source records, end exclusive | Broader missing training forms | Unseen heldout codes | Admission |
|---|---|---|---:|---|
| 1 | 10646–10700 | none | 0 | yes |
| 2 | 10700–10754 | none | 0 | yes |
| 3 | 10754–10808 | none | 1 | no |
| 4 | 10809–10863 | uiiii, x | 0 | no |
| 5 | 10863–10917 | atrebates | 0 | no |
| 6 | 10917–10971 | xi, uiii, uiromanduis, xii, uii | 1 | no |
| 7 | 10971–11025 | none | 2 | no |

The one-record gap before passage 4 follows the frozen structural eligibility rule. The default inventory fails training coverage in all seven passages. The five excluded cases are **not UNSAT**, and are retained in the report.

Both admitted first fits recovered 48/48 training words and 6/6 holdouts exactly: 96/96 training occurrences and 12/12 holdouts in total. Eight holdout occurrences are novel relative to their training passage; four repeat training words. Both shuffled controls were UNSAT, and both first-key exclusions were UNSAT, establishing uniqueness on the 38 and 39 observed codes within this bounded model. Unused codes remain unidentified. Positive fits took about 12 seconds end to end, almost entirely filtering and propagation; Z3 took about 4 and 2 milliseconds. All six fit/exclusion records and independent coverage audits validated; nine tests passed. This establishes recovery on two complete-coverage cases, not on all seven selected passages.

## Interpretation and next step

The method now recovers actual contiguous Latin prose under this fixed-width H2 model and full finite vocabulary. The admission rate is only 2/7. Three cases contain absent numerals or names; three require previously unseen homophones in the continuation, with one overlap. These failures would be hidden by selecting only successful passages.

Next, test a predeclared larger training context on these coverage failures and score seen-code holdouts separately from unseen-code holdouts. Preserve missing names and numerals as coverage failures rather than adding their known plaintext. This tests whether additional context improves code coverage without silently changing the dictionary or inflating recovery accuracy. Afterwards, random homophone selection on natural prose remains a useful independent extension; the current generating policy is cyclic.

These are adjacent passages from one source, with only two admitted cases. They do not establish manuscript discrimination, German-versus-Latin rankings, unknown-boundary recovery, variable code widths, or uniqueness on unused codes.

## Commands and validation

```sh
.venv/bin/python -m benchmarks.latin_h2_natural --run
.venv/bin/python -m benchmarks.latin_h2_natural --validate
.venv/bin/python -m benchmarks.latin_h2_natural_analysis
.venv/bin/python -m pytest tests/integration/test_latin_h2_natural.py tests/integration/test_compressed_candidates.py -q
```

The runner resumes stored results. Validation checks first-key decoding, finite-inventory membership, capacity, generating ciphertext, shuffled inputs, phase completion and exclusion provenance. The separate analysis independently reconstructs source selection, all seven coverage audits and unseen-code gates. Tests exercise contiguous selection and the unseen-homophone issue without changing frozen experiment code.
