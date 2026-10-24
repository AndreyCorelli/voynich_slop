"""Replay all source-only profile probabilities and exclusion guarantees."""
from collections import Counter
import json
import numpy as np
from benchmarks.grammar_predicate_profiles_iteration42 import OUT,PREVIOUS,RESERVE,SEEDS,load,save,digest,shuffled_profiles
from voynich_smt.predicate_profiles import build_profiles,vectorize,train,probability,transfer
from voynich_smt.predicate_case import probability as lexical_probability


def validate():
    hashes=0
    for filename in ('manifest.json','prediction-freeze.json','evaluation-freeze.json','sensitivity-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    source=load(OUT/'source-annotations.json');built=build_profiles(source.values());assert built==load(OUT/'source-profiles.json');manifest=load(OUT/'manifest.json');assert set(source)==set(manifest['split_ids']['source']);reserved={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(sum(manifest['split_ids'].values(),[]))&reserved
    assert not set(source)&(set(manifest['split_ids']['Jerome'])|set(manifest['split_ids']['Caesar']))
    assert not any(f.startswith('prep:in:') for row in built['profiles'].values() for f in row)
    rec=load(PREVIOUS/'records-truth.json');models=load(OUT/'models.json');v=vectorize(built['profiles']);pred=load(OUT/'predictions.json');audit=load(OUT/'neighbor-audit.json');replay=0
    for mode in ('oracle','nearest'):assert models[mode]==train(rec['source'][mode],built['profiles'])
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];near=rec[author]['nearest'];m=models['oracle']
        expected=dict(baseline=[m['base']]*len(rows),lexical=[lexical_probability(m,r['predicate']) for r in rows],hybrid=[probability(m,r['predicate'],True,v) for r in rows],transfer_only=[probability(m,r['predicate'],False,v) for r in rows],nearest_matched=[probability(models['nearest'],r['predicate'],True,v) for r in near],nearest_oracle_model=[probability(m,r['predicate'],True,v) for r in near]);assert pred[author]==expected;replay+=len(rows)*len(expected)
    for r in audit:
        p,neighbors=transfer(models['oracle'],r['predicate'],v);assert p==r['transfer_p'] and neighbors==r['neighbors'];assert all(n['predicate']!=r['predicate'] for n in neighbors);assert len(neighbors)<=5
    for seed,saved in zip(SEEDS,load(OUT/'shuffled-predictions.json')):
        assert seed==saved['seed'];fake=shuffled_profiles(built['profiles'],built['occurrences'],seed)
        assert Counter(json.dumps(x,sort_keys=True) for x in fake.values())==Counter(json.dumps(x,sort_keys=True) for x in built['profiles'].values())
        assert set(fake)==set(built['profiles']);vv=vectorize(fake);m=dict(models['oracle'],profiles=fake)
        for a in ('Jerome','Caesar'):
            expected=[probability(m,r['predicate'],True,vv) for r in rec[a]['oracle']];assert expected==saved['predictions'][a];replay+=len(expected)
    lpo=load(OUT/'leave-predicate-out.json')
    for lemma in {r['predicate'] for r in lpo}:
        kept=[r for r in rec['source']['oracle'] if r['predicate']!=lemma];m=train(kept,built['profiles']);assert lemma not in m['counts']
        for r in lpo:
            if r['predicate']==lemma:assert r['baseline']==m['base'] and r['profile']==probability(m,lemma,False,v);replay+=1
    sensitivity=load(OUT/'sensitivity-predictions.json')
    for key,saved in sensitivity.items():
        author,k,strength=key.split('/');m=train(rec['source']['oracle'],built['profiles'],int(k),float(strength));selected=[r for r in rec[author]['oracle'] if r['predicate'] not in models['oracle']['counts'] and r['predicate'] in v]
        expected=[probability(m,r['predicate'],False,v) for r in selected];assert expected==saved;replay+=len(expected)
    result=dict(hash_checks=hashes,prediction_replays=replay,profile_lemmas=len(v),source_verbal_lemmas=len(built['occurrences']),excluded_in_bearing_subtrees=built['excluded_subtrees'],reserved_unscored=len(reserved),leave_predicate_out_rows=len(lpo));save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
