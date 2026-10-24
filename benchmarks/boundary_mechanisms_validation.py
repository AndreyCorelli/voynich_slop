"""Independent encoding, likelihood and structural audits for known fixtures."""
import json
from statistics import mean
from benchmarks import boundary_mechanisms as b
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def distance_one(a,z):
    if a==z or abs(len(a)-len(z))>1: return False
    if len(a)==len(z): return sum(x!=y for x,y in zip(a,z))==1
    short,long=(a,z) if len(a)<len(z) else (z,a)
    return any(long[:i]+long[i+1:]==short for i in range(len(long)))


def structural(blocks):
    rows=[]
    for block in blocks:
        words=[''.join(w) for w in block['words']]; n=len(words); allpairs=[(i,j) for i in range(n) for j in range(i+1,n)]; local=[(i,j) for i,j in allpairs if j-i<=8]
        def rate(pairs,near=False): return sum(distance_one(words[i],words[j]) if near else words[i]==words[j] for i,j in pairs)/len(pairs)
        rows.append({'mean_length':sum(map(len,words))/n,'unique_ratio':len(set(words))/n,'adjacent_repeat':sum(words[i]==words[i-1] for i in range(1,n))/(n-1),'repeat_local_excess':rate(local)-rate(allpairs),'one_edit_pair_fraction':rate(allpairs,True),'one_edit_local_excess':rate(local,True)-rate(allpairs,True)})
    return {k:mean(r[k] for r in rows) for k in rows[0]}


def validate():
    p=b.prepare(); natural=b.prose_prepare()['cases']['german-113']; source=pred.prepare(); reports=[]; checked=decoded=0
    for name,case in p['cases'].items():
        if case['kind'].startswith('encoder'):
            assert case['keys']['train']==case['keys']['heldout']; key=case['keys']['train']; inverse={v:k for k,v in key['payload'].items()}; assert len(inverse)==26 and len(set(key['marker'].values()))==26
            for split in ('train','heldout'):
                for original,cipher in zip(natural[split],case[split],strict=True):
                    for i,(plain,word) in enumerate(zip(original['words'],cipher['words'],strict=True)):
                        marked=i>0 and cipher['line_ids'][i]==cipher['line_ids'][i-1] and i%int(1/case['dose'])==0
                        if marked and case['kind']=='encoder': assert word[0]==key['marker'][cipher['words'][i-1][-1]]
                        payload=word[1:] if marked else word; assert [inverse[c] for c in payload]==plain; decoded+=1
        else:
            pool={''.join(w) for block in source['development'] for w in block['words']}
            assert all(''.join(w) in pool for split in ('train','heldout') for block in case[split] for w in block['words'])
    for i in range(1,8):
        r=json.loads((b.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((b.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None) and r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]
            for row,block in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position')):
                    for t,(loss,novel) in zip(row['tokens'],manual(case['train'],block,spec),strict=True): assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10 and t['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
    for name,blocks in [('manuscript',p['reference_blocks'])]+[(n,c['heldout']) for n,c in p['cases'].items()]:
        expected=structural(blocks)
        for k,v in expected.items(): assert abs(v-reports[-1]['structure'][name][k])<1e-12
    write_json(b.OUT/'validation.json',{'status':'passed','stages':7,'independent_word_model_scores':checked,'independently_decoded_words':decoded,'structural_metrics_independently_verified':True}); print('Validated',checked,'word/model scores and',decoded,'decoded words',flush=True)

if __name__=='__main__': validate()
