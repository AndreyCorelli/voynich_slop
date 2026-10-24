import numpy as np
from voynich_smt.marker_structure import attachment_features
from voynich_smt.predicate_structure import morph_features
from tests.unit.test_predicate_structure import Adapter
from benchmarks.grammar_parent_interactions_iteration10 import gate_decision


def test_marker_interactions_can_distinguish_parents_with_the_same_child_role():
    tokens=['a','b','c','d','e'];predicates=[0,2,4];adapter=Adapter()
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    attached=[{'position':1,'target':2,'kinds':['subordination']}]
    def marker_effect(parent,interactions):
        with_marker=np.array(attachment_features(tokens,2,parent,predicates,morph,'subordination',attached,interactions))
        without=np.array(attachment_features(tokens,2,parent,predicates,morph,'subordination',[],interactions))
        return with_marker-without
    assert np.array_equal(marker_effect(0,False),marker_effect(4,False))
    assert not np.array_equal(marker_effect(0,True),marker_effect(4,True))


def test_primary_gate_does_not_select_the_better_replication_arm():
    rows=[]
    for features in ['marker_only','interactions']:
        for markers,mode in [('gold','both'),('predicted','both'),('predicted','unrestricted')]:
            rows.append({'split':'development','training':'oof','features':features,'markers':markers,'condition':mode,
                'diagnostic':{'ambiguous_nonroot_accuracy':.5 if features=='marker_only' else .56},
                'metrics':{'edges':{'f1':.5},'roots':{'recall':.9}}})
    assert gate_decision(rows)['passed']
    # Parent-choice gain alone does not pass if deployable edge F1 declines.
    for r in rows:
        if (r['features'],r['markers'],r['condition'])==('interactions','predicted','unrestricted'):r['metrics']['edges']['f1']=.49
    assert not gate_decision(rows)['passed']
