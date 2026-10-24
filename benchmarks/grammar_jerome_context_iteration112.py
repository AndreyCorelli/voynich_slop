"""Frozen-policy Jerome FORM-only context replication."""
from benchmarks.grammar_omission_gate_iteration111 import *
from voynich_smt.form_only_context import project
OUT=ROOT/'iteration112'
RAW=Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu')


def run():
    assert not OUT.exists();OUT.mkdir()
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/form_only_context.py'),RAW,ROOT/'iteration40/manifest.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration49/manifest.json',Path('experiments/holdouts/grammar-construction-next.json'),ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration85/anchor-budgets.json',BASE/'models.json',ROOT/'iteration89/models.json',ROOT/'iteration109/policies.json',ROOT/'iteration111/policies.json',ROOT/'iteration111/routing.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design="Jerome second-author DEVELOPMENT replication, no fresh confirmation. Original100 cached40 labels scored ONLY; no new grammar labels. Raw CoNLL-U streaming uses source/sent_id metadata and integer-ID FORM only, alphabetic-content punctuation filter; never POS/FEATS/HEAD/DEPREL. Exclude ALL200reserve and ALL49sourcepartitionIDs BEFORE FORM projection. Check original100 projection exactly equals40 word sequences. Exclude original IDs, exact duplicate normalized sequences and original-sequence duplicates. Sort eligible unique sentences by SHA256('jerome112|'+sid), take first729, append after original100. Inherited treebank segmentation privilege. Freeze selection/publics before scores. Both frozen109 highcoverage and111 strict policies with existing shortOFF and long>=829 bands, NO refit/target thresholds. All64swap errors+3controls in base100 and expanded829, fixed195 suppliedanchors, fixed93 joint pair classifier; 256 sentence bootstraps seed112000+viewindex shared across pairs/cases. Original97 Jerome salt for exact original-view/cache comparison. Apply EVERY recommendation blindly with full context assignments; score ONLY original100 PP with fixed85/89 models and cutoffs. Report affected/zeroaffected and unsupported errors; no new nuclei or clean coverage claim. No reserve features/scores, sealed lexical test or new annotations."))
    ids=load(ROOT/'iteration40/manifest.json')['split_ids']['Jerome'];truth=load(ROOT/'iteration40/data-truth.json')
    reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows}
    source={sid for rows in load(ROOT/'iteration49/manifest.json')['partitions']['0'].values() for sid in rows}
    assert not set(ids)&(reserved|source)
    with RAW.open() as f: projected=project(f,"Jerome's Vulgate",reserved|source)
    lookup={s['sent_id']:s for s in projected};assert len(lookup)==len(projected)
    scored=[dict(sent_id=sid,tokens=[dict(word=t['word']) for t in truth[sid]]) for sid in ids]
    assert all(lookup[s['sent_id']]==s for s in scored)
    seq=lambda s:tuple(t['word'] for t in s['tokens'])
    seen={seq(s) for s in scored};extra=[]
    for s in sorted(projected,key=lambda s:hashlib.sha256(('jerome112|'+s['sent_id']).encode()).hexdigest()):
        if s['sent_id'] not in ids and seq(s) not in seen:extra.append(s);seen.add(seq(s))
    assert len(extra)>=729;extra=extra[:729]
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];public=ag.public_sentences(scored,anchors,'bank97-Jerome')
    assert public==load(ROOT/'iteration97/jerome/public-clean.json')
    publics=dict(base=public,expanded=public+ag.public_sentences(extra,anchors,'bank97-Jerome'))
    save(OUT/'context-selection.json',dict(eligible_projected=len(projected),added_ids=[s['sent_id'] for s in extra],original_ids=ids,original_projection_exact=True,reserved_ids_excluded=len(reserved),source_ids_excluded=len(source),views={v:dict(sentences=len(p),tokens=sum(len(s['tokens']) for s in p)) for v,p in publics.items()}))
    policies={a:load(ROOT/('iteration'+a)/'policies.json') for a in ['109','111']};bands=load(ROOT/'iteration111/routing.json')
    save(OUT/'policies.json',policies);save(OUT/'routing.json',bands)
    for v,p in publics.items():save(OUT/('public-'+v+'.json'),p)
    save(OUT/'context-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'context-selection.json',OUT/'policies.json',OUT/'routing.json']+list(OUT.glob('public-*.json'))}))
    words=load(ROOT/'iteration93/types.json')['candidates'];bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];cases=[];basecounts=Counter(t['anchor'] for s in public for t in s['tokens'])
    for vi,(view,context) in enumerate(publics.items()):
        folder=OUT/view;folder.mkdir();weights=np.random.default_rng(112000+vi).multinomial(len(context),np.full(len(context),1/len(context)),size=256);np.savez_compressed(folder/'weights.npz',weights=weights)
        for ci,(case,replacements) in enumerate(bank.items()):
            row=compute(context,case,replacements,anchors,words,model,weights,folder)
            row.update(block=view,regime=view,context_sentences=len(context),scored_affected_tokens=sum(basecounts[w] for w in replacements));cases.append(row)
            if ci%5==0:print(view,ci+1,'/',len(bank),flush=True)
    save(OUT/'pair-cases.json',cases)
    actions={a:{c['block']+'/'+c['case']:select_conditional(c['features'],c['context_sentences'],p,bands) for c in cases} for a,p in policies.items()}
    save(OUT/'actions.json',actions);save(OUT/'pair-summary.json',{a:evaluate109(cases,p,bands) for a,p in policies.items()})
    save(OUT/'pair-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'pair-cases.json',OUT/'actions.json']+list(OUT.glob('*/*.json'))+list(OUT.glob('*/*.npz'))}))
    print('PAIRS',load(OUT/'pair-summary.json'),flush=True)
    labels=load(ROOT/'iteration97/jerome/reference-rows.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};store=OUT/'pp-cache';store.mkdir();cache={};sources={}
    def predictions(view):
        sig=signature(view)
        if sig not in cache:
            path=ROOT/'iteration97/jerome/pp-cache'/(sig+'.json')
            if path.exists():
                payload=load(path);assert apply_delta(public,payload['delta'])==view;sources[sig]=str(path)
            else:
                payload=dict(delta=delta_public(public,view),scores={a:compact(infer85(query_rows(view,labels),m)) for a,m in models.items()});sources[sig]='new'
            save(store/(sig+'.json'),payload);cache[sig]={a:expand(labels,s) for a,s in payload['scores'].items()}
        return sig,cache[sig]
    clean_sig,clean=predictions(public);transforms={}
    for c in cases:
        key=c['block']+'/'+c['case'];context=perturb(publics[c['block']],bank[c['case']],anchors);before=context[:100];bs,_=predictions(before);arms={}
        for a in policies:
            pair=actions[a][key];after=repair_prefix(before,context,pair);sig,_=predictions(after);arms[a]=dict(pair=pair,after=sig,changed_tokens=sum(x!=y for s,t in zip(before,after) for x,y in zip(s['tokens'],t['tokens'])))
        transforms[key]=dict(before=bs,arms=arms)
    save(OUT/'transforms.json',transforms);save(OUT/'cache-sources.json',sources)
    save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'actions.json',OUT/'transforms.json',OUT/'cache-sources.json']+list(store.glob('*.json'))}))
    evaluation={}
    for c in cases:
        key=c['block']+'/'+c['case'];t=transforms[key];before=cache[t['before']];evaluation[key]={}
        for a,info in t['arms'].items():
            after=cache[info['after']];pair=info['pair'];hit=pair is not None and pair==c['reference']['pair']
            evaluation[key][a]=dict(pair=dict(selected=pair,hit=int(hit),wrong=int(pair is not None and not hit),abstain=pair is None,reference_supported=c['reference']['supported']),changed_tokens=info['changed_tokens'],scored_affected_tokens=c['scored_affected_tokens'],public_equals_clean=info['after']==clean_sig,pp={m:{name:dict(effect(after[m],before[m],clean[m],cut),maximum_probability_difference_from_clean=max(abs(x['scores']['pooled_pos']['pp']-y['scores']['pooled_pos']['pp']) for x,y in zip(after[m],clean[m]))) for name,cut in cuts.items()} for m,cuts in PP_SETTINGS.items()})
    save(OUT/'evaluation.json',evaluation);save(OUT/'run-summary.json',dict(cases=len(cases),scored_sentences=100,scored_tokens=len(labels),unique_pp_inputs=len(cache),new_pp_inputs=sum(s=='new' for s in sources.values())))
    print('DONE',load(OUT/'run-summary.json'),flush=True)
if __name__=='__main__':run()
