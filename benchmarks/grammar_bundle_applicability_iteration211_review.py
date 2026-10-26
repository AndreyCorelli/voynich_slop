"""Independent source-only Newton fits, products, ranks and metrics."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.special import expit
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration211'
def read(p):return json.loads(p.read_text())
def near(x,y,tol=1e-10):assert np.allclose(x,y,atol=tol,rtol=tol),(x,y)
def run():
    ff=read(O/'features.json');yy=read(O/'applicability-labels.json');refs=read(P/'iteration209/details.json');sy=read(P/'iteration207/teacher-labels.json');old=read(P/'iteration207/predictions.json');om=read(P/'iteration207/summary.json');models=read(O/'models.json');pred=read(O/'predictions.json');sel=read(O/'selections.json');ss=read(O/'summary.json');assert ff==read(P/'iteration207/features.json');fits=0;lists=0
    for a,rows in ff.items():
        assert yy[a]==[int(r['center_global_case_fraction']>0) for r in refs[a]]
        assert ss[a]['candidates']==len(rows) and ss[a]['case_bearing']==sum(yy[a]) and ss[a]['supported']==sum(sy[a])
        for name,m in models[a].items():
            src=[s for s in ff if s!=a];raw=np.array([r['values'] for s in src for r in ff[s]])[:,m['columns']];y=np.array([v for s in src for v in yy[s]]);w=np.array([1/(3*len(ff[s])) for s in src for r in ff[s]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);beta=np.zeros(x.shape[1]);pen=np.eye(len(beta))*.1;pen[0,0]=0
            def loss(b):return w@(np.logaddexp(0,x@b)-y*(x@b))+.5*b@pen@b
            for it in range(100):
                p=expit(x@beta);grad=x.T@(w*(p-y))+pen@beta
                if max(abs(grad))<1e-12:break
                step=np.linalg.solve(x.T@((w*p*(1-p))[:,None]*x)+pen,grad);rate=1.
                while loss(beta-rate*step)>loss(beta)-1e-4*rate*(grad@step):
                    rate*=.5
                    if rate<1e-10:break
                beta-=rate*step
            near(beta,m['beta'],2e-6);fits+=1
            tx=np.array([r['values'] for r in rows])[:,m['columns']];out=expit(np.column_stack([np.ones(len(rows)),(tx-mu)/sd])@np.array(m['beta']));near(out,pred[a][name]['applicability']);close(independent_evaluate(yy[a],pred[a][name]['applicability']),ss[a]['models'][name]['applicability']);assert pred[a][name]['support']==old[a][name];near(pred[a][name]['product'],[p*q for p,q in zip(out,old[a][name])])
            for kind,scores in pred[a][name].items():
                pos=[i for i,v in enumerate(sy[a]) if v];neg=[i for i,v in enumerate(sy[a]) if not v];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in pos for j in neg)/(len(pos)*len(neg)) if pos and neg else None
                for k in [3,5]:
                    label='top'+str(k);cut=sorted(scores,reverse=True)[k-1];ix=[i for i,s in enumerate(scores) if s>=cut];assert ix==sel[a][name][kind][label];v=ss[a]['models'][name]['lists'][kind][label];hit=sum(sy[a][i] for i in ix);assert v['case_bearing']==sum(yy[a][i] for i in ix);expected=dict(selected=len(ix),supported=hit,precision=hit/len(ix),recall=hit/len(pos) if pos else None,coverage=len(ix)/len(rows),auc=auc);close(expected,v['support'])
                    if kind=='support':close(v['support'],om[a]['models'][name]['lists'][label])
                    lists+=1
    hashes=0
    for name in ['design-freeze.json','feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/name).items():
            path=Path(p) if '/' in p else O/p;assert hashlib.sha256(path.read_bytes()).hexdigest()==h;hashes+=1
    for it in ['iteration207','iteration209','iteration210']:
        for p,h in read(P/it/'verification-manifest.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',newton_refits=fits,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
