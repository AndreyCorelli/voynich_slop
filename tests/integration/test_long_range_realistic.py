from benchmarks.long_range_realistic import rows,evaluate,generate


def test_lags_never_cross_line_boundary_and_oracle_matches_features():
    blocks=generate(7,'state-local','train')
    normal=rows(blocks); oracle=rows(blocks,True)
    assert len(normal)==512
    for a,b in zip(normal,oracle):
        assert a['lags']==b['lags'] and a['target']==b['target'] and a['previous']==b['previous']
        assert b['pos'].startswith(a['pos']+':state')
    assert normal[8]['lags']['8']==blocks[0]['words'][16][-1]


def test_unseen_context_has_finite_uniform_prior_loss():
    r={'pos':'unseen','previous':'z','target':'z','lags':{str(d):'z' for d in range(2,9)}}
    result=evaluate([], [r])
    import math
    assert abs(result['rows'][0]['baseline']-math.log2(26))<1e-12
    assert abs(result['gain'])<1e-12
