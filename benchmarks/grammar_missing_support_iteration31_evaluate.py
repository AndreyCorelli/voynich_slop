"""Separate unavoidable excluded-class errors from covered-token spillover."""
import numpy as np
from benchmarks.grammar_missing_support_iteration31 import OUT,BASELINE,EXACT,PREVIOUS,RATES,MASK_SEEDS,load,save,digest
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.latent_cipher_classes import forward_backward
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics


def predict(chain,emissions,obs):return np.concatenate(forward_backward(chain,emissions,obs['sequences'])[1]).argmax(axis=1)


def summarize_pair(prediction,baseline,gold,masks):
    score=token_metrics(prediction,gold,masks);base=token_metrics(baseline,gold,masks);paired={}
    for name,mask in masks.items():
        lost=int(((baseline==gold)&(prediction!=gold)&mask).sum());gained=int(((baseline!=gold)&(prediction==gold)&mask).sum());n=int(mask.sum())
        paired[name]=dict(tokens=n,lost=lost,gained=gained,net_harm=lost-gained,accuracy_delta=(gained-lost)/n if n else None)
    query=masks['all_query'];covered=masks['covered_query'];counts=np.bincount(gold[query],minlength=8);covered_counts=np.bincount(gold[covered],minlength=8)
    return dict(scores=score,baseline=base,paired=paired,query_ceiling=float(covered.sum()/query.sum()),
        query_balanced_ceiling=float(np.mean(covered_counts[counts>0]/counts[counts>0])),
        query_error_decomposition=dict(unavoidable=int(masks['excluded_query'].sum()),covered_errors=int((covered&(prediction!=gold)).sum()),total=int((query&(prediction!=gold)).sum())))


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'deletions.json')==load(OUT/'manifest.json')['deletions_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(OUT/'deletions.json');baseline_predictions={};cells=[]
    for seed in MASK_SEEDS:
        for arm in ('word','ending'):
            b=load(BASELINE/f'fits-{seed}-1.0-{arm}.json');selected=b['random'][b['selected']];baseline_predictions[seed,arm]=predict(chain,selected['final_emissions'],obs)
    for filename in load(OUT/'fit-index.json'):
        c=load(OUT/filename);seed=c['mask_seed'];arm=c['arm'];support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],c['rate']);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);baseline=baseline_predictions[seed,arm]
        r={k:c[k] for k in ('mask_seed','rate','arm')};r['selected_seed']=c['random'][c['selected']]['seed'];r['convergence']=dict(oracle=c['oracle']['converged'],random=sum(t['converged'] for t in c['random']));r['random_query_range']=[min(t['trace'][-1]['scores']['all_query']['accuracy'] for t in c['random']),max(t['trace'][-1]['scores']['all_query']['accuracy'] for t in c['random'])]
        for name,trial in [('selected',c['random'][c['selected']]),('oracle',c['oracle'])]:
            pred=predict(chain,trial['final_emissions'],obs);r[name]=summarize_pair(pred,baseline,gold,masks);assert r[name]['scores']==trial['trace'][-1]['scores']
            assert r[name]['scores']['excluded']['correct']==0
        cells.append(r)
    summary={}
    for arm in ('word','ending'):
        summary[arm]={}
        for rate in RATES:
            group=[c for c in cells if c['rate']==rate and c['arm']==arm];assert len(group)==len(MASK_SEEDS)
            row=dict(query_ceiling=spread([c['selected']['query_ceiling'] for c in group]),query_balanced_ceiling=spread([c['selected']['query_balanced_ceiling'] for c in group]),
                query_accuracy=spread([c['selected']['scores']['all_query']['accuracy'] for c in group]),oracle_query_accuracy=spread([c['oracle']['scores']['all_query']['accuracy'] for c in group]),
                query_balanced_accuracy=spread([c['selected']['scores']['all_query']['balanced_accuracy'] for c in group]),error_decomposition={k:spread([c['selected']['query_error_decomposition'][k] for c in group]) for k in ('unavoidable','covered_errors','total')})
            for cohort in ('covered_query','untouched_query','covered_neighbors_query','covered_affected_query','ambiguous_covered_query'):
                row[cohort]=dict(tokens=spread([c['selected']['scores'][cohort]['tokens'] for c in group]),accuracy=spread([c['selected']['scores'][cohort]['accuracy'] for c in group]),
                    baseline=spread([c['selected']['baseline'][cohort]['accuracy'] for c in group]),delta=spread([c['selected']['paired'][cohort]['accuracy_delta'] for c in group]),net_harm=spread([c['selected']['paired'][cohort]['net_harm'] for c in group]))
            summary[arm][str(rate)]=row
    output=dict(cells=cells,summary=summary,convergence=dict(oracle=sum(c['convergence']['oracle'] for c in cells),random=sum(c['convergence']['random'] for c in cells)))
    save(OUT/'evaluation.json',output)
    for arm,rows in summary.items():
        print(arm)
        for rate,r in rows.items():print(rate,'ceiling',r['query_ceiling'],'accuracy',r['query_accuracy'],'covered',r['covered_query']['accuracy'],'delta',r['covered_query']['delta'],'untouched_delta',r['untouched_query']['delta'],'errors',r['error_decomposition'])
    plot(summary)


def plot(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained');x=np.asarray(RATES)*100
    for arm in ('word','ending'):
        axes[0].plot(x,[summary[arm][str(r)]['query_accuracy']['mean']*100 for r in RATES],'o-',label=arm)
        axes[1].plot(x,[summary[arm][str(r)]['covered_query']['delta']['mean']*100 for r in RATES],'o-',label=arm)
    axes[0].plot(x,[summary['word'][str(r)]['query_ceiling']['mean']*100 for r in RATES],'k--',label='candidate coverage ceiling')
    axes[0].set(title='All query tokens',ylabel='Accuracy (%)',ylim=(0,100));axes[1].axhline(0,color='k',linestyle='--');axes[1].set(title='Still-covered query tokens',ylabel='Accuracy change vs matched baseline (points)')
    for ax in axes:ax.set_xlabel('Word types with one true class removed (%)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Missing-candidate diagnostic: oracle chain; five perturbation seeds');fig.savefig(OUT/'missing-support-response.svg');plt.close(fig)

if __name__=='__main__':run()
