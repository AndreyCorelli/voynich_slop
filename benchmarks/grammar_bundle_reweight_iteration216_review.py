"""Independent three-group weights, Newton refits and scalar output audit."""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
from scipy.special import expit
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration216'
def read(p):return json.loads(p.read_text())
def near(a,b,tol=1e-10):assert np.allclose(a,b,atol=tol,rtol=tol)
def run():
    ff=read(O/'features.json');app=read(P/'iteration211/applicability-labels.json');yy=read(P/'iteration207/teacher-labels.json');support=read(P/'iteration207/predictions.json');weights=read(O/'weights.json');models=read(O/'models.json');pred=read(O/'predictions.json');sel=read(O/'selections.json');ss=read(O/'summary.json');sources=read(O/'source-summary.json');old=read(P/'iteration214/summary.json');oldpred=read(P/'iteration215/predictions.json');fits=0;lists=0
    assert ff==read(P/'iteration211/features.json')
    for target in ff:
        src=[a for a in ff if a!=target];raw=[];y=[];ww=[]
        assert list(weights[target])==src
        for a in src:
            groups=['supported' if yy[a][i] else 'other_case' if app[a][i] else 'no_case' for i in range(len(ff[a]))];c=Counter(groups);w=[1/(3*len(c)*c[g]) for g in groups];assert weights[target][a]['groups']==groups and weights[target][a]['counts']==dict(c);near(w,weights[target][a]['weights']);raw.extend(r['values'] for r in ff[a]);y.extend(app[a]);ww+=w
        raw=np.array(raw);w=np.array(ww);w/=w.sum();y=np.array(y);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;m=models[target]['balanced'];near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);b=np.zeros(13);pen=np.eye(13)*.1;pen[0,0]=0
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
        for name,m in models[target].items():
            for a,rows in ff.items():
                x=np.column_stack([np.ones(len(rows)),(np.array([r['values'] for r in rows])-m['mean'])/m['scale']]);near(expit(x@np.array(m['beta'])),pred[target][name][a]);pp=pred[target][name][a];r=independent_evaluate(app[a],pp)
                if name=='baseline':assert pp==oldpred[target]['full12'][a]
                if a!=target:
                    assert sources[target][name][a]['supported']==sum(yy[a]);assert sources[target][name][a]['retained']==sum(v and pp[i]>=.5 for i,v in enumerate(yy[a]));close(r,sources[target][name][a]['applicability']);continue
                v=ss[a][name];close(r,v['applicability']);positive=[i for i,z in enumerate(yy[a]) if z];keep=[i for i,z in enumerate(pp) if z>=.5];assert keep==sel[a][name]['eligible'] and v['eligible']==len(keep);assert v['retained_supported']==[i for i in positive if i in keep] and v['rejected_supported']==[i for i in positive if i not in keep]
                if name=='baseline':assert v==old[a]['full12'].__class__(**{k:old[a]['full12'][k] for k in v})
                for mode,scores,universe in [('hard',support[a]['full12'],keep),('product',[p*q for p,q in zip(pp,support[a]['full12'])],list(range(len(pp))))]:
                    neg=[i for i,z in enumerate(yy[a]) if not z];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in positive for j in neg)/(len(positive)*len(neg)) if positive and neg else None
                    for k in [3,5]:
                        label=f'top{k}';cut=sorted([scores[i] for i in universe],reverse=True)[min(k,len(universe))-1] if universe else None;ix=[i for i in universe if scores[i]>=cut] if universe else [];assert ix==sel[a][name][mode][label];hits=sum(yy[a][i] for i in ix);close(v['lists'][mode][label]['support'],dict(selected=len(ix),supported=hits,precision=hits/len(ix) if ix else None,recall=hits/len(positive) if positive else None,coverage=len(ix)/len(pp),auc=auc));assert v['lists'][mode][label]['case_bearing']==sum(app[a][i] for i in ix);lists+=1
    hashes=0
    for fn in ['design-freeze.json','feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/fn).items():
            path=Path(p) if '/' in p else O/p;assert hashlib.sha256(path.read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(P/'iteration215/verification-manifest.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',newton_refits=fits,prediction_groups=32,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
