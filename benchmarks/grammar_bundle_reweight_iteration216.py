"""Source-only relevance-balanced applicability; fixed loss and comparators."""
from pathlib import Path
from collections import Counter
import json,hashlib
from benchmarks.grammar_multi_author_iteration193 import weighted_fit
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
from benchmarks.grammar_bundle_selector_iteration207 import metrics
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration216'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_multi_author_iteration193.py','grammar_case_applicability_iteration180.py','grammar_bundle_selector_iteration207.py','grammar_bundle_hard_gate_iteration212.py']]+[P/n for n in ['iteration211/features.json','iteration211/models.json','iteration211/applicability-labels.json','iteration207/teacher-labels.json','iteration207/predictions.json','iteration215/verification-manifest.json','iteration210/summary.json','iteration214/summary.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration215/verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration211/features.json');save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');baseline=read(P/'iteration211/models.json');support=read(P/'iteration207/predictions.json');weights={};models={};pred={};lists={}
    for target in ff:
        src=[a for a in ff if a!=target];raw=[];y=[];ww=[];weights[target]={}
        for a in src:
            groups=['supported' if yy[a][i] else 'other_case' if app[a][i] else 'no_case' for i in range(len(ff[a]))];assert all(app[a][i] for i,g in enumerate(groups) if g=='supported');counts=Counter(groups);w=[1/(3*len(counts)*counts[g]) for g in groups];weights[target][a]=dict(groups=groups,counts=dict(counts),weights=w);raw.extend(r['values'] for r in ff[a]);y.extend(app[a]);ww.extend(w)
        models[target]=dict(baseline=baseline[target]['full12'],balanced=weighted_fit(raw,y,ww,list(range(12))));pred[target]={};lists[target]={}
        for name,m in models[target].items():
            pred[target][name]={a:predict(rows,m) for a,rows in ff.items()};p=pred[target][name][target];product=[x*y for x,y in zip(p,support[target]['full12'])];eligible=[i for i,z in enumerate(p) if z>=.5];lists[target][name]=dict(eligible=eligible,hard={f'top{k}':top(support[target]['full12'],eligible,k) for k in [3,5]},product={f'top{k}':top(product,list(range(len(p))),k) for k in [3,5]})
    for n,v in [('weights',weights),('models',models),('predictions',pred),('selections',lists)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['weights.json','models.json','predictions.json','selections.json']})
    summary={};source={}
    for target in ff:
        summary[target]={};source[target]={}
        for name in models[target]:
            p=pred[target][name][target];product=[x*y for x,y in zip(p,support[target]['full12'])];eligible=lists[target][name]['eligible'];positive=[i for i,v in enumerate(yy[target]) if v];summary[target][name]=dict(applicability=evaluate(app[target],p),eligible=len(eligible),retained_supported=[i for i in positive if i in eligible],rejected_supported=[i for i in positive if i not in eligible],lists={mode:{label:dict(support=metrics(yy[target],support[target]['full12'] if mode=='hard' else product,ix),case_bearing=sum(app[target][i] for i in ix)) for label,ix in lists[target][name][mode].items()} for mode in ['hard','product']})
            source[target][name]={a:dict(supported=sum(yy[a]),retained=sum(v and pred[target][name][a][i]>=.5 for i,v in enumerate(yy[a])),applicability=evaluate(app[a],pred[target][name][a])) for a in ff if a!=target}
    save(O/'summary.json',summary);save(O/'source-summary.json',source)
    for a,mm in summary.items():print(a,{n:dict(auc=round(v['applicability']['auc'],4),retained=len(v['retained_supported']),hard5=v['lists']['hard']['top5']['support']['supported'],product5=v['lists']['product']['top5']['support']['supported']) for n,v in mm.items()})
    print('SOURCE',{n:(sum(v[n][a]['retained'] for t,v in source.items() for a in v[n]),sum(v[n][a]['supported'] for t,v in source.items() for a in v[n])) for n in ['baseline','balanced']})
if __name__=='__main__':run()
