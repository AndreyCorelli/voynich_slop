"""Blindly transfer all iteration104 repairs to the original100-token-position set."""
from benchmarks.grammar_unlabeled_caesar_iteration104 import *
OUT=ROOT/'iteration105';PREVIOUS=ROOT/'iteration104'


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_anchor_shadow_pp_iteration96.py'),Path('benchmarks/grammar_anchor_budget_iteration85.py'),Path('src/voynich_smt/anchor_shadow_repair.py'),Path('src/voynich_smt/anchor_grammar.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'public-base.json',PREVIOUS/'actions.json',PREVIOUS/'evaluation-cases.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration85/anchor-budgets.json',BASE/'models.json',ROOT/'iteration89/models.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration40/manifest.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Freeze104ALL54cases(18errors/controlsxbase/Civil/expanded)andALL5policies(frozen95PRIMARY,gain_gapSECONDARY,3OFF). ApplyeveryrecommendedpairblindlytoONLYoriginal100Caesarsentences104publicbase, mappingglobalwithin100, no truthgate/candidatefilter. ExistingopaqueIDs retained. AdditionaltextONLYinfluencesfrozenrecommendation; NOextraPPpoolpositions/context. Perturbbasewithsameglobalcase98bank, then swapallpublicanchor/tagassignmentsforrecommendedIDs. Sharedsignaturecache ofpublicassignments dedupONLYsame100positions. Recompute fixed85PPoriginal195(.80PRIMARY),89augmented(.71selected/.80secondary) atoriginal thresholds; nofit/recalibration. SaveALLtransforms/publicdeltas,predictionarraysandfreezes BEFOREPPmetrics. Groundtruth cached40annotations SAME100; no newannotation/reserve/sealedtest. ForALLcases/actions comparecorrupt/repaired/clean, TP/FP/precision/recall/F1, hidden, newTP/newFP/lostTP/removedFP, probability/decisiondistanceclean. Reportgrosslosses/anywrongaction; exacthitdoesnotlicenseomitcounterexamples. Caseaggregates arecorrelatedsyntheticreplicates,NOTuniquegrammartokens. PPtargetgovernednode-membership,NOTfullphrase/Case/exactgovernor/lexicalnuclei. Originalpublic100andmodelsunchanged acrossrecommendationcontexts; source/cachedauthor reuseddevelopmentnotfreshconfirmation.'))
    clean_public=load(PREVIOUS/'public-base.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];cache=load(ROOT/'iteration40/data-truth.json');ids=load(ROOT/'iteration40/manifest.json')['split_ids']['Caesar'];sentences=cached_sentences(cache,ids);public,labels=transfer_rows(sentences,anchors,'unlabeled104-Caesar',models['original']['pos_classes']);assert public==clean_public;save(OUT/'public-clean.json',public)
    store=OUT/'pp-cache';store.mkdir();cached={}
    def predictions(view):
        sig=signature(view)
        if sig not in cached:
            rows={a:infer85(query_rows(view,labels),m) for a,m in models.items()};payload=dict(delta=delta_public(clean_public,view),scores={a:compact(r) for a,r in rows.items()});path=store/(sig+'.json');save(path,payload);save(store/(sig+'.freeze.json'),dict(inputs={str(path):digest(path)}));cached[sig]=rows
        return sig,cached[sig]
    clean_sig,clean=predictions(public);save(OUT/'reference-rows.json',[{k:r[k] for k in ('sid','index','word','visible','labels')} for r in clean['original']]);bank=load(ROOT/'iteration98/calibration-bank.json');actions=load(PREVIOUS/'actions.json');frozen_cases=load(PREVIOUS/'evaluation-cases.json');transforms={}
    # No reference correctness or annotation label controls these actions.
    for c in frozen_cases:
        key=c['block']+'/'+c['case'];before_public=perturb(public,bank[c['case']],anchors);before_sig,_=predictions(before_public);arms={}
        for arm,bycase in actions.items():
            pair=bycase[key];after_public=swap_assignments(before_public,pair);after_sig,_=predictions(after_public);arms[arm]=dict(pair=pair,after=after_sig,changed_tokens=sum(x!=y for s,t in zip(before_public,after_public) for x,y in zip(s['tokens'],t['tokens'])))
        transforms[key]=dict(before=before_sig,arms=arms)
    save(OUT/'transforms.json',transforms);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'transforms.json',OUT/'reference-rows.json']+list(store.glob('*.json'))}));evaluation={}
    for c in frozen_cases:
        key=c['block']+'/'+c['case'];action=transforms[key];before=cached[action['before']];result={}
        for arm,info in action['arms'].items():
            after=cached[info['after']];pair=info['pair'];hit=pair is not None and pair==c['reference']['pair'];result[arm]=dict(pair=dict(selected=pair,hit=int(hit),wrong=int(pair is not None and not hit),abstain=pair is None,reference_supported=c['reference']['supported']),changed_tokens=info['changed_tokens'],public_equals_clean=info['after']==clean_sig,pp={a:{policy:dict(effect(after[a],before[a],clean[a],cut),maximum_probability_difference_from_clean=max(abs(x['scores']['pooled_pos']['pp']-y['scores']['pooled_pos']['pp']) for x,y in zip(after[a],clean[a]))) for policy,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()})
        evaluation[key]=result
    save(OUT/'evaluation.json',evaluation);save(OUT/'run-summary.json',dict(cases=len(evaluation),arms=len(actions),unique_pp_inputs=len(cached),original_sentences=len(public),original_tokens=sum(len(s['tokens']) for s in public),clean_signature=clean_sig));print(load(OUT/'run-summary.json'))
if __name__=='__main__':run()
