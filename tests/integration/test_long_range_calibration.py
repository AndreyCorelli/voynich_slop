from collections import Counter
from benchmarks.long_range_calibration import ALPHABET,LAGS,fit,probabilities,null_rows


def fixture():
    return [{'pos':'early','previous':'a','target':ALPHABET[i%4],'lags':{str(d):ALPHABET[(i+d)%4] for d in LAGS}} for i in range(40)]


def test_predictive_distributions_are_normalized():
    data=fixture(); model=fit(data)
    for r in data:
        base,extended=probabilities(model,r)
        assert abs(sum(base.values())-1)<1e-12
        assert all(abs(sum(p.values())-1)<1e-12 and min(p.values())>0 for p in extended.values())


def test_conditional_null_preserves_baseline_and_feature_marginals():
    data=fixture(); shuffled=null_rows(data,17)
    assert [(r['pos'],r['previous'],r['target']) for r in data]==[(r['pos'],r['previous'],r['target']) for r in shuffled]
    for d in LAGS:
        assert Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in data)==Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in shuffled)
    assert any(a['lags']!=b['lags'] for a,b in zip(data,shuffled))
