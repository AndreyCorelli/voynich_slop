"""Seeded word-level surrogates with explicitly audited preserved properties."""
from collections import Counter
import random


def _position(index, length):
    return 'single' if length == 1 else 'first' if index == 0 else 'last' if index == length - 1 else 'interior'


def make_control(segments, *, kind, seed):
    rng = random.Random(seed)
    segments = tuple(tuple(s) for s in segments)
    if any(not isinstance(w, str) or not w for s in segments for w in s):
        raise ValueError('Controls require nonempty words without UNKNOWNs')
    result = [list(s) for s in segments]
    if kind == 'within-segment-shuffle':
        for segment in result:
            rng.shuffle(segment)
    elif kind == 'position-shuffle':
        slots = {}
        for i, segment in enumerate(result):
            for j, _ in enumerate(segment):
                slots.setdefault(_position(j, len(segment)), []).append((i, j))
        for positions in slots.values():
            words = [result[i][j] for i, j in positions]
            rng.shuffle(words)
            for (i, j), word in zip(positions, words):
                result[i][j] = word
    elif kind == 'bigram-surrogate':
        result = []
        for segment in segments:
            if not segment:
                result.append([])
                continue
            start, end = object(), object()
            words = [start, *segment, end]
            outgoing = {}
            for a, b in zip(words, words[1:]):
                outgoing.setdefault(a, []).append(b)
            for edges in outgoing.values():
                rng.shuffle(edges)
            stack, reverse = [start], []
            while stack:
                edges = outgoing.get(stack[-1])
                if edges:
                    stack.append(edges.pop())
                else:
                    reverse.append(stack.pop())
            path = list(reversed(reverse))
            if path[0] is not start or path[-1] is not end or len(path) != len(words):
                raise ValueError('Invalid surrogate Euler path')
            result.append(path[1:-1])
    else:
        raise ValueError('Unknown word control')
    result = tuple(tuple(s) for s in result)
    audit = control_audit(segments, result)
    if not audit['same_unigrams'] or not audit['same_segment_lengths']:
        raise ValueError('Control violated base preservation constraints')
    if kind == 'position-shuffle' and not audit['same_position_unigrams']:
        raise ValueError('Position control changed positional counts')
    if kind == 'bigram-surrogate' and not audit['same_segment_bigrams']:
        raise ValueError('Bigram surrogate changed edge counts')
    return result, {'kind': kind, 'seed': seed, 'version': 1, **audit,
                    'scope': 'matched surrogate; not proof of non-language or impossible cipher'}


def control_audit(original, control):
    def unigrams(stream):
        return Counter(w for s in stream for w in s)
    def positions(stream):
        return Counter((_position(i, len(s)), w) for s in stream for i, w in enumerate(s))
    def bigrams(segment):
        # Tagged values avoid conflating reserved strings with actual words.
        words = [('bos',), *(('word', w) for w in segment), ('eos',)]
        return Counter(zip(words, words[1:]))
    return {'same_unigrams': unigrams(original) == unigrams(control),
        'same_segment_lengths': tuple(map(len, original)) == tuple(map(len, control)),
        'same_position_unigrams': positions(original) == positions(control),
        'same_segment_bigrams': len(original) == len(control) and all(
            bigrams(a) == bigrams(b) for a, b in zip(original, control)),
        'changed_tokens': sum(a != b for sa, sb in zip(original, control) for a, b in zip(sa, sb))}
