from voynich_smt.anchor_perturbation import perturb,source_patterns


def test_missing_and_swapped_keep_type_identity_and_original():
    anchors={'in':'ADP','et':'CCONJ'}
    public=[{'sent_id':'a','tokens':[{'id':'i','anchor':'in','tag':'ADP'},{'id':'e','anchor':'et','tag':'CCONJ'},{'id':'x','anchor':None,'tag':'X'}]}]
    swapped=perturb(public,{'in':'et','et':'in'},anchors)[0]['tokens']
    assert [t['id'] for t in swapped]==['i','e','x']
    assert [t['tag'] for t in swapped]==['CCONJ','ADP','X']
    missing=perturb(public,{'in':None},anchors)[0]['tokens']
    assert missing[0]=={'id':'i','anchor':None,'tag':'X'}
    assert public[0]['tokens'][0]['anchor']=='in'
    assert swapped[2]==public[0]['tokens'][2]


def test_patterns_use_fit_frequency_with_deterministic_ties():
    anchors={'a':'ADP','b':'ADP','c':'CCONJ','d':'SCONJ','e':'CCONJ'}
    fit=[{'tokens':[{'word':w} for w in ['c','c','b','b','a','d','e']]}]
    p=source_patterns(fit,anchors)
    assert p['missing_top1']=={'b':None}
    assert p['missing_top_adp']=={'b':None}
    assert p['swap_adps']=={'b':'a','a':'b'}
    assert p['swap_adp_conjunction']=={'b':'c','c':'b'}
