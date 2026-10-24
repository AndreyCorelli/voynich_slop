"""Public-input invariance, OOF provenance and corrected pooling replay."""
from benchmarks.grammar_anchor_only_iteration84 import *
from benchmarks.grammar_anchor_only_iteration84_pool_control import CONTROL,fold_pool
from voynich_smt.coarse_government import objective

def compare(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert all(x[k]==y[k] for k in ('sid','index','word','labels','pos_gold'))
        for a in ARMS:assert math.isclose(x['scores'][a]['pp'],y['scores'][a]['pp'],abs_tol=1e-12,rel_tol=1e-10)
        for f in ('pos_probabilities','pooled_pos_probabilities'):assert np.allclose(x[f],y[f],atol=1e-12,rtol=1e-10)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'anchors.json')==load(OUT/'anchor-freeze.json')['anchors']
    for freeze in ('model-freeze.json','calibration-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    for p,h in load(CONTROL/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for file,key,freeze in [('models.json','models','model-freeze.json'),('policy.json','policy','policy-freeze.json'),('predictions.json','predictions','prediction-freeze.json')]:assert digest(CONTROL/file)==load(CONTROL/freeze)[key]
    models=load(OUT/'models.json');anchors=load(OUT/'anchors.json');oof=load(OUT/'oof.json');data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];classes=models['pos_classes'];assert all(not set(part[a])&set(part[b]) for a,b in [('fit','test'),('fit','calibration'),('calibration','test')])
    def source(split):return [dict(sent_id=sid,**data[sid]) for sid in part[split]]
    assert ag.anchor_inventory(source('fit'))==anchors
    pub,rows=prepare84(source('fit'),anchors,'fit84',classes);assert pub==load(OUT/'fit-public.json');xx=[r['features'] for r in rows];q=np.array(oof['probabilities']);grad={}
    for f in range(3):
        train=[i for i,r in enumerate(rows) if fold(r['sid'])!=f];held=[i for i,r in enumerate(rows) if fold(r['sid'])==f];m=models['pos'][str(f)];record=oof['provenance'][str(f)];assert set(record['training_sids'])=={rows[i]['sid'] for i in train};assert set(record['training_sids']).isdisjoint({rows[i]['sid'] for i in held})
        loss,g=objective(np.array(m['weights']).ravel(),ag.matrix([xx[i] for i in train],m['vocabulary']),np.array([rows[i]['pos_gold'] for i in train]),len(classes));assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;grad['pos'+str(f)]=float(max(abs(g)))
        pred=ag.anchor_override([rows[i] for i in held],ag.predict([xx[i] for i in held],m),classes);assert np.allclose(pred,q[held],atol=1e-12,rtol=1e-10)
    pooled=ag.pool(rows,q);strict=fold_pool(rows,q);correct=load(CONTROL/'models.json')
    for name,soft,group in [('anchors',None,models['pp']['anchors']),('context_pos',q,models['pp']['context_pos']),('pooled_pos',pooled,models['pp']['pooled_pos']),('corrected_pool',strict,correct)]:
        for f in range(3):
            ids=[i for i,r in enumerate(rows) if fold(r['sid'])!=f];m=group[str(f)];loss,g=objective(np.array(m['weights']).ravel(),ag.matrix([xx[i] for i in ids],m['vocabulary'],None if soft is None else soft[ids]),np.array([rows[i]['structure_gold'] for i in ids]),8);assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;grad[name+str(f)]=float(max(abs(g)))
    pub,calq=prepare84(source('calibration'),anchors,'cal84',classes);assert pub==load(OUT/'calibration-public.json');cal=load(OUT/'calibration-predictions.json');compare(infer84(calq,models),cal);pol=load(OUT/'policies.json')
    for a in ARMS:assert select_policy(cal,'pp',a)==pol[a]
    pub,testq=prepare84(source('test'),anchors,'test84',classes);assert pub==load(OUT/'test-public.json');test=load(OUT/'predictions.json');compare(infer84(testq,models),test);assert evaluate83(test,pol)==load(OUT/'evaluation.json')
    modified=dict(models,pp=dict(models['pp'],pooled_pos=correct));cc=load(CONTROL/'calibration-predictions.json');compare(infer84(calq,modified),cc);cpol=load(CONTROL/'policy.json');assert select_policy(cc,'pp','pooled_pos')==cpol;ct=load(CONTROL/'predictions.json');compare(infer84(testq,modified),ct);assert evaluate83(ct,{'pooled_pos':cpol})==load(CONTROL/'evaluation.json')
    rekeyed=ag.public_features(ag.public_sentences(source('test'),anchors,'differentKEY'));assert [r['features'] for r in rekeyed]==[r['features'] for r in testq]
    changed=[dict(r,word=x['word'],labels={'pp':not r['labels']['pp']},pos_gold=0) for r,x in zip(testq,rekeyed)];new=infer84(changed,modified)
    for a,b in zip(ct,new):
        for arm in ARMS:assert math.isclose(a['scores'][arm]['pp'],b['scores'][arm]['pp'],abs_tol=1e-12,rel_tol=1e-10)
    hidden=[t['anchor'] is None for s in pub for t in s['tokens']];details={}
    for name,rr in [('all',ct),('hidden',[r for r,h in zip(ct,hidden) if h]),('anchors',[r for r,h in zip(ct,hidden) if not h])]+[(a,[r for r in ct if data[r['sid']]['author']==a]) for a in ('Cicero','Palladius')]:details[name]=evaluate83(rr,{'pooled_pos':cpol})
    posmetrics={f:dict(hidden_accuracy=float(np.mean([np.argmax(r[f])==r['pos_gold'] for r,h in zip(ct,hidden) if h])),all_accuracy=float(np.mean([np.argmax(r[f])==r['pos_gold'] for r in ct]))) for f in ('pos_probabilities','pooled_pos_probabilities')}
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(sourcefit_rows=len(rows),calibration_replayed=len(cal),test_replayed=len(test),anchors=len(anchors),visible_test_tokens=sum(not h for h in hidden),gradient_max=grad,prior_hashes_verified=checked,rekey_and_label_invariance=True,corrected_pool_fold_local=True,corrected_breakdown=details,pos_metrics=posmetrics,reserve_unscored=True);save(OUT/'audit.json',result);print({k:v for k,v in result.items() if k not in ('gradient_max','corrected_breakdown','pos_metrics')})
if __name__=='__main__':run()
