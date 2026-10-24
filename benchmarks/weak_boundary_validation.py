"""Independent scoring and exact-inventory checks for weak boundary controls."""
from collections import Counter
import json
from statistics import mean
from benchmarks import weak_boundary_calibration as w
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventory(blocks):
    return Counter((b['folio'],('0' if n==0 else '1' if n==1 else '2-3' if n<4 else '4+'),len(word),''.join(word)) for b in blocks for n,word in zip(b['positions'],b['words']))


def validate():
    p=w.prepare(); original=pred.prepare(); reports=[]; checked=0; summaries={}
    for i in range(1,8):
        r=json.loads((w.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((w.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None); reports.append(r)
        assert r['plan']['cases']==p['stages'][str(i)]
        for name,result in r['results'].items():
            case=p['cases'][name]; assert case['streams']['train']!=case['streams']['heldout']
            for split,key in (('train','development'),('heldout','heldout')):
                assert inventory(case[split])==inventory(original[key]); eligible=matched=0
                for a,b in zip(original[key],case[split],strict=True):
                    assert [len(word) for word in a['words']]==[len(word) for word in b['words']]
                    assert a['positions']==b['positions'] and a['line_ids']==b['line_ids']
                    for j in range(1,len(b['words'])):
                        if b['line_ids'][j]==b['line_ids'][j-1]: eligible+=1; matched+=b['words'][j][0]==b['words'][j-1][-1]
                assert case['stats'][split]['eligible']==eligible and case['stats'][split]['matched']==matched
            for row,b in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((p['spec'],None),({**p['spec'],'gate':'none'},'gain_position')):
                    expected=manual(case['train'],b,spec)
                    for token,(loss,novel) in zip(row['tokens'],expected,strict=True):
                        assert abs((token['loss'] if gain is None else token['loss']+token[gain])-loss)<1e-10 and token['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
            summaries[name]={**r['summary'][name],**{f'{split}_matching_fraction':case['stats'][split]['matched']/case['stats'][split]['eligible'] for split in ('train','heldout')}}
    prior=json.loads((pred.OUT/'iteration-7.json').read_text()); baseline=prior['models'][prior['selected']]
    for r in reports:
        for result in r['results'].values():
            for a,b in zip(result['folios'],baseline['folios'],strict=True):
                assert a['folio']==b['folio'] and abs((a['bits_per_character']+a['gain_position'])-(b['bits_per_character']+b['gain_position']))<1e-10
    doses={}
    for rate in w.RATES:
        values=[summaries[w.name(seed,rate)]['gain_position_per_character'] for seed in w.SEEDS]
        doses[str(rate)]={'gains':values,'mean':mean(values),'positive_realizations':sum(v>0 for v in values),'matching_fractions':[summaries[w.name(seed,rate)]['heldout_matching_fraction'] for seed in w.SEEDS]}
    result={'status':'passed','independent_word_model_scores':checked,'stages':7,'summary':summaries,'dose_response':doses,
            'prior_manuscript_gain':baseline['gain_position'],'position_baseline_invariant':True,'interpretation':'Weak doses not reliably positive; maximum constrained matching remains below manuscript gain. Three realizations do not estimate power. The injection targets final-to-initial equality, not the full learned suffix relationship, and depletion limits achievable matches. No language or mechanism conclusion.'}
    write_json(w.OUT/'validation.json',result); print(json.dumps({k:v for k,v in result.items() if k!='summary'},indent=2))

if __name__=='__main__': validate()
