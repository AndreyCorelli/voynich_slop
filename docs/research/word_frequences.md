# Historical alchemy and astrology word frequencies

These are thematic comparanda, not evidence that Voynich is alchemical or written in any of these languages. Selection balances historical relevance and available transcriptions. Latin, Greek and English frequency lists must be compared separately. Original historical languages are prioritized; Mirror of Alchemy is an English supplement because a usable complete Latin transcription was not located. Latin has no articles.

## Method

Lowercase Unicode alphabetic word forms; internal apostrophes retained; no stopword filtering or lemmatization; ties alphabetically; numbers excluded. Chapter headings retained where present.

Website navigation and editorial framing excluded. Greek normalized to NFC; accents retained. Latin Turba ampersands expanded to et. Spelling and inflection preserved, including Latin u/v variants and enclitics. Counts are edition-specific. The Emerald Tablet has ties at rank 10: mundi, sic, sicut, and terram all occur 3 times; alphabetical tie-breaking selects mundi.

## Results

**Audit correction:** the original Turba incipit-to-`FINISH.` extraction includes
English prose after the Latin material. Its 33,292-token counts are therefore
mixed-language, not Latin frequencies. The raw snapshots and original generated
counts are preserved, but this row is quarantined from Latin comparisons. See
[the audited passage screen](thematic_latin_passages.md).

| Text | Language | Tokens | Top ten (word: count) |
|---|---|---:|---|
| [emerald-tablet](https://la.wikisource.org/wiki/Tabula_Smaragdina) | Latin | 161 | est: 14, et: 5, quod: 5, eius: 4, in: 4, totius: 4, a: 3, ab: 3, hic: 3, mundi: 3 |
| [grosseteste-de-sphaera](https://la.wikisource.org/wiki/De_sphaera) | Latin | 5,700 | et: 270, in: 238, est: 173, quod: 74, a: 62, cum: 57, per: 56, sol: 54, lunae: 45, uero: 44 |
| [mirror-of-alchemy](https://www.alchemywebsite.com/mirror.html) | English | 3,698 | the: 204, and: 196, of: 151, it: 84, is: 79, in: 75, to: 68, that: 67, a: 60, we: 53 |
| [turba-philosophorum](https://www.alchemy-texts.com/book/turba-philosophorum-extended-edition/) | Mixed Latin/English; quarantined | 33,292 | et: 2,252, in: 838, est: 788, quod: 658, non: 314, cum: 313, aqua: 307, donec: 296, ex: 289, hoc: 218 |
| [manilius-astronomica](https://www.thelatinlibrary.com/manilius.html) | Latin | 27,462 | et: 893, in: 597, per: 353, est: 287, nec: 219, cum: 173, quae: 163, sub: 158, non: 139, atque: 131 |
| [ptolemy-tetrabiblos](https://github.com/PerseusDL/canonical-greekLit/blob/master/data/tlg0363/tlg007/tlg0363.tlg007.perseus-grc2.xml) | Greek | 38,027 | καὶ: 2,839, τῶν: 1,296, δὲ: 1,277, τοῦ: 1,046, τῆς: 812, τὸ: 726, μὲν: 648, ἢ: 593, τὴν: 506, τῷ: 475 |

## Editions and relevance

- **emerald-tablet**: Alchemical microcosm/macrocosm text; medieval Latin version of an Arabic tradition. Very short and transcription has uncertain editorial provenance; use as a small control.
- **grosseteste-de-sphaera**: Early thirteenth-century celestial-sphere treatise. Astronomy rather than divinatory astrology; useful for zodiac, solar and lunar vocabulary. Baur edition via Wikisource.
- **mirror-of-alchemy**: Alchemical manual attributed to Roger Bacon, attribution uncertain; English text from the 1597 edition, as transcribed by Adam McLean. Count begins with chapter I prose.
- **turba-philosophorum**: Medieval alchemical dialogue, Arabic-derived and circulating in Latin by the twelfth century. The original extraction begins at the Latin section but runs into later English prose. This is a compilation of recensions and related exercises, not a single medieval witness; transcription provenance and OCR accuracy are uncertain. Counts are quarantined, and unresolved abbreviations are not expanded speculatively.
- **manilius-astronomica**: First-century CE Latin astrological poem; all five books. Relevant to zodiac and planetary lore, but verse differs from recipe prose.
- **ptolemy-tetrabiblos**: Second-century CE astrological work. Original Greek from the Perseus TEI corpus, edited by F. E. Robbins (1940), all four books. TEI notes and publication metadata excluded; chapter headings retained. Greek accents and breathings retained and normalized to NFC; no lemmatization or accent removal.

## Reproduction

Run `.venv/bin/python benchmarks/historical_word_frequencies.py data/raw/historical-comparanda`. Downloaded HTML snapshots, extracted text and JSON counts are retained in the repository. Accessed 2026-10-09.

The [equal-window repetition analysis](word_repetition.md) now uses these
hash-checked snapshots alongside the existing corpora. It distinguishes
repetition amount from exact placement and documents the frequency extractor's
boundary limitations before these texts are used for passage screening.
