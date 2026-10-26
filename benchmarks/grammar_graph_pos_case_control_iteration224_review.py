"""Independent rational Case-conditioned whole-profile permutation audit."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import random,json,hashlib,math
P=Path('experiments/results/grammar-restoration');O=P/'iteration224'
def read(p):return json.loads(p.read_text())
def near(a,b):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
def run():
    graphs=read(P/'iteration223/anonymous-graphs.json');gg=read(P/'iteration193/graphs.json');ref=read(P/'iteration201/development-references.json');old=read(P/'iteration223/details.json');olds=read(P/'iteration223/summary.json');case=read(P/'iteration220/labels.json');strata=read(O/'strata.json');dd=read(O/'details.json');ss=read(O/'summary.json');edgeschecked=0;stratacount=0
    for a,g in graphs.items():
        counts=defaultdict(Counter)
        for i,p in enumerate(gg[a]['positions']):
            if p is not None:counts[gg[a]['ids'][i]][ref[a]['pos'][i]]+=1
        prob={r['word']:{t:F(n,sum(counts[r['word']].values())) for t,n in counts[r['word']].items()} for r in g['nodes']};buckets=defaultdict(list)
        for r in g['nodes']:buckets[(r['bin'],case[a][r['word']])].append(r['word'])
        expected=[]
        for (b,c),words in sorted(buckets.items()):
            distinct={tuple(sorted((t,float(v)) for t,v in prob[w].items())) for w in words};expected.append(dict(frequency_bin=b,case_bearing=c,words=sorted(words),size=len(words),distinct_profiles=len(distinct)))
        assert strata[a]==expected;stratacount+=len(expected)
        for j,seed in enumerate(range(22400,22599)):
            rng=random.Random(seed);mapping={}
            for key,words in sorted(buckets.items()):
                source=sorted(words);rng.shuffle(source);mapping.update(zip(sorted(words),source));assert Counter(source)==Counter(words)
            assert all(case[a][w]==case[a][v] for w,v in mapping.items())
            values=[float(sum((x*prob[mapping[v]].get(t,0) for t,x in prob[mapping[u]].items()),F(0))) for u,v in g['edges']];edgeschecked+=len(values)
            for name,ix in old[a]['groups'].items():
                if ix:near(sum(values[i] for i in ix)/len(ix),dd[a]['null'][name][j])
                else:assert dd[a]['null'][name][j] is None
        for name,ix in old[a]['groups'].items():
            r=ss[a][name];assert r['edges']==len(ix);assert r['agreement']==olds[a][name]['agreement'];assert r['frequency_only_null_mean']==olds[a][name]['null_mean']
            if ix:
                nn=dd[a]['null'][name];near(sum(nn)/199,r['conditioned_null_mean']);near(min(nn),r['conditioned_null_min']);near(max(nn),r['conditioned_null_max']);near((1+sum(v>=r['agreement']-1e-12 for v in nn))/200,r['upper_tail'])
    hashes=0
    frozen=read(O/'design-freeze.json');assert frozen['seeds']==list(range(22400,22599))
    for manifest in [frozen['inputs'],read(P/'iteration223/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',rational_null_edges=edgeschecked,strata=stratacount,groups=16,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
