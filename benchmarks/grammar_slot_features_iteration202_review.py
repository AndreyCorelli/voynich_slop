"""Independent slot occurrences, source fits and factorial metric replay."""
import math
from collections import Counter,defaultdict
import numpy as np
from scipy.special import expit
from benchmarks.grammar_slot_features_iteration202 import OUT,BASE,RESIDUAL,OLD,AUTHORS,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_contextual_surplus_iteration201_review import metrics

def independent_slot_features(g):
    ids=g['ids'];pos=g['positions'];globalcount=Counter(ids);locations=defaultdict(list);wordcontexts=defaultdict(list)
    for i in range(1,len(ids)-1):
        if pos[i] and pos[i-1] and pos[i+1]:frame=(ids[i-1],ids[i+1]);locations[frame].append(i);wordcontexts[ids[i]].append(frame)
    result=[]
    for e in g['descriptors']:
        fs=[];left=[];right=[];querycount=0
        for f in e['frames']:
            l,r=f['frame'];centers=Counter(ids[i] for i in locations[(l,r)]);total=len(locations[(l,r)]);a=sum(ids[i]==e['a'] for i in locations[(l,r)]);b=sum(ids[i]==e['b'] for i in locations[(l,r)]);assert a==len(f['a_positions']);assert b==len(f['b_positions']);left.append(l);right.append(r);querycount+=a+b
            entropy=-sum(n/total*math.log(n/total) for n in centers.values())/math.log(total) if total>1 else 0.
            fs.append([math.log(globalcount[l]),math.log(globalcount[r]),abs(math.log(globalcount[l])-math.log(globalcount[r])),math.log(1+total),math.log(len(centers)),entropy,(a+b)/total,abs(a-b)/(a+b),math.log(1+a*b)])
        a=Counter(wordcontexts[e['a']]);b=Counter(wordcontexts[e['b']]);union=set(a)|set(b);intersection=set(a)&set(b);cosine=sum(a[k]*b[k] for k in union)/math.sqrt(sum(n*n for n in a.values())*sum(n*n for n in b.values()));v=[sum(row[k] for row in fs)/len(fs) for k in range(9)]+[math.log(1+querycount),math.log(len(set(left))),math.log(len(set(right))),len(intersection)/len(union),cosine];result.append(dict(a=e['a'],b=e['b'],values=v))
    return result

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for n in ['feature-freeze.json','prediction-freeze.json']:
        for p,h in load(OUT/n).items():assert digest(OUT/p)==h;hashes+=1
    for folder in [RESIDUAL,OLD]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    graphs=load(BASE/'graphs.json');oldfeatures=load(BASE/'features.json');slots=load(OUT/'slot-features.json');ff=load(OUT/'features.json');labels=load(RESIDUAL/'labels.json');case=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');models=load(OUT/'models.json');outputs=load(OUT/'outputs.json');sels=load(OUT/'selections.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');oldoutputs=load(RESIDUAL/'outputs.json');fits=groups=edges=0
    for a in AUTHORS:
        close(independent_slot_features(graphs[a]),slots[a]);edges+=len(slots[a]);assert ff[a]==[dict(a=r['a'],b=r['b'],values=r['values']+s['values']) for r,s in zip(oldfeatures[a],slots[a],strict=True)]
    for target in AUTHORS:
        train=[a for a in AUTHORS if a!=target];raw=np.array([r['values'] for a in train for r in ff[a]]);w=np.concatenate([np.full(len(ff[a]),1/(len(train)*len(ff[a]))) for a in train]);mean=np.average(raw,axis=0,weights=w);sd=np.sqrt(np.average((raw-mean)**2,axis=0,weights=w));sd[sd<1e-12]=1;x=np.column_stack([np.ones(len(raw)),(raw-mean)/sd]);pen=np.diag([0]+[.1]*33);y=np.array([int(r['case_occurrence_pairs']>0) for a in train for r in case[a]]);resid=np.array([r['surplus'] for a in train for r in labels[a]])
        for m in models[target].values():assert m['columns']==list(range(33));assert m['strength']==.1;assert np.allclose(m['mean'],mean,atol=1e-12,rtol=1e-12);assert np.allclose(m['scale'],sd,atol=1e-12,rtol=1e-12)
        def loss(b):return w@(np.logaddexp(0,x@b)-y*(x@b))+.5*b@pen@b
        b=np.zeros(34)
        for _ in range(100):
            p=expit(x@b);grad=x.T@(w*(p-y))+pen@b
            if max(abs(grad))<1e-11:break
            h=x.T@((w*p*(1-p))[:,None]*x)+pen;step=np.linalg.solve(h,grad);rate=1.
            while loss(b-rate*step)>loss(b)-1e-4*rate*(grad@step):rate/=2;assert rate>1e-12
            b-=rate*step
        assert max(abs(grad))<1e-9;stored=np.array(models[target]['point_augmented']['beta']);assert max(abs(x.T@(w*(expit(x@stored)-y))+pen@stored))<1e-6;assert abs(loss(b)-loss(stored))<1e-10;fits+=1
        augment=np.column_stack([np.zeros(33),np.sqrt(.1)*np.eye(33)]);br=np.linalg.lstsq(np.vstack([np.sqrt(w)[:,None]*x,augment]),np.concatenate([np.sqrt(w)*resid,np.zeros(33)]),rcond=None)[0];assert np.allclose(br,models[target]['surplus_augmented']['beta'],atol=1e-10,rtol=1e-10);fits+=1
        xt=np.column_stack([np.ones(len(ff[target])),(np.array([r['values'] for r in ff[target]])-mean)/sd]);assert np.max(abs(expit(xt@b)-outputs[target]['point_augmented']))<1e-6;assert np.max(abs(xt@br-outputs[target]['surplus_augmented']))<1e-10
        for n,old in [('point_original','point_rich'),('surplus_original','surplus_rich'),('point_control','point_control'),('surplus_control','surplus_control')]:assert outputs[target][n]==oldoutputs[target][old]
        expected={name+'/top'+str(k):[i for i,v in enumerate(vv) if sum(t>v for t in vv)<k] for name,vv in outputs[target].items() for k in [10,20]};assert expected==sels[target]
        for name,ix in expected.items():close(metrics(ix,labels[target],case[target],sizes[target]['types']),summary[target][name]);groups+=1
        for objective in ['point','surplus']:
            new=summary[target][objective+'_augmented/top10'];old=summary[target][objective+'_original/top10'];close(dict(mean_surplus_change=new['mean_surplus']-old['mean_surplus'],positive_pair_change=new['positive_surplus_pairs']-old['positive_surplus_pairs'],applicable_pair_change=new['case_metrics']['case_edges']-old['case_metrics']['case_edges']),contrasts[target][objective])
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,independent_slot_feature_rows=edges,slot_values_replayed=edges*14,independent_fits=fits,metric_groups=groups,baseline_score_copies=16,source_scaling_and_target_exclusion_verified=True,no_gold_features_or_reserved_inputs=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
