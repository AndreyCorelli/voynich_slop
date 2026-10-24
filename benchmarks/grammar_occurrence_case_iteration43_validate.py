"""Replay context extraction, source-only fitting, controls, and held-sentence CV."""
from copy import deepcopy
from collections import Counter
import hashlib
import numpy as np
from benchmarks.grammar_occurrence_case_iteration43 import OUT,ROOT,RECORDS,RESERVE,SEEDS,load,save,digest,get_features,shuffle
from voynich_smt.occurrence_case import fit,predict
from voynich_smt.predicate_case import probability as lexical_probability


def validate():
    hashes=0
    for filename in ('manifest.json','prediction-freeze.json','evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    manifest=load(OUT/'manifest.json');splits=manifest['split_ids'];reserved={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(sum(splits.values(),[]))&reserved;assert not set(splits['source'])&(set(splits['Jerome'])|set(splits['Caesar']))
    data=load(OUT/'annotations-truth.json');records=load(RECORDS);features=load(OUT/'features.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');replays=0;mutations=0
    for split,modes in records.items():
        for mode,rows in modes.items():
            assert get_features(rows,data,mode)==features[split][mode]
            altered=deepcopy(data)
            for tokens in altered.values():
                for t in tokens:t['features'].update(Case='CORRUPTED',Number='CORRUPTED',Gender='CORRUPTED')
            assert get_features(rows,altered,mode)==features[split][mode];mutations+=len(rows)
    for mode in ('oracle','nearest'):
        for arm in ('context','calibration','context_only'):
            m=fit(records['source'][mode],features['source'][mode],arm);saved=models[f'{mode}/{arm}'];assert m['vocabulary']==saved['vocabulary'];assert np.allclose(m['weights'],saved['weights'],rtol=0,atol=1e-9)
    audit=[]
    for author in ('Jerome','Caesar'):
        rows=records[author]['oracle'];near=records[author]['nearest'];expected={'lexical':[lexical_probability(models['oracle/context']['lexical'],r['predicate']) for r in rows]}
        for arm in ('context','calibration','context_only'):expected[arm]=predict(models[f'oracle/{arm}'],features[author]['oracle'],[r['predicate'] for r in rows])
        expected['nearest_matched']=predict(models['nearest/context'],features[author]['nearest'],[r['predicate'] for r in near]);expected['nearest_oracle_model']=predict(models['oracle/context'],features[author]['nearest'],[r['predicate'] for r in near])
        for arm,p in expected.items():assert np.allclose(p,pred[author][arm],rtol=0,atol=1e-10);replays+=len(p)
        m=models['oracle/context'];index={k:i for i,k in enumerate(m['vocabulary'])}
        for i,r in enumerate(rows):
            contributions=sorted([(k,v*m['weights'][index[k]]) for k,v in features[author]['oracle'][i].items() if k in index],key=lambda x:-abs(x[1]));a=pred[author]['lexical'][i];b=pred[author]['context'][i];gold=r['case']=='Acc';audit.append(dict(author=author,**r,lexical_p=a,context_p=b,corrected=(a>.5)!=gold and (b>.5)==gold,spoiled=(a>.5)==gold and (b>.5)!=gold,feature_contributions=contributions))
    source=records['source']['oracle'];sf=features['source']['oracle']
    for seed,saved in zip(SEEDS,load(OUT/'shuffled-predictions.json')):
        assert seed==saved['seed'];fake=shuffle(sf,source,seed);m=fit(source,fake,'context')
        for a in ('Jerome','Caesar'):
            expected=predict(m,features[a]['oracle'],[r['predicate'] for r in records[a]['oracle']]);assert np.allclose(expected,saved['predictions'][a],rtol=0,atol=1e-9);replays+=len(expected)
    cv=load(OUT/'source-cv.json');assert Counter((r['sent_id'],r['construction']) for r in cv)==Counter((r['sent_id'],r['construction']) for r in source)
    fold=lambda sid:int(hashlib.sha256(sid.encode()).hexdigest(),16)%5
    for f in range(5):
        trainix=[i for i,r in enumerate(source) if fold(r['sent_id'])!=f];test=[r for r in cv if r['fold']==f];trainrows=[source[i] for i in trainix];trainfeatures=[sf[i] for i in trainix];testfeatures=get_features(test,data,'oracle');assert not {r['sent_id'] for r in test}&{r['sent_id'] for r in trainrows}
        for arm in ('context','calibration','context_only'):
            m=fit(trainrows,trainfeatures,arm);expected=predict(m,testfeatures,[r['predicate'] for r in test]);assert np.allclose(expected,[r['predictions'][arm] for r in test],rtol=0,atol=1e-9);replays+=len(test)
        assert np.allclose([lexical_probability(m['lexical'],r['predicate']) for r in test],[r['predictions']['lexical'] for r in test]);replays+=len(test)
    save(OUT/'case-audit.json',audit);result=dict(hash_checks=hashes,prediction_replays=replays,case_number_gender_mutation_replays=mutations,reserved_unscored=len(reserved),source_examples=len(source),source_mixed_examples=sum(sum(v.values()) for v in manifest['mixed_source_predicates'].values()));save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
