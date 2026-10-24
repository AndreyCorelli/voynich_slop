"""Replay eligibility factorials, exact logits, pooling arithmetic and parent invariance."""
from benchmarks.grammar_anchor_merge_iteration101 import *


def close(a,b):
    if isinstance(a,dict):assert a.keys()==b.keys();[close(a[k],b[k]) for k in a]
    elif isinstance(a,list):assert len(a)==len(b);[close(x,y) for x,y in zip(a,b)]
    elif isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12),(a,b)
    else:assert a==b,(a,b)


def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=load(PREVIOUS/'core.json');blocks=load(PREVIOUS/'blocks.json');availability=load(PREVIOUS/'availability.json');bank={case:m for case,m in load(ROOT/'iteration98/calibration-bank.json').items() if not case.startswith('swap_') or set(m)<=set(core)};cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];model=load(ROOT/'iteration93/models.json')['context'];groups={sid:'100-'+str(i) for i in range(4) for sid in blocks['100-'+str(i)]};factorial={};summary={};traces={};invariant={};focus_comparisons=0;endpoint_checks=0
    for merge in range(2):
        left='100-'+str(2*merge);right='100-'+str(2*merge+1);merged='200-'+str(merge);sets=eligibility_sets(availability[left]['core_supported'],availability[right]['core_supported']);assert sets==load(OUT/(merged+'-eligibility.json'))
        for view in (left,right,merged):
            base,_=public101(data,blocks[view],anchors,view,{});inverse={t['id']:t['anchor'] for s in base for t in s['tokens'] if t['anchor'] in core}
            for case,replacements in bank.items():
                scores=load(PREVIOUS/view/(case+'.json'))['scores'];ref=reference_for(base,replacements,case.startswith('swap_'),scores,core);arms={}
                for gate,allowed in sets.items():
                    ss=eligible_pairs(scores,allowed,inverse);r=curve_metrics(ss,ref,cut);arms[gate]=dict(all=r,common=r if not ref['error'] or set(replacements)<=set(sets['intersection']) else None)
                factorial[merged+'/'+view+'/'+case]=arms
    assert factorial==load(OUT/'factorial.json')
    for block,ids in blocks.items():
        base,_=public101(data,ids,anchors,block,{});lookup={t['anchor']:t['id'] for s in base for t in s['tokens'] if t['anchor'] in core};inverse={v:k for k,v in lookup.items()}
        for case,replacements in bank.items():
            path=OUT/block/(case+'.json')
            for p,h in load(OUT/block/(case+'.freeze.json'))['inputs'].items():assert digest(p)==h,p
            stored=load(path);assert stored['identities']==inverse;_,public=public101(data,ids,anchors,block,replacements);proposed={t['id']:t['tag'] for s in public for t in s['tokens'] if t['id'] in inverse};cached={tuple(r['pair']):r for r in load(PREVIOUS/block/(case+'.json'))['scores'] if set(r['pair'])<=set(inverse)};assert len(stored['traces'])==len(cached)
            for t in stored['traces']:
                replay=trace_pair(public,t['pair'],proposed,model,lookup.get('ex'),groups);replay['supported']=cached[tuple(t['pair'])]['supported'];close(replay,t);assert math.isclose(t['gain'],cached[tuple(t['pair'])]['gain'],rel_tol=1e-10,abs_tol=1e-12)
                semantic=tuple(sorted(inverse[i] for i in t['pair']))
                for e in t['endpoints']:
                    weighted=np.sum([g['n']*np.asarray(g['mean']) for g in e['groups'].values()],axis=0)/e['n'];assert np.allclose(weighted,e['mean'],rtol=1e-10,atol=1e-12);endpoint_checks+=1
                for occurrence in t['focus_occurrences']:
                    key=(case,semantic,occurrence['sid'],occurrence['index'])
                    if key in invariant:close(occurrence,invariant[key]);focus_comparisons+=1
                    else:invariant[key]=occurrence
            traces[block+'/'+case]=stored['traces']
        print('replayed traces',block,flush=True)
    equal={}
    for merge in range(2):
        block='200-'+str(merge);sets=load(OUT/(block+'-eligibility.json'));base,_=public101(data,blocks[block],anchors,block,{});inverse={t['id']:t['anchor'] for s in base for t in s['tokens'] if t['anchor'] in core}
        for case,replacements in bank.items():
            rows=traces[block+'/'+case];ss=[dict(pair=t['pair'],gain=equal_group_gain(t),supported=t['supported']) for t in rows];ref=reference_for(base,replacements,case.startswith('swap_'),ss,core);equal[block+'/'+case]={g:curve_metrics(eligible_pairs(ss,a,inverse),ref,cut) for g,a in sets.items()}
            for t in rows:
                semantic=tuple(sorted(inverse[i] for i in t['pair']))
                for e in t['endpoints']:
                    word=inverse[e['id']]
                    for group,v in e['groups'].items():
                        parent=load(OUT/group/(case+'.json'));pinv=parent['identities'];pt=next(x for x in parent['traces'] if tuple(sorted(pinv[i] for i in x['pair']))==semantic);pe=next(x for x in pt['endpoints'] if pinv[x['id']]==word);assert v['n']==pe['n'];assert np.allclose(v['mean'],pe['mean'],rtol=1e-10,atol=1e-12)
    assert equal==load(OUT/'equal-parent.json')
    for key,arms in factorial.items():
        merge,view,case=key.split('/')
        for gate,values in arms.items():
            for stratum,row in values.items():
                if row is not None:summary.setdefault(merge+'/'+view+'/'+gate+'/'+stratum,[]).append(row)
    assert {k:aggregate(v) for k,v in summary.items()}==load(OUT/'factorial-summary.json');assert load(OUT/'run-summary.json')==dict(trace_scenarios=162,factorial_scenarios=108,equal_parent_scenarios=36);checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all162trace_and108factorial_and36equal_parent_cases_replayed=True,pooled_endpoint_reconstructions=endpoint_checks,unchanged_occurrence_feature_probability_comparisons=focus_comparisons,parent_means_reconstruct_merged=True,prior_input_hashes_verified=checked,no_policy_change_or_reserve_scoring=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
