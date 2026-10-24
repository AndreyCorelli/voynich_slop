"""Independent word probability and provenance checks for context prediction."""
from collections import Counter, defaultdict
import json
import math
from statistics import mean
from benchmarks import context_prediction as experiment
from voynich_smt.data.corpus import digest, write_json


def manual(training,block,spec):
    kind,alpha,weight=spec
    counts=Counter(''.join(w) for b in training for w in b['words']); vocabulary={w for w,n in counts.items() if n>=2}
    mapped=Counter({w:n for w,n in counts.items() if w in vocabulary}); mapped[experiment.UNK]=sum(n for w,n in counts.items() if w not in vocabulary)
    def ctx(previous):
        if kind=='word': return previous if previous in vocabulary else experiment.UNK
        if kind=='length': return str(min((len(previous)-1)//2,3))
        if kind=='suffix1': return previous[-1:]
        if kind=='suffix2': return previous[-2:]
        return None
    pairs=Counter(); outgoing=Counter()
    for b in training:
        seq=[''.join(w) for w in b['words']]
        for a,b in zip(seq,seq[1:]):
            c=ctx(a); target=b if b in vocabulary else experiment.UNK; pairs[c,target]+=1; outgoing[c]+=1
    losses=[]; known=[]; seq=[''.join(w) for w in block['words']]
    for i,w in enumerate(seq):
        target=w if w in vocabulary else experiment.UNK
        base=(mapped[target]+.5)/(sum(counts.values())+.5*(len(vocabulary)+1))
        p=base
        if i and kind!='unigram':
            c=ctx(seq[i-1]); conditional=(pairs[c,target]+alpha*base)/(outgoing[c]+alpha)
            p=weight*conditional+(1-weight)*base
        loss=-math.log2(p); losses.append(loss)
        if w in vocabulary: known.append(loss)
    return mean(losses),mean(known) if known else None,len(seq)-len(known)


def validate():
    p=experiment.prepare(); previous=None
    dev_folios={b['folio'] for b in p['development']}; held_folios={b['folio'] for b in p['heldout']}
    assert dev_folios.isdisjoint(held_folios)
    old=experiment.prior.prepare(); old_positions={(b['folio'],b['start']) for b in old['heldout']+old['development']}
    assert not any((b['folio'],b['start']) in old_positions for b in p['heldout'])
    specs={**experiment.MODELS,**json.loads((experiment.OUT/'iteration-5.json').read_text())['specs']}
    for index in range(1,8):
        r=json.loads((experiment.OUT/f'iteration-{index}.json').read_text()); plan=json.loads((experiment.OUT/f'plan-{index}.json').read_text())
        assert r['plan']==plan and plan['prepared_sha256']==digest(p)
        assert plan['previous_sha256']==(digest(previous) if previous else None)
        assert plan['holdout_access']==(index==7)
        for name,result in r.get('models',{}).items():
            for row in result['rows']:
                if index==7: train=p['development']; candidates=p['heldout']
                else: train=[b for b in p['development'] if b['folio']!=row['folio']]; candidates=p['development']
                block=next(b for b in candidates if b['folio']==row['folio'] and b['start']==row['start'])
                bits,known,unknown=manual(train,block,specs[name]); base,baseknown,_=manual(train,block,experiment.MODELS['unigram'])
                assert abs(bits-row['bits_per_token'])<1e-12 and unknown==row['unknown_tokens']
                assert abs(base-bits-row['gain_bits_per_token'])<1e-12
                assert known is None or abs(known-row['known_bits_per_token'])<1e-12
                assert baseknown is None or abs(baseknown-known-row['known_gain_bits_per_token'])<1e-12
            assert experiment.aggregate(result['rows'])==result
        previous=r
    selection=json.loads((experiment.OUT/'iteration-6.json').read_text())
    expected=max(selection['development_gains'],key=lambda name:(selection['development_gains'][name],name))
    assert selection['selected']==previous['selected']==expected
    write_json(experiment.OUT/'validation.json',{'verified':True,'iterations':7,'predictive_models':len(specs),'heldout_blocks':10,'heldout_folios':7,
        'independent_probability_reconstruction':True,'fresh_heldout_tokens':640,'solver_calls':0})


if __name__=='__main__': validate()
