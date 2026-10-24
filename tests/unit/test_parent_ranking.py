import numpy as np
import pytest
from scipy.special import softmax
from voynich_smt.parent_ranking import ConditionalRanker,choices,parents_for,infer_links
from voynich_smt.predicate_structure import morph_features,validate_structure
from tests.unit.test_predicate_structure import Adapter


def test_conditional_fit_ranks_within_groups_and_cancels_shared_features():
    groups=[([[1,0,10],[0,1,10]],1),([[1,0,-10],[0,-1,-10]],0)]*8
    ranker=ConditionalRanker.fit_groups(groups)
    for features,answer in groups:
        values=ranker.logits(features)
        assert np.argmax(values)==answer
        assert np.isclose(sum(softmax(values)),1)
    # A common per-group feature contributes nothing to conditional likelihood.
    assert abs(ranker.weights[-1])<1e-10


def test_parent_pool_sizes_and_boundary_restrictions():
    predicates=list(range(10))
    assert len(parents_for(4,predicates,radius=3))==7
    assert len(parents_for(4,predicates,radius=None))==10
    assert parents_for(4,predicates,[4,10],radius=3)==[None,5,6,7]


def test_typed_choices_have_only_legal_relation_labels():
    adapter=Adapter();tokens=['a','b'];morph=[morph_features(adapter.analyze(w)) for w in tokens]
    rows=choices(tokens,0,[0,1],morph,typed=True,radius=None)
    assert [(r['parent'],r['relation']) for r in rows]==[(None,'root'),(1,'coordination'),(1,'subordination')]
    assert len({len(r['features']) for r in rows})==1


class PreferEdges:
    def logits(self,x):return np.array([1-r[0] for r in x])


class Constant:
    def logits(self,x):return np.zeros(len(x))


def test_acyclic_forest_preserves_optimal_edge_count_and_probabilities():
    result=infer_links(['a','b','c'],[0,1,2],Adapter(),PreferEdges(),radius=None)
    assert result['status']=='optimal' and validate_structure(result)
    assert sum(v is not None for v in result['parents'].values())==2
    assert result['forest_score_integer']==2000000
    for rows in result['arc_candidates'].values():
        assert np.isclose(sum(r['conditional_probability'] for r in rows),1)


def test_relation_multiplicity_does_not_reward_a_forest():
    base=infer_links(['a','b'],[0,1],Adapter(),Constant(),radius=None)
    typed=infer_links(['a','b'],[0,1],Adapter(),Constant(),typed=True,radius=None)
    assert base['forest_score_integer']==typed['forest_score_integer']==0


def test_invalid_positions_and_boundaries_are_rejected():
    with pytest.raises(ValueError):infer_links(['a','b'],[1,0],Adapter(),Constant())
    with pytest.raises(ValueError):infer_links(['a','b'],[0,0],Adapter(),Constant())
    with pytest.raises(ValueError):infer_links(['a','b'],[2],Adapter(),Constant())
    with pytest.raises(ValueError):infer_links(['a','b'],[0],Adapter(),Constant(),boundaries=[1])
