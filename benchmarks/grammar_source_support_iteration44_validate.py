"""Audit fresh source boundaries and replay every fitted source-only prediction."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import numpy as np
from benchmarks.grammar_source_support_iteration44 import OUT,RESERVE,AUTHORS,load,save,digest,fold
from voynich_smt.occurrence_case import context,fit,predict
from voynich_smt.predicate_case import probability as lexical_probability


def strings_with_keys(x):
    if isinstance(x,str):yield x
    elif isinstance(x,list):
        for v in x:yield from strings_with_keys(v)
    elif isinstance(x,dict):
        for k,v in x.items():yield str(k);yield from strings_with_keys(v)


def validate():
    hashes=0
    for filename in ('selection-manifest.json','fit-freeze.json','evaluation-freeze.json','purged-config.json','purged-evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    selection=load(OUT/'selection-manifest.json');used=set()
    for p,h in selection['prior_declarations'].items():assert digest(p)==h,p;used.update(strings_with_keys(load(Path(p))));hashes+=1
    data=load(OUT/'annotations-truth.json');rows=load(OUT/'records-truth.json');features=load(OUT/'features.json');reserve={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group};assert not set(data)&(used|reserve);assert all(s['author'] in AUTHORS for s in data.values())
    assert features==[context(data[r['sent_id']]['tokens'],r['head'],r['oracle_index']) for r in rows]
    altered=deepcopy(data)
    for s in altered.values():
        for t in s['tokens']:t['case']='CORRUPTED';t['features'].update(Case='CORRUPTED',Number='CORRUPTED',Gender='CORRUPTED')
    assert features==[context(altered[r['sent_id']]['tokens'],r['head'],r['oracle_index']) for r in rows]
    pred=load(OUT/'predictions.json');replays=0;fitted=0;shared={}
    def replay(trainix,testix,trained,savedrows):
        nonlocal replays,fitted
        trainrows=[rows[i] for i in trainix];testrows=[rows[i] for i in testix];expected={}
        for arm in ('context','calibration','context_only'):
            model=fit(trainrows,[features[i] for i in trainix],arm);fitted+=1;assert model['vocabulary']==trained[arm]['vocabulary'];assert np.allclose(model['weights'],trained[arm]['weights'],rtol=0,atol=1e-8);expected[arm]=predict(model,[features[i] for i in testix],[r['predicate'] for r in testrows])
        expected['lexical']=[lexical_probability(model['lexical'],r['predicate']) for r in testrows]
        assert [(r['sent_id'],r['construction']) for r in savedrows]==[(r['sent_id'],r['construction']) for r in testrows]
        for arm,p in expected.items():assert np.allclose(p,[r['predictions'][arm] for r in savedrows],rtol=0,atol=1e-8);replays+=len(p)
    for saved in load(OUT/'models.json'):
        scheme,group=saved['scheme'],saved['group'];eligible=[i for i,r in enumerate(rows) if scheme!='predicate' or r['predicate'] is not None];key=lambda r:r['author'] if scheme=='author' else fold(r['sent_id'] if scheme=='sentence' else r['predicate']);trainix=[i for i in eligible if key(rows[i])!=group];testix=[i for i in eligible if key(rows[i])==group]
        trainids={rows[i]['sent_id'] for i in trainix};testids={rows[i]['sent_id'] for i in testix};assert trainids==set(saved['train_ids']) and testids==set(saved['test_ids']);shared[f'{scheme}/{group}']=len(trainids&testids)
        if scheme!='predicate':assert not trainids&testids
        else:assert not {rows[i]['predicate'] for i in trainix}&{rows[i]['predicate'] for i in testix}
        selected=[r for r in pred if r['scheme']==scheme and r['group']==group];replay(trainix,testix,saved['models'],selected)
    purged=load(OUT/'purged-predictions.json')
    for saved in load(OUT/'purged-models.json'):
        trainix,testix=saved['train_ix'],saved['test_ix'];assert not {rows[i]['sent_id'] for i in trainix}&{rows[i]['sent_id'] for i in testix};assert not {rows[i]['predicate'] for i in trainix}&{rows[i]['predicate'] for i in testix};replay(trainix,testix,saved['models'],[r for r in purged if r['group']==saved['group']])
    assert Counter((r['sent_id'],r['construction']) for r in purged)==Counter((r['sent_id'],r['construction']) for r in rows if r['predicate'] is not None)
    result=dict(hash_checks=hashes,fresh_source_sentences=len(data),examples=len(rows),refitted_models=fitted,prediction_replays=replays,case_number_gender_mutation_replays=len(rows),reserved_unscored=len(reserve),original_predicate_fold_sentence_overlap=shared,purged_overlap=0,prior_queries_scored=0);save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
