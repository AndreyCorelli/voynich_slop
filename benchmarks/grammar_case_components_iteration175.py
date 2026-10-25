"""Label-free connected components and transitive case-compatibility audit."""
from benchmarks.grammar_case_word_profiles_iteration174 import *
from itertools import combinations
OUT=ROOT/'iteration175'
MODES=['all','direct','transitive']

def components(dd):
    adj={};positions={};direct=set()
    for e in dd:
        a,b=e['a'],e['b'];adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a);direct.add(tuple(sorted([a,b])))
        for f in e['frames']:
            positions.setdefault(a,set()).update(f['a_positions']);positions.setdefault(b,set()).update(f['b_positions'])
    seen=set();result=[]
    for a in sorted(adj):
        if a in seen:continue
        todo=[a];seen.add(a);cc=[]
        while todo:
            x=todo.pop();cc.append(x)
            for y in sorted(adj[x]-seen):seen.add(y);todo.append(y)
        cc=sorted(cc);result.append(dict(types=cc,positions={x:sorted(positions[x]) for x in cc},pairs=[dict(a=x,b=y,direct=(x,y) in direct) for x,y in combinations(cc,2)]))
    return result

def pair_scores(cc,tags,cases):
    result=[]
    for ci,c in enumerate(cc):
        hist={x:Counter((tags[i] in PD,cases[i]) for i in pp) for x,pp in c['positions'].items()}
        for pair in c['pairs']:
            stats={g:[0,0,0] for g in GROUPS}
            for (pa,ca),na in hist[pair['a']].items():
                for (pb,cb),nb in hist[pair['b']].items():
                    leaf='both_pd' if pa and pb else 'exactly_one_pd' if pa!=pb else 'neither_pd';gg=['all',leaf]+(['pd_involving'] if pa or pb else [])
                    for g in gg:
                        n=na*nb;stats[g][0]+=n
                        if ca in CASES and cb in CASES:stats[g][1]+=n;stats[g][2]+=n*int(ca==cb)
            result.append(dict(component=ci,**pair,stats=stats))
    return result

def summarize_components(records,cc):
    result={}
    for mode in MODES:
        result[mode]={}
        rows=[r for r in records if mode=='all' or r['direct']==(mode=='direct')]
        for g in GROUPS:
            by={};total=valid=matches=covered=0;types=set()
            for r in rows:
                n,v,m=r['stats'][g];total+=n;valid+=v;matches+=m
                if v:by.setdefault(r['component'],[]).append(m/v);covered+=1;types.update([r['a'],r['b']])
            means=[sum(v)/len(v) for v in by.values()]
            result[mode][g]=dict(components=len(cc),types=sum(len(c['types']) for c in cc),type_pairs=len(rows),case_components=len(by),case_type_pairs=covered,case_types=len(types),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matches,component_macro_agreement=sum(means)/len(means) if means else None,type_pair_macro_agreement=sum(sum(v) for v in by.values())/covered if covered else None,pooled_agreement=matches/valid if valid else None,component_details={str(k):dict(case_type_pairs=len(v),agreement=sum(v)/len(v)) for k,v in by.items()})
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration174/verification-manifest.json',ROOT/'iteration174/case-assignments.json.gz',ROOT/'iteration172/references.json']+[p[n] for p in POOLS.values() for n in ['descriptors','transforms']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Label-free connected components of exact floor5/two-frame graphs in both pools: original plus16 existing word-null graphs. Freeze sorted component members, all distinct unordered member pairs and direct-edge flag, union of each types incident-frame occurrence positions BEFORE label scoring. Evaluate all distinct type pairs using Cartesian products of these context-selected positions, recognized cases and five172 occurrence-POS strata. Primary component-macro case agreement (equal eligible typepairs within component, equal covered components), both_pd stratum; secondary typepair-macro and pooled. Report direct and transitive-only pairs separately, empty groups retained, all components including case-free. Same original components evaluated under199 frozen174 word/POS-profile case permutations, plus exact original baseline. Word-null labels travel with tokens; graph/selection differs, report counts. Context-position union collapses individual shared frames, so this is NOT old frame-macro score or named-case clustering; pairwise compatibility need not be transitive. Full score records as gzip JSON lines before aggregation. No labels choose components, edges, thresholds or confidence; no new annotations/reserve/sealed data or lexical nuclei. Sameauthor/development limits.'))
    graphs={}
    for pool,p in POOLS.items():
        vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv
        graphs[pool]={v:components([e for e in dd if e['shared_frames']>=2]) for v,dd in vv.items()}
    save(OUT/'components.json',graphs);save(OUT/'components-freeze.json',dict(inputs={str(OUT/'components.json'):digest(OUT/'components.json')}))
    refs=load(ROOT/'iteration172/references.json');assignments=gzload(ROOT/'iteration174/case-assignments.json.gz')
    with gzip.open(OUT/'scores.jsonl.gz','wt') as f:
        for pool,p in POOLS.items():
            tags=refs[pool]['pos'];cases=refs[pool]['case'];trans=load(p['transforms'])[p['key']]
            for view,cc in graphs[pool].items():
                ix=trans[view];tt=tags if ix is None else [tags[k] for k in ix];ca=cases if ix is None else [cases[k] for k in ix];f.write(json.dumps(dict(pool=pool,view=view,records=pair_scores(cc,tt,ca)),separators=(',',':'))+'\n')
            for view,ca in assignments[pool].items():
                if view!='original':f.write(json.dumps(dict(pool=pool,view=view,records=pair_scores(graphs[pool]['original'],tags,ca)),separators=(',',':'))+'\n')
    save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'scores.jsonl.gz'):digest(OUT/'scores.jsonl.gz')}));summary={p:{} for p in POOLS}
    with gzip.open(OUT/'scores.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);pool,view=row['pool'],row['view'];summary[pool][view]=summarize_components(row['records'],graphs[pool]['original' if view.startswith('case') else view])
    save(OUT/'summary.json',summary);contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for mode in MODES:
            contrasts[pool][mode]={}
            for g in GROUPS:
                a=vv['original'][mode][g];x=a['component_macro_agreement'];contrasts[pool][mode][g]={'actual':a}
                for name,views in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][mode][g]['component_macro_agreement'] for v in views if vv[v][mode][g]['case_type_pairs']];contrasts[pool][mode][g][name]=dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(y>=x for y in nn) if x is not None else None)
        print(pool,json.dumps({m:contrasts[pool][m]['both_pd'] for m in MODES}),flush=True)
    save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
