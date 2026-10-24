"""Source-calibrated independent singleton alternative; frozen113 challenge."""
from benchmarks.grammar_context_loss_iteration113 import *
from voynich_smt.unknown_partner_gate import singleton_scores, contrast, choose
OUT=ROOT/'iteration114'


def stats(rows, singles, base, cutoff):
    out=dict(n=len(rows),hit=0,wrong=0,calls=0,clean_wrong=0,unsupported_wrong=0,distinct_hits=0)
    distinct=set()
    for r in rows:
        pair=choose(r['features'],singles[r['case']],base,cutoff);hit=pair is not None and pair==r['reference']['pair'];wrong=pair is not None and not hit
        out['calls']+=pair is not None;out['hit']+=hit;out['wrong']+=wrong;out['clean_wrong']+=wrong and not r['reference']['error'];out['unsupported_wrong']+=wrong and r['reference']['error'] and not r['reference']['supported']
        if hit:distinct.add(r['case'])
    out['distinct_hits']=len(distinct);return out


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/unknown_partner_gate.py'),ROOT/'iteration110/cases.json',ROOT/'iteration113/verification-manifest.json',ROOT/'iteration98/blocks.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration111/policies.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY unknown-partner contrast diagnostic, noauthor/PP/newannotation/reserve/sealedtest. Base111strict frozen. Compute singleton flip gain with SAME93binarymodel but masking ONLY singletonID, not bothpairIDs, meanP(CCONJ), support5occ3sentences. Global strongest supported singleton OR zero(noerror) competes with chosen jointlymasked pair. Contrast=pairgain-max(0,allsupportedunarygains); DIFFERENT masks imply heuristic pseudo-likelihood contrast, NOT calibrated likelihood/Bayesfactor. All16visible sourcecataloguetypes may supply singleton alternative even when excluded from repaircatalogue110; unknownpartner means one observed class error can be explained without asserting supported mate. This is not110jointmaskendpointpositivity. CalibrateONLY110complete67+catalogueomission1072, reusedsourcecal. Candidate cutoffs zero plus all attainable contrasts plus negative-infinity(noadditionalgate). Require>=90percentprecision separatelycomplete/omission, zeroclean/unsupportedwrong, retain>=80percentstrict111complete48=>39hits andomission674=>540hits, >=20distinctomissionhitcases. Maxcompletehits, omissionhits, distinctomissionhits, minwrong, highestcutoff. OFFifnone. FreezechoiceBEFORE computing113literal-loss singleton scores. EvaluateALL1072challengecases, unchanged113reference/support, fixedchoice even iffails; challengeadaptivelyinspected113notindependentconfirmation. Also report cutoffzero as predeclared uncalibrated modelcomparison diagnostic, neverreplacement if guardfails. No targetthresholdselection/wordexceptions/defaultchange/nucleiclaim.'))
    ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];d=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];public=ag.public_sentences([dict(sent_id=i,**d[i]) for i in ids],anchors,'cal98-full');words=load(ROOT/'iteration93/types.json')['candidates'];candidates={t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];base=load(ROOT/'iteration111/policies.json')['full'];source=load(ROOT/'iteration110/cases.json');singles={}
    for i,(case,replacements) in enumerate(bank.items()):
        singles[case]=singleton_scores(perturb(public,replacements,anchors),candidates,model)
        if i%10==0:print('calibration singleton',i,flush=True)
    save(OUT/'source-singletons.json',singles)
    # Source calibration is complete before challenge contexts are loaded.
    complete=[r for r in source if r['regime']=='complete'];omitted=[r for r in source if r['regime']=='omission'];values={contrast(r['features'],singles[r['case']]) for r in source if r['features']['pair'] is not None};cuts=sorted(values|{0.,float('-inf')});curve=[]
    for cut in cuts:
        c=stats(complete,singles,base,cut);o=stats(omitted,singles,base,cut);ok=c['hit']>=39 and o['hit']>=540 and o['distinct_hits']>=20 and all(s['calls'] and s['hit']/s['calls']>=.9 and not s['clean_wrong'] and not s['unsupported_wrong'] for s in [c,o]);curve.append(dict(cutoff=cut,complete=c,omission=o,qualified=ok))
    eligible=[r for r in curve if r['qualified']];chosen=max(eligible,key=lambda r:(r['complete']['hit'],r['omission']['hit'],r['omission']['distinct_hits'],-r['complete']['wrong']-r['omission']['wrong'],r['cutoff'])) if eligible else dict(cutoff=None,qualified=False)
    save(OUT/'calibration-curve.json',curve);save(OUT/'chosen.json',chosen);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'chosen.json',OUT/'calibration-curve.json',OUT/'source-singletons.json']}));print('CHOSEN',chosen,flush=True)
    challenge=load(ROOT/'iteration113/cases.json');cache={};result=[]
    for i,r in enumerate(challenge):
        word=r['removed_word'];case=r['case'];key=word+'/'+case
        # Compute only if base policy would call; otherwise contrast cannot affect the action.
        if gate(r['features'],base) is not None:
            p=load(ROOT/'iteration113'/('public-'+word+'.json'));ss=singleton_scores(perturb(p,bank[case],anchors),candidates,model);cache[key]=ss
        else:ss={}
        result.append(dict(case=case,removed_word=word,reference=r['reference'],true_endpoint_absent=r['true_endpoint_absent'],features=r['features'],base_pair=gate(r['features'],base),contrast=contrast(r['features'],ss) if ss else None,actions={a:choose(r['features'],ss,base,cut) for a,cut in [('calibrated',chosen['cutoff']),('zero_diagnostic',0.)]}))
        if i%67==66:print('challenge',word,flush=True)
    save(OUT/'challenge-singletons.json',cache);save(OUT/'challenge-cases.json',result);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'challenge-singletons.json',OUT/'challenge-cases.json',OUT/'chosen.json']}))
    print('DONE',len(result),flush=True)
if __name__=='__main__':run()
