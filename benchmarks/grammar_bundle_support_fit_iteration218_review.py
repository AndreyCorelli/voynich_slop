"""Independent scalar scores, tied rankings, metrics and baseline replay."""
from pathlib import Path
import json,math,hashlib
from benchmarks.grammar_case_applicability_iteration180_review import close
P=Path('experiments/results/grammar-restoration');O=P/'iteration218'
def read(p):return json.loads(p.read_text())
def run():
    ff=read(P/'iteration207/features.json');models=read(P/'iteration207/models.json');pred=read(O/'predictions.json');yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');dd=read(O/'details.json');ss=read(O/'summary.json');old=read(P/'iteration207/predictions.json');os=read(P/'iteration207/selections.json');oracle=read(P/'iteration210/details.json');lists=0;rankrecords=0;scalar=0
    for target,variants in models.items():
        for name,m in variants.items():
            for a,rows in ff.items():
                scores=[]
                for r in rows:
                    z=m['beta'][0]+sum((r['values'][col]-m['mean'][j])/m['scale'][j]*m['beta'][j+1] for j,col in enumerate(m['columns']));scores.append(1/(1+math.exp(-z)))
                close(scores,pred[target][name][a]);scalar+=len(rows);scores=pred[target][name][a];r=dd[target][name][a];assert r['role']==('held_out' if a==target else 'source_in_sample');pos=[i for i,v in enumerate(yy[a]) if v];neg=[i for i,v in enumerate(yy[a]) if not v];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in pos for j in neg)/(len(pos)*len(neg)) if pos and neg else None
                for view,eligible in [('original',list(range(len(rows)))),('oracle',[i for i,v in enumerate(app[a]) if v])]:
                    v=r['views'][view];assert v['eligible']==len(eligible);assert [z['index'] for z in v['ranks']]==pos
                    for z in v['ranks']:
                        i=z['index'];assert z['first']==1+sum(scores[j]>scores[i] for j in eligible) and z['last']==sum(scores[j]>=scores[i] for j in eligible);rankrecords+=1
                    for k in [3,5]:
                        label=f'top{k}';order=sorted(eligible,key=lambda i:-scores[i]);cut=scores[order[min(k,len(order))-1]];ix=sorted(i for i in order if scores[i]>=cut);assert ix==v['lists'][label];hit=sum(yy[a][i] for i in ix);close(v['metrics'][label],dict(selected=len(ix),supported=hit,precision=hit/len(ix),recall=hit/len(pos) if pos else None,coverage=len(ix)/len(rows),auc=auc));lists+=1
                    if a==target:
                        assert scores==old[a][name]
                        if view=='original':assert v['lists']==os[a][name]
                        else:assert v['lists']==oracle[a]['models'][name]['lists']['gated'] and v['ranks']==oracle[a]['models'][name]['gated_ranks']
    for name,roles in ss.items():
        for role,views in roles.items():
            for view,groups in views.items():
                for label,v in groups.items():
                    rr=[d[name][a]['views'][view]['metrics'][label] for t,d in dd.items() for a in d[name] if (a==t)==(role=='held_out')];hit=sum(r['supported'] for r in rr);n=sum(r['selected'] for r in rr);assert v['author_evaluations']==len(rr) and v['supported_instances']==hit and v['selected_instances']==n;close(v['pooled_precision'],hit/n)
    hashes=0
    manifests=[read(O/'design-freeze.json')]+[read(P/it/'verification-manifest.json') for it in ['iteration207','iteration210','iteration217']]+[read(P/'iteration217/correction-manifest.json')]
    for manifest in manifests:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'prediction-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',scalar_predictions=scalar,lists=lists,supported_rank_records=rankrecords,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
