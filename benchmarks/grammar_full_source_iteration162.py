"""Full source function inventory: explicitly relaxed lexical-type holdout."""
from benchmarks.grammar_regularization_iteration153 import *
OUT=ROOT/'iteration162';STRENGTHS={'weak':.0005,'strong':.5}

def metrics_for(pp,labels):return metrics([dict(type=w,n=1,sentences=1,supported=True,probabilities=dict(raw=p),**{'class':labels[w]}) for w,p in pp.items()],'raw')

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration161/verification-manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration116/type-split.json',ROOT/'iteration93/types.json',ROOT/'iteration152/models.json',ROOT/'iteration152/oof.json',ROOT/'iteration153/models.json',ROOT/'iteration153/oof.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration150/selection.json',ROOT/'iteration85/anchor-budgets.json',Path('experiments/holdouts/grammar-construction-next.json'),Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Differentvalidationquestion: SOURCEFITonly allmodalADP/CCONJ types>=5occurrences (expected29,18ADP11CC), NOmodalpuritycutoff so old13retained; explicitlyALLOWS16previouslyexcludedcommonwordtypes fromsourceannotations, nottargetannotations. Sameanonymous2scalars/noidentityfeatures/independenttargetsalts. Authortransfer onall7alreadyinspectedfullstreams, supplied16candidatecatalogue unchanged, notstrictwordtypeholdout. Original13sourcefolds116preserved; added16 sortedSHA(fullsource162|word)withinclass roundrobin3, OOFall29 andsameold13subsetseparately, noequaldenominatorclaim. Fixedmonotonic2feature model primaryridge.0005 secondary.5, no selection/offsets/thresholdchanges. Fit3OOF+fullperstrength; all29trainingtypeomissions andall7frozen150focalsubsets sourcefeaturesrecomputedforall29. Comparestrict13frozen152/153matchedmodels; omittedadded16strictbaseline unchangedfullsincealreadyexcluded. Freezeeligibility/folds beforefeatures, allmodels beforetargetpredictions, allpredictions beforemodalmetrics. All7texts/arms/perturbations reportaccuracyNLLAUC nofavorableauthor/modelselection. Sourcefitsaltfit116, targetfeatures144differentIDs. No anchors/names at inference/newannotations/reserve/sealedworks/generalPOS/nuclei/defaultclaims.'))
    public,_,anchors,split,targets,_=training_inputs();old=split['training'];data=load(ROOT/'iteration44/annotations-truth.json');sids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(sids)&reserved;counts={}
    for sid in sids:
        for t in data[sid]['tokens']:counts.setdefault(t['word'],Counter())[t['pos']]+=1
    records={}
    for w,c in counts.items():
        tag,n=sorted(c.items(),key=lambda x:(-x[1],x[0]))[0];total=sum(c.values())
        if total>=5 and tag in ['ADP','CCONJ']:records[w]=dict(n=total,label=tag,purity=n/total)
    train=sorted(records);assert len(train)==29 and set(old)<=set(train) and set(targets)<=set(train);labels={w:r['label'] for w,r in records.items()};lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};folds=dict(split['oof_folds'])
    for tag in ['ADP','CCONJ']:
        added=sorted([w for w in train if w not in old and labels[w]==tag],key=lambda w:hashlib.sha256(('fullsource162|'+w).encode()).hexdigest());folds.update({w:k%3 for k,w in enumerate(added)})
    save(OUT/'eligibility.json',dict(records=records,training=train,old=old,folds=folds,lookup=lookup,previously_excluded_now_source_trained=targets));save(OUT/'eligibility-freeze.json',dict(inputs={str(OUT/'eligibility.json'):digest(OUT/'eligibility.json')}));ids=[t['id'] for s in public for t in s['tokens']];wanted=set(lookup.values());features={'full':features_for(ids,wanted)};sel=load(ROOT/'iteration150/selection.json')
    for mask,positions in sel['transforms'].items():
        seq=list(ids)
        for pos in positions:assert seq[pos]==lookup['siue'];seq[pos]=sel['fresh'][sel['positions'].index(pos)]
        features['motif/'+mask]=features_for(seq,wanted)
    models={};oof={};strict={};oldmodels={'weak':load(ROOT/'iteration152/models.json'),'strong':load(ROOT/'iteration153/models.json')}
    for strength_name,strength in STRENGTHS.items():
        models[strength_name]={};oof[strength_name]={};strict[strength_name]={}
        for fold in range(3):
            held=[w for w in train if folds[w]==fold];m=fit_strength(features['full'],[w for w in train if w not in held],lookup,labels,strength);models[strength_name]['oof'+str(fold)]=m;oof[strength_name].update({w:predict_vector(features['full'][lookup[w]],m) for w in held})
        models[strength_name]['full']=fit_strength(features['full'],train,lookup,labels,strength);strict[strength_name]['full']=oldmodels[strength_name]['full']
        for w in train:
            key='omit/'+w;models[strength_name][key]=fit_strength(features['full'],[t for t in train if t!=w],lookup,labels,strength);strict[strength_name][key]=oldmodels[strength_name][key] if w in old else oldmodels[strength_name]['full']
        for mask in range(1,8):
            key='motif/'+str(mask);models[strength_name][key]=fit_strength(features[key],train,lookup,labels,strength);strict[strength_name][key]=oldmodels[strength_name][key]
    for name,x in [('features',features),('models',models),('strict-models',strict),('oof',oof)]:save(OUT/(name+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['features','models','strict-models','oof']}));targetfeatures=load(ROOT/'iteration144/features.json');oldpred=load(ROOT/'iteration144/predictions.json');pred={}
    for key,configs in oldpred.items():
        if not key.endswith('/full'):continue
        work=key[:-5];pred[work]={}
        for strength_name,mm in models.items():
            pred[work][strength_name]={}
            for name,m in mm.items():
                if name.startswith('oof'):continue
                pred[work][strength_name][name]={arm:[dict(r,probabilities=dict(raw=predict_vector(targetfeatures[key][r['opaque']],model))) for r in configs['joint']] for arm,model in [('expanded',m),('strict13',strict[strength_name][name])]}
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary={w:{strength:{name:{arm:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for arm,rows in arms.items()} for name,arms in variants.items()} for strength,variants in strengths.items()} for w,strengths in pred.items()};save(OUT/'summary.json',summary);source={strength:{group:metrics_for({w:p for w,p in pp.items() if group=='all29' or w in old},labels) for group in ['all29','old13']} for strength,pp in oof.items()};save(OUT/'source-summary.json',source);print('SOURCE',source,flush=True)
    for w,ss in summary.items():print(w,{strength:{name:{arm:(r['correct'],r['n'],r['auc'],r['nll']) for arm,r in arms.items()} for name,arms in vv.items() if name in ['full','omit/siue','motif/2']} for strength,vv in ss.items()},flush=True)
if __name__=='__main__':run()
