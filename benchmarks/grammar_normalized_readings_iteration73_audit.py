"""Replay score via a separate profile-space summation and verify frozen data."""
from benchmarks.grammar_normalized_readings_iteration73 import *
def independent(model,p,rr,ww):
    pri=Counter();post=Counter()
    for (_,g),v,q in zip(model['labels'],model['prior'],p):pri[tuple(g)]+=v;post[tuple(g)]+=q
    score=0.
    for r,w in zip(rr,ww):
        admitted=[g for g in pri if compatible(g,r)];z=sum(pri[g] for g in admitted)
        if z:score+=w*sum(post[g]*pri[g]/z for g in admitted)
    return score

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    rows=load(OUT/'predictions.json');old=load(ROOT/'iteration71/predictions.json');model=load(ROOT/'iteration70/model.json');counts=Counter()
    assert len(rows)==len(old)==1273
    for r,b in zip(rows,old):
        assert all(r[k]==b[k] for k in ('sid','index','word','other','gold_profile'))
        for name,p in [('context',posterior(model,b['context'])),('shuffle',posterior(model,b['shuffled_context'])),('prior',model['prior'])]:
            for prefix,q in [('',p),('oracle_pos_',condition_pos(model,p,b['gold_profile'][0]))]:
                s=[independent(model,q,rr,w) for rr,w in zip(b['readings'],b['weights'])]
                assert np.allclose(s,r['scores'][prefix+'normalized_'+name],atol=1e-12,rtol=1e-12)
        pos,case,num=b['gold_profile'];affected=(case or num) and any(a[0]==pos and not a[1] and not a[2] for a in b['readings'][1])
        if affected:
            counts['affected']+=1
            for arm in ['normalized_context','oracle_pos_normalized_context']:
                d=r['scores'][arm][0]-r['scores'][arm][1];counts[arm+('/win' if d>1e-10 else '/loss' if d< -1e-10 else '/tie')]+=1
    assert summarize(rows)['arms']==load(OUT/'evaluation.json')['arms']
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(independent_replay=len(rows),prior_hashes_verified=checked,affected_subset=dict(counts),reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
