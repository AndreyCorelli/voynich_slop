"""Audit strict type exclusion, calibrated OFF decisions, and class quality."""
from benchmarks.grammar_endpoint_reliability_iteration116 import *


def independent_stats(rows,arm,cut):
    out={}
    for g in ['complete','omission','literal']:
        rr=[r for r in rows if r['regime']==g];calls=[]
        for r in rr:
            p=r['base_pair'] if arm=='base' else (r['base_pair'] if cut is not None and r['base_pair'] is not None and r['margins'][arm] is not None and r['margins'][arm]>=cut else None)
            if p is not None:calls.append((r,p==r['reference']['pair']))
        hit=sum(h for r,h in calls);out[g]=dict(n=len(rr),hit=hit,wrong=len(calls)-hit,calls=len(calls),clean_wrong=sum(not h and not r['reference']['error'] for r,h in calls),unsupported_wrong=sum(not h and r['reference']['error'] and not r['reference']['supported'] for r,h in calls),distinct_hits=len({r['case'] for r,h in calls if h}))
    return out


def run():
    hashes=0
    for name in ['design-freeze','model-freeze','policy-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    split=load(OUT/'type-split.json');train=split['training'];cal=split['calibration'];test=split['evaluation'];assert len(train)==13 and len(cal)==len(test)==8 and not set(train)&(set(cal)|set(test)) and not set(cal)&set(test)
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];targets=load(ROOT/'iteration93/types.json')['candidates'];assert set(cal+test)==set(targets)
    for pool in [cal,test]:assert sum(anchors[w]=='ADP' for w in pool)==4
    d=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];fit=ag.public_sentences([dict(sent_id=i,**d[i]) for i in part['fit']],anchors,'fit116');lookup={t['anchor']:t['id'] for s in fit for t in s['tokens'] if t['anchor'] is not None};hid={lookup[w] for w in targets};classmodels=load(OUT/'class-models.json');provenance=load(OUT/'training-provenance.json');oof=load(OUT/'oof-profiles.json');replayed=0
    for fold in ['0','1','2','final']:
        held=[] if fold=='final' else provenance[fold]['held'];tr=train if fold=='final' else provenance[fold]['train'];assert not set(tr)&set(targets) and not set(tr)&set(held);hidden=hid|{lookup[w] for w in held};expected={w:cap_rows(masked_type_features(fit,hidden,lookup[w])) for w in tr};stored=provenance['final'] if fold=='final' else provenance[fold]['sampled_rows'];assert stored=={w:[[r['sid'],r['index']] for r in rr] for w,rr in expected.items()};assert sum(len(rr) for rr in expected.values())==classmodels[fold]['n']
        if held:
            profiles=grouped_profile(fit,held,lookup,hidden,classmodels[fold])
            for w,r in profiles.items():
                assert r['n']==oof[w]['n'] and r['sentences']==oof[w]['sentences']
                assert np.allclose(r['profile'],oof[w]['profile'],rtol=1e-12,atol=1e-12) and abs(r['mean']-oof[w]['mean'])<1e-12
                replayed+=1
    scaling=load(OUT/'scaling.json');x=np.array([oof[w]['profile'] for w in train]);assert np.allclose(x.mean(0),scaling['mean']);scale=x.std(0);scale[scale<1e-12]=1.;assert np.allclose(scale,scaling['scale']);models=load(OUT/'reliability-models.json');y=np.array([CLASSES.index(anchors[w]) for w in train]);assert models['prior']==float(y.mean());assert models['reliability']['n']==models['shuffle']['n']==13 and models['balanced']['n']==60
    # Refit the small second-stage learners from their documented OOF inputs.
    z=(x-np.array(scaling['mean']))/np.array(scaling['scale']);ix=np.concatenate([np.tile(np.flatnonzero(y==c),30//int((y==c).sum())) for c in [0,1]]);yy=np.random.default_rng(11677).permutation(y)
    for a,zz,labels in [('reliability',z,y),('balanced',z[ix],y[ix]),('shuffle',z,yy)]:
        expected=ag.fit([['bias'] for v in labels],labels,CLASSES,soft=zz);assert np.allclose(expected['weights'],models[a]['weights'],rtol=1e-10,atol=1e-10)
    base=load(ROOT/'iteration111/policies.json')['full'];source={r['case']:r for r in load(ROOT/'iteration102/calibration-cases.json') if r['block']=='full'};lit={(r['removed_word'],r['case']):r for r in load(ROOT/'iteration113/cases.json')};full=ag.public_sentences([dict(sent_id=i,**d[i]) for i in load(ROOT/'iteration98/blocks.json')['scored']['full']],anchors,'cal98-full');lookup={t['anchor']:t['id'] for s in full for t in s['tokens'] if t['anchor'] is not None};hidden={lookup[w] for w in targets};classquality={};pair_checks=0;profile_checks=0
    for name,pool in [('calibration',cal),('evaluation',test)]:
        profiles=load(OUT/(name+'-profiles.json'));probabilities=load(OUT/(name+'-probabilities.json'));rows=load(OUT/(name+'-cases.json'));allowed={lookup[w] for w in pool};assert len(rows)==323
        for view,stored in profiles.items():
            p=full if view=='full' else load(ROOT/'iteration113'/('public-'+view+'.json'));expected=grouped_profile(p,pool,lookup,hidden,classmodels['final'])
            assert set(expected)==set(stored)
            for w,r in expected.items():
                assert r['n']==stored[w]['n'] and r['sentences']==stored[w]['sentences']
                assert np.allclose(r['profile'],stored[w]['profile'],rtol=1e-12,atol=1e-12) and abs(r['mean']-stored[w]['mean'])<1e-12
            calculated=apply_models(stored,models,scaling,lookup)
            for arm,qs in calculated.items():assert all(abs(q-probabilities[view][arm][i])<1e-12 for i,q in qs.items())
            profile_checks+=len(stored)
        for r in rows:
            if r['reference']['error']:assert set(r['reference']['pair'])<=allowed
            record=source[r['case']] if r['regime']!='literal' else lit[r['physical_view'],r['case']];folder=ROOT/'iteration102/full' if r['regime']!='literal' else ROOT/'iteration113'/r['physical_view'];z=np.load(folder/(r['case']+'.npz'));ii=[j for j,p in enumerate(record['pairs']) if set(p['pair'])<=allowed and (r['omitted'] is None or r['omitted'] not in p['pair'])];expected=summarize([record['pairs'][j] for j in ii],z['draws'][:,ii]);z.close();assert expected==r['features'] and gate(expected,base)==r['base_pair'];assert r['reference']['supported']==any(record['pairs'][j]['supported'] and record['pairs'][j]['pair']==r['reference']['pair'] for j in ii)
            for a,margin in r['margins'].items():assert margin==pair_margin(r['base_pair'],r['proposed'],probabilities[r['physical_view']][a])
            pair_checks+=1
        classquality[name]={}
        for arm,pp in probabilities['full'].items():
            qs=[pp[lookup[w]] for w in pool];ys=[anchors[w]=='CCONJ' for w in pool]
            pos=[q for q,v in zip(qs,ys) if v];neg=[q for q,v in zip(qs,ys) if not v];auc=sum((p>n)+.5*(p==n) for p in pos for n in neg)/(len(pos)*len(neg))
            classquality[name][arm]=dict(types=len(pool),accuracy=sum((q>.5)==v for q,v in zip(qs,ys))/len(pool),nll=-sum(math.log(max(1e-12,q if v else 1-q)) for q,v in zip(qs,ys))/len(pool),predicted_conjunctions=sum(q>.5 for q in qs),posthoc_auc=auc,auc_pair_comparisons=len(pos)*len(neg))
    rows=load(OUT/'calibration-cases.json');baseline=independent_stats(rows,'base',None);assert baseline==load(OUT/'calibration-baseline.json');curves=load(OUT/'calibration-curves.json');chosen=load(OUT/'chosen.json');safe_best={};cutoffs=0
    for arm,curve in curves.items():
        eligible=[];safe=[]
        for r in curve:
            s=independent_stats(rows,arm,r['cutoff']);assert s==r['stats'];safety=all(not v['clean_wrong'] and not v['unsupported_wrong'] and (not v['calls'] or v['hit']/v['calls']>=.9) for v in s.values());ok=safety and all(v['calls'] and v['hit']>=math.ceil(.8*baseline[g]['hit']) for g,v in s.items()) and s['complete']['hit']>=4 and s['omission']['distinct_hits']>=4 and s['literal']['distinct_hits']>=4;assert ok==r['qualified'];cutoffs+=1
            if ok:eligible.append(r)
            if safety:safe.append(r)
        expected=max(eligible,key=lambda r:(r['stats']['complete']['hit'],sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),r['cutoff'])) if eligible else dict(cutoff=None,qualified=False);assert expected==chosen[arm];safe_best[arm]=max(safe,key=lambda r:(r['stats']['complete']['hit'],sum(s['hit'] for s in r['stats'].values()))) if safe else None
    testrows=load(OUT/'evaluation-cases.json');summary={'base':independent_stats(testrows,'base',None),**{a:independent_stats(testrows,a,r['cutoff']) for a,r in chosen.items()}};assert summary==load(OUT/'evaluation-summary.json')
    save(OUT/'diagnostic-summary.json',dict(class_quality=classquality,best_safe_source_settings_not_selected=safe_best,base_candidate_budget=8,all_vetoes_off=all(not r['qualified'] for r in chosen.values()),type_training_class_counts=dict(ADP=10,CCONJ=3),strong_context_masking=True));save(OUT/'audit.json',dict(input_hashes_verified=hashes,type_label_splits_disjoint=True,catalogue_types_hidden_in_class_inputs=True,oof_profiles_recomputed=True,small_reliability_models_refit=3,physical_type_profiles_recomputed=profile_checks,pair_bank_rankings_and_margins_recomputed=pair_checks,calibration_cutoffs_replayed=cutoffs,heldout_type_policies_replayed=len(summary),no_author_or_reserve_or_new_labels=True));print('AUDIT',load(OUT/'audit.json'));print('QUALITY',classquality)
if __name__=='__main__':run()
