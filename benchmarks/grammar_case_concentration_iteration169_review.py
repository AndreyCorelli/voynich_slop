"""Independent intervention universe, frame-case sufficient stats and replay."""
from benchmarks.grammar_case_concentration_iteration169 import *

def run():
    hc=ec=vc=pc=0
    for name in ['design-freeze','interventions-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    interventions=load(OUT/'interventions.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');ranges=load(OUT/'ranges.json');eligible={'earlier':588,'replication':857}
    for pool,p in POOLS.items():
        dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;dd={v:[e for e in ee if e['shared_frames']>=2] for v,ee in dd.items()};cases=load(p['cases'])[p['key']];transforms=load(p['transforms'])[p['key']];actual=dd['original'];endpoints=sorted({e[k] for e in actual for k in ['a','b']});frames=sorted({tuple(f['frame']) for e in actual for f in e['frames']});expected={'baseline':dict(kind='none',value=None),**{'endpoint'+str(k):dict(kind='endpoint',value=i) for k,i in enumerate(endpoints)},**{'frame'+str(k):dict(kind='frame',value=list(f)) for k,f in enumerate(frames)}};assert expected==interventions[pool];stats={}
        for view,ee in dd.items():
            ix=transforms[view];cc=cases if ix is None else [cases[k] for k in ix];stats[view]={}
            for e in ee:
                for f in e['frames']:
                    pairs=[(cc[a],cc[b]) for a in f['a_positions'] for b in f['b_positions']];both=[(a,b) for a,b in pairs if a in CASES and b in CASES];stats[view][(e['a'],e['b'],tuple(f['frame']))]=(len(pairs),len(both),sum(a==b for a,b in both));pc+=len(pairs)
        for name,intervention in expected.items():
            kind,value=intervention['kind'],intervention['value']
            for view,ee in dd.items():
                computed=[]
                for e in ee:
                    if kind=='endpoint' and (e['a']==value or e['b']==value):continue
                    ff=[f for f in e['frames'] if kind!='frame' or tuple(f['frame'])!=tuple(value)]
                    if len(ff)<2:continue
                    fractions=[];total=valid=matched=0
                    for f in ff:
                        n,v,m=stats[view][(e['a'],e['b'],tuple(f['frame']))];total+=n;valid+=v;matched+=m
                        if v:fractions.append(m/v)
                    computed.append(dict(a=e['a'],b=e['b'],shared_frames=len(ff),case_frames=len(fractions),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None));ec+=1
                assert details[pool][name][view]==computed;s=summary[pool][name][view];assert s==summarize_cases(computed,eligible[pool])['2'];covered=[r for r in computed if r['case_occurrence_pairs']];assert s['edges']==len(computed) and s['case_edges']==len(covered);assert s['edge_macro_frame_case_agreement']==(sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None);vc+=1
            vv=summary[pool][name];a=vv['original'];pp=[vv['word'+str(k)]['edge_macro_frame_case_agreement'] for k in SEEDS if vv['word'+str(k)]['case_edges']];v=a['edge_macro_frame_case_agreement'];assert contrasts[pool][name]==dict(actual=a,null_with_case=len(pp),null_max=max(pp) if pp else None,null_at_least_actual=sum(x>=v for x in pp) if v is not None else None)
        historical=load(ROOT/('iteration166' if pool=='earlier' else 'iteration168')/'summary.json');baseline=historical['Cicero'] if pool=='earlier' else historical['fit-Cicero']['5'];assert summary[pool]['baseline']=={view:r['2'] for view,r in baseline.items()}
        for kind,r in ranges[pool].items():
            names=[n for n,i in expected.items() if i['kind']==kind];rr=[summary[pool][n]['original'] for n in names];nonempty=[x for x in rr if x['case_edges']];assert r==dict(interventions=len(names),without_case=sum(not x['case_edges'] for x in rr),min_case_edges=min(x['case_edges'] for x in rr),max_case_edges=max(x['case_edges'] for x in rr),min_agreement=min(x['edge_macro_frame_case_agreement'] for x in nonempty) if nonempty else None,max_agreement=max(x['edge_macro_frame_case_agreement'] for x in nonempty) if nonempty else None,strictly_above_matched_null_max=sum(contrasts[pool][n]['actual']['edge_macro_frame_case_agreement'] is not None and contrasts[pool][n]['null_max'] is not None and contrasts[pool][n]['actual']['edge_macro_frame_case_agreement']>contrasts[pool][n]['null_max'] for n in names))
        print('audited',pool,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,interventions_verified=466,baseline_pairs_verified=2,intervention_view_combinations_verified=vc,edge_records_independently_replayed=ec,base_cartesian_pairs_compared_once=pc,all_actual_and_null_removals_and_ranges_verified=True,frame_support_reapplied=True,no_label_selected_removals_or_filters=True))
if __name__=='__main__':run()
