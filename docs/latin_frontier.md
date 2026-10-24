# Wider Latin vocabulary and deterministic homophone cycles

The five-word EVA sample is explainable under the wider tested models. The earlier
32-word UNSAT result does not survive vocabulary expansion. This is a verified
encoding of a short sample under dictionary membership, not a decipherment or a
measurement of the probability that the manuscript is Latin.

## What changed

Public requests now accept an optional selection policy:

```json
"selection": {"mode": "cycle", "reset": "text"}
```

The default is `{"mode":"free","reset":"text"}`, preserving earlier behavior.
Free selection allows any legal homophone at each occurrence. Cycling maintains a
separate counter for each plaintext letter. Its first occurrence uses code 0, the
next code 1, and so on modulo its actual number of codes. The order of those codes
is inferred. Counters continue across spaces with `reset: text`; `reset: word`
restarts them at each word. Nulls do not advance counters. The same rules are used
by generation, recovery, and independent verification, including optimized/null
models.

Lexical ordering of homophones is a valid symmetry break for free selection, but
would exclude valid cyclic orders. It is disabled for cycling. Constant-divisor
modulo constraints count recovered plaintext symbols, ignoring inactive dictionary
padding slots. Exhaustive independent tiny oracles check both one- and two-letter
cycles; tests also cover non-lexical orders, resets, symbolic plaintext, nulls,
optimization, and serialized generation/replay.

Text-wide cycles require uninterrupted source words in this runner. Skipping
unreadable words or rearranging selected source words would change the unknown
counter phases. The selected f1r sample has consecutive source records 0–4.
Controls are explicit newly constructed sequences, encoded as their own streams.

## Fixed assumptions and stages

The observed sample remains `fachys ykal ar ataiin shol`: five words, 22 EVA
character units. Cipher codes are globally prefix-free; spaces are preserved;
nulls and contextual code mappings are disabled. The plaintext alphabet has 24
symbols, with u/v distinct, and the cipher alphabet contains the 25 eligible EVA
character units from the acquired corpus. EVA character units are the declared
analysis convention. Physical manuscript glyph boundaries have not been modeled;
code boundaries may split conventional multi-character EVA groups.

The raw surface vocabulary grows in source order from 32 to 128 to 512 to all
5,675 distinct eligible Caesar tokens. Then the maximum homophone count grows
from 1 to 2 to 3, followed by maximum code length 2 to 3. Each stage changes one
bound; minimum code length remains 1. Free and text-wide cycling use the same
observed and generated ciphertexts at every stage. With at most one code per
letter the two selection policies describe the same family.

Each setting receives three cyclic synthetic ciphertexts (seeds 7, 17, 1729), the
Voynich sample, and two fixed controls: within-word and global frequency-preserving
shuffling. All controls have the same word lengths, token count, and token histogram
as the Voynich sample. Synthetic plaintext comes from seeded windows after public
vocabulary and length<=6 filtering. It matches word count, dictionary, alphabets,
and cipher bounds, but its ciphertext token lengths differ. Such filtered windows
are not a guarantee of grammatical sentences. Private truth is stored separately;
recovery reloads only public requests.

Inspection of the first 512-token fit found `p`, originating from the initial `P.`
in the corpus. A second configuration permits only `a`, `e`, `i`, and `o` as
single-letter words. This excludes ten single-letter surface tokens and leaves
5,665 full-vocabulary entries. It is an explicit heuristic: other names, numerals,
abbreviations, and possible source errors remain. No lexical or grammatical
validator has been added. The filtered sweep begins at 512 words and otherwise
follows the same bound relaxations. Its first 512 entries are selected after the
filter, so its vocabulary differs from the raw 512-entry variant.

## Observed frontier

| Raw vocabulary | Maximum homophones | Maximum code length | Free selection | Text-wide cycle | All three synthetic gates passed, free / cycle |
| --- | --- | --- | --- | --- | --- |
| 32 | 1 | 2 | UNSAT | UNSAT | yes / yes |
| 128 | 1 | 2 | UNSAT | UNSAT | yes / yes |
| 512 | 1 | 2 | SAT | SAT | yes / yes |
| 5,675 | 1 | 2 | SAT | SAT | no / no |
| 5,675 | 2 | 2 | SAT | SAT | no / no |
| 5,675 | 3 | 2 | SAT | SAT | no / no |
| 5,675 | 3 | 3 | SAT | UNKNOWN; prior witness still fits | no / no |

The filtered variant returned independently verified SAT for Voynich at every
stage: 512/H1/L2, then 5,665/H1/L2, H2/L2, H3/L2, and H3/L3, under both policies.
Its 512-word setting passed all three synthetic gates under both policies; the
full-vocabulary settings did not.

Both controls were UNSAT at raw width 32, SAT at width 128, and SAT at width 512.
They were SAT at the wider settings except two filtered H3/L3 cyclic checks that
timed out; their previously verified narrower explanations also satisfy H3/L3.
These observations do not establish statistical separation between text categories.
The vocabulary order, tiny sample, single control seed, and two control forms limit the comparison.

Across both sweeps, **144 solver checks** completed: 96 SAT, 8 UNSAT, and 40
UNKNOWN. Every SAT explanation independently encoded and decoded correctly. Of
72 synthetic checks, 35 returned verified SAT and 37 timed out; none returned
UNSAT. Full-vocabulary recovery is therefore not reliably calibrated at this
budget. The configured Z3 timeout is ten seconds; tactic preprocessing can exceed
it, and construction time is recorded separately. Observed UNKNOWN checks took
up to approximately 16.2 seconds, with construction up to approximately 9.0 seconds.
Some evaluations ran concurrently on the recorded machine; these times are
observations rather than controlled timing comparisons.

A timeout in a relaxed model does not erase an existing witness. The report keeps
`result.status: UNKNOWN` and its reason, then separately records
`inherited_feasibility` when an earlier explanation passes independent checks
against the new public request. This checks dictionary membership, word lengths,
alphabets, prefix-freeness, code bounds, selection policy, and exact encode/decode.
Three timed-out real/control cases carry these certificates. A later UNSAT that
conflicts with such a verified witness triggers an error. Synthetic gate flags
continue to require successful direct recovery for all three seeds.

## A concrete cyclic fit

The filtered full vocabulary with at most two homophones and maximum code length
2 produced `lacu cur i geri una`. Its inferred codes reproduce the sample:

| Dictionary word | Selected codes, in order | Ciphertext |
| --- | --- | --- |
| lacu | f · ac · hy · s | fachys |
| cur | y · k · al | ykal |
| i | ar | ar |
| geri | at · ai · i · n | ataiin |
| una | s · ho · l | shol |

Cycling alternatives are a: `ac, l`; c: `hy, y`; i: `ar, n`; r: `al, i`; and
u: `s, k`. Thus the three appearances of u select `s, k, s`. Every other letter
in this explanation has one code. The complete recovered codebook also includes
legal mappings for unused alphabet symbols. This is a five-word witness under
the language constraint, not a proposed translation or a verified Latin sentence.

The filtered 512-word cyclic fit was `vel ius ut unam hoc`, using only one code
per letter. These examples show that broadening the finite vocabulary alone can
remove the original contradiction. Multiple cycling homophones are also feasible,
but are not necessary for the tested sample under the wider word-list constraints.
No minimum code length, score, or historically plausible complexity was proved.
Selector counters are reported separately; the current weighted score does not
price selector state.

## Reproduction and artifacts

```sh
uv run python benchmarks/latin_frontier.py
uv run python benchmarks/latin_frontier.py \
  --config experiments/configs/latin-frontier-lexical.json \
  --output experiments/results/latin-frontier-lexical.json \
  --artifact-dir data/generated/latin-frontier-lexical
uv run voynich-smt compare experiments/results/latin-frontier.json \
  experiments/results/latin-frontier-lexical.json
uv run voynich-smt solve \
  data/generated/latin-frontier-lexical/inputs/vall-h2-l2/cycle-text-voynich.json \
  --output experiments/results/cyclic-witness-replay.json
uv run pytest -q
```

The default configuration is `experiments/configs/latin-frontier.json`. Use
`--stages NAME ...` to select stages and `--resume` to retain completed checkpoints.
Resume verifies configuration, source/sample identities, and environment; partial
stages are rerun. Reports record selected stage names, exact dictionary checksums,
source checksums, controls, policies, solver outcomes, construction time, and
synthetic gate flags. Public inputs and private truth are under separate
`inputs/` and `ground_truth/` directories in the artifact root. All generated data
remain local and excluded from version control. Replays may find equivalent fits.

The suite passes **292 tests**. The next useful experiment is to fit larger,
contiguous samples and test a recovered key on subsequent text with its cycle
state carried forward. Alternative explicit EVA unit groupings, stronger Latin
constraints, and reliable full-vocabulary synthetic recovery are needed before
interpreting these fits as evidence about manuscript language.
