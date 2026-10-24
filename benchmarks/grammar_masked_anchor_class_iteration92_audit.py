"""Reconstruct type-blocked fit objectives and replay pooled validation."""
from benchmarks.grammar_masked_anchor_class_iteration92 import *
from voynich_smt.coarse_government import objective

def run():
    for freeze in ('design-freeze.json','model-freeze.json','fit-prediction-freeze.json','calibration-prediction-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=sorted(w for w,p in anchors.items() if p in BINARY_CLASSES);assert load(OUT/'types.json')=={w:dict(label=anchors[w],fold=type_fold(w)) for w in words};models=load(OUT/'models.json');prov=load(OUT/'training-provenance.json');public,lookup=inputs92(source('fit'),anchors,words,'fit92');losses={}
    assert not set(part['fit'])&set(part['calibration'])
    for f in range(3):
        held=[w for w in words if type_fold(w)==f];train=[w for w in words if type_fold(w)!=f];assert set(held).isdisjoint(train);held_ids={lookup[w] for w in held};bytype={w:cap_rows(masked_type_features(public,held_ids,lookup[w])) for w in train};xx=[r['features'] for w in train for r in bytype[w]];gold={w:BINARY_CLASSES.index(anchors[w]) for w in train};labels={a:gold for a in ('context',)};shuffles={}
        for seed in range(3):
            rng=np.random.default_rng(9200+100*f+seed);shuffles[str(seed)]=dict(zip(train,rng.permutation([gold[w] for w in train]).tolist()));labels['shuffle'+str(seed)]=shuffles[str(seed)]
        expected=dict(held_types=held,train_types=train,sampled_rows={w:[[r['sid'],r['index']] for r in rows] for w,rows in bytype.items()},shuffled_type_labels=shuffles);assert prov[str(f)]==expected
        y=[gold[w] for w in train for r in bytype[w]];assert models[str(f)]['prior']==[(y.count(k)+.5)/(len(y)+1) for k in range(2)]
        for arm,lab in labels.items():
            model=models[str(f)][arm];assert model['vocabulary']==ag.vocabulary(xx);assert model['n']==len(xx);y=np.asarray([lab[w] for w in train for r in bytype[w]]);x=ag.matrix(xx,model['vocabulary']);loss,grad=objective(np.asarray(model['weights']).ravel(),x,y,2);assert math.isclose(loss,model['loss'],rel_tol=1e-10,abs_tol=1e-12);losses[str(f)+'/'+arm]=dict(loss=loss,max_gradient=float(np.abs(grad).max()))
    summary={}
    for split in ('fit','calibration'):
        rows=predict92(source(split),anchors,words,models,split+'92');stored=load(OUT/(split+'-predictions.json'));assert len(rows)==len(stored)
        for a,b in zip(rows,stored):
            assert all(a[k]==b[k] for k in ('type','fold','n','sentences','gold'))
            for arm in ARMS92:assert np.allclose(a['probabilities'][arm],b['probabilities'][arm],rtol=1e-10,atol=1e-12)
        summary[split]={a:type_summary(stored,a) for a in ARMS92};print('replayed',split,flush=True)
    c=summary['calibration'];context=c['context']['all'];prior=c['prior']['all'];sa=np.mean([c['shuffle'+str(i)]['all']['accuracy'] for i in range(3)]);sn=np.mean([c['shuffle'+str(i)]['all']['nll'] for i in range(3)]);summary['gate']=dict(passed=bool(context['accuracy']>=prior['accuracy']+.1 and context['accuracy']>=sa+.1 and context['nll']<prior['nll'] and context['nll']<sn),mean_shuffle_accuracy=float(sa),mean_shuffle_nll=float(sn));assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all12fit_objectives_reconstructed=losses,type_and_sentence_validation_separation=True,held_types_hidden_from_all_context=True,all_pooled_predictions_and_metrics_replayed=True,prior_input_hashes_verified=checked,source_test_authors_and_reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
