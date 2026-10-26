"""Independent priors, odds adjustment, sorted filters and scalar metrics."""
from pathlib import Path
from itertools import groupby
import json,math,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration217'
def read(p):return json.loads(p.read_text())
def close(a,b):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
def ranktop(scores,universe,k):
    chosen=[]
    for value,group in groupby(sorted(universe,key=lambda i:-scores[i]),key=lambda i:scores[i]):
        chosen.extend(group)
        if len(chosen)>=k:break
    return sorted(chosen) if k else []
def run():
    pred=read(P/'iteration216/predictions.json');weights=read(P/'iteration216/weights.json');app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');support=read(P/'iteration207/predictions.json');priors=read(O/'priors.json');sel=read(O/'selections.json');ss=read(O/'summary.json');old=read(P/'iteration216/summary.json');lists=0
    for a,models in pred.items():
        source=[s for s in pred if s!=a];q=sum(sum(app[s])/len(app[s]) for s in source)/3;r=sum(sum(w*y for w,y in zip(weights[a][s]['weights'],app[s])) for s in source);p=priors[a];close(q,p['original']);close(r,p['balanced']);oddsratio=(r/(1-r))/(q/(1-q));close(math.log(oddsratio),p['logit_shift']);raw=models['baseline'][a];adjusted=[(v*oddsratio)/(1-v+v*oddsratio) for v in raw]
        for v,z in zip(adjusted,p['adjusted_probabilities']):close(v,z)
        base=[i for i,v in enumerate(raw) if v>=.5];balanced=[i for i,v in enumerate(models['balanced'][a]) if v>=.5];k=len(balanced);assert p['matched_k']==k;expected=dict(baseline=base,balanced=balanced,size_matched=ranktop(raw,list(range(len(raw))),k),prior_only=[i for i,v in enumerate(adjusted) if v>=.5]);positive=[i for i,v in enumerate(yy[a]) if v]
        for name,ix in expected.items():
            assert sel[a][name]['eligible']==ix;v=ss[a][name];assert v['eligible']==len(ix) and v['matched_k']==k and v['case_tp']==sum(app[a][i] for i in ix) and v['case_fp']==sum(not app[a][i] for i in ix);assert v['size_excess']==(len(ix)-k if name=='size_matched' else None);assert v['retained_supported']==[i for i in positive if i in ix] and v['rejected_supported']==[i for i in positive if i not in ix]
            for n in [3,5]:
                label=f'top{n}';jj=ranktop(support[a]['full12'],ix,n);assert jj==sel[a][name]['lists'][label];z=v['lists'][label];hit=sum(yy[a][i] for i in jj);assert z['selected']==len(jj) and z['supported']==hit and z['case_bearing']==sum(app[a][i] for i in jj)
                if jj:close(z['precision'],hit/len(jj))
                else:assert z['precision'] is None
                if positive:close(z['recall'],hit/len(positive))
                else:assert z['recall'] is None
                if name in ['baseline','balanced']:
                    assert v['eligible']==old[a][name]['eligible'] and v['retained_supported']==old[a][name]['retained_supported'];assert hit==old[a][name]['lists']['hard'][label]['support']['supported'] and len(jj)==old[a][name]['lists']['hard'][label]['support']['selected']
                lists+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration216/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',source_prior_pairs=4,gate_groups=16,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
