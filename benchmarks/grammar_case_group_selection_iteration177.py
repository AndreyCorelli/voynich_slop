"""Frozen label-free frame-group shortlists and unconditional applicability."""
from benchmarks.grammar_case_frame_components_iteration176 import *
OUT=ROOT/'iteration177'
RANKINGS=['frequency','support','combined']
CUTOFFS=[10,20,40]

def rank_groups(cc,dd,counts):
    support={tuple(sorted([e['a'],e['b']])):e['shared_frames'] for e in dd if e['shared_frames']>=2}
    features=[]
    for ci,c in enumerate(cc):
        frequency=sum(math.log(counts[x]) for x in c['types'])/len(c['types']);direct=[p for p in c['pairs'] if p['direct']];strength=sum(math.log(support[tuple(sorted([p['a'],p['b']]))]) for p in direct)/len(direct)
        features.append(dict(component=ci,frequency=frequency,support=strength,combined=frequency+strength))
    selections={'all':list(range(len(cc)))};boundaries={}
    for rank in RANKINGS:
        values=sorted([r[rank] for r in features],reverse=True)
        for k in CUTOFFS:
            name=rank+str(k);threshold=values[min(k,len(values))-1] if values else None
            selections[name]=[r['component'] for r in features if threshold is not None and r[rank]>=threshold];boundaries[name]=dict(requested=k,selected=len(selections[name]),threshold=threshold,ties_at_boundary=sum(r[rank]==threshold for r in features))
    return features,selections,boundaries

def augmented_summary(records,cc):
    ss=summarize_components(records,cc)
    for mode,gg in ss.items():
        for g,r in gg.items():
            r['case_component_applicability']=r['case_components']/len(cc) if cc else None
            r['case_pair_applicability']=r['case_occurrence_pairs']/r['all_occurrence_pairs'] if r['all_occurrence_pairs'] else None
            r['component_joint_yield']=(sum(x['agreement'] for x in r['component_details'].values())/len(cc)) if cc else None
            r['matching_pairs_per_all_pairs']=r['matching_case_pairs']/r['all_occurrence_pairs'] if r['all_occurrence_pairs'] else None
    return ss

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_frame_components_iteration176.py'),ROOT/'iteration176/verification-manifest.json',ROOT/'iteration176/components.json',ROOT/'iteration176/scores.jsonl.gz',ROOT/'iteration176/summary.json',ROOT/'iteration164/streams.json',ROOT/'iteration168/streams.json']+[p['descriptors'] for p in POOLS.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fixed176 groups; label-free rankings: mean log global member-word frequency; mean log distinct-frame support of direct edges; combined sum of those two means (product geometric means). Fixed top10,20,40 with ALL exact floating-score boundary ties included; all-groups baseline. Primary combined20 ALL-POS all-mode, no reference family filtering. Freeze features/rankings/selections BEFORE reading176 scored records. Same ranking for every word-null graph using its own components/support; global word counts unchanged by permutation. Profile controls use original selections fixed. Reaggregate every selected group and all176 POS strata/modes, no case-based exclusions. Report conditional agreement AND unconditioned case-component applicability, recognized-pair applicability, component-joint yield (sum covered component agreement / all selected groups, zero for case-inapplicable solely as diagnostic yield not accuracy), matching/all pairs, coverage/ties. Compare combined vs frequency same cutoff and all baseline; all variants retained, no winner selection or tuning. Primary all-POS avoids relying on supplied PRON/DET membership. Same reused Cicero development data; diagnostic selection not calibrated confidence/namedcase/POS/nuclei restoration. Independently reconstruct frequency/support/tie decisions and all summaries/contrasts, exact176 baseline.'))
    graphs=load(ROOT/'iteration176/components.json');features={};selections={};boundaries={}
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';counts=Counter(load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]);dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd
        features[pool]={};selections[pool]={};boundaries[pool]={}
        for view,cc in graphs[pool].items():features[pool][view],selections[pool][view],boundaries[pool][view]=rank_groups(cc,dd[view],counts)
    for name,obj in [('features',features),('selections',selections),('boundaries',boundaries)]:save(OUT/(name+'.json'),obj)
    save(OUT/'selection-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['features','selections','boundaries']}));summary={p:{} for p in POOLS}
    with gzip.open(ROOT/'iteration176/scores.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);pool,view=row['pool'],row['view'];gv='original' if view.startswith('case') else view;cc=graphs[pool][gv];summary[pool][view]={}
            for name,indices in selections[pool][gv].items():
                remap={j:i for i,j in enumerate(indices)};records=[dict(r,component=remap[r['component']]) for r in row['records'] if r['component'] in remap];summary[pool][view][name]=augmented_summary(records,[cc[i] for i in indices])
    save(OUT/'summary.json',summary);contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for name,ss in vv['original'].items():
            contrasts[pool][name]={}
            for metric in ['component_macro_agreement','case_component_applicability','component_joint_yield','case_pair_applicability','matching_pairs_per_all_pairs']:
                actual=ss['all']['all'][metric];contrasts[pool][name][metric]={'actual':actual}
                for label,views in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][name]['all']['all'][metric] for v in views if vv[v][name]['all']['all'][metric] is not None]
                    contrasts[pool][name][metric][label]=dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(x>=actual for x in nn) if actual is not None else None)
        print(pool,json.dumps({n:vv['original'][n]['all']['all'] for n in ['all','frequency20','support20','combined20']}),flush=True)
    save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
