"""Label-free unique word-pair bundles, retaining exact within-frame scoring."""
from benchmarks.grammar_case_word_profiles_iteration174 import *
OUT=ROOT/'iteration178'
RANKINGS=['frequency','support','combined']
CUTOFFS=[10,20,40]
METRICS=['edge_macro_frame_case_agreement','edge_applicability','edge_joint_yield','pair_applicability','matching_pairs_per_all_pairs']

def ranks(dd,counts):
    features=[]
    for i,e in enumerate(dd):
        f=(math.log(counts[e['a']])+math.log(counts[e['b']]))/2;s=math.log(e['shared_frames'])
        features.append(dict(edge=i,a=e['a'],b=e['b'],shared_frames=e['shared_frames'],frequency=f,support=s,combined=f+s))
    selected={'all':list(range(len(dd)))};boundaries={}
    for rank in RANKINGS:
        values=sorted([r[rank] for r in features],reverse=True)
        for k in CUTOFFS:
            name=rank+str(k);threshold=values[min(k,len(values))-1] if values else None;selected[name]=[r['edge'] for r in features if threshold is not None and r[rank]>=threshold];boundaries[name]=dict(requested=k,selected=len(selected[name]),threshold=threshold,ties_at_boundary=sum(r[rank]==threshold for r in features))
    return features,selected,boundaries

def metrics(rows,eligible):
    r=summarize_cases(rows,eligible)['2'];r['edge_joint_yield']=sum(x['frame_macro_case_agreement'] for x in rows if x['case_occurrence_pairs'])/len(rows) if rows else None;r['matching_pairs_per_all_pairs']=r['matching_case_pairs']/r['all_occurrence_pairs'] if r['all_occurrence_pairs'] else None
    return r

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration177/verification-manifest.json',ROOT/'iteration172/details.json',ROOT/'iteration172/summary.json',ROOT/'iteration174/details.json.gz',ROOT/'iteration174/summary.json',ROOT/'iteration164/streams.json',ROOT/'iteration168/streams.json']+[p['descriptors'] for p in POOLS.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Unique primary word-pair bundles: one existing floor5/two-distinct-frame EDGE per shortlist slot, retain all its individual frame-specific comparisons/172 scoring. Same label-free frequency geometricmean(global counts a,b), support distinct shared frames, combined product, implemented mean logs and sum. Fixed top10/20/40, all exact floating-score boundary ties, all-edges baseline; primary combined20 all-POS. No case/POS family filtering or score-based selection. Freeze features/rankings/boundaries before loading172/174 cached detailed label scores. Each16 word-null graph independently ranked; all199174 profile nulls keep original fixed shortlist. Report edge/type diversity, case-edge applicability, recognized-pair applicability, edge/frame-macro consistency, edge joint yield (covered score sum / all selected bundles, diagnostic not accuracy), matching/all pair ratio. All five172 strata retained, no missing-case perfectscore, null nonempty counts explicit. Exact all-bundle baselines172/174 required and independent ranking/aggregation replay. This changes177 selection unit and weighting; do not call before/after an isolated causal gain. No new annotations/reserves/sealed data, no nucleus/POS/namedcase restoration or fresh-validation claim.'))
    graphs={};features={};selections={};boundaries={}
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';counts=Counter(load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]);vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv;graphs[pool]={v:[e for e in dd if e['shared_frames']>=2] for v,dd in vv.items()};features[pool]={};selections[pool]={};boundaries[pool]={}
        for view,dd in graphs[pool].items():
            assert len({(e['a'],e['b']) for e in dd})==len(dd)
            features[pool][view],selections[pool][view],boundaries[pool][view]=ranks(dd,counts)
    for n,obj in [('features',features),('selections',selections),('boundaries',boundaries)]:save(OUT/(n+'.json'),obj)
    save(OUT/'selection-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['features','selections','boundaries']}))
    old=load(ROOT/'iteration172/details.json');profile=gzload(ROOT/'iteration174/details.json.gz');summary={}
    for pool in POOLS:
        assert old[pool]['original']==profile[pool]['original'];vv={**old[pool],**profile[pool]};summary[pool]={}
        for view,gg in vv.items():
            gv='original' if view.startswith('case') else view;dd=graphs[pool][gv];summary[pool][view]={}
            for rows in gg.values():assert [(r['a'],r['b']) for r in rows]==[(e['a'],e['b']) for e in dd]
            for name,ix in selections[pool][gv].items():summary[pool][view][name]={g:metrics([rows[i] for i in ix],588 if pool=='earlier' else 857) for g,rows in gg.items()}
    save(OUT/'summary.json',summary);contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for name,gg in vv['original'].items():
            contrasts[pool][name]={}
            for metric in METRICS:
                actual=gg['all'][metric];contrasts[pool][name][metric]={'actual':actual}
                for label,views in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][name]['all'][metric] for v in views if vv[v][name]['all'][metric] is not None];contrasts[pool][name][metric][label]=dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(x>=actual for x in nn) if actual is not None else None)
        print(pool,json.dumps({n:vv['original'][n]['all'] for n in ['all','frequency20','support20','combined20']}),flush=True)
    save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
