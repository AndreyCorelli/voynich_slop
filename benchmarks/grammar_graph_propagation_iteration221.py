"""One synchronous half-self half-neighbor applicability step."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_bundle_selector_iteration207 import features,metrics
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration221'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_bundle_selector_iteration207.py','grammar_case_applicability_iteration180.py','grammar_bundle_hard_gate_iteration212.py']]+[P/n for n in ['iteration193/graphs.json','iteration204/bundles.json','iteration207/features.json','iteration207/predictions.json','iteration207/teacher-labels.json','iteration211/models.json','iteration211/predictions.json','iteration216/models.json','iteration216/predictions.json','iteration220/nodes.json','iteration220/labels.json','iteration220/verification-manifest.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration220/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');bundles=read(P/'iteration204/bundles.json');nodes=read(P/'iteration220/nodes.json');ff={a:features(graphs[a],bundles[a]) for a in nodes};eligible=read(P/'iteration207/features.json');indices={a:{r['word']:i for i,r in enumerate(rows)} for a,rows in ff.items()};projection={a:[indices[a][r['word']] for r in rows] for a,rows in eligible.items()}
    for a,ix in projection.items():assert [ff[a][i] for i in ix]==eligible[a]
    save(O/'features.json',ff);save(O/'center-projection.json',projection);save(O/'feature-freeze.json',{n:sha(O/n) for n in ['features.json','center-projection.json']})
    models={'baseline':read(P/'iteration211/models.json'),'balanced':read(P/'iteration216/models.json')};support=read(P/'iteration207/predictions.json');pred={};selections={}
    for a,rows in ff.items():
        pred[a]={};selections[a]={};lookup={r['word']:r for r in nodes[a]}
        for variant,mm in models.items():
            m=mm[a]['full12'] if variant=='baseline' else mm[a]['balanced'];p=predict(rows,m);refined=[.5*p[i]+.5*sum(p[indices[a][w]] for w in lookup[r['word']]['neighbors'])/len(lookup[r['word']]['neighbors']) for i,r in enumerate(rows)];pred[a][variant]=dict(original=p,refined=refined);selections[a][variant]={}
            for stage,values in pred[a][variant].items():
                centerp=[values[i] for i in projection[a]];gate=[i for i,v in enumerate(centerp) if v>=.5];product=[x*y for x,y in zip(centerp,support[a]['full12'])];selections[a][variant][stage]=dict(eligible=gate,hard={f'top{k}':top(support[a]['full12'],gate,k) for k in [3,5]},product={f'top{k}':top(product,list(range(len(centerp))),k) for k in [3,5]})
    save(O/'predictions.json',pred);save(O/'selections.json',selections);save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['predictions.json','selections.json']})
    labels=read(P/'iteration220/labels.json');yy=read(P/'iteration207/teacher-labels.json');oldbase=read(P/'iteration211/predictions.json');oldbalanced=read(P/'iteration216/predictions.json');summary={}
    for a,variants in pred.items():
        y=[labels[a][r['word']] for r in ff[a]];cy=[y[i] for i in projection[a]];summary[a]={}
        for variant,stages in variants.items():
            summary[a][variant]={}
            for stage,p in stages.items():
                cp=[p[i] for i in projection[a]];s=selections[a][variant][stage];positive=[i for i,v in enumerate(yy[a]) if v];product=[x*y for x,y in zip(cp,support[a]['full12'])];summary[a][variant][stage]=dict(all_nodes=evaluate(y,p),centers=evaluate(cy,cp),eligible=len(s['eligible']),retained_supported=[i for i in positive if i in s['eligible']],lists={mode:{label:dict(support=metrics(yy[a],support[a]['full12'] if mode=='hard' else product,ix),case_bearing=sum(cy[i] for i in ix)) for label,ix in s[mode].items()} for mode in ['hard','product']})
                if stage=='original':assert cp==(oldbase[a]['full12']['applicability'] if variant=='baseline' else oldbalanced[a]['balanced'][a])
    save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{variant:{stage:dict(auc=round(d['centers']['auc'],4),retained=len(d['retained_supported']),hard5=d['lists']['hard']['top5']['support']['supported'],product5=d['lists']['product']['top5']['support']['supported']) for stage,d in stages.items()} for variant,stages in v.items()})
if __name__=='__main__':run()
