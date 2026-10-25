"""Independent brute-force pair selection and case-score audit."""
from benchmarks.grammar_case_subfamilies_iteration172 import *

def run():
    hashes=edges=pairs=groups=0
    for name in ['design-freeze','reference-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    refs=load(OUT/'references.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');compositions=load(OUT/'composition.json')
    for pool,p in POOLS.items():
        # Reconstruct both references from cached annotations, not serialized reference inputs.
        source=load(ROOT/'iteration44/annotations-truth.json');sel=load(ROOT/('iteration159' if pool=='earlier' else 'iteration168')/'selection.json');key='Cicero' if pool=='earlier' else 'fit-Cicero'
        tokens=[t for sid in sel[key]['sent_ids'] for t in source[sid]['tokens']]
        assert refs[pool]==dict(pos=[t['pos'] for t in tokens],case=[t.get('case','') for t in tokens])
        stream=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]
        salt='frames164-Cicero|' if pool=='earlier' else 'replication168-fit-Cicero|'
        assert stream==[hashlib.sha256((salt+t['word']).encode()).hexdigest() for t in tokens]
        dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;trans=load(p['transforms'])[p['key']]
        for view,ee in dd.items():
            ix=trans[view];tt=tokens if ix is None else [tokens[j] for j in ix];expected={g:[] for g in GROUPS};counts={k:dict(all_pairs=0,case_pairs=0,matching_cases=0) for k in PAIR_KEYS}
            for e in ee:
                if e['shared_frames']<2:continue
                framepairs=[[(tt[a],tt[b]) for a in f['a_positions'] for b in f['b_positions']] for f in e['frames']];pairs+=sum(map(len,framepairs));edges+=1
                for pp in framepairs:
                    for a,b in pp:
                        k='/'.join(sorted([a['pos'],b['pos']]));r=counts[k];r['all_pairs']+=1
                        if a.get('case','') in CASES and b.get('case','') in CASES:r['case_pairs']+=1;r['matching_cases']+=int(a.get('case','')==b.get('case',''))
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
            assert counts==compositions[pool][view]
            assert expected==details[pool][view]
            for old,new in [('all_pairs','all_occurrence_pairs'),('case_pairs','case_occurrence_pairs'),('matching_cases','matching_case_pairs')]:assert sum(r[old] for r in counts.values())==sum(r[new] for r in expected['all'])
            for g,rows in expected.items():
                s=summary[pool][view][g];assert s==summarize_cases(rows,588 if pool=='earlier' else 857)['2'];covered=[r for r in rows if r['case_occurrence_pairs']];assert s['case_edges']==len(covered);assert s['edge_macro_frame_case_agreement']==(sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None);groups+=1
        historical=load(ROOT/'iteration171/summary.json')[pool]
        for v,gg in historical.items():
            for g in ['all','pd_involving','neither_pd']:assert summary[pool][v][g]==gg[g]
        for g in GROUPS:
            a=summary[pool]['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[summary[pool]['word'+str(s)][g]['edge_macro_frame_case_agreement'] for s in SEEDS if summary[pool]['word'+str(s)][g]['case_edges']]
            assert contrasts[pool][g]==dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=sum(y>=x for y in nn) if x is not None else None)
        print('audited',pool,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,reference_streams_aligned=2,graph_views=34,edge_records=edges,cartesian_pairs=pairs,stratum_metric_groups=groups,all_pair_partition_identities=True,all_detailed_scores_and_contrasts=True,historical_baselines_exact=True,all_153_pos_pair_counts_verified=True))
if __name__=='__main__':run()
