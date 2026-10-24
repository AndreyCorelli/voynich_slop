"""Replay every saved candidate score and audit dictionary ceiling attrition."""
from collections import Counter
import numpy as np
from benchmarks.grammar_role_compatibility_iteration70 import *
def run():
    d=load(OUT/'design-freeze.json')
    for p,h in d['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'model.json')==load(OUT/'model-freeze.json')['model']
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    rows=load(OUT/'predictions.json');m=load(OUT/'model.json');counts=Counter();others=Counter()
    for r in rows:
        for name,features in [('context',r['context']),('shuffle',r['shuffled_context'])]:
            p=posterior(m,features)
            assert np.allclose([mass(m,p,rr) for rr in r['readings']],r['scores'][name],atol=1e-12,rtol=1e-12)
        assert [int(any(compatible(r['gold_profile'],a) for a in rr)) for rr in r['readings']]==r['scores']['oracle_morph']
        counts['unknown' if not r['readings'][0] else 'gold_analysis_missing' if not r['scores']['oracle_morph'][0] else 'gold_analysis_present']+=1
        if r['scores']['oracle_morph']==[1,1]:counts['both_admit_gold_analysis']+=1
        others[r['other']]+=1
    assert evaluate(rows)==load(OUT/'evaluation.json')
    prior=0
    for p in ROOT.glob('iteration*/verification-manifest.json'):
        if p.parent==OUT:continue
        for f,h in load(p).get('inputs',{}).items():
            assert digest(f)==h,(p,f);prior+=1
    result=dict(replayed=len(rows),attrition=dict(counts),most_common_distractors=others.most_common(12),prior_input_hashes_verified=prior,reserve_unscored=True)
    save(OUT/'audit.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
