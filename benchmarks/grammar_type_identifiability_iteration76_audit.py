"""Rebuild all oracle pools and verify contextual pooling inputs."""
from benchmarks.grammar_type_identifiability_iteration76 import *
def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for p,h in load(OUT/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(OUT/'pooled-inputs.json');groups=data['groups'];profiles=[tuple(p) for p in data['profiles']];m=load(ROOT/'iteration70/model.json');old=load(ROOT/'iteration71/predictions.json');lookup={(r['sid'],r['index']):r for r in old};assert sum(len(g['occurrences']) for g in groups)==1273
    for g in groups:
        for o in g['occurrences']:
            b=lookup[o['sid'],o['index']];assert b['word']==g['word'] and b['gold_profile']==o['gold_profile']
            for arm,p in [('context',posterior(m,b['context'])),('shuffle',posterior(m,b['shuffled_context'])),('prior',m['prior'])]:assert np.allclose(collapse(m,p,profiles),o[arm],atol=1e-12,rtol=1e-12)
    records=[json.loads(l) for l in INVENTORY.open()];forms=[r['surface'] for r in records];ids={w:i for i,w in enumerate(forms)};queries=sorted({tuple(o['gold_profile']) for g in groups for o in g['occurrences']});supports={(mode,q):set() for q in queries for mode in ('tolerant','strict')}
    # Read raw signatures independently; explicitly test each feature's
    # knownness instead of calling the runner's reading/compatibility helpers.
    for i,r in enumerate(records):
        analyses=[]
        for p,_,features in r['signatures']:
            f=dict(features);analyses.append((POS.get(p,p),CASE.get(f.get('Case'),''),{'S':'Sing','P':'Plur'}.get(f.get('Number'),'')))
        for q in queries:
            for a in analyses:
                if a[0]!=q[0]:continue
                if all(not x or not y or x==y for x,y in zip(q[1:],a[1:])):supports['tolerant',q].add(i)
                if all(not x or x==y for x,y in zip(q[1:],a[1:])):supports['strict',q].add(i)
    rows=load(OUT/'oracle-pools.json')
    for r,g in zip(rows,groups):
        assert r['word']==g['word'];qs=[tuple(o['gold_profile']) for o in g['occurrences']]
        assert r['inventory_present']==(r['word'] in ids)
        for mode in ('tolerant','strict'):
            pool=set.intersection(*(supports[mode,q] for q in qs));z=r[mode];gold=ids.get(r['word']);assert len(pool)==z['size'] and len(supports[mode,qs[0]])==z['first_size'];assert (gold in pool)==z['gold_survives']
            if gold in pool:
                goldkey=(-m['frequency'].get(r['word'],0),r['word']);rank=1+sum((-m['frequency'].get(forms[j],0),forms[j])<goldkey for j in pool);assert rank==z['gold_rank']
            else:assert z['gold_rank'] is None
    ev=load(OUT/'evaluation.json');assert oracle_summary(rows)==ev['oracle'];assert pooling_metrics(groups,profiles,profile_space(m)[1])==ev['inferred_pooling']
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(types_replayed=len(rows),token_posteriors_replayed=len(old),inventory_forms=len(forms),prior_input_hashes_verified=checked,reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
