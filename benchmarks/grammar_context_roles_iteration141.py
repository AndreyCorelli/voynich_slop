"""One-scalar second-order neighbor-role classification with anchor-free inputs."""
from benchmarks.grammar_overlap_token_budget_iteration139 import *
from voynich_smt.opaque_context_roles import statistics as role_statistics
OUT=ROOT/'iteration141';NULL_SEEDS=list(range(14100,14116));FEATURE='role_similarity'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/opaque_context_roles.py'),Path('tests/test_opaque_context_roles.py'),ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration138/four-text-summary.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration139/verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='FreshANCHOR-FREEsecondorderrepresentation, ONESCALAR no highdimsupervisedbundle. ConcatenatewordIDs trainingfit2471andall4targetstreams, NOsentenceboundaries/names/tags. BuilddirectedadjacencycountB; L=row-normalizedBtranspose,R=row-normalizedB,eachwordroleQ=[L,R]. Forcandidatei leftrolemean=L_i Q,rightrolemean=R_i Q; FEATUREcosine(leftrolemean,rightrolemean), zeroifnormzero. Fullunlabeledwordgraph includesheldtypes butNOheldclasslabels. Source13noncataloguetypes/116folds strictall16targettraininglabel exclusion; fit2parameterbalancedlogistic andtrainfoldstandardization via135sameL2, 13OOFbalancedoffset, freezeBEFOREtargetstats. All13occurrences usedtoestimatestatistic, no occurrencecapbecauseonefeaturepertype. Testexact139full4streams, allpresent catalogue/supportocc5reportonly,c/que rawreferencecaveat retained. Frozen>.5cut, baseline135correctedfourtextfrom138 retained notrefit. 16globalcountpreservingwordnullsseeds14100..15eachtext, alltransformsfrozenbeforestats/predictions. Freezeallpredictionsbeforemodalclassreferences/metrics. Reportaccuracy/NLL/AUCvsfixedbaseline/priorandnulls, no authorpickedcutoff/graphnormalization/features. No newannotations/reserve/sealedworks/PP/nuclei/default. Treebank/rawnormalization+candidate-membershipprivileges remain. GraphcosinenotclaimedPOSuntiltested.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];stats=role_statistics(ids,{lookup[w] for w in train});models={};oof={}
    for fold in range(3):
        held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];models[str(fold)]=fit_scalar(stats,tr,lookup,anchors,FEATURE);oof.update({w:predict_scalar(stats[lookup[w]][FEATURE],models[str(fold)]) for w in held})
    models['final']=fit_scalar(stats,train,lookup,anchors,FEATURE);cal=fit_offset([oof[w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True)
    for n,x in [('training-statistics',stats),('models',models),('oof-probabilities',oof),('calibrator',cal)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['training-statistics','models','oof-probabilities','calibrator']}));streams,lookups=streams_and_lookups();transforms={w:{'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(seq)).tolist() for seed in NULL_SEEDS}} for w,seq in streams.items()};save(OUT/'transforms.json',transforms);save(OUT/'transform-freeze.json',dict(inputs={str(OUT/'transforms.json'):digest(OUT/'transforms.json')}));allstats={};pred={}
    for work,seq in streams.items():
        lookup=lookups[work];allstats[work]={};pred[work]={}
        for name,ix in transforms[work].items():
            stream=seq if ix is None else [seq[i] for i in ix];assert Counter(stream)==Counter(seq);st=role_statistics(stream,set(lookup.values()));allstats[work][name]=st;rows=[]
            for word,i in sorted(lookup.items()):
                if i not in st:continue
                raw=predict_scalar(st[i][FEATURE],models['final']);rows.append(dict(type=word,opaque=i,n=st[i]['n'],sentences=1,supported=st[i]['n']>=5,statistic=st[i][FEATURE],probabilities=dict(raw=raw,new=float(apply_offset([raw],cal)[0]),prior=.5)))
            pred[work][name]=rows
        print('predicted',work,flush=True)
    save(OUT/'statistics.json',allstats);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));summary={};contrasts={};baseline=load(ROOT/'iteration138/four-text-summary.json')
    for work,tt in pred.items():
        summary[work]={name:{p:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rr],p) for p in ['new','raw','prior']} for name,rr in tt.items()};actual=summary[work]['original']['new'];null=[summary[work]['word'+str(seed)]['new'] for seed in NULL_SEEDS];contrasts[work]=dict(actual=actual,old_overlap=baseline[work],null_mean={m:float(np.mean([r[m] for r in null])) for m in ['accuracy','nll','auc']},null_auc_range=[min(r['auc'] for r in null),max(r['auc'] for r in null)],null_auc_at_least_actual=sum(r['auc']>=actual['auc'] for r in null));print('RESULT',work,contrasts[work],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
