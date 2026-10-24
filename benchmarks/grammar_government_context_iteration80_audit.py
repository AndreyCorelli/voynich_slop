"""Replay richer-context models, matched controls and annotation invariance."""
from benchmarks.grammar_government_context_iteration80 import *
from benchmarks.grammar_direct_nominative_iteration79_audit import close_rows
from voynich_smt.contextual_nominative import objective
from voynich_smt.dependency_role_proxy import encode

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'models.json')==load(OUT/'model-freeze.json')['models']
    for p,h in load(OUT/'calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    role=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert not set(part['fit'])&set(part['calibration']);models=load(OUT/'models.json');assert models['baseline']==load(ROOT/'iteration79/model.json')
    fitrows=dataset80([dict(sent_id=sid,**data[sid]) for sid in part['fit']],pm,lex,morph,7901);gradients={}
    for name in ('geometry','anchors'):
        m=models[name];x=encode([r[name+'_features'] for r in fitrows],m['vocabulary']);y=np.array([r['labels']['nominative'] for r in fitrows],float);loss,g=objective(np.array(m['weights']),x,y);assert abs(loss-m['loss'])<1e-10 and max(abs(g))<1e-5;gradients[name]=float(max(abs(g)))
    calq=dataset80([dict(sent_id=sid,**data[sid]) for sid in part['calibration']],pm,lex,morph,7701);cal=load(OUT/'calibration-predictions.json');close_rows(infer80(calq,role,models),cal);pol=load(OUT/'policies.json')
    for task,arms in pol.items():
        for a in arms:assert select_policy(cal,task,a)==pol[task][a]
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            r=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    q=dataset80(target,pm,lex,morph,7001);rows=load(OUT/'predictions.json');close_rows(infer80(q,role,models),rows)
    old={(r['sid'],r['index']):r for r in load(ROOT/'iteration79/predictions.json')}
    for r in rows:
        b=old[r['sid'],r['index']]
        for new,a in [('baseline','direct'),('baseline_shuffle','direct_shuffle'),('local','local')]:
            for task,v in r['scores'][new].items():assert math.isclose(v,b['scores'][a][task],abs_tol=1e-12,rel_tol=1e-10)
    modified=[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word'],pos='NOUN',rel='nsubj',features={'Case':'Nom'}) for t in s['tokens']]) for s in target];altered={(r['sid'],r['index']):r for r in infer80(dataset80(modified,pm,lex,morph,7001),role,models)}
    for r in rows:
        for a,vv in r['scores'].items():
            for task,v in vv.items():assert math.isclose(v,altered[r['sid'],r['index']]['scores'][a][task],abs_tol=1e-12,rel_tol=1e-10)
    assert evaluation(rows,pol)==load(OUT/'evaluation.json')
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(fit_tokens=len(fitrows),calibration_replayed=len(cal),target_replayed=len(rows),fit_gradient_max=gradients,prior_hashes_verified=checked,baseline_and_shuffle_reproduced=True,target_annotation_invariance=True,reserve_unscored=True);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
