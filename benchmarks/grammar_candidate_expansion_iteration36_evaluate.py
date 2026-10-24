"""Candidate retrieval gains, false additions, and downstream decoding damage."""
import numpy as np
from benchmarks.grammar_candidate_expansion_iteration36 import OUT,FLAGS,PROBES,DATA,FITS,HARD,BASELINE,EXACT,SETTINGS,EPSILON,load,save,digest
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.missing_class_support import missing_support,cohorts,token_metrics
from voynich_smt.candidate_expansion import expand
from voynich_smt.candidate_abstention import abstention_metrics


def predict(chain,component,q,obs):return np.concatenate(forward_backward(chain,mixture(component,q,EPSILON),obs['sequences'])[1]).argmax(axis=1)


def bootstrap(rows,reps=1000):
    sizes=np.array(rows[0]['sentence_tokens']);d=np.array([r['sentence_delta'] for r in rows]);rng=np.random.default_rng(3601);values=[]
    for _ in range(reps):
        ix=rng.integers(len(sizes),size=len(sizes));values.append(float(d[:,ix].sum()/(len(rows)*sizes[ix].sum())))
    return dict(replicates=reps,paired_sentence_95=[float(v) for v in np.quantile(values,[.025,.975])])


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings']);gold=np.concatenate(truth);ids=np.concatenate(obs['sequences']);offset=sum(map(len,obs['sequences'][:obs['offset']]));query=np.arange(len(gold))>=offset;sizes=list(map(len,obs['sequences'][obs['offset']:]));bounds=np.r_[0,np.cumsum(sizes)];cells=[]
    for proposal,filename in zip(load(OUT/'proposals.json'),load(OUT/'fit-index.json')):
        seed=proposal['mask_seed'];rate=proposal['rate'];arm=proposal['arm'];support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);enlarged=expand(support,proposal['additions']);newpairs=enlarged&~support;originalcovered=support[gold,ids];newcovered=enlarged[gold,ids];regained=~originalcovered&newcovered;flagged=np.array(proposal['flagged']);old=load(FITS/f'fits-{seed}-{rate}-{EPSILON}-{arm}.json');baseline=predict(chain,old['random'][old['selected']]['final_component'],q,obs);fit=load(OUT/filename);selected=fit['random'][fit['selected']];pred=predict(chain,selected['final_component'],q,obs);warm=predict(chain,fit['warm']['final_component'],q,obs);_,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
        good=(pred==gold)&(baseline!=gold);bad=(pred!=gold)&(baseline==gold);delta=(pred==gold).astype(int)-(baseline==gold).astype(int);bq=baseline[query];pq=pred[query];gq=gold[query];eq=~originalcovered[query];fq=flagged[query]
        row=dict(**{k:proposal[k] for k in ('mask_seed','rate','arm','strategy','k')},selected_seed=selected['seed'],
            proposal=dict(words=len(proposal['additions']),added_pairs=int(newpairs.sum()),true_added_pairs=int((newpairs&reference).sum()),false_added_pairs=int((newpairs&~reference).sum()),
                original_excluded_query=int((query&~originalcovered).sum()),candidate_regained_query=int((query&regained).sum()),candidate_regained_all=int(regained.sum()),candidate_regained_unflagged_query=int((query&regained&~flagged).sum()),
                old_query_candidate_coverage=float(originalcovered[query].mean()),new_query_candidate_coverage=float(newcovered[query].mean())),
            scores=token_metrics(pred,gold,masks),baseline_scores=token_metrics(baseline,gold,masks),warm_scores=token_metrics(warm,gold,masks),
            changes=dict(corrected_query=int((good&query).sum()),spoiled_query=int((bad&query).sum()),net_query=int(delta[query].sum()),recovered_originally_excluded_query=int(((pred==gold)&~originalcovered&query).sum()),
                recovered_regained_query=int(((pred==gold)&regained&query).sum()),spoiled_correct_covered_query=int((bad&originalcovered&query).sum())),
            abstention=abstention_metrics(pq,gq,eq,fq),baseline_abstention=abstention_metrics(bq,gq,eq,fq),predicted_query=pq.tolist(),
            convergence=dict(warm=fit['warm']['converged'],random=sum(r['converged'] for r in fit['random'])),sentence_tokens=sizes,sentence_delta=[int(delta[offset+a:offset+b].sum()) for a,b in zip(bounds[:-1],bounds[1:])])
        assert row['scores']['all_query']==selected['trace'][-1]['scores']['all_query'];cells.append(row)
    summary=[]
    for arm in ('word','ending'):
        for rate in (.1,.5):
            for strategy,k in SETTINGS:
                group=[c for c in cells if c['arm']==arm and c['rate']==rate and c['strategy']==strategy and c['k']==k];assert len(group)==5
                summed={key:sum(r['proposal'][key] for r in group) for key in ('words','added_pairs','true_added_pairs','false_added_pairs','original_excluded_query','candidate_regained_query','candidate_regained_unflagged_query')}
                changes={key:sum(r['changes'][key] for r in group) for key in group[0]['changes']}
                summary.append(dict(arm=arm,rate=rate,strategy=strategy,k=k,proposal_counts=summed,changes=changes,
                    pair_precision=summed['true_added_pairs']/summed['added_pairs'] if summed['added_pairs'] else None,retrieval_recall_gain=summed['candidate_regained_query']/summed['original_excluded_query'],
                    baseline_accuracy=spread([r['baseline_scores']['all_query']['accuracy'] for r in group]),accuracy=spread([r['scores']['all_query']['accuracy'] for r in group]),warm_accuracy=spread([r['warm_scores']['all_query']['accuracy'] for r in group]),
                    candidate_coverage=spread([r['proposal']['new_query_candidate_coverage'] for r in group]),retained_accuracy=spread([r['abstention']['retained_accuracy'] for r in group]),baseline_retained_accuracy=spread([r['baseline_abstention']['retained_accuracy'] for r in group]),retained_coverage=spread([r['abstention']['coverage'] for r in group]),bootstrap=bootstrap(group)))
    result=dict(cells=cells,summary=summary,convergence=dict(warm=sum(c['convergence']['warm'] for c in cells),random=sum(c['convergence']['random'] for c in cells)))
    save(OUT/'evaluation.json',result)
    for s in summary:print(s['arm'],s['rate'],s['strategy'],s['k'],'pairP',s['pair_precision'],'retrieved',s['proposal_counts']['candidate_regained_query'],'/',s['proposal_counts']['original_excluded_query'],'accuracy',s['accuracy']['mean'],'base',s['baseline_accuracy']['mean'],'changes',s['changes'])

if __name__=='__main__':run()
