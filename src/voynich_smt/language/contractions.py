"""Complete optional reversible tokenizations for a bounded explicit inventory."""
from functools import lru_cache


def validate_rules(rules):
    ids = [r['id'] for r in rules]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate contraction ID')
    for r in rules:
        if (not r['id'] or not r['id'].isascii()
                or not r['id'].replace('-', '').isalnum()
                or not r['expansion'].isalpha() or len(r['expansion']) < 2
                or r['position'] not in {'any', 'initial', 'final', 'whole'}):
            raise ValueError('Invalid contraction rule')


def expand_units(units, rules):
    validate_rules(rules)
    table = {'<'+r['id']+'>':r['expansion'] for r in rules}
    out = []
    for unit in units:
        if unit in table:
            out.append(table[unit])
        elif len(unit) == 1 and unit.isalpha():
            out.append(unit)
        else:
            raise ValueError('Unknown contraction unit')
    return ''.join(out)


def tokenizations(word, rules, max_variants=10000):
    """Return all paths, including distinct paths of equal length; never truncate."""
    validate_rules(rules)
    if not word or not word.isalpha():
        raise ValueError('Expected normalized alphabetic word')
    if type(max_variants) is not int or max_variants < 1:
        raise ValueError('Positive variant cap required')

    @lru_cache(None)
    def paths(i):
        if i == len(word):
            return ((),)
        edges = [(i+1, word[i])]
        for r in rules:
            end = i+len(r['expansion'])
            if (word.startswith(r['expansion'], i)
                    and (r['position'] not in {'initial','whole'} or i == 0)
                    and (r['position'] not in {'final','whole'} or end == len(word))):
                edges.append((end, '<'+r['id']+'>'))
        out = []
        for end, unit in edges:
            for tail in paths(end):
                out.append((unit,)+tail)
                if len(out) > max_variants:
                    raise ValueError('Complete tokenization exceeds variant cap')
        return tuple(out)

    result = paths(0)
    if any(expand_units(p, rules) != word for p in result):
        raise RuntimeError('Contraction round trip failed')
    return result


def tokenize_dictionary(words, rules, max_variants=10000):
    """No source spelling is lost: each unit word expands uniquely."""
    return tuple(sorted({p for w in words for p in tokenizations(w, rules, max_variants)}))
