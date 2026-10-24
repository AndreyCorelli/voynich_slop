from voynich_smt.paired_anchor_class import target_features,recommend,pair_metrics,calibrate_pair
from voynich_smt import anchor_grammar as ag


def test_selected_feature_builder_equals_full_public_features():
    public=[dict(sent_id='s',tokens=[dict(id='a',anchor='ad',tag='ADP'),dict(id='x',anchor=None,tag='X'),dict(id='b',anchor='que',tag='CCONJ'),dict(id='c',anchor='ille',tag='PRON'),dict(id='a',anchor='ad',tag='ADP')])]
    masked=[dict(s,tokens=[dict(t,anchor=None,tag='X') if t['id'] in {'a','b'} else t for t in s['tokens']]) for s in public]
    assert target_features(public,{'a','b'})==[r for r in ag.public_features(masked) if r['word'] in {'a','b'}]
    assert public[0]['tokens'][0]['anchor']=='ad'


def test_ties_abstain_and_wrong_pairs_count_as_misses():
    p=[dict(pair=['a','b'],gain=1.,supported=True),dict(pair=['c','d'],gain=1.,supported=True)]
    assert recommend(p,0) is None
    p[1]['gain']=2.
    result=pair_metrics(p,0,dict(error=True,pair=['a','b']))
    assert result['false_pair']==1 and result['miss']==1 and result['hit']==0
    assert pair_metrics(p,0,dict(error=True,pair=None))['miss']==1
    selected,_=calibrate_pair([],p,dict(error=False,pair=None),dict(error=True,pair=['a','b']))
    assert selected['threshold'] is None


def test_calibration_selects_exact_pair_and_preserves_clean_guard():
    clean=[dict(pair=['a','b'],gain=-.2,supported=True)]
    error=[dict(pair=['a','b'],gain=.8,supported=True)]
    chosen,_=calibrate_pair(clean,error,dict(error=False,pair=None),dict(error=True,pair=['a','b']))
    assert chosen['threshold']==.8 and chosen['corrupted']['hit']==1
