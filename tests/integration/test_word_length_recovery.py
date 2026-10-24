from dataclasses import asdict
from itertools import product
import pytest
from tests.integration.test_segmented_recovery import request
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.segmented import recover_segmented, recover_with_word_lengths, validate_word_lengths


def test_known_lengths_preserve_symbolic_boundaries_and_public_contract():
    q=request()
    result=recover_with_word_lengths(q,(2,2))
    assert result.verified and tuple(map(len,result.plaintext.words))==(2,2)
    assert result.capacity['oracle_word_lengths']
    assert not result.capacity.get('oracle_segmentation')
    assert not result.capacity.get('pinned_symbols')
    # Two distinct segmentations remain feasible at these same word lengths.
    assert recover_segmented(q,((0,3,4),(0,3,4))).verified
    assert recover_segmented(q,((0,2,4),(0,2,4))).verified
    with pytest.raises(ValueError):
        HiddenRecoveryRequest.from_dict({**asdict(q),'known_word_lengths':[2,2]})


@pytest.mark.parametrize('lengths',[[],[2],[2,2,2],[False,2],[0,2],[1,2],[5,2],[2.0,2]])
def test_bad_lengths_rejected(lengths):
    q=request()
    with pytest.raises(ValueError):validate_word_lengths(q.ciphertext,q.bounds,lengths)


def test_length_model_equals_union_of_matching_boundary_models():
    rows={1:((0,3),),2:((0,1,3),(0,2,3)),3:((0,1,2,3),)}
    for word in product('xy',repeat=3):
        q=request(''.join(word))
        hidden=q.solve()
        length_results=[]
        for count,boundaries in rows.items():
            r=recover_with_word_lengths(q,(count,))
            oracle=[recover_segmented(q,(b,)) for b in boundaries]
            assert r.status!='UNKNOWN' and all(x.status!='UNKNOWN' for x in oracle)
            assert (r.status=='SAT')==any(x.status=='SAT' for x in oracle)
            assert r.status!='SAT' or r.verified
            length_results.append(r)
        assert (hidden.status=='SAT')==any(r.status=='SAT' for r in length_results)


def test_length_wrapper_exposes_no_boundary_or_plaintext_fields(monkeypatch):
    import benchmarks.segmentation_diagnostic as runner
    from voynich_smt.solver.recovery import Recovery
    calls=[]
    def fake(q,lengths):
        calls.append((q,lengths));return Recovery('UNKNOWN',0,'test timeout')
    monkeypatch.setattr(runner,'recover_with_word_lengths',fake)
    payload={'request':asdict(request()),'word_lengths':[2,2]}
    runner.solve_payload(payload,1000)
    assert calls[0][0].timeout_ms==1000 and calls[0][1]==[2,2]
    with pytest.raises(ValueError):runner.solve_payload({**payload,'segmentation':[[0,3,4],[0,3,4]]})
