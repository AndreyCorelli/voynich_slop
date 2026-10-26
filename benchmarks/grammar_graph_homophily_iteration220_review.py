"""Independent graph, labels, permutation mixing and mistake replay."""
from pathlib import Path
from collections import Counter,defaultdict
import json,random,hashlib,math
P=Path('experiments/results/grammar-restoration');O=P/'iteration220'
def read(p):return json.loads(p.read_text())
def near(a,b):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
def run():
    gg=read(P/'iteration193/graphs.json');ref=read(P/'iteration201/development-references.json');nodes=read(O/'nodes.json');cc=read(O/'components.json');labels=read(O/'labels.json');dd=read(O/'details.json');ss=read(O/'summary.json');mistakes=read(O/'mistakes.json');ff=read(P/'iteration207/features.json');base=read(P/'iteration211/predictions.json');bal=read(P/'iteration216/predictions.json');edgechecks=0;mistakechecks=0
    for a,rows in nodes.items():
        g=gg[a];edges=[(e['a'],e['b']) for e in g['descriptors']];adj=defaultdict(set)
        for u,v in edges:adj[u].add(v);adj[v].add(u)
        counts=Counter(g['ids']);case=Counter()
        for i,p in enumerate(g['positions']):
            if p is not None and ref[a]['case'][i]:case[g['ids'][i]]+=1
        y={w:int(case[w]>0) for w in sorted(adj)};assert y==labels[a];bins=defaultdict(list)
        for row in rows:
            w=row['word'];b=sum(counts[w]>=t for t in [10,20,50,100]);assert row==dict(word=w,frequency=counts[w],bin=b,degree=len(adj[w]),neighbors=sorted(adj[w]));bins[b].append(w)
        components=[];remaining=set(adj)
        while remaining:
            root=min(remaining);found={root};todo=[root]
            while todo:
                w=todo.pop()
                for v in adj[w]-found:found.add(v);todo.append(v)
            remaining-=found;components.append(sorted(found))
        assert components==cc[a];s=ss[a];assert s['components']==len(components) and s['nodes']==len(adj) and s['edges']==len(edges) and s['case_bearing']==sum(y.values());expectedcomp=[dict(words=c,size=len(c),case_bearing=sum(y[w] for w in c),mixed=len({y[w] for w in c})>1) for c in components];assert expectedcomp==dd[a]['components'];assert s['mixed_components']==sum(c['mixed'] for c in expectedcomp) and s['nodes_in_mixed_components']==sum(c['size'] for c in expectedcomp if c['mixed'])
        mix=Counter('both_case' if y[u]+y[v]==2 else 'neither_case' if y[u]+y[v]==0 else 'mixed' for u,v in edges);assert dict(mix)==s['edge_types'];observed=(mix['both_case']+mix['neither_case'])/len(edges);near(observed,s['agreement']);null=[]
        for seed in range(22000,22199):
            rng=random.Random(seed);permuted={}
            for b,words in sorted(bins.items()):
                words=sorted(words);values=[y[w] for w in words];rng.shuffle(values);permuted.update(zip(words,values));assert sum(values)==sum(y[w] for w in words)
            null.append(sum(permuted[u]==permuted[v] for u,v in edges)/len(edges));edgechecks+=len(edges)
        assert null==dd[a]['null_agreement'];near(sum(null)/199,s['null_mean']);near(max(null),s['null_max']);near((1+sum(v>=observed-1e-12 for v in null))/200,s['upper_tail'])
        for name,pp in [('baseline',base[a]['full12']['applicability']),('balanced',bal[a]['balanced'][a])]:
            expected=[]
            for i,f in enumerate(ff[a]):
                w=f['word'];same=sum(y[v]==y[w] for v in adj[w]);expected.append(dict(index=i,word=w,truth=y[w],predicted=int(pp[i]>=.5),error=int(pp[i]>=.5)!=y[w],degree=len(adj[w]),same_label_neighbors=same,same_fraction=same/len(adj[w])));mistakechecks+=1
            assert expected==mistakes[a][name]
            for label,rr in [('correct',[r for r in expected if not r['error']]),('false_positive',[r for r in expected if r['error'] and r['predicted']]),('false_negative',[r for r in expected if r['error'] and not r['predicted']])]:
                assert s[name][label]['n']==len(rr)
                if rr:near(s[name][label]['mean_same_fraction'],sum(r['same_fraction'] for r in rr)/len(rr))
                else:assert s[name][label]['mean_same_fraction'] is None
        for name,test in [('degree1',lambda w:len(adj[w])==1),('degree2plus',lambda w:len(adj[w])>=2)]:assert s['by_degree'][name]==dict(nodes=sum(test(w) for w in adj),case_bearing=sum(y[w] for w in adj if test(w)))
    hashes=0
    freeze=read(O/'design-freeze.json');assert freeze['seeds']==list(range(22000,22199))
    for manifest in [freeze['inputs'],read(P/'iteration219/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'graph-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',nodes=sum(map(len,nodes.values())),null_edge_comparisons=edgechecks,mistake_records=mistakechecks,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
