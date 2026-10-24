from collections import defaultdict
from benchmarks.character_calibration import transform
from benchmarks import character_prediction as pred


def block():
    return {'folio':'test','start':0,'words':[list(w) for w in ('ab','bc','ca','abc','bca','cab')], 'positions':[0,1,2,0,1,2], 'line_ids':['a','a','a','b','b','b']}


def test_homophones_have_disjoint_reversible_codes():
    b=block(); encrypted=transform([b],'homophonic',26001)[0]; decoder={}
    for plain,cipher in zip(b['words'],encrypted['words']):
        assert len(cipher)==2*len(plain)
        for i,c in enumerate(plain):
            code=''.join(cipher[2*i:2*i+2]); assert code not in decoder or decoder[code]==c; decoder[code]=c
    assert [''.join(decoder[''.join(w[i:i+2])] for i in range(0,len(w),2)) for w in encrypted['words']]==[''.join(w) for w in b['words']]


def test_relabeling_preserves_predictive_scores():
    b=block(); transformed=transform([b],'mono',26001)[0]; spec={'order':2,'strength':10,'position':4,'gate':'all'}
    original=pred.score(b,pred.fit([b],spec)); encoded=pred.score(transformed,pred.fit([transformed],spec))
    assert all(abs(x['loss']-y['loss'])<1e-10 for x,y in zip(original,encoded))


def test_positive_control_and_position_shuffle_constraints():
    b=block(); positive=transform([b],'positive',26001)[0]
    for i in (1,2,4,5): assert positive['words'][i][0]==positive['words'][i-1][-1]
    assert positive['words'][0]==b['words'][0] and positive['words'][3]==b['words'][3]
    shuffled=transform([b],'shuffle',26001)[0]
    def groups(x):
        d=defaultdict(list)
        for n,w in zip(x['positions'],x['words']): d[pred.prior.position_bin(n,4)].append(''.join(w))
        return {k:sorted(v) for k,v in d.items()}
    assert groups(b)==groups(shuffled)
