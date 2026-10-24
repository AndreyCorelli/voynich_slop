from itertools import product
from dataclasses import asdict
import pytest
from tests.integration.test_segmented_recovery import request
from voynich_smt.solver.segmented import recover_with_word_lengths


def test_engines_match_feasibility_on_fixed_length_branches():
    for word in product('xy',repeat=3):
        for count in (1,2,3):
            q=request(''.join(word))
            results=[recover_with_word_lengths(q,(count,),solver_backend=b) for b in ('qffd','smt')]
            assert results[0].status==results[1].status and results[0].status!='UNKNOWN'
            assert all(r.status!='SAT' or r.verified for r in results)
            assert results[0].capacity['constraints']==results[1].capacity['constraints']
            assert results[0].capacity['formula_sha256']==results[1].capacity['formula_sha256']
            assert [r.capacity['solver_backend'] for r in results]==['qffd','smt']


def test_bad_backend_rejected_and_public_request_stays_clean():
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    q=request()
    with pytest.raises(ValueError):recover_with_word_lengths(q,(2,2),solver_backend='bad')
    with pytest.raises(ValueError):HiddenRecoveryRequest.from_dict({**asdict(q),'solver_backend':'smt'})
