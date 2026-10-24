"""Explain oracle-initialized EM drift using development labels only."""
import numpy as np
from benchmarks.grammar_oracle_emission_challenge_iteration27 import OUT,PREVIOUS,load,save,digest
from voynich_smt.class_alignment import FINE


def gold_joint(chain,emissions,sequences,truth):
    e=np.log(emissions);a=np.log(chain['start']);t=np.log(chain['transition']);z=np.log(chain['stop']);r=dict(start=0.,transition=0.,stop=0.,emission=0.)
    for seq,y in zip(sequences,truth):
        r['start']+=float(a[y[0]]);r['stop']+=float(z[y[-1]])
        r['transition']+=float(sum(t[x,w] for x,w in zip(y,y[1:])));r['emission']+=float(sum(e[s,w] for s,w in zip(y,seq)))
    r['total']=sum(r.values());return r


def run():
    if (OUT/'analysis.json').exists():raise ValueError('Preserve analysis')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    results=load(OUT/'results.json');obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];chain=load(PREVIOUS/'source-models.json')['chains']['pooled'];data=load(PREVIOUS/'datasets.json');records=data['background_calibration']+data['calibration'];out={}
    for arm,r in results.items():
        o=r['oracle'];first=o['first_corruption'];gold={name:gold_joint(chain,first[name+'_emissions'],obs['sequences'],truth) for name in ('before','after')}
        changed=[]
        before=np.asarray(first['before_emissions']);after=np.asarray(first['after_emissions'])
        for c in first['changes']:
            s=records[c['sentence_index']];w=c['word_id'];y=c['gold'];old=c['before'];new=c['after']
            changed.append(dict(c,sent_id=s['sent_id'],word=s['tokens'][c['position']],sentence=s['tokens'],gold_name=FINE[y],before_name=FINE[old],after_name=FINE[new],
                before_emissions=before[:,w].tolist(),after_emissions=after[:,w].tolist()))
        delta={k:gold['after'][k]-gold['before'][k] for k in gold['before']}
        posterior_delta=delta['total']-first['delta']['log_likelihood']
        random=[dict(seed=a['seed'],converged=a['converged'],iterations=a['trace'][-1]['iteration'],**a['trace'][-1]) for a in r['random']]
        selected=max(random,key=lambda a:a['objective'])
        out[arm]=dict(initial=o['trace'][0],first_update=o['trace'][1],final=o['trace'][-1],converged=o['converged'],
            first_corruption_iteration=first['iteration'],components=first['delta'],gold_path=gold,gold_path_delta=delta,
            gold_path_plus_prior_delta=delta['total']+first['delta']['prior'],gold_path_log_posterior_delta=posterior_delta,
            changed_tokens=changed,lost=sum(c['lost'] for c in changed),gained=sum(c['gained'] for c in changed),
            query_lost=sum(c['lost'] and c['query'] for c in changed),query_gained=sum(c['gained'] and c['query'] for c in changed),
            random_finals=random,objective_selected_random=selected,random_beating_oracle_final=[a['seed'] for a in random if a['objective']>o['trace'][-1]['objective']])
        print(arm,'gold-path change',delta['total'],'gold+prior',out[arm]['gold_path_plus_prior_delta'],'log posterior delta',posterior_delta,'query lost/gained',out[arm]['query_lost'],out[arm]['query_gained'])
        for c in changed:
            print('query' if c['query'] else 'background',c['word'],c['gold_name'],c['before_name'],'->',c['after_name'],'lost',c['lost'],'gained',c['gained'])
    save(OUT/'analysis.json',out)

if __name__=='__main__':run()
