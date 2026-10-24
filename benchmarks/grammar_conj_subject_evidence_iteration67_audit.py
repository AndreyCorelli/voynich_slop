"""Refit POS probes and replay calibrated evidence and all saved outputs."""
from benchmarks.grammar_conj_subject_evidence_iteration67 import *


def run():
    hashes=0
    for name in ('design-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];cal=load(BASE/'calibration-lattices.json');test=load(BASE/'test-lattices.json');base=load(BASE/'policies.json');units=load(UNIT/'models.json');models=load(OUT/'models.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};refits=checks=0
    for r in load(PREVIOUS/'frame-predictions.json'):assert all(lookup[(r['sid'],r['subject'])][k]==v for k,v in r.items())
    for f in range(5):
        for mode in MODES:
            record=models[str(f)][mode];retrained=fit((data[sid]['tokens'] for sid in parts[str(f)]['fit']),mode)
            np.testing.assert_allclose(retrained['weights'],record['model']['weights'],rtol=1e-6,atol=1e-7);np.testing.assert_allclose(retrained['loss'],record['model']['loss'],rtol=1e-9,atol=1e-11)
            for key in ('mode','vocabulary','training_nominals','conj_labels','regularization','minimum_feature_count'):assert retrained[key]==record['model'][key]
            refits+=1;assert calibrate(cal[str(f)],data,base[str(f)],units[str(f)]['model'],record['model'])==record['policy']
            frames=adjusted(test[str(f)],data,record['model'],record['policy']['selected']['weight']);p,_=decode_sentences(frames,base[str(f)]['cutoff'],base[str(f)]['selected']['carrier']['penalty']);u=unit_predictions(p,data,units[str(f)]['model'],{})
            for key,v in p.items():assert v==lookup[key]['conj_carrier'][mode];assert u[key]==lookup[key]['conj_unit'][mode];checks+=1
    fold_by_sid={sid:str(f) for f in range(5) for sid in parts[str(f)]['test']};probes=load(OUT/'probe-predictions.json');grouped=defaultdict(list)
    for r in probes:grouped[r['sid']].append(r)
    for sid,rs in grouped.items():
        tokens=data[sid]['tokens'];subjects=[r['subject'] for r in rs]
        for mode in MODES:
            p=probabilities(tokens,subjects,models[fold_by_sid[sid]][mode]['model']);np.testing.assert_allclose(p,[r['probabilities'][mode] for r in rs],rtol=1e-10,atol=1e-12)
        for r in rs:assert r['label']==(tokens[r['subject']]['rel'].split(':')[0]=='conj')
    assert evaluate(rows)==load(OUT/'evaluation.json');save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,refitted_models=refits,calibration_policies_replayed=10,assignment_replays=checks,probe_replays=len(probes),prior_fields_unchanged=True,targets_unchanged=True,reserve_unscored=200,prior_queries_scored=0));print('Audit passed',refits,checks,len(probes))
if __name__=='__main__':run()
