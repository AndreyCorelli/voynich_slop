"""Independent feature, joint-model, interval-bound and four-text audit."""
from benchmarks.grammar_joint_scalars_iteration142 import *
from benchmarks.grammar_context_roles_iteration141_review import dictionary_stats
from benchmarks.grammar_context_overlap_iteration135_review import independent_stats

def combined(ids,wanted):
    a=independent_stats([dict(tokens=[dict(id=i) for i in ids])],wanted);b=dictionary_stats(ids,wanted)
    return {i:dict(n=a[i]['n'],corrected=a[i]['corrected'],role_similarity=b[i]['role_similarity']) for i in a}

def run():
    hashes=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];f=combined(ids,{lookup[w] for w in train});saved=load(OUT/'training-features.json');assert set(f)==set(saved)
    for i in f:
        for c in ['corrected','role_similarity']:assert abs(f[i][c]-saved[i][c])<1e-11
    models=load(OUT/'models.json');oof=load(OUT/'oof-probabilities.json');cal=load(OUT/'calibrators.json');guards=load(OUT/'guards.json');maxpdiff=0.
    for name,cols in CONFIGS.items():
        for key in ['0','1','2','final']:
            held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];m=fit_vector(f,tr,lookup,anchors,cols);assert m['training']==models[name][key]['training'];assert abs(m['loss']-models[name][key]['loss'])<1e-8;pd=max(abs(predict_vector(f[lookup[w]],m)-predict_vector(f[lookup[w]],models[name][key])) for w in tr);maxpdiff=max(maxpdiff,pd);assert pd<1e-5
            for w in held:assert abs(predict_vector(f[lookup[w]],models[name][key])-oof[name][w])<1e-10
        expected=fit_offset([oof[name][w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);assert expected==cal[name];m=models[name]['final'];weights=np.array(m['weights']);coef=(weights[1:,1]-weights[1:,0])/np.array(m['scale']);intercept=float(weights[0,1]-weights[0,0]-np.dot(coef,m['mean']))
        for label,offset in [('raw_domain',0.),('calibrated_domain',cal[name]['offset'])]:
            lo=intercept+offset+sum(min(coef[j]*BOUNDS[c][0],coef[j]*BOUNDS[c][1]) for j,c in enumerate(cols));hi=intercept+offset+sum(max(coef[j]*BOUNDS[c][0],coef[j]*BOUNDS[c][1]) for j,c in enumerate(cols));g=guards[name][label];assert abs(lo-g['min_logit'])<1e-10 and abs(hi-g['max_logit'])<1e-10;assert g['both_classes_possible']==(lo<0<hi)
        assert guards[name]['offset_accepted']==guards[name]['calibrated_domain']['both_classes_possible'];assert guards[name]['effective_offset']==(cal[name]['offset'] if guards[name]['offset_accepted'] else 0.)
    assert not guards['roles']['offset_accepted'];streams,lookups=streams_and_lookups();transforms=load(ROOT/'iteration141/transforms.json');target=load(OUT/'target-features.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');statchecks=probchecks=metricchecks=0
    for work,seq in streams.items():
        for view,ix in transforms[work].items():
            if ix is None:stream=seq
            else:
                seed=int(view[4:]);assert seed in NULL_SEEDS;assert ix==np.random.default_rng(seed).permutation(len(seq)).tolist();stream=[seq[i] for i in ix]
            assert Counter(stream)==Counter(seq);features=combined(stream,set(lookups[work].values()));assert set(features)==set(target[work][view]);statchecks+=len(features)
            for i in features:
                assert features[i]['n']==target[work][view][i]['n']
                for c in ['corrected','role_similarity']:assert abs(features[i][c]-target[work][view][i][c])<1e-11
            for name,rows in pred[work][view].items():
                for r in rows:
                    raw=predict_vector(features[r['opaque']],models[name]['final']);assert abs(raw-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal[name])[0])-r['probabilities']['offset'])<1e-10;assert abs(float(apply_offset([raw],dict(offset=guards[name]['effective_offset']))[0])-r['probabilities']['guarded'])<1e-10;probchecks+=1
                for p,m in summary[work][view][name].items():
                    q=np.array([r['probabilities'][p] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);a=q>.5;assert m['correct']==int((a==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert m['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));assert m['confusion']==dict(ADP_as_ADP=int((~y&~a).sum()),ADP_as_CCONJ=int((~y&a).sum()),CCONJ_as_ADP=int((y&~a).sum()),CCONJ_as_CCONJ=int((y&a).sum()));metricchecks+=1
        for name,pp in contrasts[work].items():
            for p,c in pp.items():
                a=summary[work]['original'][name][p];null=[summary[work]['word'+str(seed)][name][p] for seed in NULL_SEEDS];assert c['actual']==a;assert abs(c['null_mean_auc']-np.mean([r['auc'] for r in null]))<1e-12;assert c['null_max_auc']==max(r['auc'] for r in null);assert c['null_auc_at_least_actual']==sum(r['auc']>=a['auc'] for r in null)
        print('audited',work,flush=True)
    diagnostics={}
    for work,views in pred.items():
        rows=views['original']['joint'];m=summary[work]['original']['joint']['raw'];diagnostics[work]=dict(wrong_types=[r['type'] for r in rows if (r['probabilities']['raw']>.5)!=(anchors[r['type']]=='CCONJ')],type_accuracy=m['accuracy'],balanced_accuracy=(m['confusion']['ADP_as_ADP']/sum(anchors[r['type']]=='ADP' for r in rows)+m['confusion']['CCONJ_as_CCONJ']/sum(anchors[r['type']]=='CCONJ' for r in rows))/2)
    save(OUT/'diagnostic.json',diagnostics);save(OUT/'audit.json',dict(input_hashes_verified=hashes,models_retrained=12,maximum_retrained_training_probability_difference=maxpdiff,oof_predictions_replayed=39,independent_target_feature_pairs=statchecks,model_probabilities_replayed=probchecks,metric_groups=metricchecks,all68_transforms_and_domain_guards_verified=True,strict_type_exclusion_checked=True));print(load(OUT/'audit.json'));print(diagnostics)
if __name__=='__main__':run()
