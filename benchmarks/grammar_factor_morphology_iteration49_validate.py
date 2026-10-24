"""Replay feature supervision, calibration budgets, held-out supports and metrics."""
from copy import deepcopy
import numpy as np
from benchmarks.grammar_factor_morphology_iteration49 import OUT,PREVIOUS,SOURCE,EXAMPLES,RESERVE,SUPERVISIONS,ARMS,fold,load,save,digest
from voynich_smt.factor_morphology import fit,calibrate,predict,FEATURES,POLICIES
from voynich_smt.source_morphology import group,domains
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_lattice,sv_summary
from voynich_smt.morphology_stress import encode,decode,link_summary


def validate():
    checks=0
    for filename in ('manifest.json','fit-freeze.json','prediction-freeze.json','evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;checks+=1
    data=load(SOURCE);manifest=load(OUT/'manifest.json');assert manifest['partitions']==load(PREVIOUS/'manifest.json')['partitions'];reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve;models=load(OUT/'models.json');oldmodels=load(PREVIOUS/'models.json');predictions={};type_replays=0;support_replays=0
    for f in range(5):
        partition=manifest['partitions'][str(f)];fitids,calids,testids=map(set,(partition['fit'],partition['calibration'],partition['test']));assert not fitids&calids and not fitids&testids and not calids&testids;assert fitids|calids|testids==set(data)
        for supervision in SUPERVISIONS:
            model=fit((data[sid]['tokens'] for sid in partition['fit']),supervision);assert model==models[str(f)][supervision]['model'];policies=calibrate(model,(data[sid]['tokens'] for sid in partition['calibration']));assert policies==models[str(f)][supervision]['policies']
            for g in ('nominal','pronoun','verbal'):
                original=oldmodels[str(f)]['model']['totals'][g]
                if supervision=='matched':
                    assert model['training_labels']['role/'+g]==sum(original.values());assert model['training_labels']['number/'+g]==sum(v for k,v in original.items() if k!='OTHER')
                else:
                    matched=models[str(f)]['matched']['model']['training_labels'];assert all(count>=matched.get(key,0) for key,count in model['training_labels'].items())
        saved=load(OUT/f'predictions-{f}.json');predictions[f]=saved;keys={readings_key(t) for sid in testids for t in data[sid]['tokens'] if group(t['pos'])};assert set(saved['types'])==keys
        for key,output in saved['types'].items():
            word,pos=key.split('\t')
            for supervision in SUPERVISIONS:
                trained=models[str(f)][supervision];expected=predict(trained['model'],trained['policies'],word,pos);assert expected==output['components'][supervision];assert np.isclose(sum(expected['probabilities']),1);sets=expected['sets'];assert set(sets['set95'])<=set(sets['set99'])<=set(sets['total99']);assert set(sets['set95'])<=set(sets['total95'])<=set(sets['total99']);type_replays+=1
        for sid,arms in saved['sentences'].items():
            assert sid in testids;tokens=data[sid]['tokens'];changed=deepcopy(tokens)
            for t in changed:t['head']=None;t['rel']='CORRUPTED';t['features']={'Case':'CORRUPTED','VerbForm':'CORRUPTED','Number':'CORRUPTED','Person':'CORRUPTED'}
            for arm in ARMS:
                domain=domains(tokens,saved['types'],arm);assert domain==domains(changed,saved['types'],arm)
                for rule in ('none','agreement'):
                    expected=encode(sv_lattice(domain,rule));assert expected==arms[arm][rule];support_replays+=1
    refs={(r['sent_id'],r['subject'],r['predicate']):r for r in load(OUT/'reference-evaluation.json')};examples=load(EXAMPLES);assert len(refs)==len(examples)==326;summary_replays=0
    for e in examples:
        saved=refs[e['sent_id'],e['subject'],e['predicate']];pred=predictions[fold(e['sent_id'])]
        for arm in ARMS:
            for rule in ('none','agreement'):
                blocks=pred['sentences'][e['sent_id']][arm][rule];summary=link_summary(blocks,e['reference']);assert summary==saved['arms'][arm][rule];oracle=sv_summary(decode(blocks),e['reference']);assert summary['reference_exact']==oracle['reference_retained'] and summary['reference_link']==oracle['reference_link_retained'];assert summary['unique_correct']==oracle['unique_link_correct'] and summary['false_unique']==oracle['false_unique_link'];summary_replays+=1
    result=dict(hash_checks=checks,source_models_refitted=10,source_policies_recalibrated=40,word_type_predictions_replayed=type_replays,sentence_supports_replayed=support_replays,reference_summaries_replayed=summary_replays,heldout_morphology_mutation_invariant=True,reserved_unscored=len(reserve),prior_queries_scored=0);save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
