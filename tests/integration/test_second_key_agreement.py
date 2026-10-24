from copy import deepcopy
from benchmarks import second_key_agreement as b
from voynich_smt.solver.recovery import Recovery
from voynich_smt.data.corpus import digest


def test_agreement_can_be_wrong_and_partial_is_not_agreement():
    a={'fully_decoded':True,'decoded_prefix':['a']}
    incomplete={'fully_decoded':False,'decoded_prefix':['a']}
    case={'kind':'positive','first':{'prediction':{'word_results':[a,a]}},'holdout_plaintext':{'words':[['b'],['a']]}}
    result=b.agreement(case,{'prediction':{'word_results':[a,incomplete]}})
    assert result['agree_words']==1 and result['agree_correct_words']==0
    assert not result['word_results'][1]['agree']


def test_resume_and_no_first_key_handling(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);calls=[]
    def spy(q,rule):
        calls.append(rule);return Recovery('UNKNOWN',.01)
    monkeypatch.setattr(b,'solve',spy)
    r=b.run();p=b.prepare()
    assert len(calls)==6 and len(r['cases'])==12
    for case in p['cases']:
        if case['exclusion']:
            used={s for w in case['first']['result']['plaintext']['words'] for s in w}
            assert set(case['exclusion']['mappings'])==used
            changed=deepcopy(case['first']['result']);changed['exact_words']=999
            assert digest(b.exclusion(changed))==digest(case['exclusion'])
    assert all('agreement' not in a for a in r['cases'])
    assert digest(b.run())==digest(r) and len(calls)==6
    b.validate()
