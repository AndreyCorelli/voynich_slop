"""Separate forced unambiguous tags from residual supported ambiguity."""
import numpy as np
from benchmarks.grammar_supported_classes_iteration29 import OUT,BASELINE,PREVIOUS,load,save,digest,scores
from voynich_smt.latent_cipher_classes import forward_backward,word_counts
from voynich_smt.class_alignment import FINE


def run():
    if (OUT/'analysis.json').exists():raise ValueError('Preserve analysis')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'support-truth.json')==load(OUT/'manifest.json')['support_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];st=load(OUT/'support-truth.json');mask=np.asarray(st['support']);counts=np.asarray(st['gold_counts']);chain=load(BASELINE/'chains.json')['oracle_development'];data=load(PREVIOUS/'datasets.json');records=data['background_calibration']+data['calibration'];results=load(OUT/'results.json');old=load(BASELINE/'results.json');ambiguous=mask.sum(axis=0)>1
    majority=counts.argmax(axis=0);majority_gamma=[np.eye(8)[majority[s]] for s in obs['sequences']]
    out=dict(support=dict(types=len(ambiguous),ambiguous_types=int(ambiguous.sum()),allowed_pairs=int(mask.sum()),total_pairs=mask.size,
        ambiguous_all_tokens=sum(int(ambiguous[s].sum()) for s in obs['sequences']),ambiguous_query_tokens=sum(int(ambiguous[s].sum()) for s in obs['sequences'][obs['offset']:])),
        privileged_word_majority=scores(majority_gamma,truth,obs['sequences'],mask,obs['offset']),arms={})
    for arm,result in results.items():
        oracle=result['oracle'];r=dict(initial=oracle['trace'][0],final=oracle['trace'][-1],converged=oracle['converged'],objective_gain=oracle['trace'][-1]['objective']-oracle['trace'][0]['objective'],
            query_correct_range=[min(t['query']['correct'] for t in oracle['trace']),max(t['query']['correct'] for t in oracle['trace'])])
        r['random_finals']=[dict(seed=a['seed'],converged=a['converged'],**a['trace'][-1]) for a in result['random']];r['objective_selected_random']=max(r['random_finals'],key=lambda a:a['objective'])
        _,gamma=forward_backward(chain,old[arm]['oracle']['final_emissions'],obs['sequences']);r['unrestricted_oracle_final']=scores(gamma,truth,obs['sequences'],mask,obs['offset'])
        violations=[]
        for s,g in zip(obs['sequences'],gamma):violations.append(sum(not mask[c,w] for c,w in zip(g.argmax(axis=1),s)))
        r['unrestricted_forbidden_predictions']=dict(all=sum(violations),query=sum(violations[obs['offset']:]))
        first=oracle['first_corruption'];r['first_corruption']=None
        if first:
            changes=[]
            for c in first['changes']:
                s=records[c['sentence_index']];changes.append(dict(c,sent_id=s['sent_id'],word=s['tokens'][c['position']],gold_name=FINE[c['gold']],before_name=FINE[c['before']],after_name=FINE[c['after']]))
            a=np.array(first['before_emissions']);b=np.array(first['after_emissions']);_,ga=forward_backward(chain,a,obs['sequences']);soft_counts=word_counts(obs['sequences'],ga,a.shape[1],8)
            log_ratio=np.log(b[mask]/a[mask]);q_delta=float(soft_counts[mask]@log_ratio);gold_delta=float(counts[mask]@log_ratio)
            delta={k:first['after'][k]-first['before'][k] for k in ('log_likelihood','prior','objective')}
            r['first_corruption']=dict(iteration=first['iteration'],changes=changes,lost=sum(c['lost'] for c in changes),gained=sum(c['gained'] for c in changes),
                query_lost=sum(c['lost'] and c['query'] for c in changes),query_gained=sum(c['gained'] and c['query'] for c in changes),delta=delta,
                old_posterior_expected_emission_delta=q_delta,posterior_kl_old_to_new=delta['log_likelihood']-q_delta,gold_path_delta=gold_delta,gold_path_plus_prior_delta=gold_delta+delta['prior'])
        # Same masks reveal whether high aggregate scores are forced singleton tags.
        r['initial_to_final_changes']=[]
        _,a=forward_backward(chain,oracle['initial_emissions'],obs['sequences']);_,b=forward_backward(chain,oracle['final_emissions'],obs['sequences'])
        from voynich_smt.oracle_emission_challenge import changed_tokens
        for c in changed_tokens(a,b,truth,obs['sequences'],obs['offset']):
            s=records[c['sentence_index']];r['initial_to_final_changes'].append(dict(c,sent_id=s['sent_id'],word=s['tokens'][c['position']],gold_name=FINE[c['gold']],before_name=FINE[c['before']],after_name=FINE[c['after']]))
        out['arms'][arm]=r
        print(arm,'updates',r['final']['iteration'],'objective_gain',r['objective_gain'],'all',r['initial']['all'],r['final']['all'],'query',r['initial']['query'],r['final']['query'],'ambiguous',r['final']['ambiguous_query'],'random',r['objective_selected_random'])
        f=r['first_corruption'];print('first',None if f is None else {k:v for k,v in f.items() if k!='changes'},'violations',r['unrestricted_forbidden_predictions'])
    save(OUT/'analysis.json',out);print('support',out['support'],'majority',out['privileged_word_majority'])

if __name__=='__main__':run()
