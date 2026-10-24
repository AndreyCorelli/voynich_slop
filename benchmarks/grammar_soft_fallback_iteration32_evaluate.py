"""Recovery versus covered-token harm under a normalized fallback mixture."""
import numpy as np
from benchmarks.grammar_soft_fallback_iteration32 import OUT,HARD,BASELINE,EXACT,PREVIOUS,RATES,EPSILONS,PRIMARY,MASK_SEEDS,load,save,digest
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture


def predict(chain,emission,obs):return np.concatenate(forward_backward(chain,emission,obs['sequences'])[1]).argmax(axis=1)


def pair(pred,baseline,gold,masks):
    out={}
    for name,mask in masks.items():
        n=int(mask.sum());lost=int(((baseline==gold)&(pred!=gold)&mask).sum());gained=int(((baseline!=gold)&(pred==gold)&mask).sum())
        out[name]=dict(tokens=n,lost=lost,gained=gained,net_gain=gained-lost,accuracy_delta=(gained-lost)/n if n else None)
    return out


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);hard_predictions={};soft_zero={}
    for seed in MASK_SEEDS:
        for rate in RATES:
            for arm in ('word','ending'):
                path=BASELINE/f'fits-{seed}-1.0-{arm}.json' if not rate else HARD/f'fits-{seed}-{rate}-{arm}.json';c=load(path);hard_predictions[seed,rate,arm]=predict(chain,c['random'][c['selected']]['final_emissions'],obs)
        for epsilon in EPSILONS:
            for arm in ('word','ending'):
                c=load(OUT/f'fits-{seed}-0.0-{epsilon}-{arm}.json');component=c['random'][c['selected']]['final_component'];soft_zero[seed,epsilon,arm]=predict(chain,mixture(component,q,epsilon),obs)
    cells=[]
    for filename in load(OUT/'fit-index.json'):
        c=load(OUT/filename);seed=c['mask_seed'];rate=c['rate'];epsilon=c['epsilon'];arm=c['arm'];support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);hard=hard_predictions[seed,rate,arm]
        r={k:c[k] for k in ('mask_seed','rate','epsilon','arm')};r['selected_seed']=c['random'][c['selected']]['seed'];r['convergence']=dict(oracle=c['oracle']['converged'],random=sum(t['converged'] for t in c['random']));r['hard_scores']=token_metrics(hard,gold,masks);r['hard_mask_ceiling']=float(masks['covered_query'].sum()/masks['all_query'].sum())
        for name,trial in [('selected',c['random'][c['selected']]),('oracle',c['oracle'])]:
            emission=mixture(trial['final_component'],q,epsilon);pred=predict(chain,emission,obs);scores=token_metrics(pred,gold,masks);assert scores==trial['trace'][-1]['scores']
            p=pair(pred,hard,gold,masks);gains=p['all_query']['net_gain'];recovered=scores['excluded_query']['correct'];assert gains==recovered+p['covered_query']['net_gain']
            outside=sum(not support[z,w] for z,w in zip(pred,np.concatenate(obs['sequences'])))
            r[name]=dict(scores=scores,versus_hard=p,versus_undeleted_hard=pair(pred,hard_predictions[seed,0.,arm],gold,masks),versus_undeleted_soft=pair(pred,soft_zero[seed,epsilon,arm],gold,masks),fallback_use=trial['fallback_use'],outside_predictions=int(outside))
        cells.append(r)
    summary={}
    for arm in ('word','ending'):
        summary[arm]={}
        for rate in RATES:
            summary[arm][str(rate)]={}
            for epsilon in EPSILONS:
                rows=[c for c in cells if c['arm']==arm and c['rate']==rate and c['epsilon']==epsilon];assert len(rows)==5
                s=dict(query_accuracy=spread([r['selected']['scores']['all_query']['accuracy'] for r in rows]),hard_accuracy=spread([r['hard_scores']['all_query']['accuracy'] for r in rows]),
                    query_balanced_accuracy=spread([r['selected']['scores']['all_query']['balanced_accuracy'] for r in rows]),oracle_query_accuracy=spread([r['oracle']['scores']['all_query']['accuracy'] for r in rows]),
                    excluded_recovery=spread([r['selected']['scores']['excluded_query']['accuracy'] for r in rows]),excluded_recovered_count=spread([r['selected']['scores']['excluded_query']['correct'] for r in rows]),
                    excluded_tokens=spread([r['selected']['scores']['excluded_query']['tokens'] for r in rows]),net_query_correct_gain=spread([r['selected']['versus_hard']['all_query']['net_gain'] for r in rows]),
                    covered_delta_vs_hard=spread([r['selected']['versus_hard']['covered_query']['accuracy_delta'] for r in rows]),covered_lost=spread([r['selected']['versus_hard']['covered_query']['lost'] for r in rows]),covered_gained=spread([r['selected']['versus_hard']['covered_query']['gained'] for r in rows]),
                    covered_delta_vs_undeleted_soft=spread([r['selected']['versus_undeleted_soft']['covered_query']['accuracy_delta'] for r in rows]),untouched_delta_vs_undeleted_soft=spread([r['selected']['versus_undeleted_soft']['untouched_query']['accuracy_delta'] for r in rows]),
                    covered_delta_vs_undeleted_hard=spread([r['selected']['versus_undeleted_hard']['covered_query']['accuracy_delta'] for r in rows]),
                    fallback_use_query=spread([r['selected']['fallback_use']['all_query'] for r in rows]),fallback_use_covered=spread([r['selected']['fallback_use']['covered_query'] for r in rows]),fallback_use_excluded=spread([r['selected']['fallback_use']['excluded_query'] for r in rows]))
                summary[arm][str(rate)][str(epsilon)]=s
    output=dict(cells=cells,summary=summary,primary_epsilon=PRIMARY,convergence=dict(oracle=sum(c['convergence']['oracle'] for c in cells),random=sum(c['convergence']['random'] for c in cells)))
    save(OUT/'evaluation.json',output)
    for arm,rr in summary.items():
        print(arm)
        for rate,rows in rr.items():
            for eps,s in rows.items():print(rate,eps,'acc',round(100*s['query_accuracy']['mean'],2),'hard',round(100*s['hard_accuracy']['mean'],2),'recovery',s['excluded_recovery']['mean'],'covered_delta',s['covered_delta_vs_hard']['mean'],'paired_soft_spillover',s['covered_delta_vs_undeleted_soft']['mean'])
    plot(summary)


def plot(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    for ax,rate in zip(axes,RATES):
        for arm in ('word','ending'):
            y=[summary[arm][str(rate)][str(e)]['query_accuracy']['mean']*100 for e in EPSILONS];ax.plot(EPSILONS,y,'o-',label=arm)
        ax.axhline(summary['word'][str(rate)][str(PRIMARY)]['hard_accuracy']['mean']*100,color='k',linestyle='--',label='hard word baseline')
        ax.axvline(PRIMARY,color='gray',alpha=.4);ax.set(title=f'{rate:.0%} types lose one true class',xlabel='Fallback mixture mass',ylabel='Query accuracy (%)',xscale='log',ylim=(0,100));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Soft fallback: existing development, oracle chain, five perturbation seeds');fig.savefig(OUT/'soft-fallback-response.svg');plt.close(fig)

if __name__=='__main__':run()
