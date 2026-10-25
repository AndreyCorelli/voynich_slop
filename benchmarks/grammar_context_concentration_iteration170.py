"""Context-word concentration audit of two fixed Cicero case graphs."""
import gzip
from benchmarks.grammar_case_replication_iteration168 import *
OUT=ROOT/'iteration170';POOLS={'earlier':dict(descriptors=ROOT/'iteration165/descriptors.json',cases=ROOT/'iteration166/case-inputs.json',transforms=ROOT/'iteration164/transforms.json',key='Cicero',nested=False),'replication':dict(descriptors=ROOT/'iteration168/descriptors.json',cases=ROOT/'iteration168/case-inputs.json',transforms=ROOT/'iteration168/transforms.json',key='fit-Cicero',nested=True)}

def remove(dd,kind,value):
    result=[]
    for e in dd:
        ff=[f for f in e['frames'] if kind=='none' or (value not in f['frame'] if kind=='either' else f['frame'][0 if kind=='left' else 1]!=value)]
        if len(ff)>=2:result.append(dict(a=e['a'],b=e['b'],shared_frames=len(ff),frames=ff))
    return result

def universe(actual):
    ids=sorted({i for e in actual for f in e['frames'] for i in f['frame']})
    return {'baseline':dict(kind='none',value=None),**{kind+str(k):dict(kind=kind,value=i) for kind in ['either','left','right'] for k,i in enumerate(ids)}}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration168/verification-manifest.json',ROOT/'iteration166/summary.json',ROOT/'iteration168/summary.json']+[p[n] for p in POOLS.values() for n in ['descriptors','cases','transforms']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Freeze all opaque context IDs occurring in original floor5/two-frame graphs, no label selection. Remove each ID from either side (primary), left only and right only (controls), across every frame in actual and all16 shuffle graphs; reapply two distinct frames. Baseline unchanged. Fixed166 conditional case scoring; report all removals including empty outcomes, remaining coverage, ranges, matched-null contrasts. Graph concentration only, no token rewrite, no named case/POS prediction or lexical recovery, no independent replication claim. Save gzip JSON detailed scores before summaries; no new annotations, reserves or sealed works.'))
    data={};interventions={}
    for pool,p in POOLS.items():
        vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv;vv={v:[e for e in dd if e['shared_frames']>=2] for v,dd in vv.items()};actual=vv['original'];interventions[pool]=universe(actual);data[pool]=vv
    save(OUT/'interventions.json',interventions);save(OUT/'interventions-freeze.json',dict(inputs={str(OUT/'interventions.json'):digest(OUT/'interventions.json')}));details={}
    for pool,p in POOLS.items():
        cases=load(p['cases'])[p['key']];transforms=load(p['transforms'])[p['key']];details[pool]={}
        for name,r in interventions[pool].items():
            details[pool][name]={}
            for view,dd in data[pool].items():
                ix=transforms[view];cc=cases if ix is None else [cases[k] for k in ix];details[pool][name][view]=score_cases(remove(dd,r['kind'],r['value']),cc)
    
    with gzip.open(OUT/'details.json.gz','wt') as f:json.dump(details,f,separators=(',',':'))
    save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json.gz'):digest(OUT/'details.json.gz')}));eligible={'earlier':588,'replication':857};summary={pool:{name:{v:summarize_cases(rr,eligible[pool])['2'] for v,rr in vv.items()} for name,vv in nn.items()} for pool,nn in details.items()};contrasts={};ranges={}
    for pool,nn in summary.items():
        contrasts[pool]={};ranges[pool]={}
        for name,vv in nn.items():
            actual=vv['original'];pp=[vv['word'+str(k)]['edge_macro_frame_case_agreement'] for k in SEEDS if vv['word'+str(k)]['case_edges']];v=actual['edge_macro_frame_case_agreement'];contrasts[pool][name]=dict(actual=actual,null_with_case=len(pp),null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=v for p in pp) if v is not None else None)
        for kind in ['either','left','right']:
            names=[n for n,r in interventions[pool].items() if r['kind']==kind];rr=[summary[pool][n]['original'] for n in names];nonempty=[r for r in rr if r['case_edges']];ranges[pool][kind]=dict(interventions=len(names),without_case=sum(not r['case_edges'] for r in rr),min_case_edges=min(r['case_edges'] for r in rr),max_case_edges=max(r['case_edges'] for r in rr),min_agreement=min(r['edge_macro_frame_case_agreement'] for r in nonempty) if nonempty else None,max_agreement=max(r['edge_macro_frame_case_agreement'] for r in nonempty) if nonempty else None,strictly_above_matched_null_max=sum(contrasts[pool][n]['actual']['edge_macro_frame_case_agreement'] is not None and contrasts[pool][n]['null_max'] is not None and contrasts[pool][n]['actual']['edge_macro_frame_case_agreement']>contrasts[pool][n]['null_max'] for n in names))
        print(pool,ranges[pool],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts);save(OUT/'ranges.json',ranges)
if __name__=='__main__':run()
