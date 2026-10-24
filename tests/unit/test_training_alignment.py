import numpy as np
import pytest
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.training_alignment import blocked_folds, fit_graph_contrast, separability_audit
from benchmarks.grammar_training_alignment_iteration7 import vocabulary_for


def test_folds_block_within_each_author_and_partition_streams():
    authors=['a']*9+['b']*8
    folds=blocked_folds(authors)
    assert folds==[0,0,0,1,1,1,2,2,2]+[0,0,1,1,2,2,3,3]
    for f in range(4):
        held={i for i,x in enumerate(folds) if x==f}
        fit={i for i,x in enumerate(folds) if x!=f}
        assert not held&fit and held|fit==set(range(len(authors)))
    with pytest.raises(ValueError):blocked_folds(authors,1)


def test_fold_vocabulary_excludes_held_only_labels():
    streams=[{'tokens':['ut'],'markers':{0:{'kind':'subordination'}}},
             {'tokens':['ut','et'],'markers':{0:{'kind':'relative'},1:{'kind':'coordination'}}}]
    assert vocabulary_for(streams[:1])=={'ut':['subordination']}
    assert vocabulary_for(streams)['ut']==['relative','subordination']


def test_contrast_improves_wrong_graph_margin_without_rescaling():
    initial=ConditionalRanker([0.,-2.,0.],[3.,4.],[2.,5.])
    revised=fit_graph_contrast(initial,[[1.,0.],[2.,0.]])
    assert revised.weights[1]>0 and revised.weights[2]==0
    assert revised.mean==initial.mean and revised.scale==initial.scale
    with pytest.raises(ValueError):fit_graph_contrast(initial,[[1.]])
    with pytest.raises(ValueError):fit_graph_contrast(initial,[])


def test_distinct_features_can_still_be_linearly_incompatible():
    assert separability_audit([[1.,0.],[0.,1.]])['status']=='feasible'
    assert separability_audit([[1.,0.],[-1.,0.]])['status']=='infeasible'
    assert separability_audit([])['status']=='not_applicable'


def test_graph_difference_matches_forest_score_change_and_skips_abstentions():
    from benchmarks.grammar_training_alignment_iteration7 import graph_difference
    from tests.unit.test_predicate_structure import Adapter
    from voynich_smt.marker_structure import attachment_features
    from voynich_smt.predicate_structure import morph_features
    adapter=Adapter();tokens=['a','b'];predicates=[0,1]
    gold={'tokens':tokens,'finite':predicates,'parents':{0:None,1:0},
          'relations':{0:'root',1:'subordination'}}
    prediction={'status':'optimal','parents':{0:None,1:None},
                'relations':{0:'root',1:'root'},'marker_attachments':[]}
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    correct=np.array(attachment_features(tokens,1,0,predicates,morph,'subordination',[],False))
    wrong=np.array(attachment_features(tokens,1,None,predicates,morph,'root',[],False))
    model=ConditionalRanker([0.]+[.1]*len(correct),[2.]*len(correct),[3.]*len(correct))
    difference=graph_difference(prediction,gold,adapter,model)
    assert np.allclose(difference,(correct-wrong)/3/2)
    assert np.isclose(np.dot(difference,model.weights[1:])*2,model.logits([correct])[0]-model.logits([wrong])[0])
    prediction['status']='unresolved'
    assert graph_difference(prediction,gold,adapter,model) is None


def test_independent_super_root_reduction_breaks_cycles_and_selects_best_relation():
    from benchmarks.grammar_training_alignment_iteration7_validate import independent_replay
    from benchmarks.grammar_training_alignment_iteration7 import FixedMarkers
    from tests.unit.test_predicate_structure import Adapter
    class PreferCoordination:
        def logits(self,features):
            return np.array([0.]+[2.,1.]*((len(features)-1)//2))
    result=independent_replay({'tokens':['a','b','c'],'finite':[0,1,2]},PreferCoordination(),FixedMarkers([]),Adapter())
    # Three mutually attractive predicates still need one ROOT edge.
    assert result['forest_score_integer']==4_000_000
    empty=independent_replay({'tokens':['a'],'finite':[]},PreferCoordination(),FixedMarkers([]),Adapter())
    assert empty['forest_score_integer']==0
