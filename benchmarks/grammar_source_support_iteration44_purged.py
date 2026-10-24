"""Stricter predicate holdout: purge training sentences shared with test records."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_source_support_iteration44 import OUT,load,save,digest,fold,metrics
from voynich_smt.occurrence_case import fit,predict
from voynich_smt.predicate_case import probability as lexical_probability


def run():
    assert not (OUT/'purged-config.json').exists()
    save(OUT/'purged-config.json',dict(inputs={str(p):digest(p) for p in (Path(__file__),OUT/'records-truth.json',OUT/'features.json',OUT/'evaluation.json')},note='Post-primary stricter validation, unchanged model. Original predicate folds may share sentences between distinct predicates. Purge all test sentences from training. No parameter selection or target-query scoring.'))
    rows=load(OUT/'records-truth.json');features=load(OUT/'features.json');predictions=[];models=[]
    for f in range(5):
        testix=[i for i,r in enumerate(rows) if r['predicate'] is not None and fold(r['predicate'])==f];testids={rows[i]['sent_id'] for i in testix};trainix=[i for i,r in enumerate(rows) if r['predicate'] is not None and fold(r['predicate'])!=f and r['sent_id'] not in testids];trainrows=[rows[i] for i in trainix];testrows=[rows[i] for i in testix];ps={};trained={}
        for arm in ('calibration','context','context_only'):
            m=fit(trainrows,[features[i] for i in trainix],arm);trained[arm]=m;ps[arm]=predict(m,[features[i] for i in testix],[r['predicate'] for r in testrows])
        ps['lexical']=[lexical_probability(m['lexical'],r['predicate']) for r in testrows];models.append(dict(group=f,train_ix=trainix,test_ix=testix,models=trained))
        for j,r in enumerate(testrows):predictions.append(dict(**r,group=f,predictions={a:p[j] for a,p in ps.items()}))
    save(OUT/'purged-models.json',models);save(OUT/'purged-predictions.json',predictions);save(OUT/'purged-evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'purged-config.json',OUT/'purged-models.json',OUT/'purged-predictions.json')}));result={}
    mixed=load(OUT/'audit.json')['mixed_predicates']
    for subset in ('all','mixed'):
        selected=[r for r in predictions if subset=='all' or r['predicate'] in mixed]
        for arm in ('lexical','calibration','context','context_only'):result[f'{subset}/{arm}']=metrics(selected,[r['predictions'][arm] for r in selected])
    save(OUT/'purged-evaluation.json',result);print(result)
if __name__=='__main__':run()
