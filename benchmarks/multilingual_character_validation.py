"""Independent likelihood reconstruction and split checks for multilingual comparison."""
from collections import Counter
import json
from benchmarks import multilingual_character as m
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventory(blocks):
    return Counter((b['folio'],pred.prior.position_bin(n,4),len(w),''.join(w)) for b in blocks for n,w in zip(b['positions'],b['words']))


def validate():
    p=m.prepare(); reports=[]; checked=0; summaries={}
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        assert r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]; indices={split:{s for b in case[split] for s in b['source_slots']} for split in ('train','heldout')}
            assert len(indices['train'])==1024 and len(indices['heldout'])==2848 and not indices['train']&indices['heldout']
            if case['variant']=='replication':
                old=p['cases'][case['source']]; assert not (indices['train']|indices['heldout'])&{s for split in ('train','heldout') for b in old[split] for s in b['source_slots']}
            if case['variant']=='shuffle':
                for split in ('train','heldout'): assert inventory(case[split])==inventory(p['cases'][case['source']][split])
            if case['variant']=='eight-lines':
                for split in ('train','heldout'):
                    for a,b in zip(case[split],p['cases'][case['source']][split],strict=True): assert a['words']==b['words'] and a['positions']==[i%8 for i in range(32)]
            for row,b in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position')):
                    for t,(loss,novel) in zip(row['tokens'],manual(case['train'],b,spec),strict=True):
                        assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10 and t['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]; summaries[name]=r['summary'][name]
    results={name:result for r in reports for name,result in r['results'].items()}
    for name,case in p['cases'].items():
        if case['variant']=='shuffle':
            for a,b in zip(results[name]['folios'],results[case['source']]['folios'],strict=True): assert abs((a['bits_per_character']+a['gain_position'])-(b['bits_per_character']+b['gain_position']))<1e-10
    write_json(m.OUT/'validation.json',{'status':'passed','stages':7,'independent_word_model_scores':checked,'summary':summaries,'source_split_and_replication_disjointness':True,'shuffle_position_baseline_invariant':True})
    print('Validated',checked,'word/model scores across',len(results),'cases',flush=True)

if __name__=='__main__': validate()
