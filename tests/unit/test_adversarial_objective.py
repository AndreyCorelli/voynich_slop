import numpy as np
from benchmarks.latin_adversarial_objective import expanded,quality


def test_quadratic_representation_uses_fixed_fit_normalization():
    x=expanded(np.arange(8.),np.zeros(8),np.ones(8),True)
    assert len(x)==44
    assert np.array_equal(x[:8],np.arange(8.))
    assert x[8]==0 and x[-1]==49


def attack(start,edge_before,edge_after,role_before,role_after):
    def state(edge,role):return {'grammar':{'satisfied_gold_edges':edge,'eligible_gold_edges':10,'role_inflection_compatible_tokens':role,'role_inflection_eligible_tokens':20},'worst_high_scoring_edge_loss':max(0,edge_before-edge_after),'worst_high_scoring_role_loss':max(0,role_before-role_after)}
    return {'start':start,'snapshots':[state(edge_before,role_before),state(edge_after,role_after)]}


def test_role_damage_cannot_be_hidden_by_edge_repair():
    result=quality([attack('truth',10,10,20,19),attack('corrupt_high',5,10,15,14)])
    assert result['valid_stability']==0
    assert result['median_minimum_edge_role_repair']<0
    assert result['corrupt_nonregression']==0


def test_flat_score_cannot_pass_repair_requirement():
    result=quality([attack('truth',10,10,20,20),attack('corrupt_high',5,5,15,15)])
    assert result['valid_stability']==1
    assert result['median_minimum_edge_role_repair']==0
