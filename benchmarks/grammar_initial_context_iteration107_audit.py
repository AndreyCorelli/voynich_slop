"""Replay initial-preserving raw views, full-bank scores and fixed-position PP effects."""
from benchmarks.grammar_initial_context_iteration107 import *
from benchmarks.grammar_context_shadow_pp_iteration105_audit import independent_counts


def audit_preprocessing(publics):
    from voynich_smt.initial_abbreviation_context import extract_initials
    selection=load(CONTEXT/'context-selection.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];changes=load(OUT/'initial-changes.json');books={};expected_changes={}
    for book in selection['views']['expanded']['added_books']:
        raw=Path('data/raw/word-mapping-caesar')/f'voinich-caesar-{book}.html';assert digest(raw)==selection['books'][book]['raw_sha256'];books[book],expected_changes[book]=extract_initials(book,raw.read_bytes())
    assert changes['books']==expected_changes;assert changes['total_by_initial']==dict(Counter(c['before'] for cs in expected_changes.values() for c in cs))
    checked=0
    for view,public in publics.items():
        old=load(CONTEXT/('public-'+view+'.json'));assert [(s['sent_id'],len(s['tokens'])) for s in old]==[(s['sent_id'],len(s['tokens'])) for s in public]
        added=[] if view=='base' else [s for b,ss in books.items() if view=='expanded' or b.startswith('bc') for s in ss]
        expected=publics['base']+ag.public_sentences(added,anchors,'unlabeled104-Caesar');assert expected==public
        relevant=[] if view=='base' else [c for b,cs in expected_changes.items() if view=='expanded' or b.startswith('bc') for c in cs];by_position={(c['sid'],c['index']):c for c in relevant}
        for a,b in zip(old,public):
            for j,(before,after) in enumerate(zip(a['tokens'],b['tokens'])):
                c=by_position.get((a['sent_id'],j))
                if c is None:assert before==after
                else:
                    import hashlib
                    assert len(c['before'])==1 and c['after']==c['before']+'.';assert before['id']==hashlib.sha256(('unlabeled104-Caesar|'+c['before']).encode()).hexdigest();assert after['id']==hashlib.sha256(('unlabeled104-Caesar|'+c['after']).encode()).hexdigest();assert after['anchor'] is None and after['tag']=='X';checked+=1
    assert publics['base']==load(CONTEXT/'public-base.json')
    for case in load(ROOT/'iteration98/calibration-bank.json'):
        for suffix in ['.json','.npz']:assert digest(OUT/'base'/(case+suffix))==digest(PP_PREVIOUS/'base'/(case+suffix))
    return checked


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'pair-freeze.json',OUT/'predictions-freeze.json',OUT/'context-freeze.json',CONTEXT/'verification-manifest.json',PP_PREVIOUS/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    publics={v:load(OUT/('public-'+v+'.json')) for v in ['base','civil','expanded']};cases=load(OUT/'pair-cases.json');bank=load(ROOT/'iteration98/calibration-bank.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];model=load(ROOT/'iteration93/models.json')['context'];words=load(ROOT/'iteration93/types.json')['candidates'];policies=load(OUT/'policies.json');pair_replays=clean_replays=endpoint_checks=prefix_checks=0
    for view,public in publics.items():
        assert public[:100]==publics['base'];weights=np.load(CONTEXT/view/'weights.npz')['weights'];ids={t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};counts={i:np.zeros(len(public)) for i in ids}
        for j,s in enumerate(public):
            for t in s['tokens']:
                if t['id'] in counts:counts[t['id']][j]+=1
        for c in [c for c in cases if c['block']==view]:
            payload=np.load(OUT/view/(c['case']+'.npz'));draws=[]
            changed=perturb(public,bank[c['case']],anchors);proposed={t['id']:t['tag'] for s in changed for t in s['tokens'] if t['id'] in ids};expected={tuple(sorted([a,b])) for a in ids for b in ids if proposed[a]=='ADP' and proposed[b]=='CCONJ'};assert {tuple(p['pair']) for p in c['pairs']}==expected
            for j,p in enumerate(c['pairs']):
                n,q=payload['counts'][j],payload['sums'][j];tags=[proposed[i] for i in p['pair']];assert tags==c['proposed'][j];assert math.isclose(float(gains_from_totals(n.sum(0),q.sum(0),tags)),p['gain'],rel_tol=1e-9,abs_tol=1e-10)
                for k,i in enumerate(p['pair']):assert np.array_equal(n[:,k],counts[i]);endpoint_checks+=1
                assert p['supported']==all(counts[i].sum()>=5 and (counts[i]>0).sum()>=3 for i in p['pair'])
                active=np.any(n>0,axis=1);draws.append(gains_from_totals(weights[:,active]@n[active],weights[:,active]@q[active],tags))
                if c['case']=='correct':
                    nn,qq=sentence_totals(changed,p['pair'],model);assert np.array_equal(n,nn) and np.allclose(q,qq,rtol=1e-12,atol=1e-12);clean_replays+=1
            draws=np.array(draws).T;assert np.array_equal(draws,payload['draws']);assert summarize(c['pairs'],draws)==c['features'];assert reference_for(public,bank[c['case']],c['reference']['error'],c['pairs'],words)==c['reference'];pair_replays+=1
            if view!='base':
                b=load(OUT/'base'/(c['case']+'.json'));bp=np.load(OUT/'base'/(c['case']+'.npz'));index={tuple(p['pair']):j for j,p in enumerate(c['pairs'])}
                for j,p in enumerate(b['pairs']):
                    k=index[tuple(p['pair'])];assert np.array_equal(payload['counts'][k,:100],bp['counts'][j]);assert np.allclose(payload['sums'][k,:100],bp['sums'][j],rtol=1e-12,atol=1e-12);prefix_checks+=1
    assert policies==load(CONTEXT/'policies.json');assert {a:evaluate102(cases,p) for a,p in policies.items()}==load(OUT/'pair-summary.json')
    actions={a:{c['block']+'/'+c['case']:selected(c['features'],p) for c in cases} for a,p in policies.items()};assert actions==load(OUT/'actions.json')
    # Prior full-bank100scores are a control under renamed opaque IDs.
    oldpublic=load(ROOT/'iteration97/caesar/public-clean.json');oldnames={t['id']:t['anchor'] for s in oldpublic for t in s['tokens'] if t['anchor'] in words};oldbank=load(ROOT/'iteration97/bank.json');old_replays=0
    for c in [c for c in cases if c['block']=='base' and c['case'] in oldbank]:
        old=load(ROOT/'iteration97/caesar'/c['case']/'detector.json')['joint_context'];lookup={tuple(sorted(oldnames[i] for i in p['pair'])):p for p in old}
        for p in c['pairs']:
            previous=lookup[tuple(sorted(c['identities'][i] for i in p['pair']))];assert math.isclose(p['gain'],previous['gain'],rel_tol=1e-9,abs_tol=1e-10) and p['supported']==previous['supported'];old_replays+=1
    # Base control scores stay unchanged; added-context anchor features intentionally change.
    core_checks=0
    for old in [r for r in load(CONTEXT/'evaluation-cases.json') if r['block']=='base']:
        c=next(c for c in cases if (c['block'],c['case'])==(old['block'],old['case']));lookup={tuple(p['pair']):p for p in c['pairs']}
        for p in old['pairs']:
            new=lookup[tuple(p['pair'])];assert math.isclose(p['gain'],new['gain'],rel_tol=1e-9,abs_tol=1e-10) and p['supported']==new['supported'];core_checks+=1
    preprocessing_checks=audit_preprocessing(publics)
    public=publics['base'];labels=load(ROOT/'iteration105/reference-rows.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};payloads={p.stem:load(p) for p in (OUT/'pp-cache').glob('*.json') if not p.name.endswith('.freeze.json')};inferences=0
    for sig,payload in payloads.items():
        view=apply_delta(public,payload['delta']);assert signature(view)==sig and len(view)==100
        for a,m in models.items():
            predicted=compact(infer85(query_rows(view,labels),m));assert np.allclose(predicted['pooled_pos'],payload['scores'][a]['pooled_pos'],rtol=1e-12,atol=1e-12);assert predicted['left']==payload['scores'][a]['left'];inferences+=1
    clean_sig=signature(public);clean=payloads[clean_sig]['scores'];transforms=load(OUT/'transforms.json');evaluation=load(OUT/'evaluation.json');count_checks=applied=zero_cases=0
    for c in cases:
        key=c['block']+'/'+c['case'];changed=perturb(publics[c['block']],bank[c['case']],anchors);before_public=changed[:100];info=transforms[key];assert signature(before_public)==info['before'];before=payloads[info['before']]['scores'];affected=sum(x!=y for s,t in zip(public,before_public) for x,y in zip(s['tokens'],t['tokens']));assert affected==c['scored_affected_tokens']
        if c['reference']['error'] and not affected:zero_cases+=1
        for arm,action in info['arms'].items():
            assert action['pair']==actions[arm][key];after_public=repair_prefix(before_public,changed,action['pair']);assert signature(after_public)==action['after'];r=evaluation[key][arm];pair=action['pair'];hit=pair is not None and pair==c['reference']['pair'];assert r['pair']['hit']==int(hit) and r['pair']['wrong']==int(pair is not None and not hit);after=payloads[action['after']]['scores'];applied+=1
            assert action['changed_tokens']==sum(x!=y for s,t in zip(before_public,after_public) for x,y in zip(s['tokens'],t['tokens']))
            if hit:assert after_public==public
            for a,cuts in PP_SETTINGS.items():
                for policy,cut in cuts.items():
                    e=r['pp'][a][policy];new=after[a]['pooled_pos'];old=before[a]['pooled_pos'];cl=clean[a]['pooled_pos']
                    for phase,prob in [('before',old),('after',new),('clean',cl)]:
                        expected=independent_counts(labels,prob,cut);assert all(e[phase][k]==v for k,v in expected.items());count_checks+=1
                    expected=independent_counts(labels,new,cut,[t['anchor'] is None for s in after_public for t in s['tokens']]);assert all(e['hidden_after'][k]==v for k,v in expected.items())
                    changes=dict(new_tp=0,new_fp=0,lost_tp=0,removed_fp=0)
                    for ref,p,q in zip(labels,new,old):
                        if p>=cut and q<cut:changes['new_tp' if ref['labels']['pp'] else 'new_fp']+=1
                        if p<cut and q>=cut:changes['lost_tp' if ref['labels']['pp'] else 'removed_fp']+=1
                    assert changes==e['changes'];assert e['different_from_clean']==sum((p>=cut)!=(q>=cut) for p,q in zip(new,cl));assert e['maximum_probability_difference_from_clean']==max(abs(p-q) for p,q in zip(new,cl))
    assert zero_cases==6
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,bootstrap_cases_replayed=pair_replays,clean_pair_profiles_recomputed=clean_replays,endpoint_sentence_count_checks=endpoint_checks,original_prefix_probability_checks=prefix_checks,legacy100_pair_gains_replayed=old_replays,unchanged_base_core_scores_checked=core_checks,preprocessing_public_changes_verified=preprocessing_checks,blind_case_policy_actions_replayed=applied,pp_model_inferences_recomputed=inferences,independent_confusion_checks=count_checks,zero_affected_error_views=zero_cases,no_truth_gate_or_new_annotations_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
