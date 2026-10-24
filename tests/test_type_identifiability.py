from benchmarks.grammar_type_identifiability_iteration76 import strict_compatible,credible,oracle_summary,pooling_metrics

def test_strict_does_not_accept_unknown_required_feature():
    assert not strict_compatible(('NOUN','Acc','Sing'),('NOUN','',''))
    assert strict_compatible(('NOUN','','Sing'),('NOUN','Acc','Sing'))

def test_credible_set_smallest_mass_prefix_with_stable_ties():
    assert credible([.6,.3,.1])==[0,1]
    assert credible([.5,.5])==[0,1]

def test_other_occurrence_predictions_exclude_current_context():
    profiles=[('NOUN','Acc','Sing'),('NOUN','Nom','Sing')]
    occ=[dict(gold_profile=profiles[i],context=[1-i,i],shuffle=[.5,.5],prior=[.5,.5]) for i in range(2)]
    result=pooling_metrics([dict(word='x',occurrences=occ)],profiles,[.5,.5])
    assert result['profile']['context/local']['accuracy']==1
    assert result['profile']['context/other_occurrences']['accuracy']==0
    assert result['profile']['context/pooled']['accuracy']==.5

def test_singletons_not_used_for_repeated_pooling():
    profiles=[('NOUN','Acc','Sing')];o=dict(gold_profile=profiles[0],context=[1],shuffle=[1],prior=[1])
    r=pooling_metrics([dict(word='x',occurrences=[o,o]),dict(word='y',occurrences=[o])],profiles,[1])
    assert r['profile']['context/pooled']['tokens']==2
    assert r['profile']['context/pooled']['types']==1
