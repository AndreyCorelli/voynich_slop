# Raw corpora

Store immutable downloaded source files and provenance manifests here. See
`docs/data_acquisition.md`. The initial local sources are `ZL3b-n.txt` and `pg218.txt`, each with a checksum
manifest. Raw files and manifests are excluded from version control.
Use `voynich-smt corpus fetch`; cached originals are verified and never overwritten.

The independent English restoration benchmark adds a pinned CMUdict cache and
held-out Wells text under `scalable-english-independent/`, with hashes and
source/license notices. The [benchmark report](../../docs/scalable_english_independent.md)
documents extraction, frozen-resource ordering and evaluation-only coverage audits.
