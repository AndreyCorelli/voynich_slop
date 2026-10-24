import pytest

from benchmarks import fresh_voynich_screen as b
from voynich_smt.models.text import Text


def test_selection_respects_folio_and_exclusion_barriers():
    def record(folio,tokens):return {'folio':folio,'tokens':tokens}
    records=[record('old',['a'])]*5+[record('one',['a'])]*2+[record('one',[])]
    records += [record('one',['a'])]*4+[record('two',['a'])]*4
    indices=b.select_blocks(records,['a'],{'old'},4)
    assert indices==[list(range(8,12)),list(range(12,16))]
    with pytest.raises(ValueError):b.select_blocks(records,['b'],{'old'},4)


def test_preparation_novelty_and_full_vocabulary_identity(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    assert p['novelty_gate_passed'] and len(p['blocks'])==2
    used=set()
    for block in p['blocks']:
        assert not used.intersection(block['record_indices']);used.update(block['record_indices'])
        assert block['folio'] not in p['protocol']['excluded_folios']
        assert block['record_indices']==list(range(block['record_indices'][0],block['record_indices'][0]+44))
        assert block['novelty']['novel_ciphertext_words']>=11
        if block['control'] is not None:
            assert block['control_construction']['exact_repetition_partition_preserved']
        else:
            assert block['control_construction']['status'].startswith('UNAVAILABLE')
    assert p['dictionaries']['latin-letters']['expanded_spelling_count']==5655
    assert p['dictionaries']['swabian-letters']['expanded_spelling_count']==3181
    assert b.digest(p)==b.digest(b.prepare())


def test_requests_pair_models_and_controls_without_changing_inventory(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare();block=next(x for x in p['blocks'] if x['control'] is not None)
    for language in ('latin','swabian'):
        q1,r1=b.request_for(p,block,language,'letters',1,'real')
        q2,r2=b.request_for(p,block,language,'letters',2,'real')
        a=b.asdict(q1);c=b.asdict(q2);a['bounds']['max_homophones']=2
        assert a==c and r1==r2==[]
        control,_=b.request_for(p,block,language,'letters',1,'control')
        assert control.dictionary==q1.dictionary and control.ciphertext_alphabet==q1.ciphertext_alphabet
        assert tuple(map(len,control.ciphertext.words))==tuple(map(len,q1.ciphertext.words))
