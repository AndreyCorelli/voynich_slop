from dataclasses import asdict
import pytest
from benchmarks import training_vocabulary_ablation as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


def test_deletion_only_nested_public_inputs_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def solve(q):
        received.append(q)
        return Recovery('UNSAT',.01)
    monkeypatch.setattr(b,'recover_observed_codes',solve)
    r=b.run();p=b.prepare();source=b.base.prepare()
    assert len(received)==32
    for case,q in zip(p['cases'],received):
        original=next(c for c in source['cases'] if c['id']==case['original_id'])
        before=dict(original['request']);after=asdict(q);before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after) and q.timeout_ms==5000
        removed=set(map(tuple,case['removed_words']))
        assert q.dictionary.words==tuple(tuple(w) for w in original['request']['dictionary']['words'] if tuple(w) not in removed)
        assert len(q.dictionary.words)==256-case['removed_type_count']
    for one,two in zip(p['cases'][::2],p['cases'][1::2]):
        assert two['removed_words'][:1]==one['removed_words']
        assert set(map(tuple,two['request']['dictionary']['words']))<set(map(tuple,one['request']['dictionary']['words']))
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' for a in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==32
    b.validate()


def test_reject_unmatched_baseline():
    with pytest.raises(ValueError,match='Unmatched baseline'):
        b.build({}, {'complete':False})
