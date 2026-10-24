"""Audit freshness, frozen policies, all fitted objectives, and decoding replays."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_fresh_repair_iteration39 import OUT,ROOT,RESERVE,load,save,digest,strings
from voynich_smt.latent_cipher_classes import forward_backward,prior_data
from voynich_smt.fallback_emissions import mixture
from voynich_smt.budgeted_candidate_repair import anchored_emission

def validate():
    manifest=load(OUT/'manifest.json');checks=0
    for filename in ('manifest.json','fit-freeze.json','repair-freeze.json','evaluation-freeze.json'):
        record=load(OUT/filename)
        for p,h in record['inputs'].items():assert digest(p)==h,p;checks+=1
    used=set()
    for p,h in manifest['prior_declarations'].items():assert digest(p)==h,p;used.update(strings(load(Path(p))))
    ids=[sid for rows in manifest['split_ids'].values() for sid in rows];reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows}
    assert len(ids)==len(set(ids))==200 and not set(ids)&(used|reserve) and len(reserve)==200
    config=load(OUT/'configuration.json');assert config['chain']==load(ROOT/'iteration28/chains.json')['oracle_development']
    for key,budget in config['budgets'].items():assert budget==load(ROOT/'iteration38/policies.json')[key+'/0.01']['budget']
    fitfiles=list(OUT.glob('baseline-*.json'))+[p for p in OUT.glob('repair-*.json') if p.name!='repair-freeze.json'];converged=0
    for path in fitfiles:
        record=load(path);assert record['selected']==max(range(5),key=lambda i:record['runs'][i]['trace'][-1])
        for run in record['runs']:
            trace=np.array(run['trace']);assert np.all(np.diff(trace)>=-1e-6);assert np.isfinite(trace).all();converged+=run['converged']
    obs=load(OUT/'observations.json');replays=0
    for row in load(OUT/'predictions.json'):
        o=obs[row['author']];q,_,_=prior_data(o['sequences'],o['word_endings']);baseline=load(OUT/f"baseline-{row['key']}.json");base=mixture(baseline['runs'][baseline['selected']]['component'],q,.01);repair=load(OUT/f"repair-{row['key']}-{row['strategy']}.json");emission=anchored_emission(base,repair['runs'][repair['selected']]['component'],row['budget'])
        assert np.allclose(emission.sum(axis=1),1)
        for e,key in ((base,'baseline'),(emission,'prediction')):
            pred=np.concatenate(forward_backward(config['chain'],e,o['sequences'])[1]).argmax(axis=1).tolist();assert pred==row[key];replays+=1
    result=dict(hash_checks=checks,fresh_sentences=200,reserved_unscored=200,fit_cells=len(fitfiles),fits=len(fitfiles)*5,converged=converged,decoding_replays=replays)
    save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
