from benchmarks.latin_relative_search import grammatical_metrics


def entry(pos,**features):
    return [{'enclitic':None,'inflections':[{'part_of_speech':pos,'features':features}]}]


def fixture():
    sentences=[{'tokens':[
        {'id':1,'word':'magna','pos':'ADJ','head':2,'relation':'amod','features':{'Case':'Nom','Number':'Sing','Gender':'Fem'}},
        {'id':2,'word':'urbs','pos':'NOUN','head':0,'relation':'root','features':{'Case':'Nom','Number':'Sing','Gender':'Fem'}}]}]
    entries={'magna':entry('ADJ',Case='NOM',Number='S',Gender='F'),'urbs':entry('N',Case='NOM',Number='S',Gender='F'),'magno':entry('ADJ',Case='ABL',Number='S',Gender='M'),'porta':entry('N',Case='NOM',Number='S',Gender='F'),'magnae':entry('ADJ',Case='GEN',Number='S',Gender='F'),'urbis':entry('N',Case='GEN',Number='S',Gender='F')}
    return sentences,entries,{'x':'magna','y':'urbs'}


def test_alternate_vocabulary_preserves_oracle_structure():
    s,e,truth=fixture();result=grammatical_metrics(s,{'x':'magna','y':'porta'},truth,e)
    assert result['gold_edge_accuracy']==1 and result['role_inflection_accuracy']==1


def test_damaged_agreement_is_detected():
    s,e,truth=fixture();result=grammatical_metrics(s,{'x':'magno','y':'urbs'},truth,e)
    assert result['gold_edge_accuracy']==0 and result['role_inflection_accuracy']==.5


def test_agreement_alone_does_not_restore_original_role():
    s,e,truth=fixture();result=grammatical_metrics(s,{'x':'magnae','y':'urbis'},truth,e)
    assert result['gold_edge_accuracy']==1 and result['role_inflection_accuracy']==0
