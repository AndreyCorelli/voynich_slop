from copy import deepcopy
from voynich_smt.crossfit_morphology import inner_plan,sentence_fold,probability_map,replace_probabilities
from voynich_smt.factor_morphology import fit
from voynich_smt.multi_link_attachment import vector,STRUCTURAL,LOCAL


def test_crossfit_excludes_held_fold_and_exposed_control_includes_it():
    ids=[]
    for group in (0,1,2):
        ids.extend([str(i) for i in range(1000) if sentence_fold(str(i))==group][:2])
    plan=inner_plan(ids)
    for group,record in plan.items():
        held=set(record['held_ids'])
        cross={sid for sid in ids if sentence_fold(sid)!=record['crossfit_excluded']}
        exposed={sid for sid in ids if sentence_fold(sid)!=record['exposed_excluded']}
        assert not held&cross and held<=exposed
        assert len(cross)==len(exposed)==4
    assert set().union(*(set(r['held_ids']) for r in plan.values()))==set(ids)


def test_replacement_preserves_candidates_targets_and_nonprobability_features():
    tokens=[dict(word='a',pos='NOUN'),dict(word='b',pos='VERB')]
    first={i:dict(role=[.1,.9],number=[.8,.2],person=[0.,0.,1.]) for i in (0,1)}
    second={i:dict(role=[.8,.2],number=[.5,.5],person=[0.,0.,1.]) for i in (0,1)}
    frame=dict(sid='s',subject=0,predicates=[1],gold=1,vectors={arm:[vector(tokens,0,1,first,arm)] for arm in ('structural','local_morph')})
    original=deepcopy(frame);result=replace_probabilities([frame],tokens,second)[0];prefix=len(STRUCTURAL)+len(LOCAL)
    assert frame==original
    assert result['predicates']==[1] and result['gold']==1
    assert result['vectors']['structural']==frame['vectors']['structural']
    assert result['vectors']['local_morph'][0][:prefix]==frame['vectors']['local_morph'][0][:prefix]
    assert result['vectors']['local_morph'][0][prefix:]!=frame['vectors']['local_morph'][0][prefix:]


def test_probability_inference_does_not_read_scored_annotations():
    trained=[dict(word='a',pos='NOUN',features={'Case':'Nom','Number':'Sing'})]
    model=fit([trained],'expanded')
    observed=[dict(word='a',pos='NOUN',features={'Case':'Acc','Number':'Plur'},head=0,rel='obj')]
    masked=[dict(t,features={},head=None,rel='?') for t in observed]
    assert probability_map(observed,model,{})==probability_map(masked,model,{})
    assert probability_map(observed,model,{})[0]['person']==[0.,0.,1.]


def test_bad_partition_plan_is_rejected():
    import pytest
    with pytest.raises(ValueError):inner_plan([])
    with pytest.raises(ValueError):inner_plan(['one'])
