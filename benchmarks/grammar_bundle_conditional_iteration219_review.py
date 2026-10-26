"""Independent conditional eligibility, Newton fits, predictions and lists."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.special import expit
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration219'
def read(p):return json.loads(p.read_text())
def near(a,b,tol=1e-10):assert np.allclose(a,b,atol=tol,rtol=tol)
def run():
    ff=read(O/'features.json');yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');mm=read(O/'models.json');pp=read(O/'predictions.json');sel=read(O/'selections.json');ss=read(O/'summary.json');source=read(O/'source-summary.json');training=read(O/'training.json');gp=read(P/'iteration216/predictions.json');old=read(P/'iteration207/models.json');op=read(P/'iteration207/predictions.json');prior=read(P/'iteration216/summary.json');fits=0;lists=0
    assert ff==read(P/'iteration207/features.json')
    for target in ff:
        src=[a for a in ff if a!=target];expected={a:[i for i,v in enumerate(app[a]) if v] for a in src};assert training[target]==expected
        for name,variants in mm[target].items():
            m=variants['conditional'];cols=m['columns'];raw=np.array([ff[a][i]['values'] for a in src for i in expected[a]])[:,cols];y=np.array([yy[a][i] for a in src for i in expected[a]]);w=np.array([1/(3*len(expected[a])) for a in src for i in expected[a]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);b=np.zeros(len(cols)+1);pen=np.eye(len(b))*.1;pen[0,0]=0
            def loss(v):return w@(np.logaddexp(0,x@v)-y*(x@v))+.5*v@pen@v
            for it in range(100):
                p=expit(x@b);grad=x.T@(w*(p-y))+pen@b
                if max(abs(grad))<1e-12:break
                step=np.linalg.solve(x.T@((w*p*(1-p))[:,None]*x)+pen,grad);rate=1.
                while loss(b-rate*step)>loss(b)-1e-4*rate*(grad@step):
                    rate*=.5
                    if rate<1e-10:break
                b-=rate*step
            near(b,m['beta'],2e-6);fits+=1
            for variant,m in variants.items():
                if variant=='baseline':assert m==old[target][name]
                for a,rows in ff.items():
                    tx=np.array([r['values'] for r in rows])[:,m['columns']];near(expit(np.column_stack([np.ones(len(rows)),(tx-m['mean'])/m['scale']])@np.array(m['beta'])),pp[target][name][variant][a])
                    if a!=target:
                        ix=expected[a];close(independent_evaluate([yy[a][i] for i in ix],[pp[target][name][variant][a][i] for i in ix]),source[target][name][variant][a])
                p=pp[target][name][variant][target];v=ss[target][name][variant];close(independent_evaluate(yy[target],p),v['classification']);gateprob=gp[target]['balanced'][target]
                if variant=='baseline':assert p==op[target][name]
                for mode,scores,universe in [('gate',p,[i for i,z in enumerate(gateprob) if z>=.5]),('product',[a*b for a,b in zip(p,gateprob)],list(range(len(p)))),('oracle',p,[i for i,z in enumerate(app[target]) if z])]:
                    pos=[i for i,z in enumerate(yy[target]) if z];neg=[i for i,z in enumerate(yy[target]) if not z];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in pos for j in neg)/(len(pos)*len(neg)) if pos and neg else None
                    for k in [3,5]:
                        label=f'top{k}';cut=sorted([scores[i] for i in universe],reverse=True)[min(k,len(universe))-1] if universe else None;ix=[i for i in universe if scores[i]>=cut] if universe else [];assert ix==sel[target][name][variant][mode][label];hit=sum(yy[target][i] for i in ix);expectedmetric=dict(selected=len(ix),supported=hit,precision=hit/len(ix) if ix else None,recall=hit/len(pos) if pos else None,coverage=len(ix)/len(p),auc=auc);close(expectedmetric,v['lists'][mode][label]['support']);assert v['lists'][mode][label]['case_bearing']==sum(app[target][i] for i in ix)
                        if name=='full12' and variant=='baseline' and mode in ['gate','product']:close(expectedmetric,prior[target]['balanced']['lists']['hard' if mode=='gate' else 'product'][label]['support'])
                        lists+=1
    hashes=0
    for fn in ['design-freeze.json','feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/fn).items():
            path=Path(p) if '/' in p else O/p;assert hashlib.sha256(path.read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(P/'iteration218/verification-manifest.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',newton_refits=fits,prediction_groups=64,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
