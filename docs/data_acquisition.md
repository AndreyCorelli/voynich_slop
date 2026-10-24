# Corpus acquisition policy

Follow milestone 3 in TODO.md: establish synthetic solver behavior before using
real manuscript data. The selected initial sources are Zandbergen–Landini EVA 3b and Project Gutenberg
Caesar eBook 218. See [the corpus milestone](corpus_milestone.md) for exact checksums,
normalization policies, source links, and reproduction commands.

For each download, retain original bytes in `data/raw/` and record source URL,
title, provider, transcription/version, retrieval time in UTC, SHA-256 checksum,
and license or redistribution terms in a provenance manifest. Public accessibility
alone does not establish permission to redistribute.

Choose an established machine-readable EVA transcription. Preserve folio and line
IDs, spaces, uncertain readings, and transcription conventions. EVA letters are
transcription symbols; do not silently treat them as independent manuscript glyphs.
Document tokenization explicitly, including multi-character EVA conventions.

Choose a public-domain Latin text with a traceable edition. Preserve originals.
Record lowercasing, punctuation removal, j/i and u/v conventions, alphabet
restriction, and spacing policy as explicit normalization settings.

Processed outputs reference the raw checksum and normalization configuration.
Samples record source version, exact folio/line or token offsets, selection rule,
and seed when randomized. Generated controls record their seed and generator
configuration. Do not commit downloaded corpora until redistribution terms and
repository size have been evaluated.
