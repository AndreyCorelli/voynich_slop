from copy import deepcopy
import pytest
from benchmarks.grammar_boundary_role_iteration8 import masked_options,solve_options,diagnostic_counts
from tests.unit.test_predicate_structure import Adapter
from voynich_smt.parent_ranking import infer_links


class Constant:
    def logits(self,x):return [0.]*len(x)


def fixture():
    prediction=infer_links(['a','b','c'],[0,1,2],Adapter(),Constant(),typed=True,radius=None)
    gold={'tokens':['a','b','c'],'finite':[0,1,2],'boundaries':[2,3],
          'parents':{0:None,1:0,2:None},'relations':{0:'root',1:'subordination',2:'root'}}
    prediction['marker_attachments']=[]
    return prediction,gold


def test_oracle_masks_preserve_logits_without_supplying_parent_identity():
    pred,gold=fixture();before=deepcopy(pred)
    options=masked_options(pred,gold,boundaries=True,roles=True)
    assert [(r['parent'],r['relation']) for r in options[0]]==[(None,'root')]
    assert [(r['parent'],r['relation']) for r in options[1]]==[(0,'subordination')]
    assert [(r['parent'],r['relation']) for r in options[2]]==[(None,'root')]
    roles=masked_options(pred,gold,roles=True)
    assert {r['parent'] for r in roles[1]}=={0,2}  # Includes wrong parent.
    assert all(r['logit']==0 for rows in options.values() for r in rows)
    assert pred==before


def test_oracle_roles_do_not_force_the_reference_parent_among_legal_choices():
    pred,gold=fixture()
    for row in pred['arc_candidates'][1]:
        if row['parent']==2 and row['relation']=='subordination':row['logit']=10.
    result=solve_options(pred,masked_options(pred,gold,roles=True))
    assert result['parents'][1]==2
    assert diagnostic_counts(result,gold)['cross_sentence_choices']==1
    bounded=solve_options(pred,masked_options(pred,gold,True,True))
    assert bounded['parents'][1]==0
    assert diagnostic_counts(bounded,gold)['nonroot_correct']==1


def test_cycle_constraints_still_apply_with_gold_roles():
    pred,gold=fixture();gold['boundaries']=[3]
    gold['relations']={0:'root',1:'subordination',2:'subordination'};gold['parents'][2]=0
    for c in [1,2]:
        for row in pred['arc_candidates'][c]:
            if row['parent']==3-c and row['relation']=='subordination':row['logit']=10.
    result=solve_options(pred,masked_options(pred,gold,True,True))
    assert sum(result['parents'][c]==3-c for c in [1,2])==1
    assert result['forest_score_integer']==10_000_000
