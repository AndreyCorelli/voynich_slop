"""Rational profile and independent permutation/edge-group audit."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
import json,random,math,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration223'
def read(p):return json.loads(p.read_text())
def near(x,y):assert math.isclose(x,y,abs_tol=1e-11,rel_tol=1e-11)
def run():
    anon=read(O/'anonymous-graphs.json');profiles=read(O/'profiles.json');dd=read(O/'details.json');ss=read(O/'summary.json');gg=read(P/'iteration193/graphs.json');refs=read(P/'iteration201/development-references.json');case=read(P/'iteration220/labels.json');terms=0
    for a,g in anon.items():
        original=gg[a];counts=defaultdict(Counter)
        for i,p in enumerate(original['positions']):
            if p is not None:counts[original['ids'][i]][refs[a]['pos'][i]]+=1
        rational={r['word']:{t:Fraction(n,sum(counts[r['word']].values())) for t,n in counts[r['word']].items()} for r in g['nodes']}
        for w,pp in rational.items():
            assert set(pp)==set(profiles[a][w])
            for t,v in pp.items():near(float(v),profiles[a][w][t])
        edges=g['edges'];assert edges==[[e['a'],e['b']] for e in original['descriptors']]
        def dot(u,v):return sum((p*v.get(t,0) for t,p in u.items()),Fraction(0))
        actual=[float(dot(rational[u],rational[v])) for u,v in edges]
        for x,y in zip(actual,dd[a]['edge_values']):near(x,y)
        for t,v in dd[a]['pos_contributions'].items():near(float(sum((rational[u].get(t,0)*rational[v].get(t,0) for u,v in edges),Fraction(0))/len(edges)),v)
        near(sum(dd[a]['pos_contributions'].values()),ss[a]['all']['agreement'])
        groups={'all':list(range(len(edges)))}
        for k in ['both_case','mixed','neither_case']:groups[k]=[i for i,(u,v) in enumerate(edges) if ('both_case' if case[a][u]+case[a][v]==2 else 'neither_case' if case[a][u]+case[a][v]==0 else 'mixed')==k]
        assert groups==dd[a]['groups'];bins=defaultdict(list)
        for r in g['nodes']:bins[r['bin']].append(r['word'])
        for j,seed in enumerate(range(22300,22499)):
            rng=random.Random(seed);assignment={}
            for b,words in sorted(bins.items()):
                shuffled=sorted(words);rng.shuffle(shuffled);assignment.update(zip(sorted(words),shuffled))
            values=[float(dot(rational[assignment[u]],rational[assignment[v]])) for u,v in edges];terms+=len(edges)
            for k,ix in groups.items():
                val=sum(values[i] for i in ix)/len(ix) if ix else None
                if ix:near(val,dd[a]['null'][k][j])
                else:assert dd[a]['null'][k][j] is None
        for k,ix in groups.items():
            v=ss[a][k];assert v['edges']==len(ix)
            if ix:
                mean=sum(actual[i] for i in ix)/len(ix);null=dd[a]['null'][k];near(mean,v['agreement']);near(sum(null)/199,v['null_mean']);near(min(null),v['null_min']);near(max(null),v['null_max']);near((1+sum(x>=mean-1e-12 for x in null))/200,v['upper_tail'])
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration222/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'graph-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',profiles=sum(map(len,profiles.values())),rational_null_edges=terms,groups=16,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
