from dataclasses import asdict
import importlib.util
from itertools import product
from pathlib import Path
import random
import sys

import pytest
from voynich_smt.cipher.base import Bounds
from voynich_smt.language.dictionary import PrefixRelation,WordDictionary
from voynich_smt.models.text import Text


def reference():
    spec=importlib.util.spec_from_file_location('prefix_pruning_reference',Path('experiments/results/prefix-pruning/reference_dictionary.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('kind',[None,'equal','left','right'])
def test_indexed_pruning_matches_pairwise_support(kind):
    rng=random.Random(4101)
    vocabulary=[p for n in range(1,5) for p in product(('a','b'),repeat=n)]
    for _ in range(100):
        a=tuple(rng.sample(vocabulary,rng.randrange(len(vocabulary)+1)))
        b=tuple(rng.sample(vocabulary,rng.randrange(len(vocabulary)+1)))
        relation=PrefixRelation(0,1,rng.randrange(6),kind)
        keep_a=tuple(x for x in a if any(relation.accepts(x,y) for y in b))
        keep_b=tuple(y for y in b if any(relation.accepts(x,y) for x in keep_a))
        assert relation.prune(a,b)==(keep_a,keep_b)


def test_complete_graph_matches_preserved_reference():
    old=reference();rng=random.Random(4102)
    words=[p for n in range(1,5) for p in product(('a','b'),repeat=n)]
    for _ in range(100):
        vocabulary=tuple(rng.sample(words,rng.randrange(1,len(words)+1)))
        cipher=Text(tuple(tuple(rng.choice('xy') for _ in range(rng.randrange(1,10))) for _ in range(rng.randrange(1,9))))
        minimum=rng.randrange(1,3);maximum=rng.randrange(minimum,4)
        bounds=Bounds('verbose',1,minimum,maximum)
        lower=rng.randrange(1,4);upper=rng.randrange(lower,5)
        assert asdict(WordDictionary(vocabulary).candidate_graph(cipher,bounds,lower,upper))==asdict(old.WordDictionary(vocabulary).candidate_graph(cipher,bounds,lower,upper))
