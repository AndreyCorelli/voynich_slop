"""Noise-response summaries and candidate-only controls."""
import numpy as np
from benchmarks.grammar_noisy_support_iteration30 import OUT,EXACT,BASELINE,PREVIOUS,RATES,MASK_SEEDS,load,save,digest,metrics
from voynich_smt.noisy_class_support import noisy_support
from voynich_smt.latent_cipher_classes import forward_backward


def spread(values):
    values=[float(x) for x in values if x is not None]
    return dict(mean=float(np.mean(values)) if values else None,min=min(values) if values else None,max=max(values) if values else None,replicates=len(values))


def candidate_baselines(chain,obs,truth,reference,support,affected):
    probabilities=support*np.asarray(chain['source_occupancy'])[:,None];probabilities/=probabilities.sum(axis=0,keepdims=True)
    gamma=[probabilities[:,s].T for s in obs['sequences']];result=dict(class_frequency=metrics(gamma,truth,obs,reference,affected));uniform={}
    for name,mask in [('all',np.ones(support.shape[1],bool)),('affected',affected),('originally_ambiguous',reference.sum(axis=0)>1),('affected_singletons',affected&(reference.sum(axis=0)==1))]:
        for suffix,offset in [('',0),('_query',obs['offset'])]:
            probabilities=[]
            for seq in obs['sequences'][offset:]:
                probabilities.extend(1/int(support[:,w].sum()) for w in seq if mask[w])
            uniform[name+suffix]=dict(tokens=len(probabilities),expected_accuracy=float(np.mean(probabilities)) if probabilities else None)
    result['uniform']=uniform;return result


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'schedules.json')==load(OUT/'manifest.json')['schedules_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE/'chains.json')['oracle_development'];schedules=load(OUT/'schedules.json');cells=[];predictions={}
    for filename in load(OUT/'fit-index.json'):
        cell=load(OUT/filename);support,affected=noisy_support(reference,schedules[str(cell['mask_seed'])],cell['rate']);selected=cell['random'][cell['selected']];oracle=cell['oracle'];b=candidate_baselines(chain,obs,truth,reference,support,affected)
        output={k:cell[k] for k in ('mask_seed','rate','arm')};output.update(affected_types=int(affected.sum()),candidate_pairs=int(support.sum()),selected_seed=selected['seed'],selected=selected['trace'][-1],oracle_initial=oracle['trace'][0],oracle=oracle['trace'][-1],oracle_first_net_loss=oracle['first_net_loss'],baselines=b,
            converged=dict(oracle=oracle['converged'],random=sum(r['converged'] for r in cell['random'])),random_query_accuracy=[r['trace'][-1]['all_query']['accuracy'] for r in cell['random']],
            random_affected_accuracy=[r['trace'][-1]['affected_query']['accuracy'] for r in cell['random']],oracle_objective_gain=oracle['trace'][-1]['objective']-oracle['trace'][0]['objective'])
        # Confirm saved scores from final emissions without access to labels in selection.
        for name,fit in [('selected',selected),('oracle',oracle)]:
            _,gamma=forward_backward(chain,fit['final_emissions'],obs['sequences']);m=metrics(gamma,truth,obs,reference,affected)
            assert all(m[k]==output[name][k] for k in m)
        cells.append(output)
    summary={}
    for arm in ('word','ending'):
        summary[arm]={}
        for rate in RATES:
            group=[c for c in cells if c['arm']==arm and c['rate']==rate];assert len(group)==len(MASK_SEEDS)
            summary[arm][str(rate)]={}
            for cohort in ('all_query','affected_query','affected_singletons_query','originally_ambiguous_query'):
                summary[arm][str(rate)][cohort]=dict(tokens=spread([c['selected'][cohort]['tokens'] for c in group]),
                    selected=spread([c['selected'][cohort]['accuracy'] for c in group]),oracle_initial=spread([c['oracle_initial'][cohort]['accuracy'] for c in group]),oracle=spread([c['oracle'][cohort]['accuracy'] for c in group]),
                    class_frequency=spread([c['baselines']['class_frequency'][cohort]['accuracy'] for c in group]),uniform=spread([c['baselines']['uniform'][cohort]['expected_accuracy'] for c in group]),
                    selected_balanced=spread([c['selected'][cohort]['balanced_accuracy'] for c in group]))
    # Rate0 reference is reused, with the same metric definitions.
    exact={};zero=np.zeros(reference.shape[1],bool);base=load(EXACT/'results.json')
    for arm,r in base.items():
        chosen=max(r['random'],key=lambda a:a['trace'][-1]['objective']);_,g=forward_backward(chain,chosen['final_emissions'],obs['sequences']);exact[arm]=metrics(g,truth,obs,reference,zero)
    save(OUT/'evaluation.json',dict(cells=cells,summary=summary,exact=exact,convergence=dict(oracle=sum(c['converged']['oracle'] for c in cells),random=sum(c['converged']['random'] for c in cells))))
    for arm,rows in summary.items():
        print(arm)
        for rate,r in rows.items():print(rate,'all',r['all_query']['selected'],'affected',r['affected_query']['selected'],'oracle',r['affected_query']['oracle'],'baseline',r['affected_query']['class_frequency'],'tokens',r['affected_query']['tokens'])
    plot(summary,exact)


def plot(summary,exact):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    x=np.asarray(RATES)*100
    for arm in ('word','ending'):
        y=[summary[arm][str(r)]['all_query']['selected']['mean']*100 for r in RATES]
        axes[0].plot([0]+x.tolist(),[exact[arm]['all_query']['accuracy']*100]+y,'o-',label=arm)
        lo=[summary[arm][str(r)]['all_query']['selected']['min']*100 for r in RATES];hi=[summary[arm][str(r)]['all_query']['selected']['max']*100 for r in RATES]
        axes[0].fill_between(x,lo,hi,alpha=.12)
        y=[summary[arm][str(r)]['affected_query']['selected']['mean']*100 for r in RATES];axes[1].plot(x,y,'o-',label=arm)
    axes[1].plot(x,[summary['word'][str(r)]['affected_query']['class_frequency']['mean']*100 for r in RATES],'--',label='candidate class frequency')
    axes[1].plot(x,[summary['word'][str(r)]['affected_query']['uniform']['mean']*100 for r in RATES],':',label='uniform candidates (expected)')
    for ax,title in zip(axes,['All query tokens','Tokens of affected word types']):
        ax.set(title=title,xlabel='Word types given one extra false class (%)',ylabel='Accuracy (%)',ylim=(0,100));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Oracle-support noise diagnostic: existing development data; five perturbation seeds')
    fig.savefig(OUT/'support-noise-response.svg');plt.close(fig)

if __name__=='__main__':run()
