"""Full factorial oracle attribution of four class mistakes to PP membership."""
from benchmarks.grammar_class_pp_utility_iteration120 import *
import itertools
OUT=ROOT/'iteration121';PREVIOUS=ROOT/'iteration120'


def factorial_attribution(values,words):
    n=len(words);full=(1<<n)-1;contributions={}
    for j,w in enumerate(words):
        terms=[]
        for mask in range(full+1):
            if mask&(1<<j):continue
            k=mask.bit_count();weight=math.factorial(k)*math.factorial(n-k-1)/math.factorial(n);terms.append(weight*(values[mask|(1<<j)]-values[mask]))
        contributions[w]=sum(terms)
    return dict(total=values[full]-values[0],shapley=contributions,single_correction={w:values[1<<j]-values[0] for j,w in enumerate(words)},correction_last={w:values[full]-values[full^(1<<j)] for j,w in enumerate(words)},base_pair_interactions={a+'+'+b:values[(1<<j)|(1<<k)]-values[1<<j]-values[1<<k]+values[0] for j,a in enumerate(words) for k,b in enumerate(words) if j<k})


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),PREVIOUS/'verification-manifest.json',PREVIOUS/'assignments.json',PREVIOUS/'cohorts.json',PREVIOUS/'settings.json',PREVIOUS/'public-predicted.json',PREVIOUS/'public-oracle.json',PREVIOUS/'scores-predicted.json',PREVIOUS/'scores-oracle.json',PREVIOUS/'evaluation.json',BASE/'models.json',BASE/'predictions.json',ROOT/'iteration89/models.json',ROOT/'iteration118/predictions.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY ORACLE diagnostic, NOTnewpredictor/restorationpolicy. Exact120770sentences/9956positions, same16nameshiddenallarms/remaininganchors/PPmodels/cuts/cohorts. DeriveALLmistakenclasses by120predicted!=oracle assignments, assertfour source118errorsc/per/sine/uel; notselectedfromPPoutcomes. EvaluateALL16subsets ofcorrectingthoseassignments tosourceMAPreference, no droppinginteractions/nonmonotoniclosses. Everyassignmenttypeconsistent globally; IDs/words/positions unchanged; namesNoneinALLmasks. Freezefactorial assignmentsBEFOREnewinference. Reuse120baseline/fulloracle scorevectorsONLYexactmatchingviews, recomputeother14×2PPmodelvectors; nofit/thresholdchanges. Primaryoriginal.80, ALL120secondarysettings unchanged. FreezeALLscoresBEFOREmetrics. ReporteachmaskTP/FP/precision/recall/F1 andgrossnewTP/newFP/lostTP/removedFP frompredicted forALLfixedcohorts; reportprimary90percentcrossings asoracle-only, NEVERchooseword-specificcorrectionpolicy. Attribute netTPgain/FPremoved/F1/precision withsinglecorrection,lastcorrection,exact4factorShapley(allbackgroundweightedmarginals)andbasepairinteractions; ShapleyallocationdescriptiveNOTgeneralcausalimportance. Independent24permutationattributioncheck. Goldclassinformation isprivileged, newsourcePPscoresdevelopmentonly. No authors/newannotation/reserve/sealedtest/nuclei/defaultchange; preserve120conditionalstructuralbenefitandfailedprimaryguard.'))
    old=load(PREVIOUS/'assignments.json');pred=old['predicted'];oracle=old['oracle'];lookup={r['opaque']:r['type'] for r in load(ROOT/'iteration118/predictions.json')['full']['rows']};errors=sorted([lookup[i] for i in pred if pred[i]!=oracle[i]]);assert errors==['c','per','sine','uel'];opaque={w:i for i,w in lookup.items()};public=load(PREVIOUS/'public-predicted.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&reserved;views={};assignments={};full=(1<<len(errors))-1
    for mask in range(full+1):
        tags=dict(pred);corrected=[w for j,w in enumerate(errors) if mask&(1<<j)]
        for w in corrected:tags[opaque[w]]=oracle[opaque[w]]
        view=inject(public,set(pred),tags);assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in pred);views[mask]=view;assignments[str(mask)]=dict(corrected=corrected,tags=tags);save(OUT/('public-'+str(mask)+'.json'),view)
    assert views[0]==public and views[full]==load(PREVIOUS/'public-oracle.json');save(OUT/'factorial-assignments.json',dict(errors=errors,masks=assignments));save(OUT/'input-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'factorial-assignments.json']+list(OUT.glob('public-*.json'))}))
    models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];assert [(s['sent_id'],i) for s in public for i,t in enumerate(s['tokens'])]==[(r['sid'],r['index']) for r in labels];scores={};provenance={}
    for mask,view in views.items():
        previous=PREVIOUS/('scores-'+('predicted' if mask==0 else 'oracle')+'.json') if mask in [0,full] else None
        if previous:scores[mask]=load(previous);provenance[str(mask)]=str(previous)
        else:scores[mask]={a:[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),m)] for a,m in models.items()};provenance[str(mask)]='new'
        save(OUT/('scores-'+str(mask)+'.json'),scores[mask]);print('inferred mask',mask,assignments[str(mask)]['corrected'],flush=True)
    save(OUT/'cache-provenance.json',provenance);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'cache-provenance.json']+list(OUT.glob('scores-*.json'))}));cohorts=load(PREVIOUS/'cohorts.json');settings=load(PREVIOUS/'settings.json');evaluation={};attributions={}
    for mask,by_model in scores.items():
        evaluation[str(mask)]={}
        for model,cuts in settings.items():
            evaluation[str(mask)][model]={policy:{name:dict(metrics=confusion(labels,by_model[model],cut,indices),changes_from_predicted=changes(labels,scores[0][model],by_model[model],cut,indices)) for name,indices in cohorts.items()} for policy,cut in cuts.items()}
    for model,cuts in settings.items():
        attributions[model]={}
        for policy in cuts:
            attributions[model][policy]={}
            for name in cohorts:
                entries=[evaluation[str(mask)][model][policy][name]['metrics'] for mask in range(full+1)];attributions[model][policy][name]={metric:factorial_attribution([float(e[metric]) if e[metric] is not None else 0. for e in entries],errors) for metric in ['tp','fp','f1','precision']}
    save(OUT/'evaluation.json',evaluation);save(OUT/'attributions.json',attributions);safe=[dict(mask=mask,corrected=assignments[str(mask)]['corrected'],metrics=evaluation[str(mask)]['original']['fixed80']['all']['metrics']) for mask in range(full+1) if evaluation[str(mask)]['original']['fixed80']['all']['metrics']['precision']>=.9];save(OUT/'oracle-precision-crossings.json',dict(diagnostic_only=True,passing=safe));print('PRIMARY',[(mask,assignments[str(mask)]['corrected'],evaluation[str(mask)]['original']['fixed80']['all']['metrics']) for mask in range(full+1)],flush=True);print('ATTRIBUTIONS',attributions['original']['fixed80']['all'],flush=True)
if __name__=='__main__':run()
