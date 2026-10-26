"""Conditional support fit on source Case-bearing centers only."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_multi_author_iteration193 import weighted_fit
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
from benchmarks.grammar_bundle_selector_iteration207 import metrics
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration219'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_multi_author_iteration193.py','grammar_case_applicability_iteration180.py','grammar_bundle_selector_iteration207.py','grammar_bundle_hard_gate_iteration212.py']]+[P/n for n in ['iteration207/features.json','iteration207/models.json','iteration207/predictions.json','iteration207/teacher-labels.json','iteration211/applicability-labels.json','iteration216/predictions.json','iteration216/summary.json','iteration218/verification-manifest.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration218/verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration207/features.json');save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');old=read(P/'iteration207/models.json');gatepred=read(P/'iteration216/predictions.json');models={};pred={};sel={};training={}
    for target in ff:
        sources=[a for a in ff if a!=target];training[target]={a:[i for i,v in enumerate(app[a]) if v] for a in sources};raw=[ff[a][i]['values'] for a in sources for i in training[target][a]];y=[yy[a][i] for a in sources for i in training[target][a]];w=[1/len(training[target][a]) for a in sources for i in training[target][a]];models[target]={};pred[target]={};sel[target]={}
        for name,cols in [('full12',list(range(12))),('count4',list(range(4)))]:
            models[target][name]=dict(baseline=old[target][name],conditional=weighted_fit(raw,y,w,cols));pred[target][name]={};sel[target][name]={}
            for variant,m in models[target][name].items():
                scores={a:predict(rows,m) for a,rows in ff.items()};pred[target][name][variant]=scores;targetp=scores[target];gp=gatepred[target]['balanced'][target];gate=[i for i,v in enumerate(gp) if v>=.5];oracle=[i for i,v in enumerate(app[target]) if v];product=[p*q for p,q in zip(gp,targetp)];sel[target][name][variant]={mode:{f'top{k}':top(s,ix,k) for k in [3,5]} for mode,s,ix in [('gate',targetp,gate),('product',product,list(range(len(gp)))),('oracle',targetp,oracle)]}
    for n,v in [('training',training),('models',models),('predictions',pred),('selections',sel)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['training.json','models.json','predictions.json','selections.json']})
    summary={};source={}
    for target in ff:
        summary[target]={};source[target]={}
        for name in models[target]:
            summary[target][name]={};source[target][name]={}
            for variant in models[target][name]:
                gp=gatepred[target]['balanced'][target];p=pred[target][name][variant][target];product=[a*b for a,b in zip(gp,p)];summary[target][name][variant]=dict(lists={mode:{label:dict(support=metrics(yy[target],product if mode=='product' else p,ix),case_bearing=sum(app[target][i] for i in ix)) for label,ix in lists.items()} for mode,lists in sel[target][name][variant].items()},classification=evaluate(yy[target],p));source[target][name][variant]={a:evaluate([yy[a][i] for i in ix],[pred[target][name][variant][a][i] for i in ix]) for a,ix in training[target].items()}
    save(O/'summary.json',summary);save(O/'source-summary.json',source)
    for a,v in summary.items():print(a,{n:{variant:{mode:z['support']['supported'] for mode,lists in d['lists'].items() for label,z in lists.items() if label=='top5'} for variant,d in variants.items()} for n,variants in v.items()})
if __name__=='__main__':run()
