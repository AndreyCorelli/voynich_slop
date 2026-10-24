"""Oracle-only feasibility of a global ADP gate on fixed source test inputs."""
from benchmarks.grammar_adp_confidence_iteration122 import *
OUT=ROOT/'iteration123';PREVIOUS=ROOT/'iteration120';CAL=ROOT/'iteration122'


def tagkey(tags):return json.dumps(tags,sort_keys=True)


def qualifies(m,baseline):return m['precision'] is not None and m['precision']>=.9 and m['tp']>=math.ceil(.8*baseline['tp'])


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/adp_confidence_gate.py'),CAL/'verification-manifest.json',CAL/'calibration-probabilities.json',CAL/'calibration-curve.json',ROOT/'iteration118/public.json',ROOT/'iteration118/predictions.json',PREVIOUS/'scores-predicted.json',PREVIOUS/'scores-unknown.json',PREVIOUS/'public-predicted.json',PREVIOUS/'cohorts.json',PREVIOUS/'settings.json',BASE/'models.json',BASE/'predictions.json',ROOT/'iteration89/models.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ORACLE-ONLY fixedtest feasibility, NEVERsourcecalibratedpolicy/deployablethreshold. Motivated122calibration93.67buttest87.36/noabstention. Exact120test770/9956, 118fixedclassprobabilities, sameADPconfidencegate(Noneforwithheld=>tagX,CCunchanged), all16nameshidden, fixedPPmodels85/89/cuts/cohorts. Enumerate0,1andALLattainabletestADPconfidences, inclusive>=; cacheduplicateassignmentstates, reuse120baselineonlyexactviewmatch. Freezegrid/assignmentsBEFOREnewPPscores; freezepredictionsBEFOREoraclePPmetrics. PRIMARYtestfeasibleiff85.80precision>=.90 ANDTP>=80percentungated235(>=188). ReportEVERYcut, allcohorts/secondarysettings/grosslosses; bestpassing onlyprivilegeddiagnostic,maxTP/minFP/highestcut. Ifnone showbestprecisionamongcoveragequalifiedcuts,andcoverageofbestprecision; no guardrelaxation. AdditionalPREDECLAREDjointfeasibility: unioncalibration+testconfidencebreakpoints, reuse122calibrationstatePPmetricsandnewteststatePPmetrics, checkwhetherSINGLEabsoluteconfidencecutmeets90/80onBOTHblocks; nofreshcalPPinference. Gridstates exact byassignmentpattern, reportintervals ratherthanarbitraryrepresentativepointalone. No fitting/newclassprobabilities/PPthresholdchanges/newannotations/authors/reserve/sealedtest/defaultadoption/nuclei claim. Testlabelsoveruseddevelopmentoracle, notvalidation; neverdeploywinningtestcut orlistwordexceptions. Preserve122failedsourcepolicyand120structuralutility.'))
    public=load(ROOT/'iteration118/public.json');pred=load(ROOT/'iteration118/predictions.json')['full']['rows'];prob={r['opaque']:r['probabilities']['balanced13'] for r in pred};names={r['opaque']:r['type'] for r in pred};cuts=sorted({0.,1.}|{1-p for p in prob.values() if p<=.5});assignments=[];views={}
    for cut in cuts:
        tags=adp_assignments(prob,cut);sig=hashlib.sha256(tagkey(tags).encode()).hexdigest();views[sig]=inject(public,set(prob),tags);assignments.append(dict(threshold=cut,assignment=sig,tags=tags,withheld=sorted(names[i] for i in prob if i not in tags),accepted_ADP=sum(t=='ADP' for t in tags.values())))
    save(OUT/'grid-assignments.json',assignments)
    for sig,p in views.items():save(OUT/('public-'+sig+'.json'),p)
    save(OUT/'input-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'grid-assignments.json']+list(OUT.glob('public-*.json'))}));models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];assert [(s['sent_id'],i) for s in public for i,t in enumerate(s['tokens'])]==[(r['sid'],r['index']) for r in labels];scores={};provenance={};baseline=load(PREVIOUS/'public-predicted.json')
    for sig,p in views.items():
        if p==baseline:scores[sig]=load(PREVIOUS/'scores-predicted.json');provenance[sig]=str(PREVIOUS/'scores-predicted.json')
        else:scores[sig]={name:[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(p,labels),m)] for name,m in models.items()};provenance[sig]='new'
        save(OUT/('scores-'+sig+'.json'),scores[sig]);print('inferred',sig[:8],flush=True)
    save(OUT/'cache-provenance.json',provenance);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'cache-provenance.json']+list(OUT.glob('scores-*.json'))}));settings=load(PREVIOUS/'settings.json');cohorts=load(PREVIOUS/'cohorts.json');ungated=load(PREVIOUS/'scores-predicted.json');evaluation={};curve=[]
    for r in assignments:
        sig=r['assignment']
        if sig not in evaluation:evaluation[sig]={name:{policy:{c:dict(metrics=confusion(labels,scores[sig][name],cut,ii),changes_from_ungated=changes(labels,ungated[name],scores[sig][name],cut,ii)) for c,ii in cohorts.items()} for policy,cut in policies.items()} for name,policies in settings.items()}
        curve.append(dict(r,metrics=evaluation[sig]['original']['fixed80']['all']['metrics'],unmapped_metrics=evaluation[sig]['original']['fixed80']['original_unmapped']['metrics']))
    base=curve[0]['metrics'];passing=[]
    for r in curve:
        r['oracle_qualifies']=qualifies(r['metrics'],base)
        if r['oracle_qualifies']:passing.append(r)
    best=max(passing,key=lambda r:(r['metrics']['tp'],-r['metrics']['fp'],r['threshold'])) if passing else None;calcurve=load(CAL/'calibration-curve.json');calprob=load(CAL/'calibration-probabilities.json');calstates={tagkey(r['tags']):r for r in calcurve};teststates={tagkey(r['tags']):r for r in curve};union=sorted({0.,1.}|{1-p for p in prob.values() if p<=.5}|{1-p for p in calprob.values() if p<=.5});joint=[];calbase=next(r['metrics'] for r in calcurve if r['threshold']==0.)
    for j,cut in enumerate(union):
        ct=calstates[tagkey(adp_assignments(calprob,cut))];tt=teststates[tagkey(adp_assignments(prob,cut))];calok=qualifies(ct['metrics'],calbase);testok=qualifies(tt['metrics'],base);joint.append(dict(threshold=cut,interval_lower_exclusive=None if j==0 else union[j-1],interval_upper_inclusive=cut,calibration_metrics=ct['metrics'],test_metrics=tt['metrics'],calibration_qualifies=calok,test_qualifies=testok,jointly_qualifies=calok and testok,test_withheld=tt['withheld']))
    summary=dict(oracle_only=True,test_baseline=base,test_cutoff_count=len(curve),test_assignment_states=len(views),test_feasible=bool(passing),best_passing_test=best,any_jointly_feasible=any(r['jointly_qualifies'] for r in joint),joint_settings=len(joint),joint_passing=sum(r['jointly_qualifies'] for r in joint),best_precision_with_test_coverage=max((r for r in curve if r['metrics']['tp']>=math.ceil(.8*base['tp'])),key=lambda r:(r['metrics']['precision'] or 0.,r['metrics']['tp'])))
    save(OUT/'evaluation.json',evaluation);save(OUT/'oracle-test-curve.json',curve);save(OUT/'joint-feasibility.json',joint);save(OUT/'oracle-summary.json',summary);print('SUMMARY',summary,flush=True);print('CURVE',[(r['threshold'],r['withheld'],r['metrics']['tp'],r['metrics']['fp'],r['oracle_qualifies']) for r in curve],flush=True)
if __name__=='__main__':run()
