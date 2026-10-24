"""Oracle versus cavity-inferred neighbors on existing missing-candidate cohorts."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_soft_fallback_iteration32 import OUT as FITS,HARD,BASELINE,EXACT,PREVIOUS,PRIMARY,MASK_SEEDS,load,save,digest
from voynich_smt.latent_cipher_classes import prior_data,forward_backward
from voynich_smt.fallback_emissions import mixture
from voynich_smt.missing_class_support import missing_support,cohorts
from voynich_smt.masked_class_context import local_distribution,masked_context,probability_metrics

OUT=FITS.parent/'iteration33'
RATES=(.1,.5)
EPSILONS=(PRIMARY,.3)


def produce(chain,emission,obs,truth):
    modes={name:[] for name in ('oracle_context','masked_neighbors','masked_hmm','oracle_context_with_emission','ordinary_hmm','class_frequency')};details=[]
    ordinary=forward_backward(chain,emission,obs['sequences'])[1]
    for sent_index,(seq,gold,gamma) in enumerate(zip(obs['sequences'],truth,ordinary)):
        evidence=emission[:,seq].T;masked=masked_context(chain,evidence)
        for i,y in enumerate(gold):
            left=gold[i-1] if i else None;right=gold[i+1] if i+1<len(gold) else None
            values=dict(oracle_context=local_distribution(chain,left,right),masked_neighbors=masked['neighbor_distribution'][i],masked_hmm=masked['posterior'][i],
                oracle_context_with_emission=local_distribution(chain,left,right,evidence[i]),ordinary_hmm=gamma[i],class_frequency=np.asarray(chain['source_occupancy']))
            for name,p in values.items():modes[name].append(p.tolist())
            details.append(dict(sentence_index=sent_index,position=i,word_id=seq[i],gold=y,left_gold=left,right_gold=right,left_inferred=masked['left'][i],right_inferred=masked['right'][i],
                neighbors_correct=bool(left==masked['left'][i] and right==masked['right'][i])))
    return dict(probabilities=modes,tokens=details)


def evaluate(predictions,gold,masks):
    result={}
    for name,p in predictions['probabilities'].items():result[name]={cohort:probability_metrics(p,gold,mask) for cohort,mask in masks.items()}
    correct=np.array([t['neighbors_correct'] for t in predictions['tokens']]);diagnostics={}
    for cohort in ('all_query','excluded_query','covered_query'):
        m=masks[cohort];n=int(m.sum());diagnostics[cohort]=dict(tokens=n,neighbors_correct=int((m&correct).sum()),neighbors_correct_fraction=float(correct[m].mean()) if n else None)
        for condition,selector in [('correct_neighbors',m&correct),('wrong_neighbors',m&~correct)]:
            diagnostics[cohort][condition]={mode:probability_metrics(predictions['probabilities'][mode],gold,selector) for mode in ('oracle_context','masked_neighbors','masked_hmm')}
        for mode in ('masked_neighbors','masked_hmm','oracle_context_with_emission','ordinary_hmm'):
            oracle=np.asarray(predictions['probabilities']['oracle_context']).argmax(axis=1);pred=np.asarray(predictions['probabilities'][mode]).argmax(axis=1)
            diagnostics[cohort][mode+'_versus_oracle']=dict(oracle_only_correct=int(((oracle==gold)&(pred!=gold)&m).sum()),mode_only_correct=int(((oracle!=gold)&(pred==gold)&m).sum()))
    return dict(metrics=result,neighbor_audit=diagnostics)


def run():
    if OUT.exists():raise ValueError('Preserve artifacts')
    for filename in (FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json'):
        for p,h in load(filename)['inputs'].items():assert digest(p)==h,p
    obs=load(PREVIOUS/'observations.json')['calibration'];truth=load(PREVIOUS/'observation-truth.json')['calibration'];reference=np.array(load(EXACT/'support-truth.json')['support']);chain=load(BASELINE.parent/'iteration28/chains.json')['oracle_development'];additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');q,_,_=prior_data(obs['sequences'],obs['word_endings'])
    paths=[Path(__file__),Path('src/voynich_smt/masked_class_context.py'),Path('src/voynich_smt/latent_cipher_classes.py'),FITS/'verification-manifest.json',HARD/'verification-manifest.json',BASELINE/'verification-manifest.json',EXACT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',PREVIOUS/'observations.json',PREVIOUS/'observation-truth.json',EXACT/'support-truth.json',BASELINE/'schedules.json',HARD/'deletions.json',BASELINE.parent/'iteration28/chains.json']
    OUT.mkdir();save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},rates=RATES,epsilons=EPSILONS,primary_epsilon=PRIMARY,mask_seeds=MASK_SEEDS,
        scope='Existing development240 only; no new fitting, fresh scoring or reserve access. Frozen iteration32 objective-selected random fits.',
        primary='Oracle true immediate neighbor states versus cavity-inferred neighbor MAP states, both with target emission flat over all8 classes. Conditional weights start/transition/stop only.',
        masking='For each target independently remove its emission evidence before inferring neighbor marginals. Frozen emission parameters still transductively fitted on corpus; this is masking at decode, not leave-one-out fitting.',
        other_probes='Exact target-masked HMM posterior with all other emissions observed; true-neighbor posterior retaining original target emission; ordinary HMM; oracle corpus class-frequency baseline.',
        interpretation='True-neighbor context is privileged and local first-order, not a universal performance upper bound. No claim of usable decoding from gold neighbors.',
        metrics='All/query, excluded, covered and matched cohorts; top1/balanced/top2/top3/gold-probability/log-loss; neighbor correctness and paired oracle/inferred errors; stable class-index tie breaks.'))
    index=[];results=[]
    for seed in MASK_SEEDS:
        for rate in RATES:
            support,affected=missing_support(reference,additions[str(seed)],deletions[str(seed)],rate);gold,masks=cohorts(obs['sequences'],truth,support,affected,reference,obs['offset'])
            for epsilon in EPSILONS:
                for arm in ('word','ending'):
                    print('Context',seed,rate,epsilon,arm,flush=True);fit=load(FITS/f'fits-{seed}-{rate}-{epsilon}-{arm}.json');selected=fit['random'][fit['selected']];emission=mixture(selected['final_component'],q,epsilon)
                    prediction=produce(chain,emission,obs,truth);filename=f'probe-{seed}-{rate}-{epsilon}-{arm}.json';save(OUT/filename,prediction);index.append(filename)
                    results.append(dict(mask_seed=seed,rate=rate,epsilon=epsilon,arm=arm,selected_seed=selected['seed'],**evaluate(prediction,gold,masks)))
    save(OUT/'probe-index.json',index);save(OUT/'evaluation.json',results);print('Saved',len(index),'frozen-model context probes',flush=True)

if __name__=='__main__':run()
