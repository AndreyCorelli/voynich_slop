"""Joint two-scalar anchor-free classes, with matched controls and domain guard."""
from benchmarks.grammar_context_roles_iteration141 import *
import itertools
OUT=ROOT/'iteration142';CONFIGS={'corrected':['corrected'],'roles':['role_similarity'],'joint':['corrected','role_similarity']}
BOUNDS={'corrected':[-1.,1.],'role_similarity':[0.,1.]}

def fit_vector(features,train,lookup,anchors,columns):
    raw=np.array([[features[lookup[w]][c] for c in columns] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([int(anchors[w]=='CCONJ') for w in train]);counts=np.bincount(y,minlength=2);weight=np.array([1/(2*counts[c]) for c in y]);r=minimize(weighted_objective,np.zeros(x.shape[1]*2),args=(x,y,weight),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),weights=r.x.reshape(x.shape[1],2).tolist(),loss=float(r.fun),training=train)

def predict_vector(f,m):
    z=(np.array([f[c] for c in m['columns']])-np.array(m['mean']))/np.array(m['scale']);return float(softmax(np.r_[1.,z]@np.array(m['weights']))[1])

def domain(m,offset):
    w=np.array(m['weights']);scores=[]
    for point in itertools.product(*(BOUNDS[c] for c in m['columns'])):
        z=(np.array(point)-np.array(m['mean']))/np.array(m['scale']);scores.append(float(np.r_[1.,z]@(w[:,1]-w[:,0])+offset))
    return dict(min_logit=min(scores),max_logit=max(scores),both_classes_possible=min(scores)<0<max(scores))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration141/verification-manifest.json',ROOT/'iteration141/training-statistics.json',ROOT/'iteration141/statistics.json',ROOT/'iteration141/transforms.json',ROOT/'iteration141/contrasts.json',ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration138/four-text-summary.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SmallSOURCEONLY jointclassifier: PRIMARYjointRAW(bias+2scalarscorrectedoverlap/rolecosine), matchedsinglefeaturecontrolsRAW, secondaryunconditional13OOFoffset andGUARDEDoffset forALL3arms. Same13types/116folds/classbalancedL2/optimizer, trainfoldstandardization, strict16targetlabelholdout. TrainALLfeaturesonSAMEconcatenatedfitstream(no sentenceboundaries); correctedcontrolrecomputed so comparisonsnotconfoundedbyoldsentence-awaretrainstats. Roletrainingcached141. Fit3OOF+finalperconfig, source13OOFbalancedoffset. DomaincheckBEFOREtargetload: evaluatecalibratedlogit at cornerscorrected[-1,1],role[0,1]; ifnotbothclassespossible rejectoffset/set0. Thisnecessarynotsufficient checkmayallowtargetoneclass; neveruse targetclasscounts. Freezeallmodels/offsets/guardsbeforetargetfeatures. 4exactfullstreams, allpresenttypes/occ5metadata/referencecaveats unchanged; reuse141rolefeatures/nulltransforms, recomputecorrectedonexactSAME68streams. Allchoices fixed no authorpickedarm/shift. FreezeALLpredictionsBEFOREmodalreferences/metrics. Compareaccuracy/NLL/AUCvsMATCHEDsinglefeatures andnulls; retain old138/141 ashistorynotmatchedfit. Rawprimarynotposthocfallback. No PP/newannotations/reserve/sealedworks/lexicalnuclei/default; candidatecatalogue/normalization privileges remain.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];wanted={lookup[w] for w in train};overlap=statistics([dict(tokens=[dict(id=i) for i in ids])],wanted);roles=load(ROOT/'iteration141/training-statistics.json');features={i:dict(corrected=overlap[i]['corrected'],role_similarity=roles[i]['role_similarity']) for i in wanted};models={};oof={};cal={};guards={}
    for name,columns in CONFIGS.items():
        models[name]={};oof[name]={}
        for fold in range(3):
            held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];m=fit_vector(features,tr,lookup,anchors,columns);models[name][str(fold)]=m;oof[name].update({w:predict_vector(features[lookup[w]],m) for w in held})
        models[name]['final']=fit_vector(features,train,lookup,anchors,columns);cal[name]=fit_offset([oof[name][w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);d=domain(models[name]['final'],cal[name]['offset']);guards[name]=dict(raw_domain=domain(models[name]['final'],0.),calibrated_domain=d,offset_accepted=d['both_classes_possible'],effective_offset=cal[name]['offset'] if d['both_classes_possible'] else 0.)
    for n,x in [('training-features',features),('models',models),('oof-probabilities',oof),('calibrators',cal),('guards',guards)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['training-features','models','oof-probabilities','calibrators','guards']}));print('GUARDS',guards,flush=True);streams,lookups=streams_and_lookups();transforms=load(ROOT/'iteration141/transforms.json');roledata=load(ROOT/'iteration141/statistics.json');targetfeatures={};predictions={}
    for work,seq in streams.items():
        targetfeatures[work]={};predictions[work]={};lookup=lookups[work]
        for view,ix in transforms[work].items():
            stream=seq if ix is None else [seq[i] for i in ix];st=statistics([dict(tokens=[dict(id=i) for i in stream])],set(lookup.values()));features={i:dict(n=st[i]['n'],corrected=st[i]['corrected'],role_similarity=roledata[work][view][i]['role_similarity']) for i in st};targetfeatures[work][view]=features;predictions[work][view]={}
            for name in CONFIGS:
                rows=[]
                for word,i in sorted(lookup.items()):
                    if i not in features:continue
                    raw=predict_vector(features[i],models[name]['final']);rows.append(dict(type=word,opaque=i,n=features[i]['n'],sentences=1,supported=features[i]['n']>=5,probabilities=dict(raw=raw,offset=float(apply_offset([raw],cal[name])[0]),guarded=float(apply_offset([raw],dict(offset=guards[name]['effective_offset']))[0]),prior=.5)))
                predictions[work][view][name]=rows
        print('predicted',work,flush=True)
    save(OUT/'target-features.json',targetfeatures);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['target-features.json','predictions.json']}));summary={};contrasts={}
    for work,views in predictions.items():
        summary[work]={view:{name:{p:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rr],p) for p in ['raw','offset','guarded','prior']} for name,rr in configs.items()} for view,configs in views.items()};contrasts[work]={}
        for name in CONFIGS:
            contrasts[work][name]={}
            for p in ['raw','offset','guarded']:
                actual=summary[work]['original'][name][p];null=[summary[work]['word'+str(seed)][name][p] for seed in NULL_SEEDS];contrasts[work][name][p]=dict(actual=actual,null_mean_auc=float(np.mean([r['auc'] for r in null])),null_max_auc=max(r['auc'] for r in null),null_auc_at_least_actual=sum(r['auc']>=actual['auc'] for r in null))
        print('RESULT',work,{n:{p:(m['correct'],m['auc'],m['nll']) for p,m in summary[work]['original'][n].items()} for n in CONFIGS},flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
