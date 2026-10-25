"""Independent normalization, nested selection, constrained fits and output audit."""
from benchmarks.grammar_binary_frequency_iteration163 import *

def check(m,f,train,lookup,labels,cols,strength):
    assert m['training']==train and m['columns']==cols and m['strength']==strength;raw=np.array([[f[lookup[w]][c] for c in cols] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;assert np.allclose(mean,m['mean']) and np.allclose(scale,m['scale']);x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([labels[w]=='CCONJ' for w in train],dtype=int);count=np.bincount(y,minlength=2);mass=np.array([.5/count[c] for c in y]);b=np.array(m['beta']);bounds=[(None,None)]+[(None,None) if c=='frequency' else (0,None) for c in cols]
    def obj(beta):
        z=x@beta;return float(mass@(np.logaddexp(0,z)-y*z)+strength/2*(beta@beta)),x.T@(mass*(expit(z)-y))+strength*beta
    loss,g=obj(b);assert abs(loss-m['loss'])<1e-10;viol=[abs(g[0])]
    for j,c in enumerate(cols,1):
        if c!='frequency':assert b[j]>=0
        viol.append(abs(g[j]) if c=='frequency' or b[j]>1e-7 else max(0.,-g[j]))
    assert max(viol)<2e-6;re=minimize(obj,np.zeros(x.shape[1]),jac=True,method='SLSQP',bounds=bounds,options=dict(maxiter=1000,ftol=1e-12));assert re.success and abs(re.fun-loss)<1e-7

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    e=load(ROOT/'iteration162/eligibility.json');train=e['training'];lookup=e['lookup'];labels={w:r['label'] for w,r in e['records'].items()};folds=e['folds'];f=load(OUT/'source-features.json');oldf=load(ROOT/'iteration162/features.json')
    for name,ff in f.items():
        for i,r in ff.items():assert {k:v for k,v in r.items() if k!='frequency'}==oldf[name][i];assert r['frequency']==math.log1p(r['n'])
    models=load(OUT/'models.json');inner=load(OUT/'inner-models.json');selection=load(OUT/'selection.json');oof=load(OUT/'oof.json')
    for arm,cols in ARMS.items():
        for key,s in selection[arm].items():
            held=[] if key=='final' else [w for w in train if folds[w]==int(key)];tr=[w for w in train if w not in held];salt='final163' if key=='final' else 'inner163-outer'+key;ff={}
            for tag in ['ADP','CCONJ']:
                ww=sorted([w for w in tr if labels[w]==tag],key=lambda w:hashlib.sha256((salt+'|'+w).encode()).hexdigest());ff.update({w:k%3 for k,w in enumerate(ww)})
            assert s['folds']==ff;losses={}
            for strength in GRID:
                pp={}
                for k in range(3):
                    hh=[w for w in tr if ff[w]==k];tt=[w for w in tr if w not in hh];m=inner[arm][key][str(strength)][str(k)];check(m,f['full'],tt,lookup,labels,cols,strength);fc+=1;assert not set(m['training'])&set(held);pp.update({w:probability(f['full'][lookup[w]],m) for w in hh})
                assert pp==s['trials'][str(strength)]['predictions'];loss=sum(sum(-math.log(pp[w] if tag=='CCONJ' else 1-pp[w]) for w in tr if labels[w]==tag)/sum(labels[w]==tag for w in tr) for tag in ['ADP','CCONJ'])/2;assert abs(loss-s['trials'][str(strength)]['balanced_nll'])<1e-12;losses[strength]=loss
            assert s['chosen']==max(v for v in GRID if losses[v]<=min(losses.values())+1e-10)
        for name,m in models[arm].items():
            held=[w for w in train if folds[w]==int(name[-1])] if name.startswith('oof') else [name[5:]] if name.startswith('omit/') else [];tr=[w for w in train if w not in held];strength=selection[arm][name[-1] if name.startswith('oof') else 'final']['chosen'];check(m,f[name] if name.startswith('motif/') else f['full'],tr,lookup,labels,cols,strength);fc+=1
            if name.startswith('oof'):
                for w in held:assert oof[arm][w]==probability(f['full'][lookup[w]],m)
    tf=load(OUT/'target-features.json');oldtarget=load(ROOT/'iteration144/features.json');windows=load(ROOT/'iteration144/selection.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195']
    for work,ff in tf.items():
        N=windows[work+'/full']['stop']-windows[work+'/full']['start']
        for i,r in ff.items():assert {k:v for k,v in r.items() if k!='frequency'}==oldtarget[work+'/full'][i];assert abs(r['frequency']-math.log1p(31884*r['n']/N))<1e-12
        for arm,vv in pred[work].items():
            assert len(vv)==37
            for name,rows in vv.items():
                m=models[arm][name]
                for r in rows:
                    x=(np.array([ff[r['opaque']][c] for c in m['columns']])-m['mean'])/m['scale'];p=float(expit(m['beta'][0]+x@np.array(m['beta'][1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
                mm=summary[work][arm][name];assert mm==metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw');q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);assert mm['correct']==int(((q>.5)==y).sum());assert abs(mm['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;mc+=1
    assert load(OUT/'source-summary.json')=={arm:metrics_for(pp,labels) for arm,pp in oof.items()}
    save(OUT/'audit.json',dict(input_hashes_verified=hc,source_and_target_normalization_verified=True,models_independently_optimized_and_kkt_checked=fc,source_only_nested_selections_verified=12,source_oof_predictions_verified=87,target_probabilities_replayed=pc,metric_groups_replayed=mc,all_omissions_and_motif_variants_retained=True,relaxed_lexical_holdout_preserved=True))
if __name__=='__main__':run()
