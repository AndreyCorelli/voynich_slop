"""Independent likelihood, split and permutation validation for line controls."""
from collections import Counter, defaultdict
import json
import math
import random
from statistics import mean
from benchmarks import line_context_prediction as experiment
from voynich_smt.data.corpus import digest, write_json


def manual(train,b,spec):
    counts=Counter(''.join(w) for block in train for w in block['words']); vocab={w for w,n in counts.items() if n>=2}
    uni=Counter({w:n for w,n in counts.items() if w in vocab}); uni[experiment.UNK]=sum(n for w,n in counts.items() if w not in vocab)
    def pos(index):
        if spec['position']==0: return 'all'
        if spec['position']==2: return 'start' if index==0 else 'inside'
        return '0' if index==0 else '1' if index==1 else '2-3' if index<4 else '4+'
    def gate(block,i):
        if i==0 or spec['gate']=='none': return False
        same=block['line_ids'][i]==block['line_ids'][i-1]
        return spec['gate']=='all' or (spec['gate']=='within' and same) or (spec['gate']=='cross' and not same)
    positions=defaultdict(Counter); pairs=defaultdict(Counter)
    for block in train:
        for i,word in enumerate(block['words']):
            w=''.join(word); mapped=w if w in vocab else experiment.UNK; p=pos(block['positions'][i]); positions[p][mapped]+=1
            if gate(block,i): pairs[p,''.join(block['words'][i-1])[-1]][mapped]+=1
    result=[]
    for i,word in enumerate(b['words']):
        w=''.join(word); target=w if w in vocab else experiment.UNK
        base=(uni[target]+.5)/(sum(counts.values())+.5*(len(vocab)+1)); p=pos(b['positions'][i])
        if spec['position']:
            row=positions[p]; base=(base+(row[target]+50*base)/(sum(row.values())+50))/2
        if gate(b,i):
            row=pairs[p,''.join(b['words'][i-1])[-1]]; base=(base+(row[target]+50*base)/(sum(row.values())+50))/2
        result.append(-math.log2(base))
    return result


def manual_permutation(block,seed):
    result={**block,'words':list(block['words'])}; rng=random.Random(seed+block['start']); grouped=defaultdict(list)
    for i,p in enumerate(block['positions']): grouped['0' if p==0 else '1' if p==1 else '2-3' if p<=3 else '4+'].append(i)
    for ids in grouped.values():
        words=[block['words'][i] for i in ids]; rng.shuffle(words)
        for i,w in zip(ids,words): result['words'][i]=w
    return result


def validate():
    p=experiment.prepare(); previous=None
    dev={b['folio'] for b in p['development']}; held={b['folio'] for b in p['heldout']}
    assert dev.isdisjoint(held)
    old=experiment.prior.prior.prepare()
    assert held.isdisjoint(b['folio'] for b in old['heldout'])
    selection=json.loads((experiment.OUT/'iteration-6.json').read_text())
    specs=selection['specs']
    assert selection['selected']==max(selection['development_scores'],key=lambda name:(selection['development_scores'][name]['gain_unigram'],name))
    controlled=[name for name in specs if name.startswith('position+suffix')]
    assert selection['controlled_context']==max(controlled,key=lambda name:(selection['development_scores'][name]['gain_position'],name))
    for stage in range(1,8):
        report=json.loads((experiment.OUT/f'iteration-{stage}.json').read_text()); plan=json.loads((experiment.OUT/f'plan-{stage}.json').read_text())
        assert report['plan']==plan and plan['prepared_sha256']==digest(p)
        assert plan['previous_sha256']==(digest(previous) if previous else None) and plan['holdout_access']==(stage==7)
        for name,model in report.get('models',{}).items():
            for row in model['rows']:
                candidates=p['heldout'] if stage==7 else p['development']
                b=next(b for b in candidates if b['folio']==row['folio'] and b['start']==row['start'])
                train=p['development'] if stage==7 else [b for b in p['development'] if b['folio']!=row['folio']]
                expected=manual(train,b,specs[name]); uni=manual(train,b,{'position':0,'gate':'none'}); position=manual(train,b,{'position':specs[name]['position'],'gate':'none'})
                for i,t in enumerate(row['tokens']):
                    assert abs(t['loss']-expected[i])<1e-12
                    assert abs(t['gain_unigram']-(uni[i]-expected[i]))<1e-12
                    assert abs(t['gain_position']-(position[i]-expected[i]))<1e-12
            assert model==experiment.aggregate(model['rows'])
        if stage in (5,7):
            chosen=report['context_candidate'] if stage==5 else report['controlled_context']
            for row in report['diagnostic']:
                candidates=p['development'] if stage==5 else p['heldout']; b=next(b for b in candidates if b['folio']==row['folio'] and b['start']==row['start'])
                train=[b for b in p['development'] if b['folio']!=row['folio']] if stage==5 else p['development']
                shuffled=manual_permutation(b,row['seed']); spec=specs[chosen]
                delta=mean(manual(train,shuffled,spec))-mean(manual(train,b,spec))
                assert abs(delta-row['ordering_gain'])<1e-12
                baseline={'position':spec['position'],'gate':'none'}
                assert abs(mean(manual(train,shuffled,baseline))-mean(manual(train,b,baseline)))<1e-12
        previous=report
    assert previous['selected']==selection['selected'] and previous['controlled_context']==selection['controlled_context']
    write_json(experiment.OUT/'validation.json',{'verified':True,'iterations':7,'models':len(specs),'fresh_heldout_folios':5,'fresh_heldout_blocks':11,
        'independent_probability_and_permutation_checks':True,'solver_calls':0})


if __name__=='__main__': validate()
