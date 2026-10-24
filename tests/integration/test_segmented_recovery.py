from dataclasses import asdict
from itertools import product
import pytest
from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.segmented import recover_segmented, validate_segmentation


def request(text='xxxy xxxy'):
    return HiddenRecoveryRequest(Text.from_string(text),Alphabet(tuple('ab')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','ab','ba','bbb')),
        selection=HomophoneSelection('cycle','text'),dictionary_encoding='trie')


def test_oracle_boundaries_are_exact_and_word_lengths_follow():
    q=request()
    rows=((0,3,4),(0,3,4))
    result=recover_segmented(q,rows)
    assert result.status=='SAT' and result.verified and result.segmentation==rows
    assert tuple(map(len,result.plaintext.words))==(2,2)
    assert result.capacity['oracle_segmentation']
    assert not result.capacity.get('pinned_symbols')
    assert q.solve().verified
    assert 'known_segmentation' not in asdict(q)
    with pytest.raises(ValueError):
        HiddenRecoveryRequest.from_dict({**asdict(q),'known_segmentation':rows})


@pytest.mark.parametrize('rows', [[],[[0,4],[0,3,4]],[[0,0,4],[0,3,4]],
    [[False,3,4],[0,3,4]],[[0,2,3],[0,3,4]],[[0,3,4]]])
def test_bad_boundaries_rejected(rows):
    q=request()
    with pytest.raises(ValueError):validate_segmentation(q.ciphertext,q.bounds,rows)


def test_revealed_boundary_variants_partition_hidden_feasibility():
    # All compositions of a three-glyph word under L3: oracle boundaries must
    # collectively cover exactly the ordinary hidden model.
    for word in product('xy',repeat=3):
        q=request(''.join(word))
        hidden=q.solve()
        results=[recover_segmented(q,(row,)) for row in ((0,3),(0,1,3),(0,2,3),(0,1,2,3))]
        assert all(r.status!='UNKNOWN' for r in results)
        assert (hidden.status=='SAT')==any(r.status=='SAT' for r in results)
        assert all(r.status!='SAT' or r.verified for r in results)


def test_explicit_diagnostic_wrapper_routes_only_boundaries(monkeypatch):
    import benchmarks.segmentation_diagnostic as runner
    from voynich_smt.solver.recovery import Recovery
    calls=[]
    def fake(q, rows):
        calls.append((q,rows));return Recovery('UNKNOWN',0,'test timeout')
    monkeypatch.setattr(runner,'recover_segmented',fake)
    payload={'request':asdict(request()),'segmentation':[[0,3,4],[0,3,4]]}
    runner.solve_payload(payload,1000)
    assert calls[0][0].timeout_ms==1000 and calls[0][1]==payload['segmentation']
    with pytest.raises(ValueError):runner.solve_payload({**payload,'plaintext':[['a','b']]})
