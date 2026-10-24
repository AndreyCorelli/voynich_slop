"""Source split replay, label invariance and structural oracle controls."""
from benchmarks.grammar_government_oracle_iteration81 import *
from benchmarks.grammar_direct_nominative_iteration79_audit import close_rows
from voynich_smt.contextual_nominative import objective
from voynich_smt.dependency_role_proxy import encode
from voynich_smt.government_oracle import INHERIT

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'models.json')==load(OUT/'model-freeze.json')['models']
    for p,h in load(OUT/'calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    record=load(OUT/'models.json');models=record['models'];pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert all(not set(part[a])&set(part[b]) for a,b in [('fit','test'),('fit','calibration'),('calibration','test')]);assert all(data[sid]['author']!='Caesar' for ss in part.values() for sid in ss)
    def source(split):return [dict(sent_id=sid,**data[sid]) for sid in part[split]]
    fitrows,_=rows81(source('fit'),pm,lex,morph,7901);gradients={}
    for name,model in models.items():
        x=encode([r[name] for r in fitrows],model['vocabulary']);y=np.array([r['labels']['nominative'] for r in fitrows],float);loss,g=objective(np.array(model['weights']),x,y);assert abs(loss-model['loss'])<1e-10 and max(abs(g))<1e-5;gradients[name]=float(max(abs(g)))
    calrows,_=rows81(source('calibration'),pm,lex,morph,7701);cal=load(OUT/'calibration-predictions.json');close_rows(score81(calrows,models,record['prior']),cal);pol=load(OUT/'policies.json')
    for a in ARMS:assert select_policy(cal,'nominative',a)==pol['nominative'][a]
    testrows,_=rows81(source('test'),pm,lex,morph,8101);test=load(OUT/'predictions.json');close_rows(score81(testrows,models,record['prior']),test)
    for sid in part['test']:
        rows=[r for r in testrows if r['sid']==sid]
        assert sorted(tuple(r['pp_bundle']) for r in rows)==sorted(tuple(r['pp_sham'][len(r['baseline']):]) for r in rows)
        assert sorted(tuple(r['structure_bundle']) for r in rows)==sorted(tuple(r['structure_sham'][len(r['baseline']):]) for r in rows)
    altered=[]
    for s in source('test'):
        altered.append(dict(s,tokens=[dict(t,features={'Case':'Nom'},rel=t['rel'] if t['rel'].split(':')[0] in INHERIT|{'case'} else 'obj') for t in s['tokens']]))
    alteredrows,_=rows81(altered,pm,lex,morph,8101);changed=score81(alteredrows,models,record['prior']);assert len(changed)==len(test)
    for a,b in zip(test,changed):
        assert (a['sid'],a['index'])==(b['sid'],b['index'])
        for arm in ARMS:assert math.isclose(a['scores'][arm]['nominative'],b['scores'][arm]['nominative'],abs_tol=1e-12,rel_tol=1e-10)
    expected=evaluation(test,pol);assert expected['nominative']==load(OUT/'evaluation.json')['nominative']
    byauthor={}
    for author in ('Cicero','Palladius'):
        rr=[r for r in test if data[r['sid']]['author']==author];byauthor[author]=evaluation(rr,pol)['nominative']
    chosen=[r for r in test if r['scores']['structure']['nominative']>=pol['nominative']['structure']['precision90']['threshold']]
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(fit_rows=len(fitrows),calibration_replayed=len(cal),test_replayed=len(test),fit_gradient_max=gradients,prior_hashes_verified=checked,case_and_role_value_invariance=True,source_only=True,highprecision_types=len({r['word'] for r in chosen}),by_author=byauthor,reserve_unscored=True);save(OUT/'audit.json',result);print({k:v for k,v in result.items() if k!='by_author'})
if __name__=='__main__':run()
