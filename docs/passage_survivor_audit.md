# Audit of the fixed passage survivors

All candidates from the saved ten-window screen were recovered at their exact
positions. There are **25 match entries covering 19 distinct source passages**;
entries can repeat across Voynich windows, tokenizations and Latin profiles.
No additional window or candidate was selected by changing the filter.

Every reproduced source stream and candidate count matches its saved hash and
the prior screen. German evidence includes source word number, morph index,
line attributes, raw form and word XML. Dante evidence includes book segment,
paragraph index, token index and complete raw paragraph. Normalized segment
indices are not line numbers in the original manuscript.

## Audit outcomes

| Outcome | Match entries |
| --- | --- |
| No checked normalization or lexical-sensitivity flag | 19 |
| Lexical sensitivity flagged | 6 |
| Rejected by checked normalization rules | 0 |

German forms were checked against the earlier v2 marked-initial/uncertainty
rules and applicable short-form exclusions. Their outputs are projected to
the historical-length stream's letter convention for comparison. This preserves
the paired audit's spelling convention, including its treatment of umlauts;
it is not a corrected whole-corpus rescan or a proof that all lexical issues
have been resolved. No surviving candidate depends on the tested bracket
fragments. Changed source forms would reject the old candidate rather than
silently change its boundaries or record indices.

All six flagged entries come from source 123, Hans Neidhart's 1486 German
Eunuchus translation. Raw `Che`, `Par`, `Tha` and `Phe` occur in dialogue contexts
and are treated as apparent abbreviated speaker labels in an ordinary-prose
sensitivity check. This interpretation is inferred from the dramatic source
and punctuation/context, not a new authoritative expansion. Another survivor
contains raw `etc` twice, without expansion. They remain in the historical
artifact but are not accepted as fully spelled ordinary prose in this sensitivity.
No expansions or repairs are guessed, and removing labels does not preserve
the same 22-word alignment automatically.

## Remaining grouped matches

Three grouped-tokenization match entries remain without those flags:

**A-1, source 113 (Kottanner):**

```text
gnad inne lag ich erkam gar hart vnd stuend pald auf vnd eilat in den gmach do was es voller rukchs vnd
```

**S-1, source 133 (East Franconian):**

```text
vnd sich halten vnd wer es daz sy fur alle die selen die in dem fegfewr sein pete daz sie dar zw
```

**S-1, Dante, seven-unit profile:**

```text
hiis iam liquet quod ius cum sit bonum per prius in mente dei est et cum omne quod in mente dei est
```

The saved length witness for the Dante S-1 match contracts both whole-word
`est` occurrences. It expands exactly back to this spelling. This is one
length witness, not an exhaustive set of unitizations for key fitting. The
same Dante passage also appears in other atomic/profile matches; these are
not independent discoveries. Raw spelling, including `hiis`, is retained.

Both A-1 and S-1 have no repeated ciphertext words, so the equality-implication
filter is vacuous. Several candidate plaintext words repeat, which is allowed:
different homophone choices can encode the same word differently. No
source passage above has been shown to fit a shared prefix-free cipher key.
"Retained" means only that the specific normalization/sensitivity checks did
not remove it, not a complete philological certification.

The next distinct gate, if this branch is pursued, is known-passage shared-key
consistency for these three grouped candidates, with complete optional Latin
unitizations and a fixed short budget. That would test more than necessary
length bounds without another arbitrary dictionary search. No such solver
run was performed as part of this audit.

The subsequent [known-passage key gate](known_passage_keys.md) tested those
three grouped matches and returned UNSAT for all three, with independently
checkable prefix obstructions. The necessary-filter survivors are not key fits.

## Reproduction

```sh
.venv/bin/python -m benchmarks.passage_survivor_audit
.venv/bin/python -m pytest -q \
  tests/integration/test_passage_survivor_audit.py \
  tests/integration/test_cross_window_passages.py \
  tests/integration/test_eva_tokenization.py
```

The report and validation are saved under
`experiments/results/passage-survivor-audit/`. They preserve all 25 entries,
source evidence, changed/flagged records, verified expansion witnesses and
input/code hashes. **10 focused tests pass**, covering fragment rejection,
source coordinates, gaps, scopes, lexical flags and the distinction between
normalization changes and lexical sensitivity. No downloads or solver calls.
