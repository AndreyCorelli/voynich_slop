"""Independent Newton and scalar replay of all fixed ablations."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.special import expit
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration214'
def read(p):return json.loads(p.read_text())
def near(a,b,tol=1e-10):assert np.allclose(a,b,atol=tol,rtol=tol)
def run():
    ff=read(O/'features.json');app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');support=read(P/'iteration207/predictions.json');models=read(O/'models.json');pred=read(O/'predictions.json');sel=read(O/'selections.json');ss=read(O/'summary.json');old=read(P/'iteration211/predictions.json');oldmodels=read(P/'iteration211/models.json');oldhard=read(P/'iteration212/selections.json');oracle=read(P/'iteration210/summary.json');assert ff==read(P/'iteration211/features.json');fits=0;lists=0
    variants={'full12':list(range(12)),'no_frequency':list(range(1,12)),'no_reuse':[j for j in range(12) if j!=4],'neither':[j for j in range(12) if j not in [0,4]]}
    for a,rows in ff.items():
        for name,m in models[a].items():
            assert m['columns']==variants[name];src=[b for b in ff if b!=a];raw=np.array([r['values'] for b in src for r in ff[b]])[:,m['columns']];y=np.array([v for b in src for v in app[b]]);w=np.array([1/(3*len(ff[b])) for b in src for r in ff[b]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);beta=np.zeros(x.shape[1]);pen=np.eye(len(beta))*.1;pen[0,0]=0
            def loss(b):return w@(np.logaddexp(0,x@b)-y*(x@b))+.5*b@pen@b
            for it in range(100):
                p=expit(x@beta);gradient=x.T@(w*(p-y))+pen@beta
                if max(abs(gradient))<1e-12:break
                step=np.linalg.solve(x.T@((w*p*(1-p))[:,None]*x)+pen,gradient);rate=1.
                while loss(beta-rate*step)>loss(beta)-1e-4*rate*(gradient@step):
                    rate*=.5
                    if rate<1e-10:break
                beta-=rate*step
            near(beta,m['beta'],2e-6);fits+=1;tx=np.array([r['values'] for r in rows])[:,m['columns']];out=expit(np.column_stack([np.ones(len(rows)),(tx-mu)/sd])@np.array(m['beta']));near(out,pred[a][name]['applicability']);near(out*np.array(support[a]['full12']),pred[a][name]['product']);v=ss[a][name];close(independent_evaluate(app[a],pred[a][name]['applicability']),v['applicability']);keep=[i for i,p in enumerate(pred[a][name]['applicability']) if p>=.5];assert keep==sel[a][name]['eligible'];positive=[i for i,z in enumerate(yy[a]) if z];assert v['eligible']==len(keep) and v['retained_supported']==[i for i in positive if i in keep] and v['rejected_supported']==[i for i in positive if i not in keep]
            for mode,scores,universe in [('hard',support[a]['full12'],keep),('product',pred[a][name]['product'],list(range(len(rows)))),('original',support[a]['full12'],list(range(len(rows))))]:
                neg=[i for i,z in enumerate(yy[a]) if not z];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in positive for j in neg)/(len(positive)*len(neg)) if positive and neg else None
                for k in [3,5]:
                    label=f'top{k}';cut=sorted([scores[i] for i in universe],reverse=True)[min(k,len(universe))-1] if universe else None;ix=[i for i in universe if scores[i]>=cut] if universe else [];hit=sum(yy[a][i] for i in ix);expected=dict(selected=len(ix),supported=hit,precision=hit/len(ix) if ix else None,recall=hit/len(positive) if positive else None,coverage=len(ix)/len(rows),auc=auc)
                    if mode=='original':close(expected,v['original'][label])
                    else:
                        assert ix==sel[a][name][mode][label];close(expected,v['lists'][mode][label]['support']);assert v['lists'][mode][label]['case_bearing']==sum(app[a][i] for i in ix);lists+=1
            assert v['oracle']==oracle[a]['models']['full12']['gated']
            if name=='full12':assert m==oldmodels[a]['full12'] and pred[a][name]=={k:old[a]['full12'][k] for k in ['applicability','product']} and sel[a][name]['hard']==oldhard[a]['full12']['lists']
    hashes=0
    for fn in ['design-freeze.json','feature-freeze.json','prediction-freeze.json']:
        manifest=read(O/fn);manifest=manifest.get('inputs',manifest)
        for p,h in manifest.items():
            path=Path(p) if '/' in p else O/p;assert hashlib.sha256(path.read_bytes()).hexdigest()==h;hashes+=1
    for it in ['iteration211','iteration212','iteration213']:
        for p,h in read(P/it/'verification-manifest.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',newton_refits=fits,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
