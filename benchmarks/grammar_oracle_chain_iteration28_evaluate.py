"""Compare fixed source and oracle-development chain trajectories."""
import numpy as np
from benchmarks.grammar_oracle_chain_iteration28 import OUT,BASELINE,PREVIOUS,load,save,digest
from benchmarks.grammar_oracle_emission_challenge_iteration27_evaluate import gold_joint
from voynich_smt.class_alignment import FINE


def summarize(result,chain,obs,truth,records):
    oracle=result['oracle'];trace=oracle['trace'];first=oracle['first_corruption'];random=[]
    for r in result['random']:random.append(dict(seed=r['seed'],converged=r['converged'],**r['trace'][-1]))
    output=dict(initial=trace[0],final=trace[-1],converged=oracle['converged'],objective_gain=trace[-1]['objective']-trace[0]['objective'],
        first_net_accuracy_loss=oracle['first_net_accuracy_loss'],random_finals=random,objective_selected_random=max(random,key=lambda a:a['objective']),
        random_beating_oracle_final=[r['seed'] for r in random if r['objective']>trace[-1]['objective']])
    if first is None:output['first_corruption']=None;return output
    before=gold_joint(chain,first['before_emissions'],obs['sequences'],truth);after=gold_joint(chain,first['after_emissions'],obs['sequences'],truth)
    changes=[]
    for c in first['changes']:
        record=records[c['sentence_index']];w=c['word_id']
        changes.append(dict(c,sent_id=record['sent_id'],word=record['tokens'][c['position']],sentence=record['tokens'],gold_name=FINE[c['gold']],before_name=FINE[c['before']],after_name=FINE[c['after']],
            before_emissions=np.asarray(first['before_emissions'])[:,w].tolist(),after_emissions=np.asarray(first['after_emissions'])[:,w].tolist()))
    output['first_corruption']=dict(iteration=first['iteration'],components=first['delta'],gold_joint_delta=after['total']-before['total'],
        gold_plus_prior_delta=after['total']-before['total']+first['delta']['prior'],
        old_posterior_expected_emission_delta=first['old_posterior_expected_emission_delta'],posterior_kl_old_to_new=first['posterior_kl_old_to_new'],
        changes=changes,lost=sum(c['lost'] for c in changes),gained=sum(c['gained'] for c in changes),query_lost=sum(c['lost'] and c['query'] for c in changes),query_gained=sum(c['gained'] and c['query'] for c in changes))
    return output


def run():
    if (OUT/'analysis.json').exists():raise ValueError('Preserve analysis')
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'chains.json')==load(OUT/'manifest.json')['chains_hash']
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];data=load(PREVIOUS/'datasets.json');records=data['background_calibration']+data['calibration'];chains=load(OUT/'chains.json');out={}
    for name,path in [('source',BASELINE),('oracle_development',OUT)]:
        out[name]={}
        for arm,result in load(path/'results.json').items():
            r=summarize(result,chains[name],obs,truth,records);out[name][arm]=r
            print(name,arm,'iterations',r['final']['iteration'],'initial/final accuracy',r['initial']['query']['accuracy'],r['final']['query']['accuracy'],'balanced',r['initial']['query']['balanced_accuracy'],r['final']['query']['balanced_accuracy'],'all',r['initial']['all']['accuracy'],r['final']['all']['accuracy'],'gain',r['objective_gain'],'random_best',r['objective_selected_random'])
            if r['first_corruption']:
                c=r['first_corruption'];print('first',c['iteration'],'loss/gain',c['lost'],c['gained'],'query',c['query_lost'],c['query_gained'],'delta',c['components'],'gold+prior',c['gold_plus_prior_delta'])
    save(OUT/'analysis.json',out)

if __name__=='__main__':run()
