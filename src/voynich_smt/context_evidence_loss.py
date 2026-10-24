"""Delete a type's occurrences only beyond a protected query prefix."""
from copy import deepcopy


def remove_suffix_type(public, opaque, protected=100):
    if not 0 <= protected <= len(public):
        raise ValueError('invalid protected prefix')
    result = deepcopy(public[:protected])
    for sentence in public[protected:]:
        result.append(dict(sentence, tokens=[deepcopy(t) for t in sentence['tokens'] if t['id'] != opaque]))
    return result
