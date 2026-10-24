"""Recovery/collateral tradeoff for frozen-base versus global repair."""
import numpy as np
from benchmarks.grammar_budgeted_repair_iteration37 import OUT,FULL,FITS,DATA,HARD,BASELINE,EXACT,BUDGETS,PRIMARY,EPSILON,load,save,digest
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import bootstrap
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.candidate_expansion import expand
from voynich_smt.candidate_abstention import abstention_metrics
from voynich_smt.budgeted_candidate_repair import repair_prior,anchored_emission


def predict(chain,e,obs):return np.concatenate(forward_backward(chain,e,obs['sequences'])[1]).argmax(axis=1)


def changes(pred,baseline,gold,query,covered,repaired_word):
    good=(pred==gold)&(baseline!=gold)&query;bad=(pred!=gold)&(baseline==gold)&query
    return dict(corrected=int(good.sum()),spoiled=int(bad.sum()),net=int(good.sum()-bad.sum()),excluded_recovered=int(((pred==gold)&~covered&query).sum()),
        spoiled_correct_covered=int((bad&covered).sum()),spoiled_unrepaired_words=int((bad&~repaired_word).sum()))


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];gold=np.concatenate(truth);ids=np.concatenate(obs['sequences']);offset=sum(map(len,obs['sequences'][:obs['offset']]));query=np.arange(len(gold))>=offset;sizes=list(map(len,obs['sequences'][obs['offset']:]));bounds=np.r_[0,np.cumsum(sizes)];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);proposals=load(OUT/'proposals.json');cells=[]
    for filename in load(OUT/'fit-index.json'):
        c=load(OUT/filename);seed=c['mask_seed'];rate=c['rate'];arm=c['arm'];strategy=c['strategy'];budget=c['budget'];proposal=next(p for p in proposals if all(p[k]==c[k] for k in ('mask_seed','rate','arm','strategy')));support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);newpairs=expand(support,proposal['additions'])&~support;prior=repair_prior(q,newpairs);old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');base=mixture(old['random'][old['selected']]['final_component'],q,EPSILON);baseline=predict(chain,base,obs);selected=c['runs'][c['selected']];pred=predict(chain,anchored_emission(base,selected['final_repair'],budget),obs);freq=predict(chain,anchored_emission(base,prior,budget),obs);fullfit=load(FULL/f'fits-{seed}-{rate}-{arm}-{strategy}-2.json');full=predict(chain,mixture(fullfit['random'][fullfit['selected']]['final_component'],q,EPSILON),obs);_,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset']);covered=support[gold,ids];repaired_word=newpairs.any(axis=0)[ids];flagged=np.array(proposal['flagged']);delta=(pred==gold).astype(int)-(baseline==gold).astype(int)
        row=dict(**{k:c[k] for k in ('mask_seed','rate','arm','strategy','budget')},selected_seed=selected['seed'],scores=token_metrics(pred,gold,masks),baseline=token_metrics(baseline,gold,masks),global_refit=token_metrics(full,gold,masks),frequency_only=token_metrics(freq,gold,masks),
            changes=changes(pred,baseline,gold,query,covered,repaired_word),global_changes=changes(full,baseline,gold,query,covered,repaired_word),frequency_changes=changes(freq,baseline,gold,query,covered,repaired_word),
            abstention=abstention_metrics(pred[query],gold[query],~covered[query],flagged[query]),active_states=int(newpairs.any(axis=1).sum()),converged=sum(r['converged'] for r in c['runs']),predicted_query=pred[query].tolist(),
            sentence_tokens=sizes,sentence_delta=[int(delta[offset+a:offset+b].sum()) for a,b in zip(bounds[:-1],bounds[1:])])
        assert row['scores']==selected['trace'][-1]['scores'];assert row['frequency_only']==c['frequency_only_scores'];cells.append(row)
    summary=[]
    for arm in ('word','ending'):
        for rate in (.1,.5):
            for strategy in ('context','random'):
                for budget in BUDGETS:
                    rr=[r for r in cells if r['arm']==arm and r['rate']==rate and r['strategy']==strategy and r['budget']==budget];assert len(rr)==5
                    row=dict(arm=arm,rate=rate,strategy=strategy,budget=budget,accuracy=spread([r['scores']['all_query']['accuracy'] for r in rr]),baseline_accuracy=spread([r['baseline']['all_query']['accuracy'] for r in rr]),global_accuracy=spread([r['global_refit']['all_query']['accuracy'] for r in rr]),frequency_accuracy=spread([r['frequency_only']['all_query']['accuracy'] for r in rr]),
                        changes={k:sum(r['changes'][k] for r in rr) for k in rr[0]['changes']},global_changes={k:sum(r['global_changes'][k] for r in rr) for k in rr[0]['global_changes']},frequency_changes={k:sum(r['frequency_changes'][k] for r in rr) for k in rr[0]['frequency_changes']},
                        retained_accuracy=sum(r['abstention']['retained_correct'] for r in rr)/sum(r['abstention']['retained'] for r in rr),retained_coverage=sum(r['abstention']['retained'] for r in rr)/(5*473),bootstrap=bootstrap(rr))
                    summary.append(row)
    comparisons=[]
    for arm in ('word','ending'):
        for rate in (.1,.5):
            a=sorted([r for r in cells if r['arm']==arm and r['rate']==rate and r['strategy']=='context' and r['budget']==PRIMARY],key=lambda r:r['mask_seed']);b=sorted([r for r in cells if r['arm']==arm and r['rate']==rate and r['strategy']=='random' and r['budget']==PRIMARY],key=lambda r:r['mask_seed']);diff=[dict(sentence_tokens=x['sentence_tokens'],sentence_delta=(np.array(x['sentence_delta'])-np.array(y['sentence_delta'])).tolist()) for x,y in zip(a,b)];net=sum(sum(r['sentence_delta']) for r in diff);comparisons.append(dict(arm=arm,rate=rate,accuracy_context_minus_random=net/(5*473),net_tags=net,bootstrap=bootstrap(diff)))
    save(OUT/'evaluation.json',dict(cells=cells,summary=summary,comparisons=comparisons,converged_fits=sum(c['converged'] for c in cells)))
    for r in summary:
        if r['strategy']=='context':print(r['arm'],r['rate'],r['budget'],'acc',r['accuracy']['mean'],'freq',r['frequency_accuracy']['mean'],'changes',r['changes'],'global',r['global_changes'])
    plot(summary)


def plot(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(9,4),layout='constrained')
    for ax,rate in zip(axes,(.1,.5)):
        for arm in ('word','ending'):
            rr=sorted([r for r in summary if r['arm']==arm and r['rate']==rate and r['strategy']=='context'],key=lambda r:r['budget']);ax.plot([r['changes']['spoiled'] for r in rr],[r['changes']['excluded_recovered'] for r in rr],'o-',label=arm+' fixed base');g=rr[0]['global_changes'];ax.scatter([g['spoiled']],[g['excluded_recovered']],marker='x',s=70,label=arm+' global refit')
            for r in rr:ax.annotate(f"{r['budget']:.1%}",(r['changes']['spoiled'],r['changes']['excluded_recovered']),fontsize=7,xytext=(3,3),textcoords='offset points')
        ax.set(title=f'{rate:.0%} true-class deletion',xlabel='Previously correct query tags spoiled',ylabel='Excluded query tags recovered');ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Fixed-base repair tradeoff: pooled five development perturbations');fig.savefig(OUT/'budgeted-repair-tradeoff.svg');plt.close(fig)

if __name__=='__main__':run()
