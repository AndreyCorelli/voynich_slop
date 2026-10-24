"""Label-free fitting and independently declared fresh confirmation boundaries."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_fresh_repair_iteration39 import fit,OUT,ROOT,load,strings
from voynich_smt.latent_cipher_classes import fixed_chain,prior_data
from voynich_smt.supported_emissions import supported_prior,supported_log_prior
from voynich_smt.fallback_emissions import mixture,mixture_step


def test_label_free_fit_improves_normalized_emissions_without_mutating_start():
    seq=[[0,1,0],[1,0,1]];chain=fixed_chain([[0,1,0],[1,0,1]],2);support=np.ones((2,2),bool);prior=supported_prior(seq,[0,1],support);q,_,_=prior_data(seq,[0,1]);initial=np.array([[.9,.1],[.2,.8]]);saved=initial.copy()
    run=fit(initial,lambda a:mixture(a,q,.01),lambda a:supported_log_prior(a,prior),lambda a:mixture_step(chain,a,seq,prior,q,.01),seq,chain)
    assert np.array_equal(initial,saved)
    assert run['converged'] and run['trace'][-1]>run['trace'][0]
    assert np.allclose(np.array(run['component']).sum(axis=1),1)


def test_confirmation_uses_previous_policies_and_disjoint_declarations():
    manifest=load(OUT/'manifest.json');used=set()
    for path in manifest['prior_declarations']:used.update(strings(load(Path(path))))
    ids={sid for rows in manifest['split_ids'].values() for sid in rows}
    assert len(ids)==200 and not ids&used
    config=load(OUT/'configuration.json')
    for key,budget in config['budgets'].items():assert budget==load(ROOT/'iteration38/policies.json')[key+'/0.01']['budget']
