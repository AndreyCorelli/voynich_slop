"""Frozen-gate query evaluation and excluded-class detection diagnostics."""
import numpy as np
from benchmarks.grammar_context_override_iteration34 import OUT,PREVIOUS,PROBES,PRIMARY,EPSILONS,RATES,load,save,digest,slice_features
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.context_override import choose,apply,counts,ranking


def bootstrap(rows,replicates=1000):
    # Resample sentence IDs jointly across perturbations; never treat copies of
    # the same query as independent sentences.
    delta=np.array([r['sentence_delta'] for r in rows]);sizes=np.array(rows[0]['sentence_tokens']);rng=np.random.default_rng(3401);values=[]
    for _ in range(replicates):
        selected=rng.integers(0,len(sizes),len(sizes));values.append(float(delta[:,selected].sum()/(len(rows)*sizes[selected].sum())))
    return dict(replicates=replicates,sentence_cluster_95=[float(x) for x in np.quantile(values,[.025,.975])])


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'evaluation-freeze.json')['inputs'].items():assert digest(p)==h,p
    features=load(OUT/'features.json');truth=load(OUT/'feature-truth.json');policies=load(OUT/'policies.json');obs=load(PREVIOUS/'observations.json')['calibration'];offset=sum(map(len,obs['sequences'][:obs['offset']]));query=np.arange(sum(map(len,obs['sequences'])))>=offset;sizes=[len(s) for s in obs['sequences'][obs['offset']:]];boundaries=np.r_[0,np.cumsum(sizes)];results=[];detection=[]
    for row,label in zip(features,truth):
        f=slice_features(row['features'],query);gold=np.asarray(label['gold'])[query];excluded=np.asarray(label['excluded'])[query];metadata={k:row[k] for k in ('mask_seed','rate','epsilon','arm')}
        d=dict(metadata,prevalence=float(excluded.mean()),scores={})
        detection_scores=dict(outside_mass=f['outside_mass'],conflict=f['conflict'],outside_top_confidence=(np.asarray(f['confidence'])*np.asarray(f['outside_top'])).tolist())
        for name,scores in detection_scores.items():d['scores'][name]=ranking(scores,excluded)
        detection.append(d)
        for gate in ('outside','disagreement'):
            policy=policies[f"{row['arm']}/{row['epsilon']}/{gate}"]['policy'];pred,selected=apply(f,policy);c=counts(f,gold,selected,excluded);old=np.asarray(f['old']);delta=(pred==gold).astype(int)-(old==gold).astype(int)
            result=dict(metadata,gate=gate,policy=policy,counts=c,baseline_accuracy=float((old==gold).mean()),accuracy=float((pred==gold).mean()),delta_accuracy=float(delta.mean()),
                detection_precision=c['flagged_excluded']/c['overrides'] if c['overrides'] else None,detection_recall=c['flagged_excluded']/c['excluded'] if c['excluded'] else None,
                override_correct_fraction=c['corrected']/c['overrides'] if c['overrides'] else None,spoiled_correct_covered_fraction=c['spoiled_correct_covered']/c['correct_covered'] if c['correct_covered'] else None,
                sentence_tokens=sizes,sentence_delta=[int(delta[a:b].sum()) for a,b in zip(boundaries[:-1],boundaries[1:])],predicted=pred.tolist(),selected=selected.tolist())
            results.append(result)
    summary={}
    for arm in ('word','ending'):
        summary[arm]={}
        for epsilon in EPSILONS:
            summary[arm][str(epsilon)]={}
            for rate in RATES:
                rr=[r for r in results if r['arm']==arm and r['epsilon']==epsilon and r['rate']==rate];ss={}
                for gate in ('outside','disagreement'):
                    cells=[r for r in rr if r['gate']==gate];assert len(cells)==5
                    ss[gate]=dict(policy=policies[f'{arm}/{epsilon}/{gate}'],baseline_accuracy=spread([r['baseline_accuracy'] for r in cells]),accuracy=spread([r['accuracy'] for r in cells]),delta_accuracy=spread([r['delta_accuracy'] for r in cells]),
                        counts={key:spread([r['counts'][key] for r in cells]) for key in cells[0]['counts']},detection_precision=spread([r['detection_precision'] for r in cells]),detection_recall=spread([r['detection_recall'] for r in cells]),
                        spoiled_correct_covered_fraction=spread([r['spoiled_correct_covered_fraction'] for r in cells]),bootstrap=bootstrap(cells))
                dd=[r for r in detection if r['arm']==arm and r['epsilon']==epsilon and r['rate']==rate]
                ss['detection']={name:{m:spread([r['scores'][name][m] for r in dd]) for m in ('auroc','average_precision')} for name in dd[0]['scores']};ss['prevalence']=spread([r['prevalence'] for r in dd]);summary[arm][str(epsilon)][str(rate)]=ss
    save(OUT/'evaluation.json',dict(cells=results,detection=detection,summary=summary))
    for arm,ee in summary.items():
        for eps,rr in ee.items():
            for rate,s in rr.items():
                r=s['outside'];print(arm,eps,rate,'outside AUC',s['detection']['outside_mass']['auroc']['mean'],'AP',s['detection']['outside_mass']['average_precision']['mean'],'counts',{k:r['counts'][k]['mean'] for k in ('overrides','corrected','spoiled','unchanged_wrong','recovered_excluded')},'delta',r['delta_accuracy']['mean'],'CI',r['bootstrap'])

if __name__=='__main__':run()
