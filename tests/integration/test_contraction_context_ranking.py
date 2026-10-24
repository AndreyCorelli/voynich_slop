from copy import deepcopy
import math

from benchmarks.contraction_context_ranking import model_for,context_score,select


def test_reference_pairs_do_not_cross_excluded_tokens():
    m=model_for(['a',None,'b','c'])
    assert m['tokens']==3
    assert m['pairs']==[['b','c',1]]
    assert m['outgoing']=={'b':1}


def test_context_distinguishes_order_with_equal_unigram_counts():
    m={'counts':{'a':100,'b':100,'c':100},'tokens':300,'outgoing':{'a':100,'b':100},
       'pairs':[['a','b',100],['b','c',100]],'weight':0.5,'alpha':1}
    assert context_score(['a','b','c'],m)>context_score(['a','c','b'],m)
    assert math.isfinite(context_score(['a','unknown','c'],m))


def test_selection_ignores_truth_holdout_and_appended_carriers():
    m=model_for(['et','est']*10)
    candidates=[{'result':{'plaintext':{'words':[['e','t']]*32}},'truth':True},
                {'result':{'plaintext':{'words':[['e','t']]*32}},'holdout':['est']}]
    baseline=select(candidates,m,{})
    assert baseline[1]==[0,1]
    changed=deepcopy(candidates)
    changed[0]['truth']=False
    changed[1]['holdout']=['et']*100
    changed[1]['result']['plaintext']['words'] += [['x']]*100
    assert select(changed,m,{})==baseline
