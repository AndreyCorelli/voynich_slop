"""Independent paired-inventory, likelihood, decoding and contrast verification."""
from collections import Counter
import json
from statistics import mean
from benchmarks import boundary_null_contrasts as b
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.boundary_mechanisms_validation import structural
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventory(blocks): return Counter((x['folio'],pred.prior.position_bin(n,4),len(w),''.join(w)) for x in blocks for n,w in zip(x['positions'],x['words']))


def validate():
    p=b.prepare(); base=b.prior.prepare(); reports=[]; results={}; checked=decoded=0; natural=b.prior.prose_prepare()['cases']['german-113']
    for name,case in p['cases'].items():
        if case['kind']=='shuffle':
            parent=p['cases'].get(case['parent'],base['cases'].get(case['parent']))
            for split in ('train','heldout'):
                assert inventory(case[split])==inventory(parent[split])
                for a,z in zip(case[split],parent[split],strict=True): assert list(map(len,a['words']))==list(map(len,z['words'])) and a['positions']==z['positions'] and a['line_ids']==z['line_ids']
        elif case['kind']=='encoder':
            assert case['keys']['train']==case['keys']['heldout']; key=case['keys']['train']; inverse={v:k for k,v in key['payload'].items()}; assert len(inverse)==26
            for split in ('train','heldout'):
                for cipher,plain in zip(case[split],natural[split],strict=True):
                    for i,(word,truth) in enumerate(zip(cipher['words'],plain['words'],strict=True)):
                        marked=i>0 and cipher['line_ids'][i]==cipher['line_ids'][i-1] and i%int(1/case['dose'])==0
                        if marked: assert word[0]==key['marker'][cipher['words'][i-1][-1]]
                        assert [inverse[c] for c in (word[1:] if marked else word)]==truth; decoded+=1
    for i in range(1,8):
        r=json.loads((b.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((b.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None) and r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]; results[name]=result
            for row,block in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position')):
                    for t,(loss,novel) in zip(row['tokens'],manual(case['train'],block,spec),strict=True): assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10 and t['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
    old=json.loads((b.prior.OUT/'iteration-4.json').read_text())['results']
    for name,case in p['cases'].items():
        if case['kind']=='shuffle':
            parent=results.get(case['parent'],old.get(case['parent']))
            for a,z in zip(results[name]['folios'],parent['folios'],strict=True): assert a['folio']==z['folio'] and abs((a['bits_per_character']+a['gain_position'])-(z['bits_per_character']+z['gain_position']))<1e-10
    assert b.contrasts(p,results)==reports[-1]['contrasts']
    for n,names in p['old_nulls'].items():
        c=reports[-1]['old_null_contrasts'][n]; assert c['original_gain']==old[n]['gain_position'] and c['matched_shuffle_gains']==[results[z]['gain_position'] for z in names]
        assert c['excess_over_mean_null']==c['original_gain']-mean(c['matched_shuffle_gains'])
    for n in p['families']:
        for k,v in structural(p['cases'][n]['heldout']).items(): assert abs(v-reports[-1]['structure'][n][k])<1e-12
    write_json(b.OUT/'validation.json',{'status':'passed','stages':7,'cases':len(results),'independent_word_model_scores':checked,'independently_decoded_words':decoded,'matched_inventory_and_baseline_invariance':True,'contrasts_and_structure_verified':True})
    print('Validated',checked,'word/model scores and',decoded,'decoded words across',len(results),'cases',flush=True)

if __name__=='__main__': validate()
