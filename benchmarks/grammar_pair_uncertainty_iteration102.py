"""Source-calibrated uncertainty of joint pair rankings; no target-selected policy."""
from benchmarks.grammar_repair_abstention_iteration98 import *
from voynich_smt.pair_uncertainty import sentence_totals,gains_from_totals,summarize,calibrate as calibrate102,evaluate as evaluate102
import numpy as np
OUT=ROOT/'iteration102'


def process(base,bank,anchors,model,folder,seed,cached_folder,words,core=None):
    folder.mkdir();rng=np.random.default_rng(seed);weights=rng.multinomial(len(base),np.full(len(base),1/len(base)),size=256);np.savez_compressed(folder/'weights.npz',weights=weights)
    result=[]
    for ci,(case,replacements) in enumerate(bank.items()):
        public=perturb(base,replacements,anchors);pairs=load(cached_folder/(case+'.json'))['scores']
        if core is not None:
            allowed={t['id'] for s in base for t in s['tokens'] if t['anchor'] in core};pairs=[p for p in pairs if set(p['pair'])<=allowed]
        proposed={t['id']:t['tag'] for s in public for t in s['tokens']};counts=[];sums=[];draws=[]
        for p in pairs:
            n,q=sentence_totals(public,p['pair'],model);tags=[proposed[i] for i in p['pair']];gain=float(gains_from_totals(n.sum(axis=0),q.sum(axis=0),tags));assert math.isclose(gain,p['gain'],rel_tol=1e-9,abs_tol=1e-10),(case,gain,p)
            counts.append(n);sums.append(q);draws.append(gains_from_totals(weights@n,weights@q,tags))
        boot=np.array(draws).T;features=summarize(pairs,boot);np.savez_compressed(folder/(case+'.npz'),counts=np.array(counts),sums=np.array(sums),draws=boot)
        # Reference is attached only after blind probability/ranking computation.
        ref=reference_for(base,replacements,case.startswith('swap_'),pairs,words if core is None else core)
        record=dict(case=case,features=features,reference=ref,pairs=pairs,proposed=[[proposed[i] for i in p['pair']] for p in pairs]);save(folder/(case+'.json'),record);result.append(record)
        if ci%20==0:print(folder.name,ci+1,'/',len(bank),flush=True)
    return result


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/pair_uncertainty.py'),ROOT/'iteration101/verification-manifest.json',ROOT/'iteration98/verification-manifest.json',ROOT/'iteration98/blocks.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration93/models.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration100/blocks.json',ROOT/'iteration100/core.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='256 multinomial sentence-cluster resamples, seed102000+blockindex, sharedweights ALLcases/pairs withinblock. Frozen93context jointpairmask/probabilities, frozenoriginal support5occ3sentences; resampling conditional on original eligible pool, absentendpoint invalid(-inf), no replicate count regating. Reconstructcached98/100pointgains. Originaluniquetopcandidate only; bootstrapuniquetopfrequency amongoriginalsupportedpairs(ties/missingselectedendpoint fail); lower5percentgain and gap orderstat floor(.05*(255)), missingselectedendpoint -inf. Candidate lower-bound unavailable/nonfinite =>abstain. PRIMARYgain+stability thresholds .5,.75,.9,.95,.99,1 plus allattainable nonnegative pointgains; SECONDARYlowergain allattainablenonnegative with lowergap>=0. Calibrate all603source98cases 829full+8x100,16candidates,64swaps+3controls. Same98guards>=90percent eachfull/sparse,10full20sparsecalls,zeroclean/sameclasscalls,zerounavailablewrong. Maxhits,minwrong,higherthreshold,higherstability. NoqualifierOFF. Freeze policies BEFORE loading100targetcasefeatures/results. Baselines original95cut and98gain/gappolicies. Evaluation all9existing100blocks, fixedcore8 and15crossswaps+3controls, no reselectcore. Targets developmentonly; report evenOFF noPPintegration needed. No newannotations/reserve/sealedtest/authorqueries/wordexceptions. Resampling uncertainty is diagnostic,notformalprecisionguarantee; cannot remove systematicbias.'))
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];model=load(ROOT/'iteration93/models.json')['context'];words=load(ROOT/'iteration93/types.json')['candidates'];bank=load(ROOT/'iteration98/calibration-bank.json');cases=[]
    for bi,(block,ids) in enumerate(load(ROOT/'iteration98/blocks.json')['scored'].items()):
        base=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,'cal98-'+block)
        rows=process(base,bank,anchors,model,OUT/block,102000+bi,ROOT/'iteration98'/block,words)
        for r in rows:r.update(block=block,regime='full' if block=='full' else 'sparse')
        cases+=rows
    save(OUT/'calibration-cases.json',cases);policies={}
    for arm in ['stability','lower']:
        chosen,curve=calibrate102(cases,arm);policies[arm]=chosen['policy'];save(OUT/('curve-'+arm+'.json'),curve);print('CHOSEN',arm,chosen,flush=True)
    policies['frozen95']=dict(arm='baseline',threshold=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'],gap=0.)
    for arm in ['absolute','margin']:policies['baseline98_'+arm]=dict(arm='baseline',**{k:v for k,v in load(ROOT/'iteration98/policies.json')[arm].items() if k in ['threshold','gap']})
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json',OUT/'calibration-cases.json',OUT/'curve-stability.json',OUT/'curve-lower.json']}));save(OUT/'calibration-summary.json',{a:evaluate102(cases,p) for a,p in policies.items()})
    core=load(ROOT/'iteration100/core.json');corebank={k:v for k,v in bank.items() if not k.startswith('swap_') or set(v)<=set(core)};evaluation=[]
    for bi,(block,ids) in enumerate(load(ROOT/'iteration100/blocks.json').items()):
        base=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,'testlength100-'+block)
        rows=process(base,corebank,anchors,model,OUT/('eval-'+block),103000+bi,ROOT/'iteration100'/block,words,core)
        for r in rows:r.update(block=block,regime=block)
        evaluation+=rows
    save(OUT/'evaluation-cases.json',evaluation);save(OUT/'evaluation-summary.json',{a:evaluate102(evaluation,p) for a,p in policies.items()})
if __name__=='__main__':run()
