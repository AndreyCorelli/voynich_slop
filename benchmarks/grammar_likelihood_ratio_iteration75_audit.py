"""Independent Bayes-factor replay via compatible posterior/prior mass."""
from benchmarks.grammar_likelihood_ratio_iteration75 import *
def independent(model,p,rr,ww,normalize):
    supported=total=0.
    for r,w in zip(rr,ww):
        numerator=sum(q for (_,g),q in zip(model['labels'],p) if compatible(g,r));denominator=sum(q for (_,g),q in zip(model['labels'],model['prior']) if compatible(g,r))
        if denominator:total+=w*numerator/denominator;supported+=w
    return total/supported if normalize and supported else total

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    rows=load(OUT/'predictions.json');old=load(ROOT/'iteration71/predictions.json');model=load(ROOT/'iteration70/model.json');assert len(rows)==len(old)==1273
    for r,b in zip(rows,old):
        assert all(r[k]==b[k] for k in ('sid','index','word','other','gold_profile'))
        for arm,p in [('context',posterior(model,b['context'])),('shuffle',posterior(model,b['shuffled_context'])),('prior',model['prior'])]:
            for prefix,normalized in [('likelihood_',False),('context_only_',True)]:
                s=[independent(model,p,a,w,normalized) for a,w in zip(b['readings'],b['weights'])];assert np.allclose(s,r['scores'][prefix+arm],atol=1e-12,rtol=1e-12)
    assert summarize(rows)['arms']==load(OUT/'evaluation.json')['arms']
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(independent_replay=1273,prior_input_hashes_verified=checked,reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
