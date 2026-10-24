import numpy as np
from voynich_smt.candidate_omission import omit
from voynich_smt.combined_repair_gate import select


def test_omitting_true_partner_exposes_wrong_fallback_instead_of_forcing_abstention():
    record=dict(pairs=[dict(pair=['a','b'],gain=2.,supported=True),dict(pair=['a','c'],gain=1.,supported=True)],reference=dict(pair=['a','b'],error=True,supported=True))
    draws=np.array([[2.,1.],[2.,1.]])
    result=omit(record,draws,'b')
    assert result['source_pair_indices']==[1]
    assert result['features']['pair']==['a','c'] and result['features']['stability']==1.
    assert not result['reference']['supported']
    assert select(result['features'],dict(threshold=.5,gap=0.,stability=.5))==['a','c']
    assert record['reference']['supported'] and record['pairs'][0]['gain']==2.


def test_omitting_unrelated_candidate_preserves_true_pair_but_changes_gap():
    record=dict(pairs=[dict(pair=['a','b'],gain=2.,supported=True),dict(pair=['a','c'],gain=1.,supported=True),dict(pair=['d','e'],gain=.1,supported=True)],reference=dict(pair=['a','b'],error=True,supported=True))
    result=omit(record,np.array([[2.,1.,.1],[2.,1.,.1]]),'c')
    assert result['reference']['supported'] and result['features']['pair']==['a','b']
    assert result['features']['gap']==1.9
