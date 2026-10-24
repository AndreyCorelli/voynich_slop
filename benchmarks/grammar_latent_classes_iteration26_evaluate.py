"""Evaluate frozen latent fits; oracle permutations are reporting-only."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from benchmarks.grammar_latent_classes_iteration26 import OUT,GRID,ARMS,load,save,digest,decode,oracle_gamma,edges
from benchmarks.grammar_distributional_skeleton_iteration24_evaluate import metrics,comparison
from voynich_smt.latent_cipher_classes import forward_backward


def class_metrics(gamma,truth):
    y=np.concatenate(truth);p=np.concatenate(gamma);pred=p.argmax(axis=1);cm=np.zeros((8,8),int);np.add.at(cm,(y,pred),1)
    totals=cm.sum(axis=1);present=totals>0;recall=np.divide(cm.diagonal(),totals,out=np.zeros(8),where=present)
    balanced=cm/np.maximum(totals[:,None],1);r,c=linear_sum_assignment(-balanced)
    hard=np.bincount(pred,minlength=8)/len(pred);soft=p.mean(axis=0)
    effective=lambda q:float(np.exp(-np.sum(q[q>0]*np.log(q[q>0]))))
    confidence={}
    for threshold in (.6,.8,.95):
        mask=p.max(axis=1)>=threshold
        confidence[str(threshold)]=dict(tokens=int(mask.sum()),coverage=float(mask.mean()),accuracy=float((pred[mask]==y[mask]).mean()) if mask.any() else None)
    return dict(tokens=len(y),accuracy=float((y==pred).mean()),balanced_accuracy=float(recall[present].mean()),per_class_recall=recall.tolist(),confusion=cm.tolist(),
        oracle_permutation_balanced_accuracy=float(balanced[r,c].sum()/present.sum()),oracle_permutation={str(b):int(a) for a,b in zip(r,c)},
        hard_occupancy=hard.tolist(),soft_occupancy=soft.tolist(),unused_hard_states=int((hard==0).sum()),effective_hard_states=effective(hard),effective_soft_states=effective(soft),confidence=confidence)


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'target-freeze.json')['inputs'].items():assert digest(p)==h,p
    models=load(OUT/'source-models.json');obs=load(OUT/'observations.json');truth=load(OUT/'observation-truth.json');data=load(OUT/'datasets.json');fits=load(OUT/'target-fits.json');policies=load(OUT/'policies.json')
    output={};predictions={}
    for split in ('jerome','caesar'):
        output[split]={};predictions[split]={};o=obs[split];gold=truth[split][o['offset']:]
        for arm in ARMS+('oracle_emissions','oracle_classes'):
            gamma=decode(models,o,fits[split][arm]) if arm in ARMS else oracle_gamma(models,o,truth[split],arm)
            result=class_metrics(gamma,gold);threshold=policies[arm];ee=edges(gamma,models['relations'],threshold);predictions[split][arm]=ee
            result['relations']=dict(threshold=threshold,**metrics(ee,data[split]))
            result['relation_curve']={str(t):metrics(edges(gamma,models['relations'],t),data[split])['micro'] for t in GRID}
            if arm in ARMS:
                f=fits[split][arm];seed_scores=[]
                for model in f['fits']:
                    g=forward_backward(models['chains'][f['template']],model['emissions'],o['sequences'])[1][o['offset']:]
                    s=class_metrics(g,gold);seed_scores.append(dict(seed=model['seed'],objective=model['objective'],iterations=model['iterations'],converged=model['converged'],balanced_accuracy=s['balanced_accuracy'],accuracy=s['accuracy']))
                result['seeds']=seed_scores;result['selected_seed']=f['fits'][f['selected']]['seed'];result['balanced_accuracy_range']=[min(s['balanced_accuracy'] for s in seed_scores),max(s['balanced_accuracy'] for s in seed_scores)]
            output[split][arm]=result
        output[split]['paired_relation_f1']={a:comparison(predictions[split][a],predictions[split]['word'],data[split]) for a in ('ending','shuffled_context','shuffled_endings','oracle_emissions','oracle_classes')}
    save(OUT/'evaluation.json',output);save(OUT/'relation-predictions.json',predictions)
    for split,rows in output.items():
        print(split)
        for arm in ARMS+('oracle_emissions','oracle_classes'):
            r=rows[arm];print(arm,'balanced',round(100*r['balanced_accuracy'],2),'cluster',round(100*r['oracle_permutation_balanced_accuracy'],2),'accuracy',round(100*r['accuracy'],2),'F1',round(100*r['relations']['micro']['f1'],2),'precision',r['relations']['micro']['precision'],'states',round(r['effective_hard_states'],2),'seeds',r.get('balanced_accuracy_range'))

if __name__=='__main__':run()
