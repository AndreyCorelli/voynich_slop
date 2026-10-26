"""Anonymous Case-bearing applicability pilot with fixed score products."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_multi_author_iteration193 import weighted_fit
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
from benchmarks.grammar_bundle_selector_iteration207 import metrics,top
P=Path('experiments/results/grammar-restoration');O=P/'iteration211'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),Path('benchmarks/grammar_case_applicability_iteration180.py'),Path('benchmarks/grammar_bundle_selector_iteration207.py')]+[P/f'iteration207/{n}.json' for n in ['features','predictions','teacher-labels','selections','verification-manifest']]+[P/f'iteration209/{n}.json' for n in ['details','verification-manifest']]+[P/'iteration210/verification-manifest.json']
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for it in ['iteration207','iteration209','iteration210']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration207/features.json');save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    refs=read(P/'iteration209/details.json');labels={a:[int(r['center_global_case_fraction']>0) for r in refs[a]] for a in ff};old=read(P/'iteration207/predictions.json');yy=read(P/'iteration207/teacher-labels.json');models={};pred={};selections={}
    for a in ff:
        source=[b for b in ff if b!=a];raw=[r['values'] for b in source for r in ff[b]];y=[v for b in source for v in labels[b]];w=[1/len(ff[b]) for b in source for r in ff[b]];models[a]={};pred[a]={};selections[a]={}
        for name,cols in [('full12',list(range(12))),('count4',list(range(4)))]:
            m=weighted_fit(raw,y,w,cols);models[a][name]=m;app=predict(ff[a],m);pred[a][name]={'support':old[a][name],'applicability':app,'product':[p*q for p,q in zip(app,old[a][name])]};selections[a][name]={kind:{f'top{k}':top(scores,k) for k in [3,5]} for kind,scores in pred[a][name].items()}
    for n,v in [('models',models),('predictions',pred),('selections',selections)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['models.json','predictions.json','selections.json']})
    summary={}
    for a in ff:
        summary[a]=dict(candidates=len(ff[a]),case_bearing=sum(labels[a]),supported=sum(yy[a]),models={name:dict(applicability=evaluate(labels[a],kinds['applicability']),lists={kind:{label:dict(support=metrics(yy[a],scores,ix),case_bearing=sum(labels[a][i] for i in ix)) for label,ix in selections[a][name][kind].items()} for kind,scores in kinds.items()}) for name,kinds in pred[a].items()})
    save(O/'applicability-labels.json',labels);save(O/'summary.json',summary)
    for a,d in summary.items():
        print(a,{name:dict(auc=v['applicability']['auc'],lists={kind:{k:(z['support']['supported'],z['support']['selected'],z['case_bearing']) for k,z in lists.items()} for kind,lists in v['lists'].items()}) for name,v in d['models'].items()})
if __name__=='__main__':run()
