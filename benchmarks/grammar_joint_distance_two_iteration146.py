"""One predeclared distance-two overlap addition to the frozen joint baseline."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
OUT=ROOT/'iteration146';COLUMNS=['corrected','role_similarity','distance_two'];SEEDS=list(range(14600,14616))

def distance_two(ids,wanted):
    # Parity subsequences preserve exactly the neighbors at distance two.
    return statistics([dict(tokens=[dict(id=i) for i in ids[k::2]]) for k in range(2)],wanted)

def augmented_features(ids,wanted):
    f=features_for(ids,wanted);d=distance_two(ids,wanted)
    for i in f:f[i]['distance_two']=d[i]['corrected']
    return f

def summarize(pred,anchors):
    return {w:{v:{name:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for name,rows in configs.items()} for v,configs in views.items()} for w,views in pred.items()}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_scalars_iteration142.py'),ROOT/'iteration142/models.json',ROOT/'iteration144/verification-manifest.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration143/streams.json',ROOT/'iteration143/selection.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration135/predictions.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ONE augmented class-balanced logistic model columns corrected,role_similarity,distance_two. Distance_two exact corrected left/right overlap at offset2; parity streams implement same pooled-neighbor hypergeometric expectation. Same13 non-target training types, same116 folds, fitfold standardization/L2/optimizer142; raw>.5 only, no offset/tuning/distance search. Fit3OOF+final before target loading. Baseline frozen142 jointRAW. Seven already inspected full streams, allpresent candidate types primary (not arbitrary POS); report all errors/counts/NLL/AUC and16 word-null seeds14600..15 for both models regardless outcome. Freeze transform indices before features, predictions before references. No author arm selection, annotations/reserve/sealedworks/PP/nuclei claims. Development diagnostic, targets already examined.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];f=augmented_features(ids,{lookup[w] for w in train});models={};oof={}
    for fold in range(3):
        held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];models[str(fold)]=fit_vector(f,tr,lookup,anchors,COLUMNS);oof.update({w:predict_vector(f[lookup[w]],models[str(fold)]) for w in held})
    models['final']=fit_vector(f,train,lookup,anchors,COLUMNS)
    for n,x in [('training-features',f),('models',models),('oof',oof)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['training-features','models','oof']}))
    streams,lookups=inputs();transforms={w:{'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(seq)).tolist() for seed in SEEDS}} for w,seq in streams.items()};save(OUT/'transforms.json',transforms);save(OUT/'transforms-freeze.json',dict(inputs={str(OUT/'transforms.json'):digest(OUT/'transforms.json')}));baseline=load(ROOT/'iteration142/models.json')['joint']['final'];features={};pred={}
    for w,seq in streams.items():
        features[w]={};pred[w]={}
        for view,ix in transforms[w].items():
            ids=seq if ix is None else [seq[j] for j in ix];f=augmented_features(ids,set(lookups[w].values()));features[w][view]=f;pred[w][view]={name:[dict(type=word,opaque=i,n=f[i]['n'],sentences=1,supported=f[i]['n']>=5,probabilities=dict(raw=predict_vector(f[i],m))) for word,i in sorted(lookups[w].items()) if i in f] for name,m in [('baseline',baseline),('augmented',models['final'])]}
        print('predicted',w,flush=True)
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));summary=summarize(pred,anchors);save(OUT/'summary.json',summary);contrasts={}
    for w,views in summary.items():
        contrasts[w]={}
        for name,m in views['original'].items():
            null=[views['word'+str(seed)][name]['auc'] for seed in SEEDS];contrasts[w][name]=dict(actual=m,null_max_auc=max(null),null_auc_at_least_actual=sum(a>=m['auc'] for a in null))
        print(w,contrasts[w],flush=True)
    save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
