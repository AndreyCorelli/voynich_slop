"""Replay full budget curve, fold provenance and both source calibration rules."""
from benchmarks.grammar_anchor_budget_iteration85 import *
from voynich_smt.coarse_government import objective
from voynich_smt.anchor_budget import precision_lower

def compare(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert all(x[k]==y[k] for k in ('sid','index','word','visible','labels'))
        for arm in ARMS:assert math.isclose(x['scores'][arm]['pp'],y['scores'][arm]['pp'],abs_tol=1e-12,rel_tol=1e-10)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'anchor-budgets.json')==load(OUT/'anchor-freeze.json')['catalogue']
    for p,h in load(OUT/'all-calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];catalogue=load(OUT/'anchor-budgets.json');inventory=ag.anchor_inventory(source('fit'));assert dict(budgets(source('fit'),inventory),**{'195':inventory})==catalogue;classes=load(ROOT/'iteration84/models.json')['pos_classes'];allresult=load(OUT/'evaluation.json');checks={};breakdown={};hidden={}
    for budget,anchors in catalogue.items():
        folder=OUT/('budget-'+budget)
        for freeze in ('model-freeze.json','calibration-freeze.json'):
            for p,h in load(folder/freeze)['inputs'].items():assert digest(p)==h,p
        assert digest(folder/'predictions.json')==load(folder/'prediction-freeze.json')['predictions'];models=load(folder/'models.json')
        if budget!='195':
            _,fits=prepare84(source('fit'),anchors,'fit85',classes);xx=[r['features'] for r in fits];oof=load(folder/'oof.json');q=np.array(oof['probabilities']);grad=[]
            for f in range(3):
                ids=[i for i,r in enumerate(fits) if fold(r['sid'])!=f];held=[i for i,r in enumerate(fits) if fold(r['sid'])==f];record=oof['provenance'][str(f)];assert set(record['train_sids'])=={fits[i]['sid'] for i in ids};assert not set(record['train_sids'])&{fits[i]['sid'] for i in held};m=models['pos'][str(f)];loss,g=objective(np.array(m['weights']).ravel(),ag.matrix([xx[i] for i in ids],m['vocabulary']),np.array([fits[i]['pos_gold'] for i in ids]),len(classes));assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;grad.append(float(max(abs(g))));assert np.allclose(ag.anchor_override([fits[i] for i in held],ag.predict([xx[i] for i in held],m),classes),q[held],atol=1e-12,rtol=1e-10)
            pq=fold_pool(fits,q)
            for f in range(3):
                ids=[i for i,r in enumerate(fits) if fold(r['sid'])!=f];m=models['pp'][str(f)];loss,g=objective(np.array(m['weights']).ravel(),ag.matrix([xx[i] for i in ids],m['vocabulary'],pq[ids]),np.array([fits[i]['structure_gold'] for i in ids]),8);assert abs(loss-m['loss'])<1e-9 and max(abs(g))<1e-5;grad.append(float(max(abs(g))))
            checks[budget]=max(grad)
        else:
            old=load(ROOT/'iteration84/models.json');assert models['pos']==old['pos'] and models['pp']==load(ROOT/'iteration84/fold-local-pool/models.json')
        _,calq=prepare84(source('calibration'),anchors,'cal85',classes);cal=load(folder/'calibration-predictions.json');compare(infer85(calq,models),cal);pol=load(folder/'policies.json')
        for arm in ARMS:
            assert select_policy(cal,'pp',arm)==pol[arm]['standard'];assert conservative_policy(cal,arm)==pol[arm]['conservative']
            if pol[arm]['conservative']:
                p=pol[arm]['conservative'];assert p['precision_lower']==precision_lower(p['calibration']['tp'],p['calibration']['predicted']) and p['precision_lower']>=.9
        _,queries=prepare84(source('test'),anchors,'test85',classes);rows=load(folder/'predictions.json');compare(infer85(queries,models),rows);assert evaluate85(rows,pol)==allresult[budget]['metrics'];assert sum(r['visible'] for r in rows)==allresult[budget]['visible_tokens'];assert len(rows)==9956
        breakdown[budget]={a:evaluate85([r for r in rows if data[r['sid']]['author']==a],pol) for a in ('Cicero','Palladius')};hidden[budget]=evaluate85([r for r in rows if not r['visible']],pol)
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(all_budgets_replayed=list(catalogue),fit_gradient_max=checks,test_tokens_per_budget=9956,prior_input_hashes_verified=checked,all_calibrations_frozen_before_test=True,source_only=True,by_author=breakdown,hidden=hidden,reserve_unscored=True);save(OUT/'audit.json',result);print({k:v for k,v in result.items() if k not in ('by_author','hidden')})
if __name__=='__main__':run()
