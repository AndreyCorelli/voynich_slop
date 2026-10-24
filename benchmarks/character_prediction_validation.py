"""Independent count/probability reconstruction for frozen spelling experiments."""
from collections import Counter, defaultdict
import json
import math
import string
from benchmarks import character_prediction as p
from voynich_smt.data.corpus import digest, write_json


def binpos(n,k):
    return 'all' if not k else ('start' if n==0 else 'inside') if k==2 else ('0' if n==0 else '1' if n==1 else '2-3' if n<4 else '4+')


def active(b,i,gate):
    return i>0 and (gate=='all' or gate==('within' if b['line_ids'][i]==b['line_ids'][i-1] else 'cross'))


def manual(train,b,s):
    uni=Counter(); counts=[defaultdict(Counter),defaultdict(Counter)]; pos=defaultdict(Counter); suffix=defaultdict(Counter); seen=set()
    for block in train:
        for i,w in enumerate(block['words']):
            seen.add(''.join(w)); history=['<BOS>','<BOS>']
            for c in list(w)+['<EOS>']:
                uni[c]+=1
                for order in (1,2): counts[order-1][tuple(history[-order:])][c]+=1
                history.append(c)
            key=binpos(block['positions'][i],s['position']); pos[key][w[0]]+=1
            if active(block,i,s['gate']): suffix[(key,block['words'][i-1][-1])][w[0]]+=1
    result=[]
    for i,w in enumerate(b['words']):
        history=['<BOS>','<BOS>']; loss=0
        for c in list(w)+['<EOS>']:
            start=history[-1]=='<BOS>'; alphabet=list(string.ascii_lowercase)+([] if start else ['<EOS>'])
            probability=(uni[c]+.5)/(sum(uni[a] for a in alphabet)+.5*len(alphabet))
            for order in range(1,s['order']+1):
                table=counts[order-1][tuple(history[-order:])]
                probability=(table[c]+s['strength']*probability)/(sum(table[a] for a in alphabet)+s['strength'])
            if start:
                key=binpos(b['positions'][i],s['position'])
                tables=[]
                if s['position']: tables.append(pos[key])
                if active(b,i,s['gate']): tables.append(suffix[(key,b['words'][i-1][-1])])
                for table in tables: probability=(probability+(table[c]+50*probability)/(sum(table.values())+50))/2
            loss-=math.log2(probability); history.append(c)
        result.append((loss,''.join(w) not in seen))
    return result


def validate():
    prepared=p.prepare(); reports=[json.loads((p.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)]
    train_indices={i for b in prepared['development'] for i in range(b['start'],b['end_exclusive'])}; held_indices=set()
    for b in prepared['heldout']:
        indices=set(range(b['start'],b['end_exclusive'])); assert not indices&train_indices and not indices&held_indices; held_indices|=indices
    raw=json.loads(__import__('pathlib').Path('data/processed/zl-eva.json').read_text())['records']
    earlier=p.prior.prior.prior.prepare(); word_context=p.prior.prior.prepare(); line_context=p.prior.prepare()
    previous_indices={i for b in earlier['development']+earlier['heldout']+word_context['heldout']+line_context['heldout'] for i in range(b['start'],b['end_exclusive'])}
    assert not held_indices&previous_indices
    for b in prepared['development']+prepared['heldout']:
        records=raw[b['start']:b['end_exclusive']]
        assert b['words']==[x['tokens'] for x in records]
        assert b['positions']==[x['word_in_locus'] for x in records]
        assert b['line_ids']==[f"{x['folio']}:{x['locus']}:{x['physical_line']}" for x in records]
    collected={f'{stage}:{name}':result for stage in (2,4,5) for name,result in reports[stage-1]['models'].items()}
    assert reports[5]['selected']==min(collected,key=lambda n:(collected[n]['bits_per_character'],n))
    assert reports[5]['controlled_context']==min([n for n in collected if n.startswith('5:')],key=lambda n:(-collected[n]['gain_position'],n))
    checked=0
    for stage,r in enumerate(reports,1):
        assert r['plan']==json.loads((p.OUT/f'plan-{stage}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(prepared)
        assert r['plan']['previous_sha256']==(digest(reports[stage-2]) if stage>1 else None)
        assert r['plan']['holdout_access']==(stage==7)
        if stage not in (2,4,5,7): continue
        specs=r['plan']['specs'] if stage!=7 else reports[5]['specs']
        blocks=prepared['heldout'] if stage==7 else prepared['development']
        for name,result in r['models'].items():
            spec=specs[name]
            for row in result['rows']:
                b=next(b for b in blocks if b['start']==row['start'])
                train=prepared['development'] if stage==7 else [b0 for b0 in prepared['development'] if b0['folio']!=b['folio']]
                expected=manual(train,b,spec)
                baselines=[manual(train,b,p.BASE_SPECS['char-iid']),manual(train,b,{**spec,'position':0,'gate':'none'}),manual(train,b,{**spec,'gate':'none'})]
                for i,(loss,novel) in enumerate(expected):
                    t=row['tokens'][i]; assert abs(t['loss']-loss)<1e-10 and t['novel']==novel and t['characters']==len(b['words'][i])
                    for k,base in zip(('gain_iid','gain_noexternal','gain_position'),baselines): assert abs(t[k]-(base[i][0]-loss))<1e-10
                    checked+=1
            assert p.aggregate(result['rows'])==result
    assert reports[6]['selected']==reports[5]['selected'] and reports[6]['controlled_context']==reports[5]['controlled_context']
    for stage in (2,4):
        r=reports[stage-1]; best=min(r['models'],key=lambda n:(r['models'][n]['bits_per_character'],n)); assert r['selected_base' if stage==2 else 'selected_position']==best
    for stage in (3,7):
        r=reports[stage-1]; blocks=prepared['development'] if stage==3 else prepared['heldout']
        spec=p.BASE_SPECS[r['base']] if stage==3 else reports[5]['specs'][r['controlled_context']]
        for d in r['diagnostic']:
            b=next(b for b in blocks if b['start']==d['start']); train=prepared['development'] if stage==7 else [b0 for b0 in prepared['development'] if b0['folio']!=b['folio']]
            shuffled=p.letter_shuffle(b,d['seed']) if stage==3 else p.prior.permutation(b,d['seed'])
            delta=sum(x[0] for x in manual(train,shuffled,spec))-sum(x[0] for x in manual(train,b,spec))
            assert abs(delta-d['word_order_gain_bits' if stage==3 else 'ordering_gain_bits'])<1e-9
            baseline=p.BASE_SPECS['char-iid'] if stage==3 else {**spec,'gate':'none'}
            assert abs(sum(x[0] for x in manual(train,shuffled,baseline))-sum(x[0] for x in manual(train,b,baseline)))<1e-9
    write_json(p.OUT/'validation.json',{'stages':7,'independently_checked_word_scores':checked,'fresh_words':len(held_indices),'status':'passed'})
    print('Validated seven stages:',checked,'independent word scores',flush=True)

if __name__=='__main__': validate()
