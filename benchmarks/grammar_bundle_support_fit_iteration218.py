"""Frozen support-ranker source heads and oracle Case-bearing comparators."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_case_applicability_iteration180 import predict
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
from benchmarks.grammar_bundle_selector_iteration207 import metrics
P=Path('experiments/results/grammar-restoration');O=P/'iteration218'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_case_applicability_iteration180.py','grammar_bundle_hard_gate_iteration212.py','grammar_bundle_selector_iteration207.py']]+[P/n for n in ['iteration207/models.json','iteration207/features.json','iteration207/predictions.json','iteration207/selections.json','iteration207/teacher-labels.json','iteration207/verification-manifest.json','iteration210/details.json','iteration210/verification-manifest.json','iteration211/applicability-labels.json','iteration217/verification-manifest.json','iteration217/correction-manifest.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for it in ['iteration207','iteration210','iteration217']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    for p,h in read(P/'iteration217/correction-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration207/features.json');models=read(P/'iteration207/models.json');pred={t:{n:{a:predict(rows,m) for a,rows in ff.items()} for n,m in variants.items()} for t,variants in models.items()};save(O/'predictions.json',pred);save(O/'prediction-freeze.json',{'predictions.json':sha(O/'predictions.json')})
    yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');old=read(P/'iteration207/predictions.json');oldsel=read(P/'iteration207/selections.json');oracle=read(P/'iteration210/details.json');details={};summary={}
    for target,variants in pred.items():
        details[target]={}
        for name,authors in variants.items():
            details[target][name]={}
            for a,scores in authors.items():
                views={};positive=[i for i,v in enumerate(yy[a]) if v]
                for view,eligible in [('original',list(range(len(scores)))),('oracle',[i for i,v in enumerate(app[a]) if v])]:
                    lists={f'top{k}':top(scores,eligible,k) for k in [3,5]};ranks=[dict(index=i,first=1+sum(scores[j]>scores[i] for j in eligible),last=sum(scores[j]>=scores[i] for j in eligible)) for i in positive];views[view]=dict(eligible=len(eligible),lists=lists,metrics={label:metrics(yy[a],scores,ix) for label,ix in lists.items()},ranks=ranks)
                    if a==target:
                        assert scores==old[a][name]
                        if view=='original':assert lists==oldsel[a][name]
                        else:assert lists==oracle[a]['models'][name]['lists']['gated'] and ranks==oracle[a]['models'][name]['gated_ranks']
                details[target][name][a]=dict(role='held_out' if a==target else 'source_in_sample',views=views)
    for name in ['full12','count4']:
        summary[name]={}
        for role in ['source_in_sample','held_out']:
            summary[name][role]={}
            for view in ['original','oracle']:
                result={}
                for label in ['top3','top5']:
                    rows=[r['views'][view]['metrics'][label] for t,v in details.items() for a,r in v[name].items() if r['role']==role];hits=sum(r['supported'] for r in rows);selected=sum(r['selected'] for r in rows);result[label]=dict(author_evaluations=len(rows),supported_instances=hits,selected_instances=selected,pooled_precision=hits/selected if selected else None)
                summary[name][role][view]=result
    save(O/'details.json',details);save(O/'summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
