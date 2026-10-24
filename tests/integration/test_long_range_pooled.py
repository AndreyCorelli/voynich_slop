import math
from benchmarks.long_range_pooled import evaluate
from benchmarks.long_range_realistic import ALPHABET,LAGS


def test_pooled_distribution_normalizes_with_unseen_context():
    train=[{'pos':'known','previous':'a','target':c,'lags':{str(d):c for d in LAGS}} for c in 'aaaabbc']
    held=[{'pos':'unseen','previous':'z','target':c,'lags':{str(d):'a' for d in LAGS}} for c in ALPHABET]
    for spec in ((10,.75),(200,.25)):
        scores=evaluate(train,held,spec)['rows']
        assert abs(sum(2**(-r['baseline']) for r in scores)-1)<1e-12
        assert abs(sum(2**(-r['mixture']) for r in scores)-1)<1e-12
        assert all(abs(sum(2**(-r['lags'][str(d)]) for r in scores)-1)<1e-12 for d in LAGS)


def test_no_training_information_produces_uniform_predictions():
    held=[{'pos':'x','previous':'a','target':c,'lags':{str(d):'a' for d in LAGS}} for c in ALPHABET]
    result=evaluate([],held,(10,.75))
    assert abs(result['gain'])<1e-12
    assert all(abs(r['mixture']-math.log2(26))<1e-12 for r in result['rows'])
