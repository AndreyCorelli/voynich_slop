"""Audit raw selection, shared public identities and sentence-bootstrap decisions."""
from benchmarks.grammar_unlabeled_caesar_iteration104 import *


def run():
    checked=0
    for manifest in [OUT/'design-freeze.json',OUT/'context-freeze.json',ROOT/'iteration103/verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;checked+=1
    cache=load(ROOT/'iteration40/data-truth.json');ids=load(ROOT/'iteration40/manifest.json')['split_ids']['Caesar'];scored=[dict(sent_id=sid,tokens=[dict(word=t['word']) for t in cache[sid]]) for sid in ids];fragments=overlap_fragments(scored);meta=load(OUT/'context-selection.json');books={};anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];model=load(ROOT/'iteration93/models.json')['context'];policies=load(OUT/'policies.json');bank=load(ROOT/'iteration98/calibration-bank.json');core=load(ROOT/'iteration100/core.json')
    for book in BOOKS:
        ss,m=extract(book,(RAW/f'voinich-caesar-{book}.html').read_bytes());m['excluded_overlap']=overlaps(m.pop('prose_letters'),fragments);assert m==meta['books'][book]
        if not m['excluded_overlap']:books[book]=ss
    assert meta['books']['gall6']['excluded_overlap'] and all(b in BOOKS and b!='gall6' for b in books)
    publics={view:load(OUT/('public-'+view+'.json')) for view in ['base','civil','expanded']};cases=load(OUT/'evaluation-cases.json');replayed=0;predictions=0;endpoint_checks=0
    for vi,(view,public) in enumerate(publics.items()):
        raw=scored+([] if view=='base' else [s for b,ss in books.items() if view=='expanded' or b.startswith('bc') for s in ss]);assert ag.public_sentences(raw,anchors,'unlabeled104-Caesar')==public;assert public[:100]==publics['base']
        assert len(public)==meta['views'][view]['sentences'];assert sum(len(s['tokens']) for s in public)==meta['views'][view]['tokens']
        folder=OUT/view;weights=np.load(folder/'weights.npz')['weights'];expected=np.random.default_rng(104000+vi).multinomial(len(public),np.full(len(public),1/len(public)),size=256);assert np.array_equal(expected,weights)
        for row in [c for c in cases if c['block']==view]:
            changed=perturb(public,bank[row['case']],anchors);payload=np.load(folder/(row['case']+'.npz'));draws=[]
            for j,pair in enumerate(row['pairs']):
                n,q=payload['counts'][j],payload['sums'][j];gain=float(gains_from_totals(n.sum(0),q.sum(0),row['proposed'][j]));assert math.isclose(gain,pair['gain'],rel_tol=1e-9,abs_tol=1e-10)
                active=np.any(n>0,axis=1);draws.append(gains_from_totals(weights[:,active]@n[active],weights[:,active]@q[active],row['proposed'][j]))
                for k,opaque in enumerate(pair['pair']):
                    actual=np.array([sum(t['id']==opaque for t in s['tokens']) for s in public]);assert np.array_equal(actual,n[:,k]);endpoint_checks+=1
                if row['case']=='correct':
                    nn,qq=sentence_totals(changed,pair['pair'],model);assert np.array_equal(nn,n);assert np.allclose(qq,q,rtol=1e-12,atol=1e-12);predictions+=1
            draws=np.array(draws).T;assert np.array_equal(draws,payload['draws']);assert summarize(row['pairs'],draws)==row['features'];assert reference_for(public,bank[row['case']],row['case'].startswith('swap_'),row['pairs'],core)==row['reference'];replayed+=1
    for view in ['civil','expanded']:
        for case in {c['case'] for c in cases}:
            base_row=next(c for c in cases if c['block']=='base' and c['case']==case);row=next(c for c in cases if c['block']==view and c['case']==case)
            assert row['pairs'] and [p['pair'] for p in row['pairs']]==[p['pair'] for p in base_row['pairs']]
            b=np.load(OUT/'base'/(case+'.npz'));a=np.load(OUT/view/(case+'.npz'))
            assert np.array_equal(a['counts'][:,:100],b['counts']);assert np.allclose(a['sums'][:,:100],b['sums'],rtol=1e-12,atol=1e-12)
    assert policies==load(ROOT/'iteration103/policies.json')
    assert {a:evaluate102(cases,p) for a,p in policies.items()}==load(OUT/'evaluation-summary.json')
    assert {a:{c['block']+'/'+c['case']:selected(c['features'],p) for c in cases} for a,p in policies.items()}==load(OUT/'actions.json')
    # Existing100 control pair gains agree under renamed opaque IDs with the old Caesar cache.
    oldpublic=load(ROOT/'iteration97/caesar/public-clean.json');oldwords={t['id']:t['anchor'] for s in oldpublic for t in s['tokens'] if t['anchor'] in core};oldbank=load(ROOT/'iteration97/bank.json');compared=0
    for row in [c for c in cases if c['block']=='base' and c['case'] in oldbank]:
        detector=load(ROOT/'iteration97/caesar'/row['case']/'detector.json')['joint_context'];old={tuple(sorted(oldwords[i] for i in p['pair'])):p for p in detector if set(p['pair'])<=set(oldwords)}
        for p in row['pairs']:
            key=tuple(sorted(row['identities'][i] for i in p['pair']));assert math.isclose(p['gain'],old[key]['gain'],rel_tol=1e-9,abs_tol=1e-10);assert p['supported']==old[key]['supported'];compared+=1
    save(OUT/'audit.json',dict(input_hashes_verified=checked,bootstrap_cases_replayed=replayed,clean_pair_probability_recomputations=predictions,endpoint_sentence_counts_recomputed=endpoint_checks,original_caesar_pair_gains_replayed=compared,public_scored100_prefix_identical_all_views=True,original100_probability_totals_unchanged_all_cases=True,global_mapping_and_frozen_policies=True,overlap_book_excluded=True,no_new_annotations_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
