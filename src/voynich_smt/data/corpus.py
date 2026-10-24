"""Versioned corpus artifacts, exact samples, and ordinary Python statistics."""
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random

from voynich_smt.models.text import Text


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


@dataclass(frozen=True)
class Corpus:
    kind: str
    source: dict
    normalization: dict
    records: tuple[dict, ...]
    format_version: int = 1

    @property
    def identity(self):
        return digest(asdict(self))

    def save(self, path):
        write_json(path, asdict(self))

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('format_version') != 1:
            raise ValueError('Unsupported corpus format')
        return cls(data['kind'], data['source'], data['normalization'], tuple(data['records']))

    def sample(self, words, *, offset=0, seed=None, folio=None, section=None, line=None, max_tokens=None):
        if type(words) is not int or words <= 0 or type(offset) is not int or offset < 0:
            raise ValueError('Sample words must be positive and offset nonnegative')
        if max_tokens is not None and (type(max_tokens) is not int or max_tokens <= 0):
            raise ValueError('Token budget must be positive')
        if seed is not None and offset:
            raise ValueError('Random selection cannot also specify an offset')
        candidates = [(i, r) for i, r in enumerate(self.records) if r['tokens']
                      and (folio is None or r.get('folio') == folio)
                      and (section is None or r.get('section') == section)
                      and (line is None or r.get('locus') == line)]
        if seed is not None:
            random.Random(seed).shuffle(candidates)
        chosen = candidates[offset:offset + words]
        if len(chosen) != words:
            raise ValueError('Insufficient eligible corpus words')
        if max_tokens is not None:
            bounded, count = [], 0
            for entry in chosen:
                size = len(entry[1]['tokens'])
                if count + size > max_tokens:
                    break
                bounded.append(entry)
                count += size
            chosen = bounded
            if not chosen:
                raise ValueError('First complete word exceeds token budget')
        text = Text(tuple(tuple(r['tokens']) for _, r in chosen))
        metadata = {'corpus_sha256': self.identity, 'source': self.source,
                    'normalization': self.normalization,
                    'selection': {'words': words, 'offset': offset, 'seed': seed,
                                  'folio': folio, 'section': section, 'line': line,
                                  'max_tokens': max_tokens, 'whole_words_only': True},
                    'record_indices': [i for i, _ in chosen],
                    'locations': [{k: v for k, v in r.items() if k not in {'tokens', 'raw', 'annotations'}}
                                  for _, r in chosen], 'text': asdict(text)}
        metadata['sample_sha256'] = digest(metadata)
        return text, metadata


def statistics(text):
    glyphs = Counter(g for w in text.words for g in w)
    vocabulary = Counter(text.words)
    lengths = Counter(map(len, text.words))
    pairs = Counter((a, b) for w in text.words for a, b in zip(w, w[1:]))
    total = text.size
    entropy = -sum((n / total) * math.log2(n / total) for n in glyphs.values()) if total else 0
    outgoing = Counter()
    for (a, _), n in pairs.items():
        outgoing[a] += n
    pair_total = sum(pairs.values())
    conditional = -sum(n / pair_total * math.log2(n / outgoing[a])
                       for (a, _), n in pairs.items()) if pair_total else 0
    return {'words': len(text.words), 'tokens': total, 'vocabulary': len(vocabulary),
            'glyph_counts': dict(sorted(glyphs.items())),
            'word_length_counts': dict(sorted(lengths.items())),
            'word_counts': [{'tokens': list(w), 'count': n} for w, n in sorted(vocabulary.items())],
            'glyph_entropy_bits': entropy, 'within_word_conditional_entropy_bits': conditional,
            'within_word_bigram_counts': [{'tokens': list(p), 'count': n} for p, n in sorted(pairs.items())]}
