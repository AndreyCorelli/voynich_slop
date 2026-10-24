"""Full16-candidate/64-error stress test of frozen additional author context."""
from benchmarks.grammar_context_shadow_pp_iteration105 import *
from voynich_smt.context_anchor_repair import repair_prefix
OUT=ROOT/'iteration106';CONTEXT=ROOT/'iteration104';PP_PREVIOUS=ROOT/'iteration105'


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/context_anchor_repair.py'),Path('benchmarks/grammar_unlabeled_caesar_iteration104.py'),Path('src/voynich_smt/pair_uncertainty.py'),Path('src/voynich_smt/paired_anchor_class.py'),CONTEXT/'verification-manifest.json',CONTEXT/'context-selection.json',CONTEXT/'policies.json',PP_PREVIOUS/'verification-manifest.json',PP_PREVIOUS/'reference-rows.json',ROOT/'iteration93/types.json',ROOT/'iteration93/models.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration85/anchor-budgets.json',BASE/'models.json',ROOT/'iteration89/models.json']+[CONTEXT/('public-'+v+'.json') for v in ['base','civil','expanded']]+[CONTEXT/v/'weights.npz' for v in ['base','civil','expanded']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Full16source93candidates(all8ADPx8CCONJ), ALL64globalcrossswaps+3controls perview=201cases. Frozen104base/Civil/expandedpublicviews, exactcontextselection+same100prefix/1514positions/195givenanchors; no newrawcontext/bookselection/tokenizer. Original93jointmodel,count5occ3sentences,256same104sentencebootstrapweights, allpresentoppositeproposedclasspairsexhaustively, absenttypesnotfabricated. Exactoriginal95cutPRIMARY;1038core-calibratedgain_gapSECONDARYtransferboundary(not16calibrated);3OFFpoliciesretained, no recalibration/targetthresholds. Saveallpairpredictions/actionsbeforePPmetrics. ApplyEVERYrecommendationblindlyusingGLOBALcontextassignments evenwhenendpointabsent100, thenONLYoriginal100prefixinto85/89PPfixed. No pairtruthgate. Full64errorresultsplus scored-affected vs zero-affected strata, and original15coreerrors withfull16distractors. ZeroaffectedqueriesNOTnewgrammaticalrestoration. Reportallwrongpairactions/controls/unsupportedpartners; allTP/FP/grosslosses/cleanprobabilitydistances, includingnewdamagesvsno-repair andbase. Cache105PPscoresONLYsameoriginal100positions/globalIDs; newviewsinferfixedmodels. No newannotations/reserve/sealedtest/nuclei, previouslyreusedCaesardevelopment100, conditional1globalbijectiveerror/suppliedanchors, notfreshconfirmation.'))
    publics={v:load(CONTEXT/('public-'+v+'.json')) for v in ['base','civil','expanded']};anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];policies=load(CONTEXT/'policies.json');save(OUT/'policies.json',policies);cases=[];basecounts=Counter(t['anchor'] for s in publics['base'] for t in s['tokens']);assert len(bank)==67
    for view,public in publics.items():
        folder=OUT/view;folder.mkdir();weights=np.load(CONTEXT/view/'weights.npz')['weights']
        for ci,(case,replacements) in enumerate(bank.items()):
            row=compute(public,case,replacements,anchors,words,model,weights,folder);row.update(block=view,regime=view,scored_affected_tokens=sum(basecounts[w] for w in replacements),scored_present_endpoints=sum(basecounts[w]>0 for w in replacements));cases.append(row)
            if ci%5==0:print(view,ci+1,'/',len(bank),flush=True)
    save(OUT/'pair-cases.json',cases);save(OUT/'pair-summary.json',{a:evaluate102(cases,p) for a,p in policies.items()});actions={a:{c['block']+'/'+c['case']:selected(c['features'],p) for c in cases} for a,p in policies.items()};save(OUT/'actions.json',actions);save(OUT/'pair-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'pair-cases.json',OUT/'actions.json',OUT/'policies.json']+list(OUT.glob('*/*.json'))+list(OUT.glob('*/*.npz'))}));print('PAIRSUMMARY',json.dumps(load(OUT/'pair-summary.json')),flush=True)
    public=publics['base'];labels=load(PP_PREVIOUS/'reference-rows.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};store=OUT/'pp-cache';store.mkdir();cache={};sources={}
    def predictions(view):
        sig=signature(view)
        if sig not in cache:
            previous=PP_PREVIOUS/'pp-cache'/(sig+'.json')
            if previous.exists():payload=load(previous);assert apply_delta(public,payload['delta'])==view;sources[sig]=str(previous)
            else:payload=dict(delta=delta_public(public,view),scores={a:compact(infer85(query_rows(view,labels),m)) for a,m in models.items()});sources[sig]='new'
            path=store/(sig+'.json');save(path,payload);save(store/(sig+'.freeze.json'),dict(inputs={str(path):digest(path)}));cache[sig]={a:expand(labels,scores) for a,scores in payload['scores'].items()}
        return sig,cache[sig]
    clean_sig,clean=predictions(public);transforms={}
    for c in cases:
        key=c['block']+'/'+c['case'];changed=perturb(publics[c['block']],bank[c['case']],anchors);before_public=changed[:100];before_sig,_=predictions(before_public);arms={}
        for arm,bycase in actions.items():
            pair=bycase[key];after_public=repair_prefix(before_public,changed,pair);after_sig,_=predictions(after_public);arms[arm]=dict(pair=pair,after=after_sig,changed_tokens=sum(x!=y for s,t in zip(before_public,after_public) for x,y in zip(s['tokens'],t['tokens'])))
        transforms[key]=dict(before=before_sig,arms=arms)
    save(OUT/'transforms.json',transforms);save(OUT/'pp-cache-sources.json',sources);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'transforms.json',OUT/'pp-cache-sources.json']+list(store.glob('*.json'))}));evaluation={}
    for c in cases:
        key=c['block']+'/'+c['case'];action=transforms[key];before=cache[action['before']];result={}
        for arm,info in action['arms'].items():
            after=cache[info['after']];pair=info['pair'];hit=pair is not None and pair==c['reference']['pair'];result[arm]=dict(pair=dict(selected=pair,hit=int(hit),wrong=int(pair is not None and not hit),abstain=pair is None,reference_supported=c['reference']['supported']),changed_tokens=info['changed_tokens'],public_equals_clean=info['after']==clean_sig,scored_affected_tokens=c['scored_affected_tokens'],scored_present_endpoints=c['scored_present_endpoints'],pp={a:{policy:dict(effect(after[a],before[a],clean[a],cut),maximum_probability_difference_from_clean=max(abs(x['scores']['pooled_pos']['pp']-y['scores']['pooled_pos']['pp']) for x,y in zip(after[a],clean[a]))) for policy,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()})
        evaluation[key]=result
    save(OUT/'evaluation.json',evaluation);save(OUT/'run-summary.json',dict(cases=len(cases),arms=len(policies),unique_pp_inputs=len(cache),new_pp_inputs=sum(s=='new' for s in sources.values()),original_sentences=100,original_tokens=1514,clean_signature=clean_sig));print(load(OUT/'run-summary.json'),flush=True)
if __name__=='__main__':run()
