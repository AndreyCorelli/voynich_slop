"""Reconstruct augmented training objective, replay calibration and transfer."""
from benchmarks.grammar_anchor_augmentation_iteration89 import *
from voynich_smt.coarse_government import objective

def run():
    for freeze in ('design-freeze.json','model-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];patterns=load(OUT/'patterns.json');assert patterns==source_patterns(source('fit'),load(ROOT/'iteration85/anchor-budgets.json')['20']);old=load(BASE/'models.json');models=load(OUT/'models.json');assert models['pos']==old['pos'] and models['pos_classes']==old['pos_classes'];classes=models['pos_classes'];policies=load(OUT/'policies.json')
    public,labels=prepare84(source('fit'),anchors,'fit89',classes);allrows=[];allsoft=[]
    for view in TRAIN_VIEWS:
        changed=perturb(public,patterns[view],anchors);assert [t['id'] for s in changed for t in s['tokens']]==[t['id'] for s in public for t in s['tokens']];rows=query_rows(changed,labels)
        for r,l in zip(rows,labels):r['structure_gold']=l['structure_gold']
        q=np.zeros((len(rows),len(classes)))
        for f in range(3):
            ids=[i for i,r in enumerate(rows) if fold(r['sid'])==f];q[ids]=ag.predict([rows[i]['features'] for i in ids],old['pos'][str(f)])
        q=ag.anchor_override(rows,q,classes);allsoft.append(fold_pool(rows,q));allrows.extend(rows)
    soft=np.concatenate(allsoft);xx=[r['features'] for r in allrows];losses={}
    for f in range(3):
        ids=[i for i,r in enumerate(allrows) if fold(r['sid'])!=f];m=models['pp'][str(f)];assert m['n']==len(ids);assert m['vocabulary']==ag.vocabulary([xx[i] for i in ids]);x=ag.matrix([xx[i] for i in ids],m['vocabulary'],soft[ids]);y=np.asarray([allrows[i]['structure_gold'] for i in ids]);loss,gradient=objective(np.asarray(m['weights']).ravel(),x,y,8);assert math.isclose(loss,m['loss'],rel_tol=1e-10,abs_tol=1e-12);losses[str(f)]=dict(loss=loss,max_gradient=float(np.abs(gradient).max()))
    print('training objectives reconstructed',flush=True)
    cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'calibration':source('calibration'),'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});cal={a:{} for a in ('original','augmented')};summary={};oldpol=load(BASE/'policies.json')
    for name,sentences in datasets.items():
        salt='cal89' if name=='calibration' else 'eval89-'+name;public,labels=transfer_rows(sentences,anchors,salt,classes)
        for pattern,replacements in patterns.items():
            queries=query_rows(perturb(public,replacements,anchors),labels)
            if name=='calibration':
                for arm,model in (('original',old),('augmented',models)):
                    rr=infer85(queries,model);stored=load(OUT/('calibration-'+arm+'-'+pattern)/'predictions.json');compare(rr,stored);cal[arm][pattern]=stored
            else:
                folder=OUT/(name.lower()+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                rows=load(folder/'predictions.json');compare(infer85(queries,models),rows);oldrows=load(ROOT/'iteration87'/(name.lower()+'-195-'+pattern)/'predictions.json');result={}
                for arm,rr in (('original',oldrows),('augmented',rows)):result[arm]=dict(fixed_80=score(rr,.8),clean_policy=score(rr,policies[arm]['clean_threshold']),robust_policy=score(rr,policies[arm]['robust_threshold']))
                result['nearest_f1']=counts(rows,'pp','left',oldpol['left']['standard']['f1']['threshold']);result['strict88']=load(ROOT/'iteration88/evaluation-tradeoff-grid.json')[name+'/195/'+pattern]['0.0']['selected'];assert result==load(folder/'evaluation.json');summary[name+'/'+pattern]=result
        print('replayed',name,flush=True)
    assert summary==load(OUT/'evaluation.json')
    for arm,by_pattern in cal.items():
        selected,curve=robust_policy(by_pattern,232);assert curve==load(OUT/('calibration-curve-'+arm+'.json'));assert policies[arm]['robust_threshold']==(selected['threshold'] if selected else None);clean=select_policy(by_pattern['correct'],'pp','pooled_pos')['precision90'];assert policies[arm]['clean_threshold']==(clean['threshold'] if clean else None)
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(frozen_pos_models_verified=True,training_objectives=losses,fold_local_view_separate_pooling=True,all_predictions_and_policies_replayed=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')

def compare(rows,stored):
    assert len(rows)==len(stored)
    for r,t in zip(rows,stored):
        assert all(r[k]==t[k] for k in ('sid','index','word','visible','labels'))
        for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)
if __name__=='__main__':run()
