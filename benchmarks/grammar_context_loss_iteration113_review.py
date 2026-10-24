"""Audit evidence deletion/ranking/bootstrap and contrast catalogue-only omission."""
from benchmarks.grammar_context_loss_iteration113 import *
from voynich_smt.combined_repair_gate import evaluate as evaluate_gate


def run():
    hashes=0
    for name in ['design-freeze','context-freeze','predictions-freeze']:
        for path,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(path)==h,path;hashes+=1
    ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];base=ag.public_sentences([dict(sent_id=i,**data[i]) for i in ids],anchors,'cal98-full');words=load(ROOT/'iteration93/types.json')['candidates'];lookup={t['anchor']:t['id'] for s in base for t in s['tokens'] if t['anchor'] in words};policies=load(OUT/'policies.json');meta=load(OUT/'preflight.json');cases=load(OUT/'cases.json');weights=np.load(ROOT/'iteration102/full/weights.npz')['weights'];bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];baseline={r['case']:r for r in load(ROOT/'iteration102/calibration-cases.json') if r['block']=='full'};catalogue={(r['omitted_word'],r['case']):r for r in load(ROOT/'iteration110/cases.json') if r['omitted_word'] is not None};publics={w:load(OUT/('public-'+w+'.json')) for w in words};columns=0;classifier=0
    for a in policies:assert policies[a]==load(ROOT/('iteration'+a)/'policies.json')['full']
    for w,p in publics.items():
        assert p==remove_suffix_type(base,lookup[w]) and p[:100]==base[:100]
        assert len(p)==829 and all(t['id']!=lookup[w] for s in p[100:] for t in s['tokens'])
        assert meta[w]['deleted_tokens']==sum(len(s['tokens'])-len(t['tokens']) for s,t in zip(base,p))
    for c in cases:
        w=c['removed_word'];z=np.load(OUT/w/(c['case']+'.npz'));assert c['features']==summarize(c['pairs'],z['draws']);assert c['reference']['pair']==baseline[c['case']]['reference']['pair'];assert c['reference']['supported']==any(p['supported'] and p['pair']==c['reference']['pair'] for p in c['pairs'])
        p=publics[w];changed=perturb(p,bank[c['case']],anchors)
        for j,(n,q) in enumerate(zip(z['counts'],z['sums'])):
            pair=c['pairs'][j];tags=c['proposed'][j];active=np.any(n>0,axis=1);expected=gains_from_totals(weights[:,active]@n[active],weights[:,active]@q[active],tags);assert np.allclose(expected,z['draws'][:,j],rtol=1e-12,atol=1e-12,equal_nan=True);assert abs(float(gains_from_totals(n.sum(0),q.sum(0),tags))-pair['gain'])<1e-12
            for k,opaque in enumerate(pair['pair']):assert np.array_equal(n[:,k],[sum(t['id']==opaque for t in s['tokens']) for s in p])
            assert pair['supported']==all(n[:,k].sum()>=5 and np.count_nonzero(n[:,k])>=3 for k in range(2))
            # Re-run every pair in clean views, independent of saved totals.
            if c['case']=='correct':
                nn,qq=sentence_totals(changed,pair['pair'],model);assert np.array_equal(nn,n) and np.allclose(qq,q,rtol=1e-12,atol=1e-12);classifier+=1
            columns+=1
        for a,policy in policies.items():assert c['actions'][a]==gate(c['features'],policy)
    groups={'all_errors':[c for c in cases if c['reference']['error']],'supported_errors':[c for c in cases if c['reference']['error'] and c['reference']['supported']],'unsupported_errors':[c for c in cases if c['reference']['error'] and not c['reference']['supported']],'literal_absence_errors':[c for c in cases if c['true_endpoint_absent']],'controls':[c for c in cases if not c['reference']['error']]}
    groups.update({'remove_'+w:[c for c in cases if c['removed_word']==w] for w in words});summary={}
    for name,rows in groups.items():
        summary[name]={}
        for a,policy in policies.items():
            s=evaluate_gate([dict(c,regime='all') for c in rows],policy).get('all',dict(hit=0,wrong=0,calls=0,n=0,clean_wrong=0,unavailable_wrong=0));s['precision']=s['hit']/s['calls'] if s['calls'] else None;summary[name][a]=s
    wrong=[];comparison={}
    for a,policy in policies.items():
        b=evaluate_gate([dict(c,regime='all') for c in baseline.values()],policy)['all'];cat=evaluate_gate([dict(c,regime='all') for c in catalogue.values()],policy)['all'];diff=0;lost=0;gained=0;newwrong=0;fixedwrong=0
        for c in cases:
            matched=catalogue[c['removed_word'],c['case']];old=gate(matched['features'],policy);new=c['actions'][a];ref=c['reference']['pair'];diff+=old!=new;lost+=old==ref and old is not None and new!=ref;gained+=new==ref and new is not None and old!=ref;newwrong+=new is not None and new!=ref and (old is None or old==ref);fixedwrong+=old is not None and old!=ref and (new is None or new==ref)
            if new is not None and new!=ref:wrong.append(dict(arm=a,removed_word=c['removed_word'],case=c['case'],selected_words=[c['identities'][i] for i in new],supported=c['reference']['supported'],literal_absence=c['true_endpoint_absent'],features=c['features']))
        comparison[a]=dict(complete_baseline=b,catalogue_omission=cat,actions_changed=diff,correct_lost=lost,correct_gained=gained,new_wrong=newwrong,wrong_removed=fixedwrong)
    save(OUT/'summary.json',summary);save(OUT/'comparison.json',comparison);save(OUT/'all-wrong-actions.json',wrong);save(OUT/'audit.json',dict(input_hashes_verified=hashes,public_views_reconstructed=len(publics),protected_prefix_unchanged=True,pair_rankings_replayed=len(cases),bootstrap_columns_recomputed=columns,clean_pair_classifier_totals_recomputed=classifier,blind_actions_replayed=len(cases)*len(policies)))
    print(json.dumps({k:summary[k] for k in ['all_errors','supported_errors','unsupported_errors','literal_absence_errors','controls']},indent=2));print('COMPARISON',comparison)
if __name__=='__main__':run()
