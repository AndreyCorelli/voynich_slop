"""Independent masked-feature and metric replay for source-volume diagnostic."""
from benchmarks.grammar_class_volume_iteration126 import *
from voynich_smt.paired_anchor_class import target_features

def run():
    hashes=0
    for name in ['design-freeze','selection-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];ids=part['fit'];data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];fit=ag.public_sentences([dict(sent_id=i,tokens=[dict(word=t['word']) for t in data[i]['tokens']]) for i in ids],anchors,'fit116');byid={s['sent_id']:s for s in fit};lookup={t['anchor']:t['id'] for s in fit for t in s['tokens'] if t['anchor'] is not None};split=load(ROOT/'iteration116/type-split.json');train=split['training'];catalogue=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration124/models.json');cal=load(ROOT/'iteration124/calibrator.json');selection=load(OUT/'selection.json');predictions=load(OUT/'predictions.json');summary=load(OUT/'summary.json');drift=load(OUT/'drift.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(ids)&(reserved|set(part['test'])|set(part['calibration']));assert selection['full']==ids
    for seed in SEEDS:
        order=sorted(ids,key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest())
        for n in SIZES[:-1]:assert selection[str(seed)+'/'+str(n)]==order[:n]
    assert len(selection)==16;types=checks=poisons=0;full={r['type']:r for r in predictions['full']}
    for key,sids in selection.items():
        public=[byid[i] for i in sids];rows={r['type']:r for r in predictions[key]};present=set()
        for fold in range(3):
            held=[w for w in train if split['oof_folds'][w]==fold];hidden={lookup[w] for w in catalogue+held};rr=target_features(public,hidden);q=ag.predict([r['features'] for r in rr],models[str(fold)]);poison=[dict(s,tokens=[dict(t,anchor='POISON',tag='POISON') if t['id'] in hidden else dict(t) for t in s['tokens']]) for s in public];assert target_features(poison,hidden)==rr;poisons+=1
            for w in held:
                ix=[i for i,r in enumerate(rr) if r['word']==lookup[w]]
                if not ix:assert w not in rows;continue
                present.add(w);r=rows[w];raw=float(q[ix,1].mean());assert r['n']==len(ix) and r['sentences']==len({rr[i]['sid'] for i in ix});assert r['supported']==(r['n']>=5 and r['sentences']>=3);assert abs(raw-r['probabilities']['raw'])<1e-12;assert abs(float(apply_offset([raw],cal)[0])-r['probabilities']['balanced124'])<1e-12;types+=1
        assert set(rows)==present and summary[key]['missing_types']==sorted(set(train)-present)
        for group,ms in summary[key]['metrics'].items():
            rs=[r for r in rows.values() if group=='all' or group=='supported' and r['supported'] or group in CLASSES and anchors[r['type']]==group]
            for arm,m in ms.items():
                assert m['n']==len(rs)
                if not rs:assert m['accuracy'] is None;continue
                p=np.array([r['probabilities'][arm] for r in rs]);y=np.array([anchors[r['type']]=='CCONJ' for r in rs]);a=p>.5;n=np.array([r['n'] for r in rs]);assert m['correct']==int((a==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12;assert abs(m['token_weighted_accuracy']-float(np.dot(n,a==y)/n.sum()))<1e-12
                if y.any() and (~y).any():assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
                checks+=1
        ds=drift[key];assert ds['common_types']==sorted(rows);deltas=[];cross=0
        for t in ds['transitions']:
            r=rows[t['type']];f=full[t['type']];a=r['probabilities']['balanced124'];b=f['probabilities']['balanced124'];assert t['delta_to_full']==b-a and t['crossed_cutoff']==((a>.5)!=(b>.5));assert t['correct_here']==((a>.5)==(anchors[t['type']]=='CCONJ'));assert t['correct_full']==((b>.5)==(anchors[t['type']]=='CCONJ'));deltas.append(abs(b-a));cross+=t['crossed_cutoff']
        assert ds['cutoff_crossings']==cross and abs(ds['mean_absolute_probability_shift']-np.mean(deltas))<1e-12
        for arm,m in ds['full_common_metrics'].items():assert m['correct']==sum((full[w]['probabilities'][arm]>.5)==(anchors[w]=='CCONJ') for w in rows)
    oof=load(ROOT/'iteration124/oof-profiles.json');assert all(abs(full[w]['probabilities']['raw']-oof[w]['mean'])<1e-12 for w in train)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,views_replayed=16,independent_type_probabilities=types,metric_groups=checks,poison_invariance_fold_views=poisons,full_profiles_match124=True,reserve_absent=True,no_fit_or_author_evaluation=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
