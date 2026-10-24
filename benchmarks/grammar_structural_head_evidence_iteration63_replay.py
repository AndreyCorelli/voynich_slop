"""Replay audit with numerical tolerances for sparse floating-point reductions.

The initial frozen audit required exact equality of refitted floating-point
models. Sparse feature iteration can change reduction order across processes.
No experimental model, policy or prediction is changed by this audit.
"""
from collections import Counter
from benchmarks.grammar_structural_head_evidence_iteration63 import *


def run():
    hashes=0
    for name in ('design-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];models=load(OUT/'models.json');units=load(UNIT/'models.json');rows=load(OUT/'frame-predictions.json');prior=load(UNIT/'frame-predictions.json');old={(r['sid'],r['subject']):r for r in prior};by_sid=defaultdict(list);fold_by_sid={}
    for r in rows:by_sid[r['sid']].append(r)
    refits=policies=predictions=true_type=cue_replays=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not(a&b or a&c or b&c);training,_=prepare(part['fit'],data);cal,_=prepare(part['calibration'],data);w=np.asarray(units[str(f)]['model']['weights'])
        for mode in MODES:
            record=models[str(f)][mode];retrained=fit(training,data,mode)
            np.testing.assert_allclose(retrained['weights'],record['proxy']['weights'],rtol=1e-6,atol=1e-7)
            np.testing.assert_allclose(retrained['loss'],record['proxy']['loss'],rtol=1e-9,atol=1e-11)
            for key in ('mode','vocabulary','training_frames','training_pairs','weighted_positive_rates','regularization','minimum_feature_count'):assert retrained[key]==record['proxy'][key]
            refits+=1
            frames=calibration_frames(cal,data,units[str(f)]['model'],retrained)
            for arm in ARMS:assert calibrate(frames,arm)==record['policies'][arm];policies+=1
        for sid in part['test']:
            fold_by_sid[sid]=str(f);tokens=data[sid]['tokens']
            for r in by_sid[sid]:
                assert all(r[k]==v for k,v in old[(sid,r['subject'])].items())
                gold=r['unit_gold']
                for field,v in (('structure_pipeline',r['arms']['carrierfit_carriercal']['f1']),('structure_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        assert all(p is None for p in r[field].values());continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@w;assert select(scores,options,r['subject'],v)==r[field]['baseline']
                    for mode in MODES:
                        record=models[str(f)][mode];cues=evidence(tokens,v,options,record['proxy'])
                        for arm in ARMS:
                            p=record['policies'][arm]['selected'];name=mode+'_'+arm
                            assert infer(scores,options,r['subject'],v,cues,p['phrase_weight'],p['clause_weight'])==r[field][name];predictions+=1
                            if field=='structure_oracle_endpoint':
                                kept=[j for j,(_,role) in enumerate(options) if role==gold[3]]
                                assert infer(scores[kept],[options[j] for j in kept],r['subject'],v,cues[kept],p['phrase_weight'],p['clause_weight'])==r['structure_true_type'][name];true_type+=1
    cue_rows=load(OUT/'cue-predictions.json')
    for r in cue_rows:
        f=fold_by_sid[r['sid']];tokens=data[r['sid']]['tokens'];s,h,v,_=r['gold'];options=choices(tokens,s,v);scores=matrix(tokens,s,v,options)@np.asarray(units[f]['model']['weights']);heads=[c['head'] for c in r['candidates']]
        ps={m:probabilities(tokens,v,heads,models[f][m]['proxy']) for m in MODES}
        for j,c in enumerate(r['candidates']):
            assert flags(tokens,c['head'],v)==c['flags'];assert float(scores[options.index((c['head'],'cop'))])==c['score']
            for m in MODES:np.testing.assert_allclose(ps[m][j],c['probabilities'][m],rtol=1e-10,atol=1e-12)
            cue_replays+=1
    assert evaluate(rows)==load(OUT/'evaluation.json');assert cue_metrics(cue_rows)==load(OUT/'cue-metrics.json')
    paired={}
    for arm in ALL_ARMS[1:]:
        counts=Counter()
        for r in rows:
            if r['carrier_ambiguous']:continue
            a=r['structure_pipeline']['baseline'];b=r['structure_pipeline'][arm];g=r['unit_gold']
            if a!=b:
                counts['changed']+=1
                if g is not None and a==g:counts['lost_exact']+=1
                if g is not None and b==g:counts['gained_exact']+=1
        paired[arm]=dict(counts)
    save(OUT/'additional-audit.json',dict(paired=paired));save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,refitted_models=refits,calibration_replays=policies,prediction_replays=predictions,true_type_replays=true_type,candidate_cue_replays=cue_replays,evaluation_replayed=True,prior_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0));print('Audit passed',refits,policies,predictions,true_type,cue_replays,paired)
if __name__=='__main__':run()
