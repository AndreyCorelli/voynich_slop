"""Replay privilege removal, all-token eligibility and source-only policies."""
from benchmarks.grammar_pp_privileges_iteration83 import *
from voynich_smt.coarse_government import objective
from voynich_smt.dependency_role_proxy import encode

def compare(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert all(x[k]==y[k] for k in ('sid','index','word','labels','gold_pos','structure_gold'))
        for arm,v in x['scores'].items():assert math.isclose(v['pp'],y['scores'][arm]['pp'],abs_tol=1e-12,rel_tol=1e-10)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for freeze in ('model-freeze.json','calibration-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    saved=load(OUT/'models.json');models=saved['models'];priors=saved['priors'];prov=load(OUT/'provenance.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert all(not set(part[a])&set(part[b]) for a,b in [('fit','test'),('fit','calibration'),('calibration','test')])
    def source(split):return [dict(sent_id=sid,**data[sid]) for sid in part[split]]
    fits=rows83(source('fit'),pm,lex,morph);calq=rows83(source('calibration'),pm,lex,morph);testq=rows83(source('test'),pm,lex,morph);pol=load(OUT/'policies.json');evaluation={};gradients={};by_author={};errors={}
    for cohort in ('matched','all_tokens'):
        rr=[r for r in fits if r['matched']] if cohort=='matched' else fits
        for arm in ('masked_center','predicted_pos'):
            for f in range(3):
                train=[r for r in rr if fold(r['sid'])!=f];m=models[cohort][arm][str(f)];record=prov[cohort][arm][str(f)];assert record['train_n']==len(train);assert set(record['training_sids'])=={r['sid'] for r in train};assert not set(record['training_sids'])&(set(part['calibration'])|set(part['test']))
                loss,g=objective(np.array(m['weights']).ravel(),encode([r[arm] for r in train],m['vocabulary']),np.array([r['structure_gold'] for r in train],int));assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;gradients[cohort+'/'+arm+'/'+str(f)]=float(max(abs(g)))
        cc=[r for r in calq if r['matched']] if cohort=='matched' else calq;tt=[r for r in testq if r['matched']] if cohort=='matched' else testq;cal=load(OUT/(cohort+'-calibration.json'));rows=load(OUT/(cohort+'-predictions.json'));compare(infer83(cc,models[cohort],priors[cohort]),cal);compare(infer83(tt,models[cohort],priors[cohort]),rows)
        for a in ARMS:assert select_policy(cal,'pp',a)==pol[cohort][a]
        evaluation[cohort]=evaluate83(rows,pol[cohort]);by_author[cohort]={author:evaluate83([r for r in rows if data[r['sid']]['author']==author],pol[cohort]) for author in ('Cicero','Palladius')}
        threshold=pol[cohort]['predicted_pos']['precision90']['threshold'];fp=Counter();positives=Counter()
        for r in rows:
            positives[r['gold_pos']]+=r['labels']['pp']
            if r['scores']['predicted_pos']['pp']>=threshold and not r['labels']['pp']:fp[r['gold_pos']]+=1
        errors[cohort]=dict(highprecision_fp_by_goldpos=dict(fp),reference_positives_by_goldpos=dict(positives))
    assert evaluation==load(OUT/'evaluation.json');assert len(testq)==sum(len(s['tokens']) for s in source('test'))==9956
    altered=[dict(s,tokens=[dict(t,pos='X',head=None,rel='root',features={}) for t in s['tokens']]) for s in source('test')];changedq=rows83(altered,pm,lex,morph);original=infer83(testq,models['all_tokens'],priors['all_tokens']);changed=infer83(changedq,models['all_tokens'],priors['all_tokens']);assert len(original)==len(changed)
    for x,y in zip(original,changed):
        for a in ARMS:assert math.isclose(x['scores'][a]['pp'],y['scores'][a]['pp'],abs_tol=1e-12,rel_tol=1e-10)
    old=load(ROOT/'iteration82/predictions.json');matched=load(OUT/'matched-predictions.json');assert [(r['sid'],r['index'],r['structure_gold']>=4) for r in old]==[(r['sid'],r['index'],r['labels']['pp']) for r in matched]
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(fit_all_tokens=len(fits),calibration_all_tokens=len(calq),test_all_tokens=len(testq),gradient_max=gradients,prior_input_hashes_verified=checked,gold_annotation_score_invariance=True,matched_cohort_reproduced=True,source_only=True,by_author=by_author,errors=errors,reserve_unscored=True);save(OUT/'audit.json',result);print({k:v for k,v in result.items() if k not in ('gradient_max','by_author','errors')})
if __name__=='__main__':run()
