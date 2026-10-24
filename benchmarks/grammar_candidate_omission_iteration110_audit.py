"""Independent ranking/stability and endpoint-sign replay for source omissions."""
from benchmarks.grammar_candidate_omission_iteration110 import *


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'predictions-freeze.json',PREVIOUS/'verification-manifest.json',SOURCE/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    source={c['case']:c for c in load(SOURCE/'calibration-cases.json') if c['block']=='full'};rows=load(OUT/'cases.json');policies=load(OUT/'policies.json');assert policies['long109']==load(PREVIOUS/'policies.json')['full'];ids=load(OUT/'candidate-catalogue.json');payloads={case:np.load(SOURCE/'full'/(case+'.npz')) for case in source};rank_checks=endpoint_checks=0
    assert len(rows)==1139 and len({(r['case'],r['omitted_id']) for r in rows})==1139
    for case in source:assert {r['omitted_id'] for r in rows if r['case']==case}=={None}|set(ids)
    for r in rows:
        c=source[r['case']];js=[j for j,p in enumerate(c['pairs']) if r['omitted_id'] not in p['pair']];assert js==r['source_pair_indices'];pairs=[c['pairs'][j] for j in js];draws=payloads[r['case']]['draws'][:,js];f=r['features'];supported=sorted([j for j,p in enumerate(pairs) if p['supported']],key=lambda j:pairs[j]['gain'],reverse=True)
        if supported:
            j=supported[0];gain=pairs[j]['gain'];gap=gain-pairs[supported[1]]['gain'] if len(supported)>1 else None;tied=len(supported)>1 and math.isclose(gain,pairs[supported[1]]['gain'],rel_tol=1e-12,abs_tol=1e-12);winner=None if tied else pairs[j]['pair'];assert f['pair']==winner and f['gain']==gain and f['gap']==gap
            if winner is not None:
                rival=[k for k in supported if k!=j];best_other=draws[:,rival].max(1) if rival else np.full(256,-np.inf);q=draws[:,j];wins=np.isfinite(q)&(q>best_other)&~np.isclose(q,best_other,rtol=1e-12,atol=1e-12);assert float(wins.mean())==f['stability']
        assert summarize(pairs,draws)==f
        expected_ref=dict(c['reference'],supported=any(p['supported'] and p['pair']==c['reference']['pair'] for p in pairs));assert expected_ref==r['reference'];assert r['true_endpoint_omitted']==bool(expected_ref['error'] and r['omitted_id'] in (expected_ref['pair'] or []));rank_checks+=1
        for arm,p in policies.items():
            pair=select_gate(f,p);assert pair==r['actions'][arm]
            if pair is not None:
                j=next(j for j,pairrow in enumerate(c['pairs']) if pairrow['pair']==pair);n=payloads[r['case']]['counts'][j].sum(0);q=payloads[r['case']]['sums'][j].sum(0)/n;expected=np.log((q+1e-12)/(1-q+1e-12))*[1 if tag=='ADP' else -1 for tag in c['proposed'][j]];m=r['mechanism'][arm];assert np.array_equal(expected,np.array(m['endpoint_margins']));assert m['one_endpoint_does_not_favor_flip']==bool(np.any(expected<=0));assert m['minimum_margin']==float(expected.min());endpoint_checks+=2
    summary=load(OUT/'summary.json');groups={k:[] for k in summary}
    for r in rows:
        if r['regime']=='complete':groups['complete'].append(r)
        else:
            groups['all_omissions'].append(r);groups['omit_'+r['omitted_word']].append(r)
            if not r['reference']['error']:groups['controls'].append(r)
            else:groups['available_errors' if r['reference']['supported'] else 'unavailable_errors'].append(r)
    assert len(groups['available_errors'])==896 and len(groups['unavailable_errors'])==128 and len(groups['controls'])==48
    aggregate_checks=0
    for name,rs in groups.items():
        for arm in policies:
            hit=sum(r['actions'][arm] is not None and r['actions'][arm]==r['reference']['pair'] for r in rs);wrong=sum(r['actions'][arm] is not None and r['actions'][arm]!=r['reference']['pair'] for r in rs);s=summary[name][arm];assert s['hit']==hit and s['wrong']==wrong and s['calls']==hit+wrong and s['n']==len(rs);assert s['clean_wrong']==sum(r['actions'][arm] is not None and not r['reference']['error'] for r in rs);assert s['unavailable_wrong']==sum(r['actions'][arm] is not None and r['reference']['error'] and not r['reference']['supported'] for r in rs);aggregate_checks+=6
    signs={}
    for arm in policies:
        buckets={}
        for r in rows:
            pair=r['actions'][arm]
            if pair is None:continue
            key=r['regime']+'/'+('hit' if pair==r['reference']['pair'] else 'wrong');b=buckets.setdefault(key,dict(selected=0,nonpositive_endpoint=0,both_positive=0));b['selected']+=1;b['nonpositive_endpoint']+=r['mechanism'][arm]['one_endpoint_does_not_favor_flip'];b['both_positive']+=not r['mechanism'][arm]['one_endpoint_does_not_favor_flip']
        signs[arm]=buckets
    assert signs==load(OUT/'endpoint-sign-audit.json')
    assert summary['available_errors']['long109']['hit']==896 # Removing competitors cannot defeat a retained winning pair here.
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,independent_rank_and_stability_replays=rank_checks,endpoint_margin_checks=endpoint_checks,aggregate_count_fields_checked=aggregate_checks,all_128_unavailable_errors_retained=True,all_48_controls_retained=True,source_classifier_inferences=0,policy_refits=0,no_author_or_new_annotation_or_reserve=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
