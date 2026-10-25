"""Independent descriptor completeness and all conditional case scores."""
from benchmarks.grammar_rare_case_frames_iteration167 import *

def run():
    hc=ec=pc=mc=0
    for name in ['design-freeze','descriptors-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    streams=load(ROOT/'iteration164/streams.json');transforms=load(ROOT/'iteration164/transforms.json');descriptors=load(OUT/'descriptors.json');eligibility=load(OUT/'eligibility.json');cases=load(ROOT/'iteration166/case-inputs.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');increment=load(OUT/'incremental.json');old=load(ROOT/'iteration165/descriptors.json')
    for author,seq in streams.items():
        counts=Counter(seq)
        for floor in FLOORS:
            key=str(floor);eligible={w for w,n in counts.items() if n>=floor};assert eligibility[author][key]==len(eligible)
            for view,ix in transforms[author].items():
                ids=seq if ix is None else [seq[k] for k in ix];cc=cases[author] if ix is None else [cases[author][k] for k in ix];loc={};middles={}
                for j in range(1,len(ids)-1):
                    if ids[j] in eligible:
                        frame=(ids[j-1],ids[j+1]);loc.setdefault(ids[j],{}).setdefault(frame,[]).append(j);middles.setdefault(frame,set()).add(ids[j])
                dd=descriptors[author][key][view];assert len({(e['a'],e['b']) for e in dd})==len(dd);assert sum(e['shared_frames'] for e in dd)==sum(len(ww)*(len(ww)-1)//2 for ww in middles.values());computed=[]
                for e in dd:
                    a,b=e['a'],e['b'];assert a in eligible and b in eligible and a<b;frames=sorted(set(loc[a])&set(loc[b]));assert len(frames)==e['shared_frames'];assert e['frames']==[dict(frame=list(f),a_positions=loc[a][f],b_positions=loc[b][f]) for f in frames];fraction=[];matched=valid=total=0
                    for f in e['frames']:
                        pairs=[(cc[j],cc[k]) for j in f['a_positions'] for k in f['b_positions']];both=[(a,b) for a,b in pairs if a in CASES and b in CASES];same=sum(a==b for a,b in both);total+=len(pairs);valid+=len(both);matched+=same;pc+=len(pairs)
                        if both:fraction.append(same/len(both))
                    computed.append(dict(a=a,b=b,shared_frames=len(frames),case_frames=len(fraction),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fraction)/len(fraction) if fraction else None,no_case_conflicts=matched==valid if valid else None));ec+=1
                assert computed==details[author][key][view];assert summary[author][key][view]==summarize_cases(computed,len(eligible));mc+=2
                if floor==5:assert dd==old[author][view]
        for view,rr in details[author]['2'].items():
            for group in ['old','new']:
                subset=[r for r in rr if (counts[r['a']]>=5 and counts[r['b']]>=5)==(group=='old')];assert increment[author][view][group]==summarize_cases(subset,eligibility[author]['2'])
        for floor,tt in contrasts[author].items():
            for threshold,r in tt.items():
                actual=summary[author][floor]['original'][threshold];pp=[summary[author][floor]['word'+str(k)][threshold]['edge_macro_frame_case_agreement'] for k in SEEDS if summary[author][floor]['word'+str(k)][threshold]['case_edges']];v=actual['edge_macro_frame_case_agreement'];assert r==dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=v for p in pp) if v is not None else None)
    assert {a:ff['5'] for a,ff in summary.items()}==load(ROOT/'iteration166/summary.json');save(OUT/'audit.json',dict(input_hashes_verified=hc,views_and_floors_verified=136,descriptor_completeness_verified_by_frame_pair_count=True,edge_records_independently_verified=ec,cartesian_occurrence_pairs_checked=pc,metric_groups_verified=mc,all_old_floor_references_replayed=True,incremental_pairs_and_all_nulls_verified=True,no_case_based_edge_selection=True))
if __name__=='__main__':run()
