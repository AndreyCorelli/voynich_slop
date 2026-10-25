"""Frozen source-only ridge classifier for opaque-pair case applicability."""
from benchmarks.grammar_case_pair_selection_iteration178 import *
from scipy.optimize import minimize
from scipy.special import expit
OUT=ROOT/'iteration180'
ENDPOINT=['log_frequency','log_outside_count','left_unique_fraction','right_unique_fraction','left_entropy','right_entropy','left_neighbor_frequency','right_neighbor_frequency','no_outside']
COLS=[part+'_'+x for part in ['mean','difference'] for x in ENDPOINT]+['log_support']
CONTROL=[0,len(ENDPOINT),len(COLS)-1]

def endpoint(ids,counts,positions,excluded):
    pp=[i for i in positions if i not in excluded];n=len(pp);left=Counter(ids[i-1] for i in pp);right=Counter(ids[i+1] for i in pp)
    def h(c):return -sum((v/n)*math.log(v/n) for v in c.values())/math.log(n) if n>1 else 0.
    def freq(c):return sum(v*math.log(counts[k]) for k,v in c.items())/(n*math.log(len(ids))) if n else 0.
    return [math.log(counts[ids[positions[0]]]),math.log1p(n),len(left)/n if n else 0.,len(right)/n if n else 0.,h(left),h(right),freq(left),freq(right),float(not n)]

def features_for(ids,dd):
    counts=Counter(ids);locations={}
    for i in range(1,len(ids)-1):locations.setdefault(ids[i],[]).append(i)
    result=[]
    for e in dd:
        removed={x:{i for f in e['frames'] for i in f[x+'_positions']} for x in ['a','b']}
        a=endpoint(ids,counts,locations[e['a']],removed['a']);b=endpoint(ids,counts,locations[e['b']],removed['b'])
        result.append(dict(a=e['a'],b=e['b'],excluded_a=len(removed['a']),excluded_b=len(removed['b']),outside_a=len(locations[e['a']])-len(removed['a']),outside_b=len(locations[e['b']])-len(removed['b']),values=[(x+y)/2 for x,y in zip(a,b)]+[abs(x-y) for x,y in zip(a,b)]+[math.log(e['shared_frames'])]))
    return result

def fit(raw,y,columns):
    xx=np.array(raw)[:,columns];mean=xx.mean(0);scale=xx.std(0);scale[scale<1e-12]=1;x=np.column_stack([np.ones(len(xx)),(xx-mean)/scale]);y=np.array(y);strength=.1
    def loss(beta):
        z=x@beta;pen=beta.copy();pen[0]=0
        return float(np.mean(np.logaddexp(0,z)-y*z)+strength*.5*(pen@pen)),x.T@(expit(z)-y)/len(y)+strength*pen
    r=minimize(loss,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=1000,ftol=1e-13,gtol=1e-9));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),strength=strength,objective=float(r.fun),gradient_max=float(np.max(np.abs(loss(r.x)[1]))))

def predict(rows,m):
    xx=np.array([r['values'] for r in rows])[:,m['columns']];x=np.column_stack([np.ones(len(xx)),(xx-m['mean'])/m['scale']]);return expit(x@np.array(m['beta'])).tolist()

def evaluate(y,p):
    y=np.array(y,dtype=int);p=np.array(p);positive=p>=.5;tp=int(sum(positive&(y==1)));fp=int(sum(positive&(y==0)));fn=int(sum(~positive&(y==1)));tn=int(sum(~positive&(y==0)));pos=p[y==1];neg=p[y==0];bins=[]
    for i in range(5):
        ix=(p>=i/5)&((p<(i+1)/5) if i<4 else (p<=1));bins.append(dict(lower=i/5,upper=(i+1)/5,n=int(sum(ix)),mean_probability=float(p[ix].mean()) if any(ix) else None,observed_rate=float(y[ix].mean()) if any(ix) else None))
    return dict(n=len(y),positives=int(sum(y)),predicted_positive=int(sum(positive)),tp=tp,fp=fp,fn=fn,tn=tn,accuracy=float(np.mean(positive==y)),precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,brier=float(np.mean((p-y)**2)),nll=float(np.mean(-y*np.log(np.maximum(p,1e-15))-(1-y)*np.log(np.maximum(1-p,1e-15)))),auc=float(np.mean(pos[:,None]>neg[None,:])+.5*np.mean(pos[:,None]==neg[None,:])) if len(pos) and len(neg) else None,calibration=bins)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration179/verification-manifest.json',ROOT/'iteration172/details.json',ROOT/'iteration164/streams.json',ROOT/'iteration168/streams.json']+[p['descriptors'] for p in POOLS.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},columns=COLS,design='SOURCE earlier52 primary edges, transfer unchanged to replication126. Target case-applicable = at least one paired recognized-case comparison in existing172 all-POS details, NOT POS/namedcase labels. Anonymous wordIDs only. For each query pair exclude ALL queried shared-frame endpoint occurrences from endpoint context distributions (retain global unigram frequencies); full flat streams no new boundaries. Endpoint9features defined in code, pair symmetric mean/absolute difference plus log support19. Fixed ordinary unweighted logistic meanNLL +.1/2 slopeL2, unpenalized intercept, source-only standardization; no hyperparameter/model/threshold selection. Primary rich19, control frequencymean/absolute-logfreqdifference/support3, sourceprior constant. Train source labels only; freeze models/source labels then all target probabilities BEFORE loading target labels. Fixed probability>=.5 selection and top10/top20 with all exact probability ties, no family filter. Evaluate target NLL/Brier/AUC/calibration5fixedbins, confusion/coverage and selected172 case applicability/consistency/joint yield/diversity; source in-sample explicitly not OOF evidence. No fresh validation or deployment success from reused sameauthor development; supervised source component not language-free or restored namedcases/nuclei. Independent features/modelgradient/predictions/evaluation/baseline replay.'))
    ff={}
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';ids=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key];dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;ff[pool]=features_for(ids,[e for e in dd['original'] if e['shared_frames']>=2])
    save(OUT/'features.json',ff);save(OUT/'feature-freeze.json',dict(inputs={str(OUT/'features.json'):digest(OUT/'features.json')}))
    source=load(ROOT/'iteration172/details.json')['earlier']['original']['all'];y=[int(r['case_occurrence_pairs']>0) for r in source];save(OUT/'source-labels.json',y);raw=[r['values'] for r in ff['earlier']];models={'rich':fit(raw,y,list(range(len(COLS)))),'frequency_support':fit(raw,y,CONTROL),'prior':dict(probability=sum(y)/len(y))};save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['models.json','source-labels.json']}))
    predictions={pool:{name:([m['probability']]*len(rows) if name=='prior' else predict(rows,m)) for name,m in models.items()} for pool,rows in ff.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}))
    truth=load(ROOT/'iteration172/details.json');summary={};selections={}
    for pool,mm in predictions.items():
        rr=truth[pool]['original']['all'];y=[int(r['case_occurrence_pairs']>0) for r in rr];summary[pool]={};selections[pool]={}
        for name,pp in mm.items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            selections[pool][name]=lists;summary[pool][name]=dict(classification=evaluate(y,pp),lists={label:metrics([rr[i] for i in ix],588 if pool=='earlier' else 857) for label,ix in lists.items()})
        print(pool,json.dumps(summary[pool]),flush=True)
    save(OUT/'selections.json',selections);save(OUT/'summary.json',summary)
if __name__=='__main__':run()
