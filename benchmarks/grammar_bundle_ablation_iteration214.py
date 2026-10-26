"""Fixed frequency/reuse ablation; development-only, no model selection."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_multi_author_iteration193 import weighted_fit
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
from benchmarks.grammar_bundle_selector_iteration207 import metrics
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration214'
VARIANTS={'full12':list(range(12)),'no_frequency':list(range(1,12)),'no_reuse':[i for i in range(12) if i!=4],'neither':[i for i in range(12) if i not in [0,4]]}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),Path('benchmarks/grammar_case_applicability_iteration180.py'),Path('benchmarks/grammar_bundle_selector_iteration207.py'),Path('benchmarks/grammar_bundle_hard_gate_iteration212.py')]+[P/n for n in ['iteration211/features.json','iteration211/applicability-labels.json','iteration211/models.json','iteration211/predictions.json','iteration211/verification-manifest.json','iteration207/teacher-labels.json','iteration207/predictions.json','iteration212/selections.json','iteration212/verification-manifest.json','iteration213/verification-manifest.json','iteration210/summary.json']]
    save(O/'design-freeze.json',dict(variants=VARIANTS,inputs={str(p):sha(p) for p in paths}))
    for it in ['iteration211','iteration212','iteration213']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration211/features.json');save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    app=read(P/'iteration211/applicability-labels.json');old=read(P/'iteration207/predictions.json');models={};pred={};selections={}
    for a in ff:
        src=[b for b in ff if b!=a];raw=[r['values'] for b in src for r in ff[b]];y=[v for b in src for v in app[b]];weights=[1/len(ff[b]) for b in src for r in ff[b]];models[a]={};pred[a]={};selections[a]={}
        for name,cols in VARIANTS.items():
            m=weighted_fit(raw,y,weights,cols);models[a][name]=m;p=predict(ff[a],m);product=[x*y for x,y in zip(p,old[a]['full12'])];eligible=[i for i,v in enumerate(p) if v>=.5];pred[a][name]=dict(applicability=p,product=product);selections[a][name]=dict(eligible=eligible,hard={f'top{k}':top(old[a]['full12'],eligible,k) for k in [3,5]},product={f'top{k}':top(product,list(range(len(p))),k) for k in [3,5]})
    for n,v in [('models',models),('predictions',pred),('selections',selections)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['models.json','predictions.json','selections.json']})
    yy=read(P/'iteration207/teacher-labels.json');previous=read(P/'iteration211/predictions.json');previousmodels=read(P/'iteration211/models.json');previoushard=read(P/'iteration212/selections.json');oracle=read(P/'iteration210/summary.json');summary={}
    for a in ff:
        assert models[a]['full12']==previousmodels[a]['full12'];assert pred[a]['full12']=={k:previous[a]['full12'][k] for k in ['applicability','product']};assert selections[a]['full12']['hard']==previoushard[a]['full12']['lists'];summary[a]={}
        for name,v in pred[a].items():
            s=selections[a][name];positive=[i for i,z in enumerate(yy[a]) if z];summary[a][name]=dict(applicability=evaluate(app[a],v['applicability']),eligible=len(s['eligible']),retained_supported=[i for i in positive if i in s['eligible']],rejected_supported=[i for i in positive if i not in s['eligible']],lists={mode:{label:dict(support=metrics(yy[a],old[a]['full12'] if mode=='hard' else v['product'],ix),case_bearing=sum(app[a][i] for i in ix)) for label,ix in s[mode].items()} for mode in ['hard','product']},original={f'top{k}':metrics(yy[a],old[a]['full12'],top(old[a]['full12'],list(range(len(ff[a]))),k)) for k in [3,5]},oracle=oracle[a]['models']['full12']['gated'])
    save(O/'summary.json',summary)
    for a,mm in summary.items():print(a,{n:dict(auc=round(v['applicability']['auc'],4),retained=len(v['retained_supported']),hard5=v['lists']['hard']['top5']['support']['supported'],product5=v['lists']['product']['top5']['support']['supported']) for n,v in mm.items()})
if __name__=='__main__':run()
