"""Independent weighted Newton, trial enumeration and scalar metric replay."""
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
from benchmarks.grammar_multi_author_review192_193 import listmetrics
from benchmarks.grammar_source_author_influence_iteration194 import OUT,BASE,AUTHORS,Path,load,save,digest
import numpy as np
from scipy.special import expit

def run():
    assert not (OUT/'audit.json').exists()
    hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for file in ['trial-freeze.json','prediction-freeze.json']:
        for p,h in load(OUT/file).items():assert digest(OUT/p)==h;hashes+=1
    for p,h in load(BASE/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    ff=load(BASE/'features.json');rr=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');trials=load(OUT/'trials.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');lists=load(OUT/'selections.json');contrasts=load(OUT/'contrasts.json');details=load(OUT/'shortlist-details.json');oldsummary=load(BASE/'finalized-summary.json');oldpred=load(BASE/'predictions.json')
    fits=metrics=0;sets=set();noops=0
    for target in AUTHORS:
        assert set(trials[target])=={'baseline'}|{'without-'+a for a in AUTHORS if a!=target}
        for name,trial in trials[target].items():
            omit=None if name=='baseline' else name.removeprefix('without-');train=[a for a in AUTHORS if a not in [target,omit] and ff[a]];sets.add(tuple(train));noops+=int(trial['empty_source_noop']);assert trial['source_authors']==train
            labels={a:[int(r['case_occurrence_pairs']>0) for r in rr[a]] for a in train}
            assert trial['training_rows']==sum(len(ff[a]) for a in train);assert trial['training_positives']==sum(sum(labels[a]) for a in train)
            for a in train:assert trial['per_author'][a]==dict(rows=len(ff[a]),positives=sum(labels[a]),weight=1/len(train))
            w=np.concatenate([np.full(len(ff[a]),1/(len(train)*len(ff[a]))) for a in train]);y=np.concatenate([labels[a] for a in train]);raw=np.array([r['values'] for a in train for r in ff[a]])
            for label,m in models[target][name].items():
                if label=='prior':
                    assert abs(m['probability']-sum(sum(labels[a])/len(labels[a]) for a in train)/len(train))<1e-12
                    assert pred[target][name][label]==[m['probability']]*len(ff[target])
                else:
                    assert m['columns']==(list(range(19)) if label=='rich' else [0,9,18]);xx=raw[:,m['columns']];mean=np.average(xx,axis=0,weights=w);sd=np.sqrt(np.average((xx-mean)**2,axis=0,weights=w));sd[sd<1e-12]=1
                    assert np.allclose(mean,m['mean'],rtol=1e-12,atol=1e-12);assert np.allclose(sd,m['scale'],rtol=1e-12,atol=1e-12)
                    x=np.column_stack([np.ones(len(xx)),(xx-mean)/sd]);reg=np.diag([0]+[.1]*(len(m['columns'])));b=np.zeros(x.shape[1])
                    def loss(v):return w@(np.logaddexp(0,x@v)-y*(x@v))+.5*v@reg@v
                    for _ in range(100):
                        p=expit(x@b);g=x.T@(w*(p-y))+reg@b
                        if max(abs(g))<1e-11:break
                        h=x.T@((w*p*(1-p))[:,None]*x)+reg;step=np.linalg.solve(h,g);rate=1.
                        while loss(b-rate*step)>loss(b)-1e-4*rate*(g@step):
                            rate/=2
                            assert rate>1e-12
                        b-=rate*step
                    assert max(abs(g))<1e-9;stored=np.array(m['beta']);assert abs(loss(b)-loss(stored))<1e-10;assert max(abs(x.T@(w*(expit(x@stored)-y))+reg@stored))<1e-6
                    if ff[target]:
                        xt=np.array([r['values'] for r in ff[target]])[:,m['columns']];check=expit(np.column_stack([np.ones(len(xt)),(xt-mean)/sd])@b);assert np.max(np.abs(check-pred[target][name][label]))<1e-6
                    fits+=1
                pp=pred[target][name][label];refs=rr[target];yy=[int(r['case_occurrence_pairs']>0) for r in refs];sel={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
                for k in [10,20]:
                    if pp:
                        order=sorted(range(len(pp)),key=lambda i:pp[i],reverse=True);threshold=pp[order[min(k,len(pp))-1]];sel['top'+str(k)]=sorted(i for i in order if pp[i]>=threshold)
                    else:sel['top'+str(k)]=[]
                assert sel==lists[target][name][label]
                expected=dict(classification=independent_evaluate(yy,pp) if pp else None,lists={key:listmetrics([refs[i] for i in ix],sizes[target]['types']) for key,ix in sel.items()})
                close(expected,summary[target][name][label]);metrics+=3
                assert details[target][name][label]==[dict(edge=i,probability=pp[i],applicable=bool(yy[i]),**refs[i]) for i in sel['top10']]
                s=expected;bsummary=summary[target]['baseline'][label];baseix=lists[target]['baseline'][label]['top10']
                delta=dict(top10_applicable_change=s['lists']['top10']['case_edges']-bsummary['lists']['top10']['case_edges'],top10_size_change=s['lists']['top10']['edges']-bsummary['lists']['top10']['edges'],nll_change=s['classification']['nll']-bsummary['classification']['nll'] if pp else None,brier_change=s['classification']['brier']-bsummary['classification']['brier'] if pp else None,auc_change=s['classification']['auc']-bsummary['classification']['auc'] if pp and s['classification']['auc'] is not None else None,top10_entered=sorted(set(sel['top10'])-set(baseix)),top10_left=sorted(set(baseix)-set(sel['top10'])))
                close(delta,contrasts[target][name][label])
            if trial['empty_source_noop']:assert models[target][name]==models[target]['baseline'];assert pred[target][name]==pred[target]['baseline']
        assert pred[target]['baseline']==oldpred[target];close(summary[target]['baseline'],oldsummary[target])
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,trial_model_sets=36,distinct_nonempty_source_sets=len(sets),independent_newton_fits=fits,list_metric_groups=metrics,empty_source_noops=noops,exact_193_baselines=True,all_omissions_and_deltas_replayed=True,no_new_raw_data_or_reserved_labels=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
