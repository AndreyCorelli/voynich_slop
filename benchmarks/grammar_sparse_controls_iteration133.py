"""Type-shuffle and proximity controls for matched sparse grammatical utility."""
from benchmarks.grammar_sparse_training_iteration132 import *
OUT=ROOT/'iteration133';SEEDS=list(range(13300,13316))

def proximity(public,width):
    return [float(any(s['tokens'][j]['tag']=='ADP' for j in range(max(0,i-width),i))) for s in public for i,t in enumerate(s['tokens'])]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration132/verification-manifest.json',ROOT/'iteration132/predictions.json',ROOT/'iteration132/scores.json',ROOT/'iteration130/cohorts.json',ROOT/'iteration120/cohorts.json',BASE/'models.json',BASE/'predictions.json']+list((ROOT/'iteration132').glob('public-*.json'))+list(LABELS.values())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen1325anchor/model/.80all5contexts, source770 and4cachedauthorviews scoredoriginal100only. Arms actual132classes,unknown,allADP,allCCONJ,16typeconsistentpermutations seeds13300..13315(sortedopaqueIDs, permuteactualhardtags). Preserve typeclasscounts nottokenweightedclassmass; neverselectnullseed. Cachedactualscores reusedonlyexact132view. CompletePPmodel85inference eacharm, alltargetnameshidden. Simplecontrols left1/left2: selecttokenifANYADPtaginprevious1/2positionswithinSAMEsentence, noPOScohortfilter/wordidentity/labels, evaluateat.5sincebinaryrule. Controlscomputed forEVERYassignment inclnulls, samefixedcohorts120/130. Freezeassignments BEFOREnewPPscores, scores BEFOREmetrics. ReportALLnulls andmean/min/max F1/TP/FP, actualrankdescriptive (+1tailcount/17 descriptive NOTpvalue independenttexts). Report actualvsproximity grossgains/losses, actualclassPPvsnullPP fixedcut.80. No inferredgrammargainclaimifshuffles/proximityexplain it; preservepreviousconditionalcountswithcontrols. No fitting/threshold/budget/authorselection/newannotations/reserve/sealedlexicaltest/defaultchange/nuclei; correlatedreuseddevelopment/nulltypefrequencyconfound explicit.'))
    predictions=load(ROOT/'iteration132/predictions.json');publics={key:load(ROOT/'iteration132'/('public-'+key+'.json')) for key in predictions};assignments={}
    for key,rows in predictions.items():
        actual={r['opaque']:('CCONJ' if r['probabilities']['matched']>.5 else 'ADP') for r in rows};ids=sorted(actual);assignments[key]=dict(actual=actual,unknown={},all_ADP={i:'ADP' for i in ids},all_CCONJ={i:'CCONJ' for i in ids})
        for seed in SEEDS:assignments[key]['shuffle'+str(seed)]=dict(zip(ids,np.random.default_rng(seed).permutation([actual[i] for i in ids]).tolist()))
    save(OUT/'assignments.json',assignments);save(OUT/'input-freeze.json',dict(inputs={str(OUT/'assignments.json'):digest(OUT/'assignments.json')}));labels={'source':load(BASE/'predictions.json')};labels.update({a+'-'+v:load(p) for a,p in LABELS.items() for v in ['base','expanded']});model=load(BASE/'models.json');old=load(ROOT/'iteration132/scores.json');scores={};mass={}
    for key,arms in assignments.items():
        scores[key]={};mass[key]={};targets={r['opaque'] for r in predictions[key]}
        for arm,tags in arms.items():
            view=inject(publics[key],targets,tags)
            if arm=='actual':assert view==publics[key];pp=old[key]
            else:pp=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels[key]),model)]
            scores[key][arm]=dict(pp=pp,left1=proximity(view,1),left2=proximity(view,2));mass[key][arm]=dict(type_counts=dict(Counter(tags.values())),target_token_counts=dict(Counter(t['tag'] for s in view for t in s['tokens'] if t['id'] in targets)))
        print('inferred',key,flush=True)
    save(OUT/'scores.json',scores);save(OUT/'class-mass.json',mass);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['scores.json','class-mass.json']}));cohorts={'source':load(ROOT/'iteration120/cohorts.json')};cohorts.update({a+'-'+v:load(ROOT/'iteration130/cohorts.json')[a] for a in INPUTS for v in ['base','expanded']});evaluation={};summary={};comparisons={}
    for key,arms in scores.items():
        evaluation[key]={arm:{method:{co:confusion(labels[key],q,.8 if method=='pp' else .5,ii) for co,ii in cohorts[key].items()} for method,q in methods.items()} for arm,methods in arms.items()};summary[key]={};comparisons[key]={}
        for co,ii in cohorts[key].items():
            actual=evaluation[key]['actual']['pp'][co];null=[evaluation[key]['shuffle'+str(seed)]['pp'][co] for seed in SEEDS];summary[key][co]=dict(actual=actual,null_count=len(null),null_mean={k:float(np.mean([r[k] for r in null])) for k in ['tp','fp','f1']},null_min_f1=min(r['f1'] for r in null),null_max_f1=max(r['f1'] for r in null),null_f1_at_least_actual=sum(r['f1']>=actual['f1'] for r in null),descriptive_rank_fraction=(1+sum(r['f1']>=actual['f1'] for r in null))/(1+len(null)));comparisons[key][co]={}
            for method in ['left1','left2']:
                a=np.array(arms['actual']['pp'])[ii]>=.8;b=np.array(arms['actual'][method])[ii]>=.5;y=np.array([labels[key][i]['labels']['pp'] for i in ii],bool);comparisons[key][co][method]=dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()))
        print('RESULT',key,summary[key]['all'],'PROX',[(m,evaluation[key]['actual'][m]['all']) for m in ['left1','left2']],flush=True)
    save(OUT/'evaluation.json',evaluation);save(OUT/'shuffle-summary.json',summary);save(OUT/'proximity-comparisons.json',comparisons)
if __name__=='__main__':run()
