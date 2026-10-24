"""Independent scoring and exact-inventory checks for mapped boundary controls."""
from collections import Counter, defaultdict
import json
from statistics import mean
from benchmarks import mapped_boundary_calibration as w
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventory(blocks):
    return Counter((b['folio'],('0' if n==0 else '1' if n==1 else '2-3' if n<4 else '4+'),len(word),''.join(word)) for b in blocks for n,word in zip(b['positions'],b['words']))


def validate():
    p=w.prepare(); original=pred.prepare()
    # Independently reconstruct position-adjusted residual mapping from original training only.
    events=[]
    for b in original['development']:
        for i in range(1,len(b['words'])):
            if b['line_ids'][i]==b['line_ids'][i-1]:
                n=b['positions'][i]; pos='0' if n==0 else '1' if n==1 else '2-3' if n<4 else '4+'
                events.append((pos,b['words'][i-1][-1],b['words'][i][0]))
    mapping={}; audit={}
    for last in sorted({e[1] for e in events}):
        chosen=[e for e in events if e[1]==last]
        if len(chosen)<10: continue
        residual={}
        for first in sorted({e[2] for e in events}):
            if sum(e[2]==first for e in events)<10: continue
            excess=0
            for pos in sorted({e[0] for e in chosen}):
                here=[e for e in chosen if e[0]==pos]; allpos=[e for e in events if e[0]==pos]
                excess+=sum(e[2]==first for e in here)-len(here)*sum(e[2]==first for e in allpos)/len(allpos)
            residual[first]=excess
        best=min(residual,key=lambda c:(-residual[c],c))
        if residual[best]>0: mapping[last]=best
        audit[last]={'transitions':len(chosen),'selected_initial':best,'excess_count':residual[best]}
    assert mapping==p['mapping']
    for last,row in audit.items():
        assert row['transitions']==p['training_audit'][last]['transitions'] and row['selected_initial']==p['training_audit'][last]['selected_initial']
        assert abs(row['excess_count']-p['training_audit'][last]['excess_count'])<1e-10
    reports=[]; checked=0; summaries={}
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
                        if b['line_ids'][j]==b['line_ids'][j-1]: eligible+=1; matched+=b['words'][j][0]==p['mapping'].get(b['words'][j-1][-1])
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
            'prior_manuscript_gain':baseline['gain_position'],'position_baseline_invariant':True,'interpretation':'Report mapped dose response relative to reused manuscript gain. Three realizations do not estimate power. Training-selected mapping and inventory depletion constrain interpretation. No language or mechanism conclusion.'}
    write_json(w.OUT/'validation.json',result); print(json.dumps({k:v for k,v in result.items() if k!='summary'},indent=2))

if __name__=='__main__': validate()
