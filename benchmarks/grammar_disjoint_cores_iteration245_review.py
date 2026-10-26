"""Independent split, strict partitions, intersection and scalar profile audit."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,gzip,hashlib,random
import numpy as np
from benchmarks.grammar_full_core_null_iteration244_review import rebuild,embedding,lloyd,near
from benchmarks.grammar_pos_cores_iteration236_review import measure
P=Path('experiments/results/grammar-restoration');O=P/'iteration245';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def expectedcores(words,groups):
    ix={w:i for i,w in enumerate(words)}
    return [dict(words=ww,indices=[ix[w] for w in ww],size=len(ww),pairs=[list(p) for p in combinations([ix[w] for w in ww],2)]) for ww in sorted(groups)]
def metrics(d,counts,tags):
    profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()};cc=[c for c in d['cores'] if c['size']>=2];selected={w for c in cc for w in c['words']};pure=[]
    for c in cc:
        if all(len(counts[w])==1 for w in c['words']):
            tt={next(iter(counts[w])) for w in c['words']}
            if len(tt)==1:pure.append(dict(words=c['words'],size=len(c['words']),reference_tag=next(iter(tt)),tokens=sum(sum(counts[w].values()) for w in c['words'])))
    return dict(core_sizes=[len(c['words']) for c in cc],covered_words=len(selected),covered_tokens=sum(sum(counts[w].values()) for w in selected),text_tokens=sum(sum(v.values()) for v in counts.values()),pure_cores=pure,largest_pure_core=max((c['size'] for c in pure),default=0),metrics=measure([profiles[w] for w in d['words']],cc))
def compare(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:compare(a[k],b[k])
    elif isinstance(a,float):near(a,b)
    else:assert a==b

def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];splits=read(O/'splits.json');cross=read(O/'cross-half-cores.json');results=read(O/'results.json');refs=read(P/'iteration201/development-references.json');tags=read(P/'iteration231/design-freeze.json')['tags'];old=read(P/'iteration238/cores.json');graphchecks=lloyds=geometry=0
    for a in AA:
        g=gg[a];first={}
        for i,p in enumerate(g['positions']):
            if p is not None:first.setdefault(tuple(p[:2]),i)
        order=sorted(first,key=first.get);mid=len(order)//2;expected=[[list(k) for k in order[:mid]],[list(k) for k in order[mid:]]];assert splits[a]==expected;assert not set(map(tuple,expected[0]))&set(map(tuple,expected[1]));dd=[];local=[defaultdict(Counter),defaultdict(Counter)];globalcounts=defaultdict(Counter);ref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'] if a=='Dante' else refs[a]['pos']
        for h,keys in enumerate(expected):
            kept=set(map(tuple,keys));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];masked=dict(ids=g['ids'],positions=positions);d=json.loads(gzip.decompress((O/f'{a}-{h}.json.gz').read_bytes()));dd.append(d);edges=rebuild(masked,set());graphchecks+=1;assert edges==d['initial_graph'];words=sorted({e[k] for e in edges for k in ['a','b']});assert words==d['words'];assert d['clusterable']==(len(words)>=17)
            for i,p in enumerate(positions):
                if p is not None:local[h][g['ids'][i]][ref[i]]+=1;globalcounts[g['ids'][i]][ref[i]]+=1
            if not d['clusterable']:assert d['initial_runs']==d['deletions']==d['cores']==[];continue
            _,x=embedding(edges,True);geometry+=1;assert len(d['initial_runs'])==31 and len(d['deletions'])==31;maps=[]
            for j,r in enumerate(d['initial_runs']):
                assert r['seed']==23500+j;y,init,n,centers=lloyd(x,r['seed']);assert y==r['labels'] and init==r['initial_center_indices'] and n==r['iterations'];near(centers,r['centers']);lloyds+=1
            for j,r in enumerate(d['deletions']):
                ss=sorted(kept);removed=sorted(random.Random(23700+j).sample(ss,int(.1*len(ss))));assert r['seed']==23700+j and r['removed']==[list(v) for v in removed];ee=rebuild(masked,set(removed));graphchecks+=1;assert ee==r['graph'];p=r['partition'];ww=sorted({e[k] for e in ee for k in ['a','b']});assert ww==p['words'] and p['clusterable']==(len(ww)>=17)
                if p['clusterable']:
                    _,z=embedding(ee,j==15);geometry+=int(j==15);y,init,n,_=lloyd(z,23500);assert y==p['labels'] and init==p['initial_center_indices'] and n==p['iterations'];maps.append(dict(zip(ww,y)));lloyds+=1
                else:assert p['labels'] is None;maps.append({})
            groups=defaultdict(list)
            for i,w in enumerate(words):
                if all(w in m for m in maps):groups[tuple(r['labels'][i] for r in d['initial_runs'])+tuple(m[w] for m in maps)].append(w)
            assert expectedcores(words,groups.values())==d['cores']
        maps=[{w:i for i,c in enumerate(d['cores']) for w in c['words']} for d in dd];common=sorted(set(maps[0])&set(maps[1]));groups=defaultdict(list)
        for w in common:groups[maps[0][w],maps[1][w]].append(w)
        shared=dict(words=common,cores=expectedcores(common,groups.values()));assert shared==cross[a]
        for h,d in enumerate(dd):
            r=results[a]['halves'][h];assert r['clusterable']==d['clusterable'] and r['nodes']==len(d['words']) and r['edges']==len(d['initial_graph']);compare(metrics(d,globalcounts,tags),r['global_profiles']);compare(metrics(d,local[h],tags),r['local_profiles'])
        compare(metrics(shared,globalcounts,tags),results[a]['shared']);pairs=[(u,v) for c in old[a] for u,v in combinations(c['words'],2)];present=[(u,v) for u,v in pairs if all(u in m and v in m for m in maps)];retained=[(u,v) for u,v in present if all(m[u]==m[v] for m in maps)];r=results[a];assert r['original_pairs']==len(pairs) and r['original_pairs_present_both']==len(present) and r['original_pairs_retained_both']==len(retained) and r['retained_pair_words']==[list(v) for v in retained] and r['unconditional_retention']==(len(retained)/len(pairs) if pairs else None);print(a,'passed',flush=True)
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(O/'selection-freeze.json'),read(P/'iteration244/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',authors=5,halves=10,graph_replays=graphchecks,lloyd_replays=lloyds,geometry_checks=geometry,strict_and_cross_intersections=15,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
