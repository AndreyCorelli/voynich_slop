"""Replay source partitions, training/calibration, predictions and structure metrics."""
from copy import deepcopy
from collections import Counter
import numpy as np
from benchmarks.grammar_source_morphology_iteration48 import OUT,SOURCE,EXAMPLES,RESERVE,ARMS,fold,load,save,digest
from voynich_smt.source_morphology import fit,calibrate,predict,domains,group
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_lattice,sv_summary
from voynich_smt.morphology_stress import encode,decode,link_summary


def validate():
    hashes=0
    for name in ('manifest.json','split-freeze.json','prediction-freeze.json','evaluation-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);manifest=load(OUT/'manifest.json');models=load(OUT/'models.json');reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve;predictions={};types_replayed=0;support_replayed=0
    for f in range(5):
        p=manifest['partitions'][str(f)];train,cal,test=map(set,(p['fit'],p['calibration'],p['test']));assert not train&cal and not train&test and not cal&test;assert train|cal|test==set(data);assert all(fold(sid)==f for sid in test) and all(fold(sid)==(f+1)%5 for sid in cal)
        model=fit(data[sid]['tokens'] for sid in p['fit']);assert model==models[str(f)]['model'];policies={name:calibrate(model,(data[sid]['tokens'] for sid in p['calibration']),alpha) for name,alpha in (('set95',.05),('set99',.01))};assert policies==models[str(f)]['policies']
        saved=load(OUT/f'predictions-{f}.json');predictions[f]=saved;keys={readings_key(t) for sid in test for t in data[sid]['tokens'] if group(t['pos'])};assert keys==set(saved['types'])
        for key,output in saved['types'].items():
            word,pos=key.split('\t');expected=predict(model,policies,word,pos);assert expected==output;assert np.isclose(sum(output['probabilities']),1);assert all(v>0 for v in output['probabilities']);assert set(output['sets']['set95'])<=set(output['sets']['set99'])<=set(output['sets']['all']);types_replayed+=1
        for sid,arms in saved['sentences'].items():
            assert sid in test;tokens=data[sid]['tokens'];altered=deepcopy(tokens)
            for t in altered:t['head']=None;t['rel']='CORRUPTED';t['features']={'Case':'CORRUPTED','Number':'CORRUPTED','Person':'CORRUPTED','VerbForm':'CORRUPTED'}
            for arm in ARMS:
                domain=domains(tokens,saved['types'],arm);assert domain==domains(altered,saved['types'],arm)
                for rule in ('none','agreement'):
                    expected=encode(sv_lattice(domain,rule));assert expected==arms[arm][rule];support_replayed+=1
    references=load(OUT/'reference-evaluation.json');examples=load(EXAMPLES);index={(r['sent_id'],r['subject'],r['predicate']):r for r in references};assert len(index)==len(examples)==326;summaries=0
    for e in examples:
        pred=predictions[fold(e['sent_id'])];saved=index[e['sent_id'],e['subject'],e['predicate']]
        for arm in ARMS:
            for rule in ('none','agreement'):
                blocks=pred['sentences'][e['sent_id']][arm][rule];s=link_summary(blocks,e['reference']);assert s==saved['arms'][arm][rule];oracle=sv_summary(decode(blocks),e['reference']);assert s['reference_exact']==oracle['reference_retained'] and s['reference_link']==oracle['reference_link_retained'];assert s['unique_correct']==oracle['unique_link_correct'] and s['false_unique']==oracle['false_unique_link'];summaries+=1
    result=dict(hash_checks=hashes,source_sentences=len(data),outer_folds=5,reference_constructions=len(examples),source_only_models_refitted=5,class_threshold_policies_recalibrated=10,word_type_predictions_replayed=types_replayed,sentence_supports_replayed=support_replayed,reference_summaries_replayed=summaries,test_morphology_mutation_invariant=True,reserved_unscored=len(reserve),prior_queries_scored=0);save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
