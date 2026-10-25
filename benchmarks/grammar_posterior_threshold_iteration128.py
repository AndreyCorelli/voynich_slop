"""Source-only exact PP threshold frontier for frozen posterior scores."""
from benchmarks.grammar_uncertain_pp_iteration127 import *
OUT=ROOT/'iteration128';PREVIOUS=ROOT/'iteration127'

def frontier(scores,labels):
    order=sorted(range(len(scores)),key=lambda i:(-scores[i],i));tp=fp=0;result=[dict(threshold=1.,tp=0,fp=0,precision=None)]
    for j,i in enumerate(order):
        tp+=bool(labels[i]['labels']['pp']);fp+=not labels[i]['labels']['pp']
        if j+1==len(order) or scores[order[j+1]]!=scores[i]:result.append(dict(threshold=scores[i],tp=tp,fp=fp,precision=tp/(tp+fp)))
    return sorted(result,key=lambda r:r['threshold'])

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),PREVIOUS/'verification-manifest.json',PREVIOUS/'calibration/scores.json',BASE/'calibration-predictions.json',ROOT/'iteration120/cohorts.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY posterior score-scale diagnostic: exact127calposteriorvector, no model/classposterior/drawcount/mixturechange. Enumerate ALLattainedcalPPscorethresholds and1(noselections), inclusive>=; tiegroupstogether. Sameprimary90%precision and>=ceil(.8*127hardcalTP310)=248TP. MaxTP,minFP,highestcut;OFFifnone. Report completefrontier, maximumTPat90%,bestprecisionatrequiredcoverage, allcohorts ifselected. Freezechosenpolicy BEFOREtestscoreloading. IfOFF doNOTload/scoretestvectorsororaclethreshold, preserve127OFF; report onlycalceiling and neverdeploydiagnosticbestcut. Ifqualified applyONLYfrozencut to127testposteriorvector, fixed120cohorts; comparehard.80/unknown.80/old120.80, require90precision+>=max(188,ceil(.8*244))=196TPtest. No guardrelaxation/author/newannotations/reserve/sealedlexicaltest/defaultadoption/nuclei;developmentreuse notindependentvalidation.'))
    labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'calibration-predictions.json')];scores=load(PREVIOUS/'calibration/scores.json');baseline=confusion(labels,scores['hard'],.8,list(range(len(labels))));minimum=math.ceil(.8*baseline['tp']);assert minimum==248;curve=frontier(scores['posterior'],labels)
    for r in curve:r['qualified']=r['tp']>=minimum and 10*r['tp']>=9*(r['tp']+r['fp'])
    good=[r for r in curve if r['qualified']];chosen=max(good,key=lambda r:(r['tp'],-r['fp'],r['threshold'])) if good else dict(threshold=None,qualified=False);precision_rows=[r for r in curve if r['tp']+r['fp'] and 10*r['tp']>=9*(r['tp']+r['fp'])];coverage_rows=[r for r in curve if r['tp']>=minimum];summary=dict(hard_calibration_baseline=baseline,minimum_required_tp=minimum,settings=len(curve),qualified_settings=len(good),maximum_tp_at90precision=max(precision_rows,key=lambda r:(r['tp'],-r['fp'],r['threshold'])) if precision_rows else None,best_precision_with_required_coverage=max(coverage_rows,key=lambda r:(r['precision'],r['tp'],r['threshold'])))
    save(OUT/'calibration-frontier.json',curve);save(OUT/'chosen.json',chosen);save(OUT/'summary.json',summary);save(OUT/'policy-freeze.json',dict(inputs={str(OUT/name):digest(OUT/name) for name in ['calibration-frontier.json','chosen.json','summary.json']}));print('SUMMARY',summary,'CHOSEN',chosen,flush=True)
    if not chosen['qualified']:
        save(OUT/'result.json',dict(calibration_qualified=False,test_scores_loaded=False,new_policy_adopted=False,reason='No source threshold meets unchanged precision and coverage requirements.'));return
    labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];scores=load(PREVIOUS/'test/scores.json');cohorts=load(ROOT/'iteration120/cohorts.json');old=load(ROOT/'iteration120/scores-predicted.json')['original'];cut=chosen['threshold'];evaluation={c:dict(metrics=confusion(labels,scores['posterior'],cut,ii),changes_from_hard={k:0 for k in []}) for c,ii in cohorts.items()}
    for c,ii in cohorts.items():
        for name,base in [('hard',scores['hard']),('unknown',scores['unknown']),('previous',old)]:
            # Compare decisions at different, source-fixed thresholds.
            a=np.array(scores['posterior'])[ii]>=cut;b=np.array(base)[ii]>=.8;y=np.array([labels[i]['labels']['pp'] for i in ii],bool);evaluation[c]['changes_from_'+name]=dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()))
    save(OUT/'evaluation.json',evaluation);m=evaluation['all']['metrics'];save(OUT/'result.json',dict(calibration_qualified=True,test_scores_loaded=True,selected=m,passed=m['precision'] is not None and m['precision']>=.9 and m['tp']>=196,new_policy_adopted=False))
if __name__=='__main__':run()
