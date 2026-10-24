# Compact exact Latin inventory membership

| Inventory | Words | States | Transitions | Shared SMT table build |
|---|---:|---:|---:|---:|
| Default | 2,550,580 | 10,727 | 49,792 | 1.10 s |
| Broader | 6,327,182 | 29,087 | 129,820 | 2.88 s |

Automaton construction takes 2.39/6.27 seconds. Exact whole-inventory checks take
5.36/15.17 seconds; every inventory word and all 6,759 frozen query/control types
match, with no disagreements. Two tests and two-mode artifact validation pass.
The broader inventory additionally contains `w`; its prototype alphabet has 24
letters versus 23 default letters. This is recorded explicitly without changing
earlier cipher alphabets.

The prototype represents each generated finite inventory as a suffix-sharing
minimal acyclic deterministic word automaton, rather than enumerating millions
of alternatives per observation. Existing strict and OOV recovery solvers remain
unchanged. No cipher recovery is attempted in this experiment.

The builder streams lexically sorted words, retaining the current prefix frontier
and interning identical finalized suffix subgraphs. State zero is a rejecting
sink; missing transitions go there. Child states precede parents, so dynamic
programming counts the accepted finite language exactly. Terminal states can
accept one word while continuing to longer words. This is exact set membership,
not a new approximation or morphology expansion.

A separate SMT prototype builds shared constant transition and accepting arrays.
Transition indices are `state * alphabet_size + symbol_index`. Every bounded word
traverses the same tables; active positions must be letters, unused positions must
be the sentinel, and the final state must accept. Word size must be positive and
within the provided slot bound. Alphabet comes from every inventory transition;
forms outside the old cipher alphabet are retained, not silently filtered.

Small exhaustive tests compare the automaton with an explicit finite word set,
check accepted-language count and invalid input ordering. A symbolic XOR check
proves SMT membership equivalent to flat membership for a toy vocabulary across
all assignments, including padding and out-of-range sizes. It also finds a
symbolic accepted word with constrained initial letter.

Large-inventory checks verify every generated spelling, compare the automaton's
accepted-language count with exact inventory size, and compare exact lookup on
all frozen query types plus deterministic anagram controls. Count equality plus
inclusion of every inventory spelling establishes finite-language equivalence,
without enumerating all possible nonwords. This relies on the independently
checked acyclic graph structure; duplicate/missing/extraneous finite words would
violate inclusion or count equality.

The representation remains canonical i/u and inherits the morphology inventory's
broad theoretical forms and known source limitations. A smaller graph improves
construction scale, but does not guarantee easy symbolic cipher search. Constant
array reasoning may still be expensive, and millions of accepted forms can still
admit incorrect explanations. Standalone table construction is not a recovery
time measurement or a demonstration of manuscript compatibility.

```sh
.venv/bin/python -m benchmarks.latin_compact_membership --run
.venv/bin/python -m benchmarks.latin_compact_membership --validate
```

Artifacts: `experiments/results/latin-compact-membership/` saves source/code
identity, compressed automata/hashes, word/state/edge counts, exact checks,
construction measurements and validation. Completed modes skip on resume.
Two integration tests cover finite language, suffix sharing, invalid input and
symbolic membership equivalence. Artifact validation rehashes automata and
rechecks every inventory word, language count and query/control membership.

The next step is a bounded standalone symbolic-membership performance check on
these full tables, before integrating with cipher recovery. Default encoding
semantics and earlier experiment hashes remain preserved.
