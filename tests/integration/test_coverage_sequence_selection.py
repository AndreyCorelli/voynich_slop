import pytest

from benchmarks import coverage_sequence_selection as b
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text


def test_coverage_selection_is_earliest_and_bounded():
    evaluation=list(enumerate(['ab','ac','ab','ac','ba','ca','ab','ac']))
    train,held=b.covered_block(evaluation,0)
    assert len(train)==4 and len(held)==4
    with pytest.raises(ValueError,match='coverage-eligible'):
        b.covered_block(list(enumerate(['a']*4+['b']*4)),0,4)


def test_prepared_controls_are_covered_and_reference_is_unchanged(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    p=b.prepare()
    for case in p['cases']:
        assert 4<=len(case['request']['ciphertext']['words'])<=32
        assert max(case['training_record_indices'])<min(case['holdout_record_indices'])
        if 'truth' in case:
            q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth'])
            held=Text(tuple(tuple(w) for w in case['holdout']['words']))
            assert b.coverage(case['truth'],held)==[True]*4
            assert case['generating_holdout_score']['dictionary_words']==4
    assert b.digest(p)==b.digest(b.prepare())
    monkeypatch.setattr(b,'identity',lambda: {'changed':'hash'})
    with pytest.raises(ValueError,match='source or code changed'):b.prepare()
