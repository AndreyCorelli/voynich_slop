"""Independent source inventory, opaque statistics, fits and author-transfer audit."""
from benchmarks.grammar_full_source_iteration162 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined
from benchmarks.grammar_regularization_iteration153_review import check_fit

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','eligibility-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    data=load(ROOT/'iteration44/annotations-truth.json');sids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(sids)&reserved;counts={}
    for sid in sids:
        for t in data[sid]['tokens']:counts.setdefault(t['word'],Counter())[t['pos']]+=1
    records={}
    for w,c in counts.items():
        tag=sorted(c,key=lambda tag:(-c[tag],tag))[0];n=sum(c.values())
        if n>=5 and tag in ['ADP','CCONJ']:records[w]=dict(n=n,label=tag,purity=c[tag]/n)
    saved=load(OUT/'eligibility.json');assert saved['records']==records;train=sorted(records);assert saved['training']==train and len(train)==29;labels={w:r['label'] for w,r in records.items()};assert Counter(labels.values())=={'ADP':18,'CCONJ':11};lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};assert saved['lookup']==lookup;split=load(ROOT/'iteration116/type-split.json');old=split['training'];targets=load(ROOT/'iteration93/types.json')['candidates'];assert set(train)==set(old)|set(targets)
    folds=dict(split['oof_folds'])
    for tag in ['ADP','CCONJ']:
        added=sorted([w for w in train if w not in old and labels[w]==tag],key=lambda w:hashlib.sha256(('fullsource162|'+w).encode()).hexdigest());folds.update({w:k%3 for k,w in enumerate(added)})
    assert folds==saved['folds'];public,*_=training_inputs();ids=[t['id'] for s in public for t in s['tokens']];features=load(OUT/'features.json');sel=load(ROOT/'iteration150/selection.json');wanted=set(lookup.values())
    for name,savedf in features.items():
        seq=list(ids)
        if name!='full':
            for pos in sel['transforms'][name[6:]]:seq[pos]=sel['fresh'][sel['positions'].index(pos)]
        f=combined(seq,wanted);assert set(f)==set(savedf)
        for i,r in f.items():
            for c in r:assert abs(r[c]-savedf[i][c])<1e-11
            fc+=1
    rename={i:hashlib.sha256(('audit162|'+i).encode()).hexdigest() for i in set(ids)};rf=features_for([rename[i] for i in ids],{rename[i] for i in wanted})
    for i,r in features['full'].items():
        for c in r:assert abs(r[c]-rf[rename[i]][c])<1e-11
    models=load(OUT/'models.json');strict=load(OUT/'strict-models.json');oof=load(OUT/'oof.json');oldmodels={'weak':load(ROOT/'iteration152/models.json'),'strong':load(ROOT/'iteration153/models.json')};fitchecks=0
    for strength_name,mm in models.items():
        assert len(mm)==40
        for name,m in mm.items():
            held=[w for w in train if folds[w]==int(name[-1])] if name.startswith('oof') else [name[5:]] if name.startswith('omit/') else [];tr=[w for w in train if w not in held];f=features[name] if name.startswith('motif/') else features['full'];assert m['strength']==STRENGTHS[strength_name];check_fit(m,f,tr,lookup,labels);fitchecks+=1
            if name.startswith('oof'):
                for w in held:assert abs(oof[strength_name][w]-predict_vector(f[lookup[w]],m))<1e-12
            else:
                expected=oldmodels[strength_name][name] if name.startswith('motif/') or (name.startswith('omit/') and name[5:] in old) else oldmodels[strength_name]['full'];assert strict[strength_name][name]==expected
    pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');tf=load(ROOT/'iteration144/features.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195']
    for work,ss in pred.items():
        for strength_name,vv in ss.items():
            for name,arms in vv.items():
                for arm,rows in arms.items():
                    m=models[strength_name][name] if arm=='expanded' else strict[strength_name][name];ww=np.array(m['weights']);b=ww[:,1]-ww[:,0]
                    for r in rows:
                        assert r['opaque'] not in wanted;f=tf[work+'/full'][r['opaque']];x=(np.array([f[c] for c in COLS])-m['mean'])/m['scale'];assert abs(float(expit(b[0]+x@b[1:]))-r['probabilities']['raw'])<1e-10;pc+=1
                    q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);s=summary[work][strength_name][name][arm];assert s==metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw');assert s['correct']==int(((q>.5)==y).sum());assert abs(s['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;mc+=1
    source=load(OUT/'source-summary.json')
    for strength_name,pp in oof.items():
        assert source[strength_name]['all29']==metrics_for(pp,labels);assert source[strength_name]['old13']==metrics_for({w:p for w,p in pp.items() if w in old},labels)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,source_inventory_verified=29,source_class_counts=dict(Counter(labels.values())),independent_source_feature_vectors=fc,source_opaque_renaming_verified=True,models_independently_optimized_and_kkt_checked=fitchecks,source_oof_predictions_verified=58,target_probabilities_replayed=pc,metric_groups_replayed=mc,all_strict13_controls_and_source_summaries_verified=True,lexical_type_holdout_explicitly_relaxed=True,no_target_annotations_used_for_training=True,reserve_overlap=0))
if __name__=='__main__':run()
