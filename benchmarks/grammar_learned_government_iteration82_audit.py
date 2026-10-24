"""Check OOF provenance, fit gradients, source policies and structural metrics."""
from benchmarks.grammar_learned_government_iteration82 import *
from voynich_smt.coarse_government import objective,case_matrix
from voynich_smt.contextual_nominative import objective as binary_objective
from voynich_smt.dependency_role_proxy import encode
from benchmarks.grammar_learned_government_iteration82_pp import pp_rows
from benchmarks.grammar_learned_government_iteration82_proximity import control_rows

def compare(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert all(x[k]==y[k] for k in ('sid','index','word','labels','structure_gold'))
        assert np.allclose(x['structure_probabilities'],y['structure_probabilities'],atol=1e-12,rtol=1e-10)
        for arm,v in x['scores'].items():assert math.isclose(v['nominative'],y['scores'][arm]['nominative'],abs_tol=1e-12,rel_tol=1e-10)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for freeze in ('model-freeze.json','calibration-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    for design in ('secondary-pp-design.json','pp-proximity-design.json'):
        for p,h in load(OUT/design)['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'pp-policy.json')==load(OUT/'pp-policy-freeze.json')['policy'];assert digest(OUT/'pp-proximity-policy.json')==load(OUT/'pp-proximity-policy-freeze.json')['policy']
    models=load(OUT/'models.json');oof=load(OUT/'oof.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert all(not set(part[a])&set(part[b]) for a,b in [('fit','test'),('fit','calibration'),('calibration','test')])
    def prepare(split,seed):return rows81([dict(sent_id=sid,**data[sid]) for sid in part[split]],pm,lex,morph,seed)[0]
    fits=prepare('fit',7901);xx=[r['baseline'] for r in fits];labels=np.array([structure_label(r) for r in fits]);probs=np.array([r['probabilities'] for r in oof['rows']]);gradient={}
    assert len(fits)==len(oof['rows'])==8840
    for a,b in zip(fits,oof['rows']):assert (a['sid'],a['index'],fold(a['sid']))==(b['sid'],b['index'],b['fold'])
    for record in oof['assignments']:
        f=record['fold'];train=[i for i,r in enumerate(fits) if fold(r['sid'])!=f];held=[i for i,r in enumerate(fits) if fold(r['sid'])==f]
        assert set(record['train_sids']).isdisjoint(record['held_sids']);assert set(record['train_sids'])=={fits[i]['sid'] for i in train};assert set(record['held_sids'])=={fits[i]['sid'] for i in held}
        m=models['probes'][str(f)];loss,g=objective(np.array(m['weights']).ravel(),encode([xx[i] for i in train],m['vocabulary']),labels[train]);assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;gradient['probe'+str(f)]=float(max(abs(g)));assert np.allclose(probe([xx[i] for i in held],m),probs[held],atol=1e-12,rtol=1e-10)
    for name,ps in [('case_predicted',probs),('case_oracle',np.eye(8)[labels])]:
        m=models[name];loss,g=binary_objective(np.array(m['weights']),case_matrix(xx,ps,m['vocabulary']),np.array([r['labels']['nominative'] for r in fits],float));assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;gradient[name]=float(max(abs(g)))
    calq=prepare('calibration',7701);cal=load(OUT/'calibration-predictions.json');compare(infer82(calq,models,8221),cal);pol=load(OUT/'policies.json')
    for a in ARMS:assert select_policy(cal,'nominative',a)==pol['nominative'][a]
    testq=prepare('test',8101);rows=load(OUT/'predictions.json');compare(infer82(testq,models,8222),rows)
    altered=[dict(r,pp_bundle=['oraclePP:present=False'],structure_bundle=['oracleHead:ROOT'],labels={'nominative':not r['labels']['nominative']}) for r in testq];changed=infer82(altered,models,8222)
    for a,b in zip(rows,changed):
        for arm in ('predicted','predicted_sham','baseline'):
            assert math.isclose(a['scores'][arm]['nominative'],b['scores'][arm]['nominative'],abs_tol=1e-12,rel_tol=1e-10)
        assert np.allclose(a['structure_probabilities'],b['structure_probabilities'],atol=1e-12,rtol=1e-10)
    ev=load(OUT/'evaluation.json');assert evaluation(rows,pol)['nominative']==ev['nominative'];assert structural_metrics(rows,models['structure_prior'])==ev['structural_prediction']
    ppol=load(OUT/'pp-policy.json');assert select_policy(pp_rows(cal),'pp','predicted')==ppol;pp=pp_rows(rows);ppeval=load(OUT/'pp-evaluation.json')
    for name,rr in [('all',pp)]+[(a,[r for r in pp if data[r['sid']]['author']==a]) for a in ('Cicero','Palladius')]:
        assert counts(rr,'pp','predicted',ppol['precision90']['threshold'])==ppeval[name]['source_precision90']
    proxpol=load(OUT/'pp-proximity-policy.json');cx=control_rows(calq);tx=control_rows(testq)
    for a in ('left','either'):
        assert select_policy(cx,'pp',a)==proxpol[a];assert counts(tx,'pp',a,proxpol[a]['f1']['threshold'])==load(OUT/'pp-proximity-evaluation.json')[a]['f1']
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(oof_provenance_verified=8840,calibration_replayed=len(cal),test_replayed=len(rows),gradient_max=gradient,predicted_inference_oracle_invariant=True,prior_input_hashes_verified=checked,source_only=True,reserve_unscored=True);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
