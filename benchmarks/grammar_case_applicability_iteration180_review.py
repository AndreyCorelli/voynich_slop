"""Independent exclusion/features, Newton fit, predictions and metric audit."""
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_applicability_iteration180 import *

def close(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif isinstance(a,(float,int)) and isinstance(b,(float,int)):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11),(a,b)
    else:assert a==b,(a,b)

def independent_features(ids,edges):
    global_counts=Counter(ids);positions={}
    for j in range(1,len(ids)-1):positions.setdefault(ids[j],[]).append(j)
    rr=[]
    for e in edges:
        frames={tuple(f['frame']) for f in e['frames']};vectors=[];excluded=[];outside=[]
        for word in [e['a'],e['b']]:
            pp=positions[word];retained=[j for j in pp if (ids[j-1],ids[j+1]) not in frames];excluded.append(len(pp)-len(retained));outside.append(len(retained));n=len(retained);counts=[Counter(ids[j+d] for j in retained) for d in [-1,1]]
            ent=[];neigh=[]
            for cc in counts:
                prob=np.array(list(cc.values()),dtype=float)/n if n else np.array([]);ent.append(float(-np.dot(prob,np.log(prob))/math.log(n)) if n>1 else 0.);neigh.append(sum(math.log(global_counts[w])*v for w,v in cc.items())/(n*math.log(len(ids))) if n else 0.)
            vectors.append([math.log(global_counts[word]),math.log1p(n),len(counts[0])/n if n else 0.,len(counts[1])/n if n else 0.,*ent,*neigh,float(n==0)])
        a,b=vectors;values=((np.array(a)+b)/2).tolist()+np.abs(np.array(a)-b).tolist()+[math.log(e['shared_frames'])];rr.append(dict(a=e['a'],b=e['b'],excluded_a=excluded[0],excluded_b=excluded[1],outside_a=outside[0],outside_b=outside[1],values=values))
    return rr

def independent_evaluate(y,pp):
    n=len(y);tp=sum(p>=.5 and t==1 for p,t in zip(pp,y));fp=sum(p>=.5 and t==0 for p,t in zip(pp,y));fn=sum(p<.5 and t==1 for p,t in zip(pp,y));tn=sum(p<.5 and t==0 for p,t in zip(pp,y));bins=[]
    for i in range(5):
        ix=[j for j,p in enumerate(pp) if p>=i/5 and (p<(i+1)/5 if i<4 else p<=1)];bins.append(dict(lower=i/5,upper=(i+1)/5,n=len(ix),mean_probability=sum(pp[j] for j in ix)/len(ix) if ix else None,observed_rate=sum(y[j] for j in ix)/len(ix) if ix else None))
    pos=[p for p,t in zip(pp,y) if t];neg=[p for p,t in zip(pp,y) if not t]
    return dict(n=n,positives=sum(y),predicted_positive=tp+fp,tp=tp,fp=fp,fn=fn,tn=tn,accuracy=(tp+tn)/n,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,brier=sum((p-t)**2 for p,t in zip(pp,y))/n,nll=-sum(t*math.log(max(p,1e-15))+(1-t)*math.log(max(1-p,1e-15)) for p,t in zip(pp,y))/n,auc=sum(float(a>b)+.5*float(a==b) for a in pos for b in neg)/(len(pos)*len(neg)) if pos and neg else None,calibration=bins)

def run():
    hc=fc=mc=0
    for name in ['design-freeze','feature-freeze','model-freeze','prediction-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hc+=1
    ff=load(OUT/'features.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');selections=load(OUT/'selections.json');summary=load(OUT/'summary.json');truth=load(ROOT/'iteration172/details.json')
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';ids=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key];dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;edges=[e for e in dd['original'] if e['shared_frames']>=2];close(ff[pool],independent_features(ids,edges));fc+=len(edges)
    y=np.array([int(r['case_occurrence_pairs']>0) for r in truth['earlier']['original']['all']]);assert y.tolist()==load(OUT/'source-labels.json');assert models['prior']['probability']==float(y.mean())
    for name,columns in [('rich',list(range(19))),('frequency_support',[0,9,18])]:
        m=models[name];assert m['columns']==columns and m['strength']==.1;raw=np.array([r['values'] for r in ff['earlier']])[:,columns];mean=raw.mean(axis=0);scale=raw.std(axis=0);scale[scale<1e-12]=1;close(m['mean'],mean.tolist());close(m['scale'],scale.tolist());x=np.column_stack([np.ones(len(raw)),(raw-mean)/scale]);beta=np.zeros(x.shape[1]);penalty=np.eye(len(beta))*.1;penalty[0,0]=0
        for step in range(100):
            p=expit(x@beta);gradient=x.T@(p-y)/len(y)+penalty@beta;hessian=(x.T*(p*(1-p)))@x/len(y)+penalty;delta=np.linalg.solve(hessian,gradient);beta-=delta
            if np.max(np.abs(delta))<1e-12:break
        assert np.max(np.abs(beta-np.array(m['beta'])))<1e-5
        frozen=np.array(m['beta']);p=expit(x@frozen);gradient=x.T@(p-y)/len(y)+penalty@frozen;assert max(abs(gradient))<1e-6;close(m['gradient_max'],float(max(abs(gradient))))
        objective=float(np.mean(np.logaddexp(0,x@frozen)-y*(x@frozen))+.5*(frozen@penalty@frozen));close(m['objective'],objective)
    for pool,mm in pred.items():
        rr=truth[pool]['original']['all'];yy=[int(r['case_occurrence_pairs']>0) for r in rr]
        for name,pp in mm.items():
            if name=='prior':assert pp==[models[name]['probability']]*len(rr)
            else:
                m=models[name];raw=np.array([r['values'] for r in ff[pool]])[:,m['columns']];z=((raw-m['mean'])/m['scale'])@np.array(m['beta'][1:])+m['beta'][0];close(pp,expit(z).tolist())
            close(summary[pool][name]['classification'],independent_evaluate(yy,pp))
            expected={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];expected['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            assert selections[pool][name]==expected
            for label,ix in expected.items():close(summary[pool][name]['lists'][label],independent_metrics([rr[i] for i in ix],588 if pool=='earlier' else 857));mc+=1
    save(OUT/'audit.json',dict(input_freeze_hashes_verified=hc,query_excluded_feature_rows_verified=fc,source_only_fits_independently_solved_by_newton=2,all_gradients_below_1e_minus6=True,all_predictions_and_calibration_metrics_verified=True,selection_metric_groups_verified=mc,target_labels_not_used_for_fitting=True,source_scaling_only=True,shared_cache_note='Joint172 JSON cache is parsed for source access; only earlier labels consumed before model/prediction freezes. Not physically isolated target-label storage.'))
    print('audit passed',fc,mc,flush=True)
if __name__=='__main__':run()
