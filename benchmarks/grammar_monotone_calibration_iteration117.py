"""Scalar monotone calibration, frozen116 split, and calibration-only ceiling."""
from benchmarks.grammar_endpoint_reliability_iteration116 import *
from voynich_smt.monotone_class_calibration import fit_offset,apply_offset,logits
OUT=ROOT/'iteration117';PREVIOUS=ROOT/'iteration116'


def annotate(rows,raw,models):
    probabilities={view:{a:dict(zip(pp['raw'],apply_offset(list(pp['raw'].values()),m).tolist())) for a,m in models.items()} for view,pp in raw.items()}
    return [dict(r,margins={a:pair_margin(r['base_pair'],r['proposed'],probabilities[r['physical_view']][a]) for a in models}) for r in rows],probabilities


def calibration_ceiling(rows,raw):
    # Any monotone map plus a common weaker-endpoint margin cutoff induces
    # one lower raw-score threshold for desired CCONJ, one upper for ADP.
    active=[r for r in rows if r['base_pair'] is not None];x=[];y=[]
    for r in active:
        pair=r['base_pair'];pp=raw[r['physical_view']]['raw'];x.append(next(float(logits([pp[i]])[0]) for i in pair if r['proposed'][i]=='ADP'));y.append(next(float(logits([pp[i]])[0]) for i in pair if r['proposed'][i]=='CCONJ'))
    x=np.asarray(x);y=np.asarray(y);hit=np.array([r['base_pair']==r['reference']['pair'] for r in active]);error=np.array([r['reference']['error'] for r in active]);unsupported=np.array([r['reference']['error'] and not r['reference']['supported'] for r in active]);regimes=np.array([r['regime'] for r in active]);best=None;qualifying=0;checked=0;baseline=evaluate(rows,'base',None)
    for low in sorted(set(x)|{float('-inf'),float('inf')}):
        for high in sorted(set(y)|{float('-inf'),float('inf')}):
            called=(x>=low)&(y<=high);safe=True;stats={}
            for g in ['complete','omission','literal']:
                mask=called&(regimes==g);hits=int((mask&hit).sum());wrong=int((mask&~hit).sum());bad=int((mask&~hit&unsupported).sum());clean=int((mask&~hit&~error).sum());safe &= bad==0 and clean==0 and (not mask.any() or hits/int(mask.sum())>=.9);stats[g]=dict(hit=hits,wrong=wrong,calls=int(mask.sum()),distinct_hits=len({r['case'] for r,m,h in zip(active,mask,hit) if m and h}))
            checked+=1
            if not safe:continue
            row=dict(lower_desired_CCONJ=float(low),upper_desired_ADP=float(high),stats=stats)
            if best is None or (stats['complete']['hit'],sum(v['hit'] for v in stats.values()),-sum(v['wrong'] for v in stats.values()))>(best['stats']['complete']['hit'],sum(v['hit'] for v in best['stats'].values()),-sum(v['wrong'] for v in best['stats'].values())):best=row
            ok=all(v['calls'] and v['hit']>=math.ceil(.8*baseline[g]['hit']) for g,v in stats.items()) and stats['complete']['hit']>=4 and stats['omission']['distinct_hits']>=4 and stats['literal']['distinct_hits']>=4;qualifying+=ok
    return dict(calibration_only_oracle=True,grid_settings=checked,qualifying_settings=qualifying,best_safe=best)


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/monotone_class_calibration.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'type-split.json',PREVIOUS/'oof-profiles.json',PREVIOUS/'calibration-cases.json',PREVIOUS/'calibration-probabilities.json',ROOT/'iteration85/anchor-budgets.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY developmental reuse116exact13train/cal8/eval8 split, frozenclassmodel/profiles and8candidatebase111pairbank. No new contextualclassifier/pairranking/samples/author/PP/annotations/reserve/sealedtest. Replace116sixfeaturecalibratorwithONEscalarintercept onrawmeanlogits, fixedslope1, convexNLLbisection[-40,40]160steps. Primaryoffset13natural andclassbalanced13OOF, secondaryvolume-matchedoffset8fitONLYcal8fullprofiles/labels; lastarmreusescal8forprobabilitycalibrationANDveto tuning, disclosed; eval8labelsneverfit. Eachinterceptsameforalltypes/views, preservesrawranking. Beforeeval loading freezeall3maps and perarm116sameguardscutoffs(allattainablecalmargins+0+-inf). Eachcomplete/omission/literal>=90percentprecision,zeroclean/unsupportedwrong,>=80percentbasecorrect eachregime,>=4completecorrect and>=4distincthits negativepools; maximizecompletehits,totalhits,minwrong,highercutoff;OFFifnone. No relaxedguard/testpickedcutoff. SecondaryCALIBRATION-ONLYoracleceiling: exhaustiveindependentlowerrawlogitthresholdfordesiredCCONJandupperfordesiredADP, includeattainablevalues+/-inf; strongestweakerendpointvetoachievablebyanyglobalmonotonemap/sharedmargincut, rankingandbasecallsfixed. Reportbestsafecoverage/qualifiers, NEVERtreatoracleasdeploymentpolicy orscoreitontest. FreezeallcalibrationBEFORE117evaluationpredictions, despite116typespreviouslyinspected=>NOTfreshconfirmation. ReportNLL/accuracy/AUCandgateoutcomes, comparisonraw116/baseline; noshuffleadditionbecauseonlyscalarfitandprior116retained. Type-meanoffsetcancelsoriginalsummedpairgain, hereappliedONLYendpointveto.'))
    split=load(PREVIOUS/'type-split.json');a=load(ROOT/'iteration85/anchor-budgets.json')['195'];oof=load(PREVIOUS/'oof-profiles.json');raw=load(PREVIOUS/'calibration-probabilities.json');train=split['training'];cal=split['calibration'];lookup={w:hashlib.sha256(('cal98-full|'+w).encode()).hexdigest() for w in cal};p=[oof[w]['mean'] for w in train];y=[int(a[w]=='CCONJ') for w in train];models={'offset13':fit_offset(p,y),'balanced13':fit_offset(p,y,True),'offset8':fit_offset([raw['full']['raw'][lookup[w]] for w in cal],[int(a[w]=='CCONJ') for w in cal])};save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/'models.json'):digest(OUT/'models.json')}))
    rows,probabilities=annotate(load(PREVIOUS/'calibration-cases.json'),raw,models);save(OUT/'calibration-cases.json',rows);save(OUT/'calibration-probabilities.json',probabilities);baseline=evaluate(rows,'base',None);chosen={};curves={}
    for arm in models:
        cuts=sorted({0.,float('-inf')}|{r['margins'][arm] for r in rows if r['margins'][arm] is not None});curve=[]
        for cut in cuts:
            s=evaluate(rows,arm,cut);ok=all(v['calls'] and v['hit']/v['calls']>=.9 and not v['clean_wrong'] and not v['unsupported_wrong'] and v['hit']>=math.ceil(.8*baseline[g]['hit']) for g,v in s.items()) and s['complete']['hit']>=4 and s['omission']['distinct_hits']>=4 and s['literal']['distinct_hits']>=4;curve.append(dict(cutoff=cut,stats=s,qualified=ok))
        eligible=[r for r in curve if r['qualified']];chosen[arm]=max(eligible,key=lambda r:(r['stats']['complete']['hit'],sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),r['cutoff'])) if eligible else dict(cutoff=None,qualified=False);curves[arm]=curve
    ceiling=calibration_ceiling(rows,raw);save(OUT/'calibration-ceiling.json',ceiling);save(OUT/'chosen.json',chosen);save(OUT/'calibration-curves.json',curves);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'chosen.json',OUT/'calibration-curves.json',OUT/'calibration-ceiling.json',OUT/'models.json']}));print('CHOSEN',chosen,'CEILING',ceiling,flush=True)
    evaluation,pp=annotate(load(PREVIOUS/'evaluation-cases.json'),load(PREVIOUS/'evaluation-probabilities.json'),models);save(OUT/'evaluation-cases.json',evaluation);save(OUT/'evaluation-probabilities.json',pp);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'evaluation-cases.json',OUT/'evaluation-probabilities.json']}));save(OUT/'evaluation-summary.json',{'base':evaluate(evaluation,'base',None),**{arm:evaluate(evaluation,arm,r['cutoff']) for arm,r in chosen.items()}});print('DONE',load(OUT/'evaluation-summary.json'),flush=True)
if __name__=='__main__':run()
