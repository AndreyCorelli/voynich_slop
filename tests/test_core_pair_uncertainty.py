import numpy as np
from voynich_smt.core_pair_uncertainty import restrict


def test_restriction_recomputes_winner_and_stability_without_changing_draws():
    record=dict(case='test',block='b',regime='sparse',reference=dict(pair=['a','b']),pairs=[dict(pair=['a','outside'],gain=3.,supported=True),dict(pair=['a','b'],gain=2.,supported=True),dict(pair=['a','c'],gain=1.,supported=True)])
    draws=np.array([[3.,2.,1.],[3.,0.,1.]])
    result=restrict(record,draws,{'a','b','c'})
    assert result['source_pair_indices']==[1,2]
    assert result['features']['pair']==['a','b'] and result['features']['stability']==.5
    assert record['pairs'][0]['gain']==3. and draws[0,0]==3.
