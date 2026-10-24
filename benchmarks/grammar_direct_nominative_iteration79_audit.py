"""Replay learned predictions, oracle sums, calibration and fit optimality."""
from benchmarks.grammar_direct_nominative_iteration79 import *
from voynich_smt.contextual_nominative import objective
from voynich_smt.dependency_role_proxy import encode

def close_rows(a,b):
    assert len(a)==len(b)
    for x,y in zip(json.loads(json.dumps(a)),b):
        assert {k:v for k,v in x.items() if k!='scores'}=={k:v for k,v in y.items() if k!='scores'}
        for arm,vals in x['scores'].items():
            for task,v in vals.items():assert math.isclose(v,y['scores'][arm][task],rel_tol=1e-10,abs_tol=1e-12)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'model.json')==load(OUT/'model-freeze.json')['model']
    for p,h in load(OUT/'calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    model=load(ROOT/'iteration70/model.json');direct=load(OUT/'model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');parts=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert not set(parts['fit'])&set(parts['calibration'])
    fitrows=dataset([dict(sent_id=sid,**data[sid]) for sid in parts['fit']],pm,lex,7901);x=encode([r['features'] for r in fitrows],direct['vocabulary']);y=np.array([r['labels']['nominative'] for r in fitrows],float);loss,grad=objective(np.array(direct['weights']),x,y);assert abs(loss-direct['loss'])<1e-10 and np.max(np.abs(grad))<1e-5
    calrows=dataset([dict(sent_id=sid,**data[sid]) for sid in parts['calibration']],pm,lex,7701);cal=load(OUT/'calibration-predictions.json');close_rows(infer(calrows,model,direct),cal)
    policies=load(OUT/'policies.json')
    for task,arms in policies.items():
        for arm in arms:assert select_policy(cal,task,arm)==policies[task][arm]
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            r=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    queries=dataset(target,pm,lex,7001);rows=load(OUT/'predictions.json');close_rows(infer(queries,model,direct),rows)
    for r in rows:
        b=ann[r['sid'],r['index']]
        for name,p in [('context',posterior(model,b['context'])),('shuffle',posterior(model,b['shuffled_context'])),('prior',model['prior'])]:
            for field,col in [('pos',None),('case',1),('number',2)]:
                z=den=0.
                for (role,g),v in zip(model['labels'],p):
                    if g[0]==b['gold_profile'][0] and (col is None or g[col]==b['gold_profile'][col]):
                        den+=v
                        if role=='nsubj':z+=v
                expected=z/den if den else 0.;assert abs(expected-r['scores']['oracle_'+field+'_'+name]['subject'])<1e-12
    changed=[dict(r,g=['NOUN','Nom','Sing'],labels=dict(subject=not r['labels']['subject'],nominative=not r['labels']['nominative'])) for r in queries];altered=infer(changed,model,direct)
    for a,b in zip(rows,altered):
        for arm in ('local','direct','direct_shuffle'):
            for task,v in a['scores'][arm].items():assert math.isclose(v,b['scores'][arm][task],rel_tol=1e-10,abs_tol=1e-12)
    assert evaluation(rows,policies)==load(OUT/'evaluation.json')
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(fit_tokens=len(fitrows),calibration_tokens=len(cal),target_replayed=len(rows),fit_gradient_max=float(np.max(np.abs(grad))),prior_hashes_verified=checked,inferred_score_annotation_invariance=True,fit_calibration_disjoint=True,reserve_unscored=True);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
