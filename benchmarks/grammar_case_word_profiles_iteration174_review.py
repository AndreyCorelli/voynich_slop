"""Independent brute-force pair selection and case-score audit."""
from benchmarks.grammar_case_word_profiles_iteration174 import *

def run():
    hashes=edges=pairs=groups=0
    for name in ['design-freeze','assignment-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    refs=load(ROOT/'iteration172/references.json');details=gzload(OUT/'details.json.gz');assignments=gzload(OUT/'case-assignments.json.gz');inventory=load(OUT/'inventory.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');group_inputs=load(OUT/'group-inputs.json');movement=load(OUT/'movement.json')
    for pool,p in POOLS.items():
        # Reconstruct both references from cached annotations, not serialized reference inputs.
        source=load(ROOT/'iteration44/annotations-truth.json');sel=load(ROOT/('iteration159' if pool=='earlier' else 'iteration168')/'selection.json');key='Cicero' if pool=='earlier' else 'fit-Cicero'
        tokens=[t for sid in sel[key]['sent_ids'] for t in source[sid]['tokens']]
        assert refs[pool]==dict(pos=[t['pos'] for t in tokens],case=[t.get('case','') for t in tokens])
        stream=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]
        salt='frames164-Cicero|' if pool=='earlier' else 'replication168-fit-Cicero|'
        assert stream==[hashlib.sha256((salt+t['word']).encode()).hexdigest() for t in tokens]
        dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;ee=dd['original']
        tags=np.array(refs[pool]['pos']);original=np.array(refs[pool]['case'])
        expected_groups={}
        for i,(word,tag) in enumerate(zip(stream,refs[pool]['pos'])):expected_groups.setdefault(word+'|'+tag,[]).append(i)
        assert group_inputs[pool]==expected_groups
        group_arrays={k:np.array(expected_groups[k]) for k in sorted(expected_groups)}
        movable=set()
        for k,ix in expected_groups.items():
            assert inventory[pool][k]==dict(Counter(refs[pool]['case'][i] for i in ix))
            if len(inventory[pool][k])>1:movable.update(ix)
        positions={g:set() for g in GROUPS}
        for e in ee:
            if e['shared_frames']<2:continue
            for f in e['frames']:
                for a in f['a_positions']:
                    for b in f['b_positions']:
                        aa=refs[pool]['pos'][a] in {'PRON','DET'};bb=refs[pool]['pos'][b] in {'PRON','DET'}
                        for g in GROUPS:
                            if g=='all' or (g=='pd_involving' and (aa or bb)) or (g=='both_pd' and aa and bb) or (g=='exactly_one_pd' and aa!=bb) or (g=='neither_pd' and not aa and not bb):positions[g].update([a,b])
        for g,pp in positions.items():
            r=movement[pool][g];assert r['positions']==sorted(pp);assert r['graph_positions']==len(pp);assert r['potentially_movable']==len(pp&movable);assert r['recognized_original_movable']==sum(i in movable and refs[pool]['case'][i] in CASES for i in pp)
            assert r['changed_by_seed']=={'case'+str(seed):sum(assignments[pool]['case'+str(seed)][i]!=refs[pool]['case'][i] for i in pp) for seed in LABEL_SEEDS}
        assert set(assignments[pool])=={'original',*('case'+str(seed) for seed in LABEL_SEEDS)}
        for view,labels in assignments[pool].items():
            if view=='original':assert labels==refs[pool]['case']
            else:
                rng=np.random.default_rng(int(view[4:]));reconstructed=original.copy()
                for k,ix in group_arrays.items():reconstructed[ix]=original[ix[rng.permutation(len(ix))]]
                assert reconstructed.tolist()==labels
            for k,ix in expected_groups.items():assert dict(Counter(labels[i] for i in ix))==inventory[pool][k]
            tt=[dict(pos=t,case=c) for t,c in zip(refs[pool]['pos'],labels)];expected={g:[] for g in GROUPS}
            for e in ee:
                if e['shared_frames']<2:continue
                framepairs=[[(tt[a],tt[b]) for a in f['a_positions'] for b in f['b_positions']] for f in e['frames']];pairs+=sum(map(len,framepairs));edges+=1
                for g in GROUPS:
                    nums=[];total=valid=matches=0
                    for pp in framepairs:
                        chosen=[]
                        for a,b in pp:
                            pd=a['pos'] in {'PRON','DET'} or b['pos'] in {'PRON','DET'}
                            both=a['pos'] in {'PRON','DET'} and b['pos'] in {'PRON','DET'}
                            if g=='all' or (g=='pd_involving' and pd) or (g=='neither_pd' and not pd) or (g=='both_pd' and both) or (g=='exactly_one_pd' and pd and not both):chosen.append((a.get('case',''),b.get('case','')))
                        cc=[(a,b) for a,b in chosen if a in {'Nom','Gen','Dat','Acc','Abl','Voc','Loc'} and b in {'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}];m=sum(a==b for a,b in cc);total+=len(chosen);valid+=len(cc);matches+=m
                        if cc:nums.append(m/len(cc))
                    expected[g].append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=len(nums),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matches,frame_macro_case_agreement=sum(nums)/len(nums) if nums else None,no_case_conflicts=matches==valid if valid else None))
                for k in ['all_occurrence_pairs','case_occurrence_pairs','matching_case_pairs']:
                    assert expected['all'][-1][k]==sum(expected[g][-1][k] for g in ['both_pd','exactly_one_pd','neither_pd'])
                    assert expected['pd_involving'][-1][k]==expected['both_pd'][-1][k]+expected['exactly_one_pd'][-1][k]
            assert expected==details[pool][view]
            for g,rows in expected.items():
                s=summary[pool][view][g];assert s==summarize_cases(rows,588 if pool=='earlier' else 857)['2'];covered=[r for r in rows if r['case_occurrence_pairs']];assert s['case_edges']==len(covered);assert s['edge_macro_frame_case_agreement']==(sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None);groups+=1
        assert summary[pool]['original']==load(ROOT/'iteration172/summary.json')[pool]['original']
        for g in GROUPS:
            vv=summary[pool];a=vv['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[vv['case'+str(seed)][g]['edge_macro_frame_case_agreement'] for seed in LABEL_SEEDS if vv['case'+str(seed)][g]['case_edges']];tail=sum(y>=x for y in nn) if x is not None else None
            assert contrasts[pool][g]==dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_min=min(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=tail,conditional_tail=(1+tail)/(1+len(LABEL_SEEDS)) if x is not None and len(nn)==len(LABEL_SEEDS) else None,min_null_case_edges=min(vv['case'+str(seed)][g]['case_edges'] for seed in LABEL_SEEDS),max_null_case_edges=max(vv['case'+str(seed)][g]['case_edges'] for seed in LABEL_SEEDS))
        print('audited',pool,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,reference_streams_aligned=2,graph_views=400,edge_records=edges,cartesian_pairs=pairs,stratum_metric_groups=groups,all_pair_partition_identities=True,all_detailed_scores_and_contrasts=True,historical_baselines_exact=True,within_word_pos_inventories_and_all_398_permutations_verified=True,all_movement_counts_verified=True))
if __name__=='__main__':run()
