"""Summarize matched-clean attribution and independently verify all clean scores."""
from benchmarks.grammar_evidence_attribution_iteration115 import *
from voynich_smt.paired_anchor_class import target_features


def run():
    hashes=0
    for name in ['design-freeze','selection-freeze','inference-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    for iteration in ['102','113']:
        for p,h in load(ROOT/('iteration'+iteration)/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p;hashes+=1
    chosen=load(OUT/'selections.json');rows=load(OUT/'attributions.json');cache=load(OUT/'clean-joint-pair-cache.json');single=load(OUT/'clean-singletons.json');pol={a:load(ROOT/('iteration'+a)/'policies.json')['full'] for a in ['109','111']};model=load(ROOT/'iteration93/models.json')['context'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];d=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];publics={'full':ag.public_sentences([dict(sent_id=i,**d[i]) for i in ids],anchors,'cal98-full')};words=load(ROOT/'iteration93/types.json')['candidates'];publics.update({w:load(ROOT/'iteration113'/('public-'+w+'.json')) for w in words});lookup={t['id']:t['anchor'] for s in publics['full'] for t in s['tokens'] if t['anchor'] in words};caseinputs=load(ROOT/'iteration110/cases.json');literal=load(ROOT/'iteration113/cases.json');bank=load(ROOT/'iteration98/calibration-bank.json');source={r['case']:r for r in load(ROOT/'iteration102/calibration-cases.json') if r['block']=='full'};litlookup={(r['removed_word'],r['case']):r for r in literal};selected={s['key']:s for s in chosen};assert len(chosen)==2211
    for s in chosen:
        assert s['actions']=={a:gate(s['features'],p) for a,p in pol.items()}
    recomputed=0
    for entry in cache.values():
        pair=entry['pair'];p=publics[entry['physical_view']];rr=target_features(p,set(pair));pred=ag.predict([r['features'] for r in rr],model)
        for k,opaque in enumerate(pair):
            indices=[i for i,r in enumerate(rr) if r['word']==opaque];assert len(indices)==entry['counts'][k];assert abs(float(pred[indices,1].sum())-entry['sums'][k])<1e-10;recomputed+=1
    for view,ss in single.items():
        p=publics[view]
        for opaque,e in ss.items():
            rr=target_features(p,{opaque});pred=ag.predict([r['features'] for r in rr],model);q=float(pred[:,1].mean());tag=next(t['tag'] for s in p for t in s['tokens'] if t['id']==opaque);margin=math.log((q+1e-12)/(1-q+1e-12))*(1 if tag=='ADP' else -1);assert abs(margin-e['gain'])<1e-10 and len(rr)==e['n'];assert len({r['sid'] for r in rr})==e['sentences'];recomputed+=1
    endpoints=0
    for r in rows:
        assert all(r[k]==selected[r['key']][k] for k in selected[r['key']]);assert r['pair']==next(p for p in r['actions'].values() if p is not None)
        physical=r['physical_view'];record=source[r['case']] if r['kind']=='source' else litlookup[physical,r['case']];path=(ROOT/'iteration102/full' if r['kind']=='source' else ROOT/'iteration113'/physical)/(r['case']+'.npz');z=np.load(path);j=next(j for j,p in enumerate(record['pairs']) if p['pair']==r['pair']);n=z['counts'][j].sum(0);q=z['sums'][j].sum(0);z.close();entry=cache[physical+'/'+'+'.join(r['pair'])]
        for k,e in enumerate(r['endpoints']):
            p0=entry['sums'][k]/entry['counts'][k];p1=q[k]/n[k];s0=1 if e['clean_tag']=='ADP' else -1;s1=1 if e['proposed_tag']=='ADP' else -1;m0=math.log((p0+1e-12)/(1-p0+1e-12))*s0;m1=math.log((p1+1e-12)/(1-p1+1e-12))*s1;counter=m0*s0*s1
            assert abs(m0-e['clean_flip_margin'])<1e-10 and abs(m1-e['corrupt_flip_margin'])<1e-10 and abs(m1-counter-e['context_delta'])<1e-10;assert e['preexisting_false_flip']==(s0==s1 and m0>1e-12);assert e['observed_false_flip']==(s0==s1 and m1>1e-12);endpoints+=1
    groups={}
    for regime in ['full','catalogue','literal']:
        for arm in pol:
            for outcome in ['hit','wrong']:
                rr=[r for r in rows if r['regime']==regime and r['actions'][arm] is not None and (r['actions'][arm]==r['reference']['pair'])==(outcome=='hit')]
                innocent=[e for r in rr for e in r['endpoints'] if not e['class_changed']];positive=[e for e in innocent if e['observed_false_flip']]
                groups[regime+'/'+arm+'/'+outcome]=dict(calls=len(rr),unsupported=sum(not r['reference']['supported'] for r in rr),literal_absence=sum(r['true_endpoint_absent'] for r in rr),class_changed_endpoints=sum(e['class_changed'] for r in rr for e in r['endpoints']),unchanged_endpoints=len(innocent),unchanged_positive_observed=len(positive),unchanged_positive_already_clean=sum(e['preexisting_false_flip'] for e in positive),unchanged_positive_new_in_context=sum(not e['preexisting_false_flip'] for e in positive),unchanged_positive_invariant=sum(e['context_invariant'] for e in positive),wrong_calls_with_preexisting_positive=sum(any(e['preexisting_false_flip'] and e['observed_false_flip'] for e in r['endpoints']) for r in rr),unique_physical_pairs=len({(r['physical_view'],tuple(r['pair'])) for r in rr}),unique_innocent_viewtypes=len({(r['physical_view'],e['opaque']) for r in rr for e in r['endpoints'] if not e['class_changed']}))
    clean_prevalence={};bytype={}
    for view,ss in single.items():
        supported=[r for r in ss.values() if r['supported']];false=[i for i,r in ss.items() if r['supported'] and r['gain']>1e-12];clean_prevalence[view]=dict(present_types=len(ss),supported_types=len(supported),false_flip_types=len(false),false_flip_words=[lookup[i] for i in false])
        for i,e in ss.items():
            b=bytype.setdefault(lookup[i],dict(present_views=0,supported_views=0,false_flip_supported_views=0,gains=[]));b['present_views']+=1;b['supported_views']+=e['supported'];b['false_flip_supported_views']+=e['supported'] and e['gain']>1e-12;b['gains'].append(e['gain'])
    for b in bytype.values():b['minimum_gain']=min(b.pop('gains')); # all views are correlated diagnostics
    save(OUT/'summary.json',dict(groups=groups,clean_singleton_prevalence_by_view=clean_prevalence,clean_singleton_by_type=bytype))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,frozen_actions_replayed=len(chosen)*2,clean_endpoint_scores_independently_recomputed=recomputed,selected_endpoint_attributions_verified=endpoints,selected_viewcases=len(rows),unique_clean_pair_views=len(cache),no_policy_change=True))
    print(json.dumps(groups,indent=2));print('CLEAN',clean_prevalence);print('AUDIT',load(OUT/'audit.json'))
if __name__=='__main__':run()
