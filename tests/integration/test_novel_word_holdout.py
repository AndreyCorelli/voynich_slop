import pytest

from benchmarks import novel_word_holdout as b
from benchmarks.l3_conflict import verify
from voynich_smt.models.text import Text


def test_selection_is_deterministic_and_requires_joint_unit_coverage():
    vocabulary=['ab','ac','ba','bc','ca','cb']
    train,held=b.select_types(vocabulary,[])
    assert len(held)==3 and not set(train)&set(held)
    assert b.select_types(list(reversed(vocabulary)),[])==(train,held)
    assert set(''.join(held))<=set(''.join(train))
    with pytest.raises(ValueError,match='covered three-type'):b.select_types(['a','b','c','d'],[])


def test_all_held_words_are_novel_and_codes_seen(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    assert len(p['cases'])==8 and p['protocol']['holdout_type_count']==3
    for case in p['cases']:
        q=b.request_for(case,case['generating_h']);verify(q,case['truth'])
        train=case['truth']['plaintext']['words'];held=case['holdout_plaintext']['words']
        assert len(held)==3 and len(set(b.expanded(held,case['rules'])))==3
        assert not set(b.expanded(train,case['rules']))&set(b.expanded(held,case['rules']))
        assert not set(q.ciphertext.words)&set(tuple(w) for w in case['holdout']['words'])
        seen={tuple(m['code']) for m in b.used_mappings(case['truth'])}
        assert all(tuple(w[i:i+2]) in seen for w in case['holdout']['words'] for i in range(0,len(w),2))
        assert case['generating_score']['novel_dictionary_words']==3
        assert case['generating_score']['seen_ciphertext_words']==0
    assert b.digest(p)==b.digest(b.prepare())


def test_nested_recovery_models_only_change_homophone_cap(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);p=b.prepare()
    for case in p['cases']:
        one=b.asdict(b.request_for(case,1));two=b.asdict(b.request_for(case,2))
        one['bounds']['max_homophones']=2
        assert one==two
