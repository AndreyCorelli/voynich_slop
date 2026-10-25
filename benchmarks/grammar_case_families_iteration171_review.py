"""Independent brute-force pair selection and case-score audit."""
from benchmarks.grammar_case_families_iteration171 import *

def run():
    hashes=edges=pairs=groups=0
    for name in ['design-freeze','reference-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    refs=load(OUT/'references.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json')
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
            ix=trans[view];tt=tokens if ix is None else [tokens[j] for j in ix];expected={g:[] for g in GROUPS}
            for e in ee:
                if e['shared_frames']<2:continue
                framepairs=[[(tt[a],tt[b]) for a in f['a_positions'] for b in f['b_positions']] for f in e['frames']];pairs+=sum(map(len,framepairs));edges+=1
                for g in GROUPS:
                    nums=[];total=valid=matches=0
                    for pp in framepairs:
                        chosen=[]
                        for a,b in pp:
                            pd=a['pos'] in {'PRON','DET'} or b['pos'] in {'PRON','DET'}
                            nom=a['pos'] in {'NOUN','PROPN','ADJ','NUM'} and b['pos'] in {'NOUN','PROPN','ADJ','NUM'}
                            if g=='all' or (g=='pd_involving' and pd) or (g=='neither_pd' and not pd) or (g=='both_nominal' and not pd and nom) or (g=='other_neither' and not pd and not nom):chosen.append((a.get('case',''),b.get('case','')))
                        cc=[(a,b) for a,b in chosen if a in {'Nom','Gen','Dat','Acc','Abl','Voc','Loc'} and b in {'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}];m=sum(a==b for a,b in cc);total+=len(chosen);valid+=len(cc);matches+=m
                        if cc:nums.append(m/len(cc))
                    expected[g].append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=len(nums),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matches,frame_macro_case_agreement=sum(nums)/len(nums) if nums else None,no_case_conflicts=matches==valid if valid else None))
                for k in ['all_occurrence_pairs','case_occurrence_pairs','matching_case_pairs']:
                    assert expected['all'][-1][k]==sum(expected[g][-1][k] for g in ['pd_involving','both_nominal','other_neither'])
                    assert expected['neither_pd'][-1][k]==expected['both_nominal'][-1][k]+expected['other_neither'][-1][k]
            assert expected==details[pool][view]
            for g,rows in expected.items():
                s=summary[pool][view][g];assert s==summarize_cases(rows,588 if pool=='earlier' else 857)['2'];covered=[r for r in rows if r['case_occurrence_pairs']];assert s['case_edges']==len(covered);assert s['edge_macro_frame_case_agreement']==(sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None);groups+=1
        historical=load(ROOT/('iteration166' if pool=='earlier' else 'iteration168')/'summary.json');baseline=historical['Cicero'] if pool=='earlier' else historical['fit-Cicero']['5']
        for v,r in baseline.items():assert summary[pool][v]['all']==r['2']
        for g in GROUPS:
            a=summary[pool]['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[summary[pool]['word'+str(s)][g]['edge_macro_frame_case_agreement'] for s in SEEDS if summary[pool]['word'+str(s)][g]['case_edges']]
            assert contrasts[pool][g]==dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=sum(y>=x for y in nn) if x is not None else None)
        print('audited',pool,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,reference_streams_aligned=2,graph_views=34,edge_records=edges,cartesian_pairs=pairs,stratum_metric_groups=groups,all_pair_partition_identities=True,all_detailed_scores_and_contrasts=True,historical_baselines_exact=True))
if __name__=='__main__':run()
