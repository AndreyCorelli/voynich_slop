"""Source-wide matched-clean attribution of frozen swap recommendations."""
from benchmarks.grammar_unknown_partner_iteration114 import *
from voynich_smt.anchor_evidence_attribution import endpoint
OUT=ROOT/'iteration115'


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/anchor_evidence_attribution.py'),ROOT/'iteration110/cases.json',ROOT/'iteration113/cases.json',ROOT/'iteration102/calibration-cases.json',ROOT/'iteration98/blocks.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration93/models.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',ROOT/'iteration109/policies.json',ROOT/'iteration111/policies.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY descriptive attribution, no new gate/fit/author/PP/labels/reserve/sealedtest. Freeze ALL109/111 fullbranch actions for110complete+catalogueomissions(1139) AND113literal-loss(1072), no dropped errors/controls. No114contrast actions; failed114unchanged. For each selectedpair collect endpointP(CCONJ) under jointpairmask in exactlymatched CLEAN publiccontext, same physicaltokens/deletionview and samepairmask. CorruptP from existing102/113cachedq/counts; ifsamecleanclasspairnotin102clean enumerate directly with93model. Cleanmargin relative correctclass; observedmargin relative proposedclass. Separate pure signchange from q/contextdelta: counterfactual=cleanmargin*(-1 ifclasschanged else1), delta=observed-counterfactual. Unchangedendpoint positivecleanmargin>1e-12 ispreexistingfalseflip; unchangedpositiveobservedmargin isobservedfalseflip; invariance absdelta<=1e-10. Summary predefined full/catalogue/literal × policy × hit/wrong, all/unsupported/literalabsence and counts ofpositiveinnocentendpoints/preexisting/new/invariant. Report uniquephysicalview+pair and view+type alongside correlatedcasecounts. Also singleton falseflip prevalence overALL16types andALL17cleanphysicalviews, support stratified; no selected-onlyprevalenceclaim. Freezeactions BEFORE matchedcleaninferences. Knowncleanstates are diagnostic oracles, NEVER deploymentfeatures or corrections. No wordexception/thresholdchange/nucleiclaim.'))
    source=load(ROOT/'iteration110/cases.json');literal=load(ROOT/'iteration113/cases.json');policies={a:load(ROOT/('iteration'+a)/'policies.json')['full'] for a in ['109','111']};selections=[]
    for kind,rr in [('source',source),('literal',literal)]:
        for r in rr:
            regime=('full' if r['regime']=='complete' else 'catalogue') if kind=='source' else 'literal'
            key=(('complete' if r['omitted_word'] is None else 'omit-'+r['omitted_word']) if kind=='source' else 'delete-'+r['removed_word'])+'/'+r['case']
            selections.append(dict(key=key,kind=kind,regime=regime,physical_view='full' if kind=='source' else r['removed_word'],case=r['case'],reference=r['reference'],true_endpoint_absent=r.get('true_endpoint_absent',False),features=r['features'],actions={a:gate(r['features'],p) for a,p in policies.items()}))
    save(OUT/'selections.json',selections);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selections.json'):digest(OUT/'selections.json')}))
    ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];d=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];base=ag.public_sentences([dict(sent_id=i,**d[i]) for i in ids],anchors,'cal98-full');words=load(ROOT/'iteration93/types.json')['candidates'];lookup={t['id']:t['anchor'] for s in base for t in s['tokens'] if t['anchor'] in words};clean_tags={t['id']:t['tag'] for s in base for t in s['tokens']};model=load(ROOT/'iteration93/models.json')['context'];bank=load(ROOT/'iteration98/calibration-bank.json');publics={'full':base,**{w:load(ROOT/'iteration113'/('public-'+w+'.json')) for w in words}};original={c['case']:c for c in load(ROOT/'iteration102/calibration-cases.json') if c['block']=='full'};changed={(r['removed_word'],r['case']):r for r in literal};clean_cache={};npz_cache={};attributions=[]
    for i,s in enumerate(selections):
        pair=next((p for p in s['actions'].values() if p is not None),None)
        if pair is None:continue
        view=s['physical_view'];cachekey=view+'/'+'+'.join(pair)
        if cachekey not in clean_cache:
            n,q=sentence_totals(publics[view],pair,model);clean_cache[cachekey]=dict(pair=pair,physical_view=view,counts=n.sum(0).tolist(),sums=q.sum(0).tolist())
        cl=clean_cache[cachekey];record=original[s['case']] if s['kind']=='source' else changed[view,s['case']];path=(ROOT/'iteration102/full' if s['kind']=='source' else ROOT/'iteration113'/view)/(s['case']+'.npz')
        # One selected pair per case, reused across policies and catalogue masks.
        pk=str(path)
        if pk not in npz_cache:
            z=np.load(path);npz_cache[pk]=(z['counts'].sum(1),z['sums'].sum(1));z.close()
        ns,qs=npz_cache[pk];j=next(j for j,p in enumerate(record['pairs']) if p['pair']==pair);proposed=record['proposed'][j];endpoints=[]
        for k,opaque in enumerate(pair):
            assert cl['counts'][k]==ns[j,k] and ns[j,k]>0
            e=endpoint(cl['sums'][k]/cl['counts'][k],float(qs[j,k]/ns[j,k]),clean_tags[opaque],proposed[k]);endpoints.append(dict(e,opaque=opaque,word=lookup[opaque],clean_tag=clean_tags[opaque],proposed_tag=proposed[k],n=int(ns[j,k])))
        assert abs(sum(e['corrupt_flip_margin'] for e in endpoints)-s['features']['gain'])<1e-10
        attributions.append(dict(s,endpoints=endpoints,pair=pair,words=[lookup[x] for x in pair]))
        if i%100==0:print('attributed',i,flush=True)
    save(OUT/'clean-joint-pair-cache.json',clean_cache);save(OUT/'attributions.json',attributions)
    clean_singletons={v:singleton_scores(p,set(lookup),model) for v,p in publics.items()};save(OUT/'clean-singletons.json',clean_singletons);save(OUT/'inference-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'clean-joint-pair-cache.json',OUT/'attributions.json',OUT/'clean-singletons.json']}));print('DONE',len(attributions),'selectedviewcases',len(clean_cache),'unique cleanpairviews',flush=True)
if __name__=='__main__':run()
