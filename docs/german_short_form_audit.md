# Audit of short forms in the source-133 witness

The user-run sensitivity test returned **UNSAT in 5.55 seconds** after
excluding both `k` and `x`. The original full-block SAT therefore depends on
allowing at least one of these unexplained entries. This is stronger than
observing that one witness happens to use `k`: no fit exists under the
same bounded model when both entries are removed.

The [saved result](../experiments/results/german-133-without-k-x-30min.json)
and [validation](../experiments/results/german-133-without-k-x-validation.json)
check that only these two dictionary entries and the timeout differ from
the original SAT request. The ciphertext, original plaintext alphabet and
all cipher rules remain fixed. The original SAT witness re-verifies.
UNSAT remains solver-reported, without an independently checked proof
certificate. The test does not establish whether `k`, `x`, or either one
individually is necessary, nor does it exclude German generally.

The 30-word SAT witness uses `k` at positions 7 and 23. All four source
occurrences of `k` and both occurrences of `x` belong to two repeated
`k x k` sequences in prayer instructions. They are retained source text,
not entries inside excluded editorial XML elements, but their ordinary
lexical status and intended expansion are unestablished. Treating them as
unqualified German dictionary words weakens the linguistic interpretation
of this SAT result.

The audit does not identify an expansion, declare the forms a transcription
error, or retroactively invalidate the mathematical SAT certificate. It
separates source attestation from lexical interpretation.

## Source evidence

The XML member is `XML/133.xml` in the cached Bonner corpus archive. `k`
appears at word numbers 5908, 5910, 6030 and 6032; `x` at 5909 and 6031.
They share running lines 589 and 600 on corpus page 182. Their contexts
include `pater noster`, `heb ... an`, `k x k` and `vater vnser`.

The alternative one-letter form `o` occurs five times, including `O wye ...`
contexts supporting an interjection. It is retained. `aue` occurs six times
in prayer contexts including `aue Maria`; it is a source-spelled form, not
an inserted normalization artifact.

All 18 audited short forms (witness forms of at most three letters, plus
the complete one-letter inventory) trace to retained source `morph` elements.
The audit reproduces the original vocabulary's complete occurrence counts,
records raw forms, word numbers, line context, annotations and grouped morph
forms, and checks the XML hash against the vocabulary manifest.

Some short forms occur both independently and as separate morph children
grouped within one `wortform`. The corpus's
[documentation, section 4.2](https://korpora.org/FnhdC/Dokumentation.html#Raute)
explains that these can represent separately written parts grouped as one
annotated unit. That structure alone does not establish a normalization
error. Likewise, an annotation type of `unbekannt` is not sufficient evidence
that a form is an artifact; many ordinary function words have that annotation.

The machine-readable evidence is
[german-short-form-audit.json](../experiments/results/german-short-form-audit.json).

## Conservative sensitivity variant

A separate input excludes only `k` and `x`, leaving 2,423 of 2,425 words and
retaining `o` as the sole one-letter entry. It preserves the original plaintext
alphabet, all 30 ciphertext words, free selection and every cipher setting.
No speculative expansions or new contractions are introduced. Original
requests and results remain intact.

The existing witness fails dictionary membership under this variant because
it uses `k` twice. That does not establish UNSAT: a new key and plaintext may
still fit. The subsequent user-run solve excludes that possibility within
the fixed model, as recorded above. No Z3 call was made during the provenance
audit itself.

```sh
.venv/bin/python -m benchmarks.german_short_form_audit
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-short-form-audit/133-without-k-x.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-133-without-k-x-30min.json
```

Tests cover provenance traversal excluding editorial/annotation content,
retained separate morph forms and nested names in context, exact real
occurrence counts, repeated prayer-sequence evidence, dictionary-only
replacement, absence of added words, preservation of `o`, rejected original
witness membership and preparation without solver calls.
