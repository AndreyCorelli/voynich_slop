"""Fixed degree-preserving rewiring and global-mean controls."""
from pathlib import Path
import json,hashlib,random
import numpy as np
from benchmarks.grammar_case_applicability_iteration180 import evaluate
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration222'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def rewire(edges,seed):
    rng=random.Random(seed);ee=[tuple(e) for e in edges];present=set(ee);accepted=attempts=0
    while accepted<10*len(ee) and attempts<100*len(ee):
        attempts+=1;i,j=rng.sample(range(len(ee)),2);a,b=ee[i];c,d=ee[j]
        if len({a,b,c,d})<4:continue
        if rng.randrange(2):c,d=d,c
        x=tuple(sorted((a,c)));y=tuple(sorted((b,d)))
        if x in present or y in present:continue
        present.remove(ee[i]);present.remove(ee[j]);present.update([x,y]);ee[i]=x;ee[j]=y;accepted+=1
    return sorted(ee),dict(seed=seed,attempts=attempts,accepted=accepted,target=10*len(ee))
def propagate(p,edges):
    sums=np.zeros(len(p));degree=np.zeros(len(p))
    for u,v in edges:sums[u]+=p[v];sums[v]+=p[u];degree[u]+=1;degree[v]+=1
    return (.5*np.array(p)+.5*sums/degree).tolist()
def compact(p,y,projection,support,sy):
    cp=[p[i] for i in projection];cy=[y[i] for i in projection];allm=evaluate(y,p);cm=evaluate(cy,cp);keep=[i for i,v in enumerate(cp) if v>=.5];product=[a*b for a,b in zip(cp,support)];result=dict(all_auc=allm['auc'],all_nll=allm['nll'],center_auc=cm['auc'],center_nll=cm['nll'],retained=sum(sy[i] for i in keep),admissions=len(keep))
    for mode,scores,ix in [('hard',support,keep),('product',product,list(range(len(cp))))]:
        for k in [3,5]:
            jj=top(scores,ix,k);result[f'{mode}{k}_hits']=sum(sy[i] for i in jj);result[f'{mode}{k}_selected']=len(jj)
    return result

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),Path('benchmarks/grammar_bundle_hard_gate_iteration212.py')]+[P/n for n in ['iteration221/features.json','iteration221/predictions.json','iteration221/center-projection.json','iteration221-finalization/verification-manifest.json','iteration220/nodes.json','iteration220/labels.json','iteration207/predictions.json','iteration207/teacher-labels.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration221-finalization/verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration221/features.json');nodes=read(P/'iteration220/nodes.json');graphs={};audit={};actualedges={}
    for a,rows in ff.items():
        index={r['word']:i for i,r in enumerate(rows)};edges=sorted({tuple(sorted((index[r['word']],index[v]))) for r in nodes[a] for v in r['neighbors']});actualedges[a]=edges;graphs[a]=[];audit[a]=[]
        for seed in range(22200,22399):
            e,log=rewire(edges,seed);graphs[a].append(e);audit[a].append(log)
    save(O/'rewired-edges.json',graphs);save(O/'rewiring-audit.json',audit);save(O/'graph-freeze.json',{n:sha(O/n) for n in ['rewired-edges.json','rewiring-audit.json']})
    pred=read(P/'iteration221/predictions.json');projection=read(P/'iteration221/center-projection.json');scores={}
    for a,variants in pred.items():
        scores[a]={}
        for variant,stages in variants.items():
            p=stages['original'];globalmean=sum(p)/len(p);actual=propagate(p,actualedges[a]);assert np.allclose(actual,stages['refined'],atol=1e-14,rtol=1e-14);scores[a][variant]=dict(original=p,actual=actual,global_mean=[.5*v+.5*globalmean for v in p],rewired=[propagate(p,e) for e in graphs[a]])
    save(O/'scores.json',scores);save(O/'score-freeze.json',{'scores.json':sha(O/'scores.json')})
    labels=read(P/'iteration220/labels.json');support=read(P/'iteration207/predictions.json');sy=read(P/'iteration207/teacher-labels.json');details={};summary={}
    for a,variants in scores.items():
        y=[labels[a][r['word']] for r in ff[a]];details[a]={};summary[a]={}
        for variant,methods in variants.items():
            rows={name:([compact(p,y,projection[a],support[a]['full12'],sy[a]) for p in pp] if name=='rewired' else compact(pp,y,projection[a],support[a]['full12'],sy[a])) for name,pp in methods.items()};details[a][variant]=rows;summary[a][variant]={}
            for metric,value in rows['actual'].items():
                null=[r[metric] for r in rows['rewired']];low=metric.endswith('nll');tail=(1+sum(v<=value+1e-12 if low else v>=value-1e-12 for v in null))/200;summary[a][variant][metric]=dict(original=rows['original'][metric],actual=value,global_mean=rows['global_mean'][metric],null_mean=sum(null)/len(null),null_min=min(null),null_max=max(null),directional_tail=tail)
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{variant:{k:d for k,d in mm.items() if k in ['center_auc','center_nll','retained','hard5_hits']} for variant,mm in v.items()})
if __name__=='__main__':run()
