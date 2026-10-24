"""Recompute weighted predictions and check all frozen prior inputs."""
from benchmarks.grammar_weighted_readings_iteration71 import *
def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'word-pos-model.json')==load(OUT/'model-freeze.json')['word_pos']
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    pm=load(OUT/'word-pos-model.json');m=load(PREVIOUS/'model.json');rows=load(OUT/'predictions.json');old=load(PREVIOUS/'predictions.json')
    for r,b in zip(rows,old):
        for k in b:
            if k!='scores':assert r[k]==b[k]
        ww=[weights(w,rr,pm) for w,rr in zip((r['word'],r['other']),r['readings'])];assert ww==r['weights']
        for name,p in [('context',posterior(m,r['context'])),('shuffle',posterior(m,r['shuffled_context'])),('prior',m['prior'])]:
            assert np.allclose([weighted_mass(m,p,rr,w) for rr,w in zip(r['readings'],ww)],r['scores']['weighted_'+name],atol=1e-12,rtol=1e-12)
    ev=load(OUT/'evaluation.json');assert {k:v for k,v in ev.items() if k!='non_attribution'}==evaluate71(rows)
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    # Descriptive candidate-only control added after the primary result; no tuning.
    ds=[sum(r['weights'][0])-sum(r['weights'][1]) for r in rows]
    save(OUT/'audit.json',dict(rows_replayed=len(rows),prior_inputs_verified=checked,candidate_only_posthoc=dict(win=sum(d>1e-10 for d in ds),loss=sum(d< -1e-10 for d in ds),tie=sum(abs(d)<=1e-10 for d in ds)),non_source_pos=pm['words']['non'],reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
