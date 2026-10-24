"""Reconstruct fixed fits; replay policies, target evidence and invariances."""
from benchmarks.grammar_fixed_anchor_detector_iteration93 import *
from benchmarks.grammar_anchor_class_audit_iteration91_audit import compare_records
from voynich_smt.coarse_government import objective

def run():
    for freeze in ('design-freeze.json','model-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];types=load(OUT/'types.json');trainwords=sorted(w for w,p in anchors.items() if p in BINARY_CLASSES);candidates=sorted(w for w,p in cat['20'].items() if p in BINARY_CLASSES);assert types==dict(training=trainwords,candidates=candidates);models=load(OUT/'models.json');prov=load(OUT/'training-provenance.json');policies=load(OUT/'policies.json');patterns=load(OUT/'patterns.json');assert patterns==challenge_patterns(source('fit'),cat['20']);public,lookup=inputs92(source('fit'),anchors,trainwords,'fit93');bytype={w:cap_rows(masked_type_features(public,set(),lookup[w])) for w in trainwords};xx=[r['features'] for w in trainwords for r in bytype[w]];labels={w:BINARY_CLASSES.index(anchors[w]) for w in trainwords};y=[labels[w] for w in trainwords for r in bytype[w]];labs={'context':labels};shuffles={}
    for seed in range(3):
        rng=np.random.default_rng(9300+seed);shuffles[str(seed)]=dict(zip(trainwords,rng.permutation([labels[w] for w in trainwords]).tolist()));labs['shuffle'+str(seed)]=shuffles[str(seed)]
    assert prov==dict(sampled_rows={w:[[r['sid'],r['index']] for r in rows] for w,rows in bytype.items()},shuffled_type_labels=shuffles);assert models['prior']==[(y.count(k)+.5)/(len(y)+1) for k in range(2)];losses={}
    for arm,lab in labs.items():
        m=models[arm];assert m['vocabulary']==ag.vocabulary(xx) and m['n']==len(xx);x=ag.matrix(xx,m['vocabulary']);y=np.asarray([lab[w] for w in trainwords for r in bytype[w]]);loss,gradient=objective(np.asarray(m['weights']).ravel(),x,y,2);assert math.isclose(loss,m['loss'],rel_tol=1e-10,abs_tol=1e-12);losses[arm]=dict(loss=loss,max_gradient=float(np.abs(gradient).max()))
    cal={};summary={};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'calibration':source('calibration'),'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS})
    assert set(part['fit']).isdisjoint(part['calibration']) and set(part['fit']).isdisjoint(part['test'])
    for name,sentences in datasets.items():
        salt='cal93' if name=='calibration' else 'eval93-'+name
        for pattern in (('correct','rehearsed_in_et') if name=='calibration' else patterns):
            pred=prepare93(sentences,anchors,candidates,patterns[pattern],salt,models)
            if name=='calibration':stored=load(OUT/('calibration-'+pattern+'.json'));cal[pattern]=stored['records']
            else:
                folder=OUT/(name.lower()+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                stored=load(folder/'predictions.json');result={arm:metrics(rows,float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold']) for arm,rows in stored['records'].items()};result['frozen91']=load(ROOT/'iteration91/evaluation.json')[name+'/'+pattern];assert result==load(folder/'evaluation.json');summary[name+'/'+pattern]=result
            assert pred['identities']==stored['identities']
            for arm in DETECTOR_ARMS:compare_records(pred['records'][arm],stored['records'][arm])
        # Reference fields never enter the detector; salted rekeying cannot select a model.
        stripped=[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word']) for t in s['tokens']]) for s in sentences];original=prepare93(sentences,anchors,candidates,{},salt,models);changed=prepare93(stripped,anchors,candidates,{},'anotherkey-'+name,models)
        for arm in DETECTOR_ARMS:
            a=[{k:v for k,v in r.items() if k!='anchor_id'} for r in original['records'][arm]];b=[{k:v for k,v in r.items() if k!='anchor_id'} for r in changed['records'][arm]];compare_records(a,b)
        print('replayed',name,flush=True)
    for arm in DETECTOR_ARMS:
        chosen,curve=choose_threshold(cal['correct'][arm],cal['rehearsed_in_et'][arm]);assert chosen==policies[arm];assert curve==load(OUT/('calibration-curve-'+arm+'.json'))
    assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(training_objectives=losses,all26scenarios_and5arms_replayed=True,policies_source_calibration_only=True,reference_removal_and_rekey_invariance=True,no_type_based_model_routing=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
