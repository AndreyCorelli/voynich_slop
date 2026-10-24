from copy import deepcopy
import pytest
from voynich_smt.predicate_carriers import target,relabel


def token(pos,head,rel,form=''):
    return dict(pos=pos,head=head,rel=rel,features={'VerbForm':form} if form else {})


def test_unique_copula_and_auxiliary_carriers():
    ts=[token('NOUN',2,'nsubj'),token('AUX',2,'cop','Fin'),token('ADJ',None,'root')]
    assert target(ts,0)==dict(direct=None,carrier=1,kind='copula',ambiguous=False,choices=[1])
    ts[1]['rel']='aux';ts[2]=token('VERB',None,'root','Part')
    assert target(ts,0)['kind']=='auxiliary' and target(ts,0)['carrier']==1


def test_direct_governor_wins_without_reassigning_original_targets():
    ts=[token('NOUN',2,'nsubj'),token('AUX',2,'aux','Fin'),token('VERB',None,'root','Fin')]
    assert target(ts,0)==dict(direct=2,carrier=2,kind='direct',ambiguous=False,choices=[2])


def test_multiple_carriers_are_unscored_only_in_expanded_task():
    ts=[token('NOUN',2,'nsubj'),token('AUX',2,'cop','Fin'),token('ADJ',None,'root'),token('AUX',2,'aux','Fin')]
    frame=dict(subject=0,predicates=[1,3],vectors={'local_morph':[[1],[2]]})
    truth=target(ts,0)
    assert truth['ambiguous'] and truth['choices']==[1,3]
    assert relabel([frame],ts,'carrier')[0]==[]
    assert relabel([frame],ts,'direct')[0][0]['gold'] is None


def test_relabel_does_not_inject_gold_or_mutate_features():
    ts=[token('NOUN',2,'nsubj'),token('AUX',2,'cop','Fin'),token('ADJ',None,'root')]
    frame=dict(subject=0,predicates=[],vectors={'local_morph':[]});original=deepcopy(frame)
    rows,_=relabel([frame],ts,'carrier')
    assert rows[0]['gold']==1 and rows[0]['predicates']==[]
    assert frame==original


def test_coordination_unknown_governor_and_nonfinite_auxiliary_do_not_project():
    ts=[token('NOUN',2,'conj'),token('AUX',2,'cop','Fin'),token('ADJ',None,'root')]
    assert target(ts,0)['carrier'] is None
    ts[0]['rel']='nsubj';ts[2]=token('VERB',None,'root')
    assert target(ts,0)['kind']=='unknown_governor_form'
    ts[2]['features']['VerbForm']='Inf';ts[1]['features']['VerbForm']='Inf'
    assert target(ts,0)['kind']=='no_finite_carrier'
    with pytest.raises(ValueError):relabel([],ts,'unknown')
