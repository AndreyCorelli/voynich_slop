from dataclasses import replace
import pytest
from tests.integration.test_oov_recovery import request
from voynich_smt.solver.oov_type_recovery import recover_oov_types
from voynich_smt.solver.oov_recovery import recover_oov


def test_repeated_unknown_shares_type_budget():
    q=request('xy xy')
    assert recover_oov(q,1).status=='UNSAT'
    r=recover_oov_types(q,1)
    assert r.status=='SAT' and r.verified and r.plaintext.words[0]==r.plaintext.words[1]
    assert len({w for w in r.plaintext.words if w not in q.dictionary.words})==1
    assert recover_oov_types(q,0).status=='UNSAT'


def test_distinct_unknown_types_exceed_budget():
    q=request('xy yx')
    assert recover_oov_types(q,1).status=='UNSAT'
    assert recover_oov_types(q,2).status=='SAT'
    from voynich_smt.cipher.base import Bounds
    with pytest.raises(ValueError,match='H1'):recover_oov_types(replace(q,bounds=Bounds('verbose',2,1,1)))
