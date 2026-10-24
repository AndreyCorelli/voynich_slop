"""Replay complete new bank, cached PP inputs, blind recommendations and damage metrics."""
from benchmarks.grammar_anchor_swap_bank_iteration97 import *

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];bank=load(OUT/'bank.json');assert bank==remaining_bank(cat['20'],load(ROOT/'iteration93/patterns.json'));assert len(bank)==62 and sum(k.startswith('swap_') for k in bank)==59;classmodels=load(ROOT/'iteration93/models.json');ppmodels={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};policies=load(ROOT/'iteration95/policies.json');words=load(ROOT/'iteration93/types.json')['candidates'];oldpol=load(BASE/'policies.json');cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};pp_count=0;case_count=0
    for name,sentences in datasets.items():
        dataset=OUT/name.lower();public,labels=transfer_rows(sentences,anchors,'bank97-'+name,ppmodels['original']['pos_classes']);assert public==load(dataset/'public-clean.json');reference=load(dataset/'reference-rows.json');cached={}
        for path in sorted((dataset/'pp-cache').glob('*.json')):
            if path.name.endswith('.freeze.json'):continue
            for p,h in load(path.with_suffix('.freeze.json'))['inputs'].items():assert digest(p)==h,p
            payload=load(path);view=apply_delta(public,payload['delta']);assert signature(view)==path.stem;assert [t['id'] for s in view for t in s['tokens']]==[t['id'] for s in public for t in s['tokens']]
            for a,model in ppmodels.items():
                rows=infer85(query_rows(view,labels),model);assert [{k:r[k] for k in reference[0]} for r in rows]==reference;scores=compact(rows);assert scores['prior']==payload['scores'][a]['prior']
                for arm in ('pooled_pos','left'):assert np.allclose(scores[arm],payload['scores'][a][arm],rtol=1e-10,atol=1e-12)
                pp_count+=1
            cached[path.stem]=payload['scores']
        clean=cached[signature(public)];lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words}
        for j,(case,replacements) in enumerate(bank.items()):
            folder=dataset/case;corrupted=perturb(public,replacements,anchors)
            for p,h in load(folder/'detector-freeze.json')['inputs'].items():assert digest(p)==h,p
            stored=load(folder/'detector.json');replay=pair_scores(corrupted,independent_records(corrupted,words,classmodels),classmodels)
            for arm in PAIR_ARMS:
                aa={tuple(r['pair']):r for r in stored[arm]};bb={tuple(r['pair']):r for r in replay[arm]};assert aa.keys()==bb.keys()
                for pair,r in aa.items():assert r['supported']==bb[pair]['supported'];assert math.isclose(r['gain'],bb[pair]['gain'],rel_tol=1e-10,abs_tol=1e-12)
            selected={arm:recommend(stored[arm],float('inf') if policy['threshold'] is None else policy['threshold']) for arm,policy in policies.items()};actions=load(folder/'actions.json');assert actions['selected']==selected;before_sig=signature(corrupted);assert actions['before']==before_sig;before=cached[before_sig];ref=dict(error=case.startswith('swap_'),pair=sorted(lookup[w] for w in replacements) if case.startswith('swap_') and all(w in lookup for w in replacements) else None);assert actions['reference']==ref;assert actions['affected_tokens']==sum(x!=y for s,t in zip(public,corrupted) for x,y in zip(s['tokens'],t['tokens']));result={}
            for arm,pair in selected.items():
                repaired=swap_assignments(corrupted,pair);after_sig=signature(repaired);assert actions['after'][arm]==after_sig;after=cached[after_sig];pair_eval=pair_metrics(stored[arm],float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold'],ref);result[arm]=dict(pair=pair_eval,pp={a:{p:effect(expand(reference,after[a]),expand(reference,before[a]),expand(reference,clean[a]),cut) for p,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()},nearest_f1=counts(expand(reference,after['original']),'pp','left',oldpol['left']['standard']['f1']['threshold']))
                if pair is None:assert all(not any(e['changes'].values()) for pols in result[arm]['pp'].values() for e in pols.values())
                if pair_eval['hit']:assert after_sig==signature(public)
            assert result==load(folder/'evaluation.json');summary[name+'/'+case]=result;case_count+=1
            if j%20==0:print('replayed',name,j+1,'/',len(bank),flush=True)
    assert case_count==186 and summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all186cases_replayed=True,all6detectorarms_and_fixed_thresholds=True,unique_pp_model_inputs_replayed=pp_count,source_defined_bank_excludes5previous_pairs=True,blind_repairs_and_loss_metrics_replayed=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
