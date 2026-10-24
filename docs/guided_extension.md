# Extending the L3 suffix key

The recovered 11-word key does not extend unchanged to the original 23-word
prefix. The guided search holds the vocabulary, H2/L3 bounds, alphabets, word
boundaries and text-wide cycles fixed. Every attempt includes **all 23 original
words**; the preceding 12 words are never solved as an independent reset block.

The final schedule completed **17 checks**: 12 conditional UNSAT results and five
UNKNOWN results. It found no full-prefix SAT witness. The five UNKNOWN stages
retain four, three, two, one and zero mappings respectively; each check reached
the requested 30-second budget. Releasing every mapping therefore leaves the
same bounded family unresolved.

| Guided stage | Result | Check time |
| --- | --- | ---: |
| Complete suffix key fixed exactly, 24 letters | UNSAT | 0.80 s |
| Only `e` held fixed, rotations allowed | UNSAT | 0.74 s |
| Fourteen observed mappings, rotations allowed | UNSAT | 0.72 s |
| Release `e`, thirteen mappings retained | UNSAT; core `r,t` | 0.73 s |
| Release `e,r`, twelve mappings retained | UNSAT; core `f,u,v` | 0.75 s |
| Release all fourteen observed mappings | UNKNOWN | 30.08 s |

## A concrete necessary key change

The suffix witness assigns `e` two homophones, `y` and `qo`. Before any ambiguous
internal occurrence, the full prefix forces these appearances:

| Word index (zero-based) | Ciphertext word | Forced code for `e` |
| --- | --- | --- |
| 1 | qopal | qo |
| 5 | ycheor | y |
| 8 | qotcham | qo |
| 11 | qocheor | qo |

A pinned prefix-free code matching the beginning of a word must be its first
complete codeword. Other words in this interval contain neither homophone,
and these occurrences have no possible intervening appearances of `e`.
The sequence `qo, y, qo, qo` fails both possible cyclic orders. The complete
homophone set must therefore change; rotating it or changing other mappings
cannot repair this particular key.

An independent one-mapping SMT check confirms UNSAT with only this mapping held
fixed. Its input and result are in `data/generated/guided-refinement/inputs/`
(`single-pin-e-certified.json`) and `experiments/results/e-pin-proof.json`.
The check took 0.70 seconds after construction. This excludes a key restriction,
not the broader H2/L3 family.

There are vocabulary obstacles too: with `r -> cth` and `t -> ol`, `cthol`
uniquely decodes to `rt`, which is absent from the dictionary. At least one of
these mappings must change. The full suffix key also decodes `dam` as `fuv`,
which is absent. These complete decodings remain forced while their code owners
are pinned, regardless of homophone order or changes to other letters.

## Search procedure and semantics

The runner first fixes the complete recovered key exactly. It then frees the
ten arbitrary mappings completed for letters unused in the suffix, keeping the
14 observed letters' mappings. These retained homophone lists may rotate so
the suffix's original zero-start phase does not incorrectly reject an extension.

After a failing stage, it releases one remaining mapping. It prioritizes a
certified cycle obstruction, then a certified vocabulary obstruction, then an
SMT assumption core. Ties favor mappings used least often in the suffix.
UNKNOWN supplies no core; remaining releases then use the stated heuristic.
A core is not assumed minimal, and releasing one of its mappings is not claimed
to repair the fit. The final stage has no pinned mappings.

The source key and suffix plaintext are also submitted through Z3's initial-value
API as heuristic suggestions. They are not equations, and this tactic is not
promised to honor them. The suffix plaintext remains free to change. A returned
SAT model must re-encode and decode the **whole prefix**, satisfy vocabulary,
bounds and global cycles, and preserve every mapping still pinned at that stage.

Conditional UNSAT results reject only their pinned submodel. A whole-prefix SAT
result is also a valid witness for the unrestricted family. An unrestricted
UNKNOWN remains unresolved. A zero-pin UNSAT would exclude the original bounded
model; none of the previous timeout results establishes that exclusion.

## Implementation

`solver/guided.py` adds a separate guided recovery API rather than admitting keys
or plaintext into ordinary hidden requests. Replay files are explicit wrappers:

```text
request: unchanged public language/cipher assumptions and the full ciphertext
guidance: candidate key, pinned letters, rotation flag and heuristic hints
```

Per-letter pin assumptions allow UNSAT core extraction. Pinned code counts and
intervals are constrained together. Existing unused-code simplifications are
suspended for potential pin owners: exact pins may contain unused letters or
unvisited alternatives, which must retain their mappings. Remaining prefix-tree
capacity reserves a completion for every zero-count letter without double-counting
already pinned dormant mappings. Independent SAT verification checks pins too.

Two conservative pruning rules encode the independently justified cycle and
vocabulary obstructions above. Cycle inference stops at the first internal raw
occurrence, whose segmentation might be ambiguous. The cycle rule is restricted
to text-wide resets; a word-reset request does not receive it. Vocabulary rules
are conditional on **all** owners of a completely decoded word remaining pinned.
These rules do not restrict an unrelated free mapping.

Tests compare guided outcomes with exhaustive tiny keys and cyclic plaintexts,
check the returned pin cores by re-solving them, and cover rotated orders,
unused mappings, unvisited homophones, full-context counters, conditional decoding
rules, word-reset safety and wrapper replay. Runner tests check mapping release,
complete-prefix verification, unchanged hypotheses, UNKNOWN and resume identity.

## Reproduction

```sh
uv run python benchmarks/guided_extension.py \
  --artifact-dir data/generated/guided-extension-certified
uv run python benchmarks/guided_extension.py --resume
uv run python benchmarks/guided_extension.py \
  --replay data/generated/guided-refinement/inputs/single-pin-e-certified.json
uv run pytest -q
```

Configuration is `experiments/configs/guided-extension.json`, and the main report
is `experiments/results/guided-extension.json`. Inputs for the latest run are
under `data/generated/guided-extension-certified/inputs/`. Each result records
its exact pins, rotation policy, source input checksum, core, requested heuristic
values, timing and independent verification status.

The first exploratory release sequence remains in
`experiments/results/guided-extension-first.json`; a follow-up sequence that
prioritized the cycle certificate is in `experiments/results/guided-refinement.json`.
These retain their original inputs and timeouts. They are separate schedules
under the same scientific assumptions. Synthetic full-vocabulary hidden recovery
remains incomplete as documented in [the L3 milestone](l3_conflict.md).

The full regression suite passes **340 tests**. Wrapped one-pin replay also
returns UNSAT with core `e`, and completed checkpoint resume reuses the saved run.
