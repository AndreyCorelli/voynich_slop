"""Integer sequence scores linked to symbolic dictionary words."""
import z3


def validate_objective(spec, dictionary):
    if set(spec) != {'initial', 'transitions', 'max_checks'}:
        raise ValueError('Invalid language objective fields')
    words=set(dictionary.words)
    if set(spec['initial'])!=words or set(spec['transitions'])!={(a,b) for a in words for b in words}:
        raise ValueError('Language objective must cover every dictionary word and pair')
    if any(type(x) is not int for x in list(spec['initial'].values())+list(spec['transitions'].values())):
        raise ValueError('Language objective weights must be integers')
    if type(spec['max_checks']) is not int or spec['max_checks']<1:
        raise ValueError('Language objective check cap must be positive')


def expression(spec, dictionary_symbols, candidates, alphabet):
    matches={}
    for wi,(size,symbols) in dictionary_symbols.items():
        for word in candidates[wi]:
            matches[wi,word]=z3.And(size==len(word),
                *[symbols[i]==alphabet.index(s) for i,s in enumerate(word)])
    terms=[]
    for word in candidates[0]:
        terms.append(z3.If(matches[0,word],spec['initial'][word],0))
    for wi in range(1,len(candidates)):
        for a in candidates[wi-1]:
            for b in candidates[wi]:
                terms.append(z3.If(z3.And(matches[wi-1,a],matches[wi,b]),spec['transitions'][a,b],0))
    return z3.Sum(terms)
