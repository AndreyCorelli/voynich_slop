"""Post-result development-only continuation; primary fresh scores remain frozen."""
from benchmarks.grammar_latent_classes_iteration26 import OUT,load,save,arm_input
from benchmarks.grammar_latent_classes_iteration26_evaluate import class_metrics
from voynich_smt.latent_cipher_classes import fit,forward_backward


def run():
    if (OUT/'development-continuation.json').exists():raise ValueError('Preserve diagnostic')
    obs=load(OUT/'observations.json')['calibration'];truth=load(OUT/'observation-truth.json')['calibration'][obs['offset']:]
    chain=load(OUT/'source-models.json')['chains']['pooled'];old=load(OUT/'calibration-fits.json');out={}
    for arm in ('word','ending'):
        result=old[arm];initial=result['fits'][result['selected']];seq,we=arm_input(obs,arm)
        continued=fit(chain,seq,we,initial['seed'],sharing=arm=='ending',initial=initial['emissions'],max_iter=400)
        score=lambda e:class_metrics(forward_backward(chain,e,obs['sequences'])[1][obs['offset']:],truth)
        out[arm]=dict(before=score(initial['emissions']),after=score(continued['emissions']),objective_gain=continued['objective']-initial['objective'],continuation=continued)
        print(arm,'converged',continued['converged'],'extra_iterations',continued['iterations'],'objective_gain',out[arm]['objective_gain'],'balanced_before/after',out[arm]['before']['balanced_accuracy'],out[arm]['after']['balanced_accuracy'])
    save(OUT/'development-continuation.json',dict(scope='Post-result development-only diagnostic; no fresh target continuation or policy changes',arms=out))

if __name__=='__main__':run()
