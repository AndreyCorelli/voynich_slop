"""Scalar prediction, role and metric replay, independent of matrix predictor."""
from pathlib import Path
import json,math,hashlib
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration215'
def read(p):return json.loads(p.read_text())
def run():
    ff=read(P/'iteration214/features.json');mm=read(P/'iteration214/models.json');pp=read(O/'predictions.json');dd=read(O/'details.json');ss=read(O/'summary.json');app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');old=read(P/'iteration214/predictions.json');olds=read(P/'iteration214/summary.json');groups=0;predictions=0
    for target,variants in mm.items():
        for name,m in variants.items():
            for a,rows in ff.items():
                values=[]
                for row in rows:
                    z=m['beta'][0]+sum((row['values'][c]-m['mean'][j])/m['scale'][j]*m['beta'][j+1] for j,c in enumerate(m['columns']));values.append(1/(1+math.exp(-z)))
                close(values,pp[target][name][a]);predictions+=len(rows);r=dd[target][name][a];assert r['role']==('held_out' if a==target else 'source_in_sample');close(independent_evaluate(app[a],pp[target][name][a]),r['applicability']);positive=[i for i,v in enumerate(yy[a]) if v];ret=[i for i in positive if pp[target][name][a][i]>=.5];lost=[i for i in positive if i not in ret];assert r['supported']==len(positive) and r['retained']==ret and r['rejected']==[dict(index=i,word=rows[i]['word']) for i in lost];v=[pp[target][name][a][i] for i in positive];close(r['supported_probability_range'],[min(v),max(v)] if v else None);close(r['supported_probability_mean'],sum(v)/len(v) if v else None);close(r['support_retention'],len(ret)/len(positive) if positive else None)
                if a==target:assert pp[target][name][a]==old[a][name]['applicability'] and r['applicability']==olds[a][name]['applicability'] and ret==olds[a][name]['retained_supported']
                groups+=1
    for name,roles in ss.items():
        for role,v in roles.items():
            records=[(a,r) for t in dd for a,r in dd[t][name].items() if (a==t)==(role=='held_out')];n=sum(r['supported'] for a,r in records);k=sum(len(r['retained']) for a,r in records);assert v['author_evaluations']==len(records) and v['supported_evaluation_instances']==n and v['retained_instances']==k;close(v['retention'],k/n if n else None)
            for a,r in v['by_author'].items():
                rows=[z for b,z in records if b==a];assert r==dict(evaluations=len(rows),supported_instances=sum(z['supported'] for z in rows),retained_instances=sum(len(z['retained']) for z in rows))
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration214/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'prediction-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',scalar_predictions=predictions,evaluation_groups=groups,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
