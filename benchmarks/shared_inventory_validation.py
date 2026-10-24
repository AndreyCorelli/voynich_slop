"""Independent shared-payload inventories, decoding, likelihood and structure checks."""
from collections import Counter
import json
from statistics import mean
from benchmarks import shared_inventory_mechanisms as m
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.boundary_mechanisms_validation import structural
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventories(blocks,blockwise=False):
    return Counter((b['folio'],b['start'] if blockwise else None,pred.prior.position_bin(n,4),len(w),''.join(w)) for b in blocks for n,w in zip(b['positions'],b['words']))


def validate():
    p=m.prepare(); reports=[]; results={}; checked=decoded=0
    for source in m.SOURCES:
        for seed in m.SEEDS:
            prose=f'{source}-prose-{seed}'; local=f'{source}-local-{seed}'
            for split in ('train','heldout'):
                assert inventories(p['payloads'][prose+':'+split],True)==inventories(p['payloads'][local+':'+split],True)
                a=p['cases'][prose]; b=p['cases'][local]; assert a['keys'][split]==b['keys'][split]
                for x,y in zip(a[split],b[split],strict=True): assert list(map(len,x['words']))==list(map(len,y['words'])) and x['line_ids']==y['line_ids'] and x['positions']==y['positions']
    for name,case in p['cases'].items():
        if case['kind']=='shuffle':
            for split in ('train','heldout'): assert inventories(case[split])==inventories(p['cases'][case['parent']][split])
        else:
            assert case['keys']['train']==case['keys']['heldout']; key=case['keys']['train']; inverse={v:k for k,v in key['payload'].items()}; assert len(inverse)==26
            for split in ('train','heldout'):
                for a,z in zip(case[split],p['payloads'][name+':'+split],strict=True):
                    for i,(word,truth) in enumerate(zip(a['words'],z['words'],strict=True)):
                        marker=i>0 and a['line_ids'][i]==a['line_ids'][i-1] and i%16==0
                        if marker: assert word[0]==key['marker'][a['words'][i-1][-1]]
                        assert [inverse[c] for c in (word[1:] if marker else word)]==truth; decoded+=1
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None) and r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]; results[name]=result
            for row,b in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position')):
                    for t,(loss,novel) in zip(row['tokens'],manual(case['train'],b,spec),strict=True): assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10 and t['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
    for name,case in p['cases'].items():
        if case['kind']=='shuffle':
            for a,z in zip(results[name]['folios'],results[case['parent']]['folios'],strict=True): assert a['folio']==z['folio'] and abs(a['bits_per_character']+a['gain_position']-z['bits_per_character']-z['gain_position'])<1e-10
    for n in p['active']:
        contrast=reports[-1]['contrasts'][n]; gains=[results[n+f'-shuffle-{ns}']['gain_position'] for ns in m.NULL_SEEDS]
        assert contrast=={'gain':results[n]['gain_position'],'null_gains':gains,'excess':results[n]['gain_position']-mean(gains)}
        for representation,blocks in (('payload',p['payloads'][n+':heldout']),('encoded',p['cases'][n]['heldout'])):
            for k,v in structural(blocks).items(): assert abs(v-reports[5]['structure'][n][representation][k])<1e-12
    for source in m.SOURCES:
        for seed in m.SEEDS:
            a=f'{source}-prose-{seed}'; b=f'{source}-local-{seed}'
            assert reports[-1]['paired_excess_differences'][f'{source}-{seed}']==reports[-1]['contrasts'][b]['excess']-reports[-1]['contrasts'][a]['excess']
            for metric in ('mean_length','unique_ratio','one_edit_pair_fraction'): assert abs(reports[5]['structure'][a]['payload'][metric]-reports[5]['structure'][b]['payload'][metric])<1e-12
    write_json(m.OUT/'validation.json',{'status':'passed','stages':7,'cases':len(results),'independent_word_model_scores':checked,'decoded_words':decoded,'exact_shared_payload_inventories':True,'common_keys_schedule_lengths':True,'null_baseline_invariance':True,'structure_and_contrasts_verified':True}); print('Validated',checked,'word/model scores and',decoded,'decoded words across',len(results),'cases',flush=True)

if __name__=='__main__': validate()
