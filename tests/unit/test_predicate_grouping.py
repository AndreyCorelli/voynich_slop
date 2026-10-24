import itertools
import math
import numpy as np
from voynich_smt.predicate_grouping import pair_features,contiguous_groups,restrict_or_rescore


def test_features_are_symmetric_and_do_not_accept_annotation_inputs():
    tokens=['a','b','c','d'];morph=[[float(i),1.] for i in range(4)]
    attachments=[{'position':1,'target':2,'kinds':['subordination']}]
    assert pair_features(tokens,[0,2,3],morph,attachments,0,3)==pair_features(tokens,[0,2,3],morph,attachments,3,0)
    assert len(pair_features(tokens,[0,2,3],morph,attachments,0,3,False))==2


def test_partition_dp_matches_exhaustive_partitions_without_fixed_group_count():
    predicates=[0,2,5,9];probs={'0:2':.9,'0:5':.2,'0:9':.1,'2:5':.7,'2:9':.2,'5:9':.8}
    groups,score=contiguous_groups(predicates,probs)
    values=[]
    for cuts in itertools.product([False,True],repeat=3):
        blocks=[[predicates[0]]]
        for p,cut in zip(predicates[1:],cuts):
            if cut:blocks.append([])
            blocks[-1].append(p)
        value=sum(math.log(probs[f'{a}:{b}']/(1-probs[f'{a}:{b}'])) for g in blocks for i,a in enumerate(g) for b in g[i+1:])
        values.append(value)
    assert np.isclose(score,max(values))
    assert contiguous_groups([],{} )==([],0.)
    assert contiguous_groups([3],{})==([[3]],0.)


def test_soft_penalty_preserves_root_and_candidates_and_counts_signal_once():
    pred={'predicates':[0,2],'arc_candidates':{0:[{'parent':None,'relation':'root','logit':1.},
        {'parent':2,'relation':'subordination','logit':3.}],2:[{'parent':None,'relation':'root','logit':1.}]}}
    result,_=restrict_or_rescore(pred,{'0:2':.2},'soft')
    assert result['arc_candidates'][0][0]['logit']==1.
    edge=result['arc_candidates'][0][1]
    assert np.isclose(edge['logit'],3+math.log(.2))
    assert pred['arc_candidates'][0][1]['logit']==3.
    hard,_=restrict_or_rescore(pred,{'0:2':.2},'pair_filter')
    assert len(hard['arc_candidates'][0])==1
