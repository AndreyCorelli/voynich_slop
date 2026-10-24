from dataclasses import asdict,replace
import pytest
from voynich_smt.solver.oov_recovery import recover_oov
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.cipher.base import Bounds


def request(words):
    return HiddenRecoveryRequest(Text.from_string(words),Alphabet(tuple('ab')),Alphabet(tuple('xy')),Bounds('verbose',1,1,1),WordDictionary.from_strings(('a',)),timeout_ms=1000,max_word_length=2)


def test_oov_budget_and_empty_candidate_domain():
    q=request('xy')
    assert recover_oov(q,0).status=='UNSAT'
    r=recover_oov(q,1)
    assert r.status=='SAT' and r.verified
    assert sum(w not in q.dictionary.words for w in r.plaintext.words)==1
    q=request('xy xy')
    assert recover_oov(q,1).status=='UNSAT'
    assert recover_oov(q,2).status=='SAT'


def test_count_is_actual_membership_not_free_exemption():
    r=recover_oov(request('x'),1)
    assert r.status=='SAT' and r.verified
    with pytest.raises(ValueError):recover_oov(request('x'),-1)
