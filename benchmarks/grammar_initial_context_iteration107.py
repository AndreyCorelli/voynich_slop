"""Uniform initial-abbreviation identity fix, frozen full-bank comparison."""
from benchmarks.grammar_context_shadow_pp_iteration105 import *
from voynich_smt.context_anchor_repair import repair_prefix
from voynich_smt.initial_abbreviation_context import extract_initials
OUT=ROOT/'iteration107';CONTEXT=ROOT/'iteration104';PP_PREVIOUS=ROOT/'iteration106'


def prepare107():
    selection=load(CONTEXT/'context-selection.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];books={};changes={}
    for book in selection['views']['expanded']['added_books']:
        rawpath=Path('data/raw/word-mapping-caesar')/f'voinich-caesar-{book}.html';assert digest(rawpath)==selection['books'][book]['raw_sha256'];books[book],changes[book]=extract_initials(book,rawpath.read_bytes())
    base=load(CONTEXT/'public-base.json');publics={'base':base,'civil':base+ag.public_sentences([s for b,ss in books.items() if b.startswith('bc') for s in ss],anchors,'unlabeled104-Caesar'),'expanded':base+ag.public_sentences([s for ss in books.values() for s in ss],anchors,'unlabeled104-Caesar')}
    for view,public in publics.items():
        old=load(CONTEXT/('public-'+view+'.json'));assert [(s['sent_id'],len(s['tokens'])) for s in public]==[(s['sent_id'],len(s['tokens'])) for s in old];assert public[:100]==base;save(OUT/('public-'+view+'.json'),public)
    save(OUT/'initial-changes.json',dict(books=changes,total_by_initial=dict(Counter(c['before'] for cs in changes.values() for c in cs)),scope='Uniform uppercaseoneletter+period rule, segmentboundariesunchanged, no sourcefitlabels/wordexceptions.'))
    save(OUT/'context-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'initial-changes.json']+list(OUT.glob('public-*.json'))}))
    return publics


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/initial_abbreviation_context.py'),Path('src/voynich_smt/unlabeled_caesar_context.py'),Path('src/voynich_smt/context_anchor_repair.py'),Path('benchmarks/grammar_unlabeled_caesar_iteration104.py'),CONTEXT/'verification-manifest.json',CONTEXT/'context-selection.json',CONTEXT/'policies.json',PP_PREVIOUS/'verification-manifest.json',ROOT/'iteration105/reference-rows.json',ROOT/'iteration93/types.json',ROOT/'iteration93/models.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration85/anchor-budgets.json',BASE/'models.json',ROOT/'iteration89/models.json']+[Path('data/raw/word-mapping-caesar')/f'voinich-caesar-{b}.html' for b in load(CONTEXT/'context-selection.json')['views']['expanded']['added_books']]+[CONTEXT/('public-'+v+'.json') for v in ['base','civil','expanded']]+[CONTEXT/v/'weights.npz' for v in ['base','civil','expanded']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Failure-motivated development diagnostic, no independentconfirmation. Generic uppercase SINGLELETTER followedbyperiod in admittedrawprose retainsperiod in normalizedwordID (C.=>c., L.=>l., etc). No c-specificrule or blacklist. Keep104periodsegmentboundaries, exactSIDs/tokenpositions/counts; isolateidentity/anchormatching, doNOTjoinsentences orsplitenclitics. Original1001514tokens unchanged; ONLYadmitted104booksV/VII/CivilI-III, GallicVIstill excluded; freezeallpublicviews beforemodels. Same195anchorlookup,16candidatecatalogue,ALL64errors+3controls per3views=201cases. c. opaque(noanchor), c syntacticcomponent notfabricated. Retainmissingendpointcasesasmisses; primaryALL64,secondaryscoredaffected62/core15 andgloballypresentcompatibleendpointstrata. Same93classifier/95cut/103gain-gapsecondarytransfer(no16recalibration),3OFFpolicies,support5occ3sentences,same104bootstrapweights. Basecasesbitwisereuse106; recomputeCivil/expandedblindallpairs. SaveallrecommendationsbeforePPevaluation. ApplyALLglobalcontextrepairsblindly toonly100prefix, includingwrong/absentqueryendpoint cases; fixed85/89PP. Existing106PPcacheonlysamepositions/IDs, inferanynewview. No targettuning/droppederrors/newannotation/reserve/sealedtest/nuclei. Reportremainingfailure/coverage/zeroaffectedcases andallgrossPPdamage, notjustuncollidedsubset.'))
    publics=prepare107();anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];policies=load(CONTEXT/'policies.json');save(OUT/'policies.json',policies);cases=[];basecounts=Counter(t['anchor'] for s in publics['base'] for t in s['tokens']);assert len(bank)==67
    for view,public in publics.items():
        folder=OUT/view;folder.mkdir();weights=np.load(CONTEXT/view/'weights.npz')['weights']
        for ci,(case,replacements) in enumerate(bank.items()):
            if view=='base':
                for suffix in ['.json','.npz']:(folder/(case+suffix)).write_bytes((PP_PREVIOUS/view/(case+suffix)).read_bytes())
                row=load(folder/(case+'.json'))
            else:row=compute(public,case,replacements,anchors,words,model,weights,folder)
            row.update(block=view,regime=view,scored_affected_tokens=sum(basecounts[w] for w in replacements),scored_present_endpoints=sum(basecounts[w]>0 for w in replacements));cases.append(row)
            if ci%5==0:print(view,ci+1,'/',len(bank),flush=True)
    save(OUT/'pair-cases.json',cases);save(OUT/'pair-summary.json',{a:evaluate102(cases,p) for a,p in policies.items()});actions={a:{c['block']+'/'+c['case']:selected(c['features'],p) for c in cases} for a,p in policies.items()};save(OUT/'actions.json',actions);save(OUT/'pair-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'pair-cases.json',OUT/'actions.json',OUT/'policies.json']+list(OUT.glob('*/*.json'))+list(OUT.glob('*/*.npz'))}));print('PAIRSUMMARY',json.dumps(load(OUT/'pair-summary.json')),flush=True)
    public=publics['base'];labels=load(ROOT/'iteration105/reference-rows.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};store=OUT/'pp-cache';store.mkdir();cache={};sources={}
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
