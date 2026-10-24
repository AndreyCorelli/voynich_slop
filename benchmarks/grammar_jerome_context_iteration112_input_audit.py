"""Reconstruct FORM-only selection and verify cached/new inference provenance."""
from benchmarks.grammar_jerome_context_iteration112 import *


def run():
    selection=load(OUT/'context-selection.json');ids=selection['original_ids'];truth=load(ROOT/'iteration40/data-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};source={i for rows in load(ROOT/'iteration49/manifest.json')['partitions']['0'].values() for i in rows}
    with RAW.open() as f: projected=project(f,"Jerome's Vulgate",reserved|source)
    scored=[dict(sent_id=i,tokens=[dict(word=t['word']) for t in truth[i]]) for i in ids];lookup={s['sent_id']:s for s in projected};assert all(lookup[s['sent_id']]==s for s in scored)
    seq=lambda s:tuple(t['word'] for t in s['tokens'])
    seen={seq(s) for s in scored};extra=[]
    for s in sorted(projected,key=lambda s:hashlib.sha256(('jerome112|'+s['sent_id']).encode()).hexdigest()):
        if s['sent_id'] not in ids and seq(s) not in seen:extra.append(s);seen.add(seq(s))
    extra=extra[:729];assert [s['sent_id'] for s in extra]==selection['added_ids'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];public=load(OUT/'public-base.json');assert ag.public_sentences(scored,anchors,'bank97-Jerome')==public;assert public+ag.public_sentences(extra,anchors,'bank97-Jerome')==load(OUT/'public-expanded.json')
    labels=load(ROOT/'iteration97/jerome/reference-rows.json');sources=load(OUT/'cache-sources.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};new=0
    for sig,path in sources.items():
        payload=load(OUT/'pp-cache'/(sig+'.json'));view=apply_delta(public,payload['delta']);assert signature(view)==sig
        if path!='new':assert payload==load(path)
        else:
            for arm,model in models.items():
                expected=compact(infer85(query_rows(view,labels),model));assert np.allclose(expected['pooled_pos'],payload['scores'][arm]['pooled_pos'],rtol=1e-12,atol=1e-12);assert expected['left']==payload['scores'][arm]['left'];new+=1
    bootstrap=0
    for c in load(OUT/'pair-cases.json'):
        z=np.load(OUT/c['block']/(c['case']+'.npz'));w=np.load(OUT/c['block']/'weights.npz')['weights']
        for i,(n,q) in enumerate(zip(z['counts'],z['sums'])):
            active=np.any(n>0,axis=1);expected=gains_from_totals(w[:,active]@n[active],w[:,active]@q[active],c['proposed'][i]);assert np.allclose(expected,z['draws'][:,i],equal_nan=True,rtol=1e-12,atol=1e-12);bootstrap+=1
    save(OUT/'input-audit.json',dict(form_selection_reconstructed=True,original_projection_exact=True,reserved_and_source_ids_excluded_before_projection=True,publics_reconstructed=True,verified_pp_payloads=len(sources),new_model_inferences_recomputed=new,pair_bootstrap_columns_recomputed=bootstrap))
    print(load(OUT/'input-audit.json'))
if __name__=='__main__':run()
