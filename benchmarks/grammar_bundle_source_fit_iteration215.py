"""Source-side in-sample diagnostics for frozen applicability models."""
from pathlib import Path
import json,hashlib
from benchmarks.grammar_case_applicability_iteration180 import predict,evaluate
P=Path('experiments/results/grammar-restoration');O=P/'iteration215'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py')]+[P/n for n in ['iteration214/features.json','iteration214/models.json','iteration214/predictions.json','iteration214/summary.json','iteration214/verification-manifest.json','iteration211/applicability-labels.json','iteration207/teacher-labels.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration214/verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration214/features.json');models=read(P/'iteration214/models.json');pred={target:{variant:{a:predict(rows,m) for a,rows in ff.items()} for variant,m in variants.items()} for target,variants in models.items()};save(O/'predictions.json',pred);save(O/'prediction-freeze.json',{'predictions.json':sha(O/'predictions.json')})
    app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');oldpred=read(P/'iteration214/predictions.json');oldsummary=read(P/'iteration214/summary.json');details={};summary={}
    for target,variants in pred.items():
        details[target]={}
        for variant,authors in variants.items():
            details[target][variant]={}
            for a,scores in authors.items():
                positive=[i for i,v in enumerate(yy[a]) if v];kept=[i for i in positive if scores[i]>=.5];lost=[i for i in positive if scores[i]<.5];pp=[scores[i] for i in positive];r=dict(role='held_out' if a==target else 'source_in_sample',applicability=evaluate(app[a],scores),supported=len(positive),retained=kept,rejected=[dict(index=i,word=ff[a][i]['word']) for i in lost],support_retention=len(kept)/len(positive) if positive else None,supported_probability_range=[min(pp),max(pp)] if pp else None,supported_probability_mean=sum(pp)/len(pp) if pp else None);details[target][variant][a]=r
                if a==target:
                    assert scores==oldpred[target][variant]['applicability'];assert r['applicability']==oldsummary[target][variant]['applicability'];assert kept==oldsummary[target][variant]['retained_supported']
    for variant in next(iter(models.values())):
        summary[variant]={}
        for role in ['source_in_sample','held_out']:
            rows=[r for target,v in details.items() for a,r in v[variant].items() if r['role']==role];n=sum(r['supported'] for r in rows);k=sum(len(r['retained']) for r in rows);summary[variant][role]=dict(author_evaluations=len(rows),supported_evaluation_instances=n,retained_instances=k,retention=k/n if n else None,by_author={a:dict(evaluations=sum(a in v[variant] and v[variant][a]['role']==role for v in details.values()),supported_instances=sum(v[variant][a]['supported'] for v in details.values() if v[variant][a]['role']==role),retained_instances=sum(len(v[variant][a]['retained']) for v in details.values() if v[variant][a]['role']==role)) for a in ff})
    save(O/'details.json',details);save(O/'summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
