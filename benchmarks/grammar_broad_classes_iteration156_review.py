"""Independent broad-class eligibility, features, nested fits and metrics."""
from benchmarks.grammar_broad_classes_iteration156 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def check_fit(m,f,train,lookup,labels,cols,strength):
    assert m['training']==train and m['columns']==cols and m['strength']==strength;raw=np.array([[f[lookup[w]][c] for c in cols] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;assert np.allclose(mean,m['mean']) and np.allclose(scale,m['scale']);x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([labels[w] for w in train]);count=np.bincount(y,minlength=2);mass=np.array([.5/count[c] for c in y]);b=np.array(m['beta'])
    def obj(beta):
        z=x@beta;return float(mass@(np.logaddexp(0,z)-y*z)+strength/2*(beta@beta)),x.T@(mass*(expit(z)-y))+strength*beta
    loss,g=obj(b);assert abs(loss-m['loss'])<1e-10 and max(abs(g))<2e-6;re=minimize(obj,np.zeros(x.shape[1]),jac=True,method='BFGS',options=dict(gtol=1e-8,maxiter=1000));assert abs(re.fun-loss)<1e-7

def run():
    hc=fc=mc=0
    for name in ['design-freeze','eligibility-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];data=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows};assert not set(fit)&reserved;counts={}
    for sid in fit:
        for t in data[sid]['tokens']:counts.setdefault(t['word'],Counter())[t['pos']]+=1
    records={}
    for w,c in counts.items():
        tag=sorted(c,key=lambda tag:(-c[tag],tag))[0];total=sum(c.values())
        if total>=5 and c[tag]*5>=total*4:records[w]=dict(n=total,modal=tag,purity=c[tag]/total,label=int(tag in ['ADP','AUX','CCONJ','DET','PART','PRON','SCONJ']))
    saved=load(OUT/'eligibility.json');assert saved['records']==records;labels={w:r['label'] for w,r in records.items()};targets=set(load(ROOT/'iteration93/types.json')['candidates']);train=sorted(set(records)-targets);assert saved['training']==train and saved['targets']==sorted(set(records)&targets);lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in records};assert saved['lookup']==lookup;folds=fold_map(train,labels,'candidate156');assert saved['folds']==folds
    public,*_=training_inputs();ids=[t['id'] for s in public for t in s['tokens']];f=combined(ids,set(lookup.values()));features=load(OUT/'features.json')
    for i,r in f.items():
        r['frequency']=math.log1p(r['n'])
        for c in r:assert abs(r[c]-features[i][c])<1e-11
    models=load(OUT/'models.json');selection=load(OUT/'selection.json');inner=load(OUT/'inner-models.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json')
    for name,cols in DETECTORS.items():
        for key,s in selection[name].items():
            held=[] if key=='final' else [w for w in train if folds[w]==int(key)];tr=[w for w in train if w not in held];salt='final156' if key=='final' else 'inner156-outer'+key;ff=fold_map(tr,labels,salt);assert s['folds']==ff;losses={}
            for strength in GRID:
                pp={}
                for k in range(3):
                    hh=[w for w in tr if ff[w]==k];tt=[w for w in tr if w not in hh];m=inner[name][key][str(strength)][str(k)];check_fit(m,f,tt,lookup,labels,cols,strength);fc+=1;assert not set(m['training'])&set(held);pp.update({w:probability(f[lookup[w]],m) for w in hh})
                assert set(pp)==set(s['trials'][str(strength)]['predictions']) and all(abs(p-s['trials'][str(strength)]['predictions'][w])<1e-9 for w,p in pp.items());loss=sum(sum(-math.log(pp[w] if label else 1-pp[w]) for w in tr if labels[w]==label)/sum(labels[w]==label for w in tr) for label in [0,1])/2;assert abs(loss-s['trials'][str(strength)]['balanced_nll'])<1e-9;losses[strength]=loss
            chosen=max(k for k,v in losses.items() if v<=min(losses.values())+1e-10);assert s['chosen']==chosen;m=models[name][key];check_fit(m,f,tr,lookup,labels,cols,chosen);fc+=1
            for w in (saved['targets'] if key=='final' else held):
                p=probability(f[lookup[w]],m);assert abs(p-(pred['targets'][name][w] if key=='final' else pred['oof'][name][w]))<1e-9
        pp=pred['oof'][name];assert set(pp)==set(train);mm=summary[name];yy=[w for w in train if labels[w]];nn=[w for w in train if not labels[w]];auc=sum((pp[a]>pp[b])+.5*(pp[a]==pp[b]) for a in yy for b in nn)/(len(yy)*len(nn));assert abs(auc-mm['auc'])<1e-12
        ap=0.
        for q in sorted(set(pp.values()),reverse=True):
            positives_at=sum(labels[w] and pp[w]==q for w in train);above=[w for w in train if pp[w]>=q];ap+=positives_at/len(yy)*sum(labels[w] for w in above)/len(above)
        assert abs(ap-mm['average_precision'])<1e-12;assert mm==detection_metrics(pp,labels);mc+=1
    save(OUT/'audit.json',dict(input_hashes_verified=hc,eligible_types_independently_verified=len(records),training_types=len(train),positive_training_types=sum(labels[w] for w in train),independent_feature_vectors=len(f),nested_models_independently_optimized_and_gradient_checked=fc,detector_summaries_independently_checked=mc,all_nested_splits_and_selections_verified=True,target16_excluded_from_every_fit=True,reserve_overlap=0))
if __name__=='__main__':run()
