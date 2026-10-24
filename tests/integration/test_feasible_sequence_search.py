from dataclasses import asdict

import pytest

from benchmarks.feasible_sequence_search import integer_score,weights
from voynich_smt.cipher.base import Bounds
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.recovery import _recover


def fixture():
    dictionary=WordDictionary.from_strings(('a','b'))
    spec={'initial':{('a',):0,('b',):0},
          'transitions':{(('a',),('a',)):0,(('a',),('b',)):10,
                         (('b',),('a',)):0,(('b',),('b',)):0},'max_checks':3}
    return dictionary,spec


def solve(spec):
    dictionary,_=fixture()
    return _recover(None,Text.from_string('x y'),Alphabet(tuple('ab')),Alphabet(tuple('xy')),
        Bounds('verbose',1,1,1),1000,dictionary=dictionary,max_word_length=1,language_objective=spec)


def test_shared_key_feasible_objective_reaches_proved_optimum():
    _,spec=fixture();r=solve(spec)
    assert r.status=='SAT' and r.verified and r.plaintext==Text.from_string('a b')
    objective=r.capacity['language_objective']
    assert objective['score']==10 and objective['optimality_proven']
    scores=[s['score'] for s in objective['checks'] if s['status']=='SAT']
    assert all(a<b for a,b in zip(scores,scores[1:]))
    assert integer_score(r.plaintext.words,spec)==10


def test_one_check_returns_feasible_incumbent_without_optimality_claim():
    _,spec=fixture();spec['max_checks']=1;r=solve(spec)
    assert r.verified and r.status=='SAT'
    assert len(r.capacity['language_objective']['checks'])==1
    assert not r.capacity['language_objective']['optimality_proven']


def test_incomplete_score_tables_rejected():
    _,spec=fixture();spec['transitions'].pop((('a',),('b',)))
    with pytest.raises(ValueError,match='every dictionary word and pair'):solve(spec)


def test_unknown_improvement_retains_verified_sat_incumbent(monkeypatch):
    import voynich_smt.solver.recovery as recovery
    original=recovery.z3.Tactic
    class Interrupted:
        def __init__(self,inner):self.inner=inner;self.calls=0
        def __getattr__(self,name):return getattr(self.inner,name)
        def check(self,*args):
            self.calls+=1
            return self.inner.check(*args) if self.calls==1 else recovery.z3.unknown
        def reason_unknown(self):return 'forced improvement interruption'
    class Tactic:
        def __init__(self,name):self.name=name
        def solver(self):return Interrupted(original(self.name).solver())
    monkeypatch.setattr(recovery.z3,'Tactic',Tactic)
    _,spec=fixture();r=solve(spec)
    assert r.status=='SAT' and r.verified
    trace=r.capacity['language_objective']
    assert [step['status'] for step in trace['checks']]==['SAT','UNKNOWN']
    assert not trace['optimality_proven']
    assert trace['score']==integer_score(r.plaintext.words,spec)
