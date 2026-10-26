"""Independent weighted Newton fits, endpoint and contribution replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_weight_path_iteration185 import *

def run():
    hashes=fits=groups=0
    for name in ['design-freeze','model-freeze','prediction-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');y=np.array(load(ROOT/'iteration180/source-labels.json'));assert y[21]==0;reference=load(ROOT/'iteration180/models.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');sel=load(OUT/'selections.json');changes=load(OUT/'top10-grid-crossings.json');contrib=load(OUT/'endpoint-logit-contributions.json');truth=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in truth];oldpred=load(ROOT/'iteration180/predictions.json');omitted=load(ROOT/'iteration184/predictions.json')['omit12']
    assert set(models)=={str(w) for w in WEIGHTS}
    for arm,cols in ARMS.items():
        original=reference[arm];mean=np.array(original['mean']);scale=np.array(original['scale']);x=np.column_stack([np.ones(len(y)),(np.array([r['values'] for r in ff['earlier']])[:,cols]-mean)/scale]);pen=np.eye(x.shape[1])*.1;pen[0,0]=0
        for w in WEIGHTS:
            key=str(w);m=models[key][arm];assert m['columns']==cols and m['mean']==original['mean'] and m['scale']==original['scale'] and m['strength']==.1 and m['weight']==w;mass=np.ones(len(y));mass[21]=w;beta=np.zeros(x.shape[1])
            for _ in range(100):
                pp=expit(x@beta);g=x.T@(mass*(pp-y))/sum(mass)+pen@beta;h=(x.T*(mass*pp*(1-pp)))@x/sum(mass)+pen;delta=np.linalg.solve(h,g);beta-=delta
                if max(abs(delta))<1e-12:break
            frozen=np.array(m['beta']);assert max(abs(frozen-beta))<1e-5;gradient=x.T@(mass*(expit(x@frozen)-y))/sum(mass)+pen@frozen;assert max(abs(gradient))<1e-6;close(m['gradient_max'],float(max(abs(gradient))));close(m['objective'],float(mass@(np.logaddexp(0,x@frozen)-y*(x@frozen))/sum(mass)+.5*frozen@pen@frozen));fits+=1
            for pool,rows in ff.items():
                tx=np.column_stack([np.ones(len(rows)),(np.array([r['values'] for r in rows])[:,cols]-mean)/scale]);close(pred[key][pool][arm],expit(tx@frozen).tolist())
            pp=pred[key]['replication'][arm];close(summary[key][arm]['classification'],independent_evaluate(target,pp));assert summary[key][arm]['source_pair_probability']==pred[key]['earlier'][arm][21]
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            assert lists==sel[key][arm]
            for name,ix in lists.items():close(summary[key][arm]['lists'][name],independent_metrics([truth[i] for i in ix],857));groups+=1
        assert max(abs(np.array(pred['0.0']['replication'][arm])-omitted[arm]))<1e-6
        for pool in ff:assert max(abs(np.array(pred['1.0'][pool][arm])-oldpred[pool][arm]))<1e-6
        expected=[]
        for lo,hi in zip(WEIGHTS,WEIGHTS[1:]):
            before=set(sel[str(lo)][arm]['top10']);after=set(sel[str(hi)][arm]['top10']);expected.append(dict(lower=lo,upper=hi,entered=sorted(after-before),left=sorted(before-after)))
        assert expected==changes[arm];cb=contrib[arm];assert cb['columns']==['intercept']+[COLS[i] for i in cols];delta=np.array(models['1.0'][arm]['beta'])-models['0.0'][arm]['beta'];close(cb['delta_beta'],delta.tolist())
        for i,r in enumerate(cb['targets']):
            assert r['index']==i;z=[1.]+[(ff['replication'][i]['values'][j]-mean[k])/scale[k] for k,j in enumerate(cols)];values=[a*b for a,b in zip(z,delta)];close(r['contributions'],values);close(r['logit_change'],sum(values))
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,independent_weighted_newton_fits=fits,all_source_weights_and_fixed_scaling_verified=True,all180_and184_endpoint_predictions_within_1e_minus6=True,all_gradients_below_1e_minus6=True,selection_metric_groups=groups,all_source_target_predictions_and_calibration=True,all_adjacent_grid_crossings_and_252_logit_decompositions=True))
    print('audit passed',fits,groups,flush=True)
if __name__=='__main__':run()
