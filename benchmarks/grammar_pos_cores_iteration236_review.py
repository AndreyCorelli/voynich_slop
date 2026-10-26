"""Independent equivalence/pair tests, scalar profile/null and coverage replay."""
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import json,random,hashlib,math
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration236'
def read(p):return json.loads(p.read_text())
def near(x,y):assert math.isclose(x,y,abs_tol=1e-10,rel_tol=1e-10)
def measure(y,cores):
    compat=[];pairs=[];purity=[];pure=0;words=0
    for core in cores:
        ix=core['indices'];vv=[sum(x*z for x,z in zip(y[i],y[j])) for i,j in combinations(ix,2)];compat.append(sum(vv)/len(vv));pairs+=vv;mass=[sum(y[i][t] for i in ix) for t in range(17)];purity.append(max(mass)/len(ix));pure+=max(mass);words+=len(ix)
    return dict(core_macro_compatibility=sum(compat)/len(compat) if compat else None,pair_weighted_compatibility=sum(pairs)/len(pairs) if pairs else None,core_macro_oracle_purity=sum(purity)/len(purity) if purity else None,word_weighted_oracle_purity=pure/words if words else None)
def run():
    runs=read(P/'iteration235/runs.json');base=read(P/'iteration234-retry/clusters.json');cores=read(O/'cores.json');ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');strata=read(P/'iteration234-retry/strata.json');coverage=read(P/'iteration231/summary.json');dd=read(O/'details.json');ss=read(O/'summary.json');count=groups=0
    for a,cc in cores.items():
        n=len(base[a]['words']);seen=[]
        for c in cc:
            ix=c['indices'];assert c['words']==[base[a]['words'][i] for i in ix] and c['size']==len(ix) and c['pairs']==[list(p) for p in combinations(ix,2)];seen+=ix
        assert sorted(seen)==list(range(n))
        membership={i:j for j,c in enumerate(cc) for i in c['indices']}
        for i,j in combinations(range(n),2):assert (membership[i]==membership[j])==all(r['labels'][i]==r['labels'][j] for r in runs[a]);count+=1
        non=[c for c in cc if c['size']>1];lookup={r['word']:i for i,r in enumerate(ff[a])};y=[truth[a]['profiles'][lookup[w]] for w in base[a]['words']];freq=[truth[a]['frequencies'][lookup[w]] for w in base[a]['words']];actual=measure(y,non)
        for k,v in actual.items():near(v,dd[a]['actual'][k]);near(v,ss[a]['actual'][k])
        for c,r in zip(non,dd[a]['individual_cores']):
            assert r['words']==c['words'] and r['indices']==c['indices'] and r['size']==c['size']
            for k,v in measure(y,[c]).items():near(v,r['metrics'][k])
        for j,seed in enumerate(range(23300,23499)):
            rng=random.Random(seed);permutation=list(range(n))
            for bucket in strata[a]:
                ix=bucket['indices'];source=ix.copy();rng.shuffle(source)
                for i,v in zip(ix,source):permutation[i]=v
            result=measure([y[i] for i in permutation],non)
            for k,v in result.items():near(v,dd[a]['null'][j][k])
            groups+=1
        selected=[i for c in non for i in c['indices']];s=ss[a];assert s['all_cores']==len(cc) and s['nonsingleton_cores']==len(non) and s['singletons']==len(cc)-len(non);assert s['sizes']==[len(c['indices']) for c in non] and s['pairs']==sum(len(c['pairs']) for c in non) and s['covered_nodes']==len(selected) and s['graph_nodes']==n;tokens=sum(freq[i] for i in selected);assert s['covered_tokens']==tokens;near(s['graph_node_coverage'],len(selected)/n);near(s['text_token_coverage'],tokens/coverage[a]['coverage']['text_tokens']);near(s['text_type_coverage'],len(selected)/coverage[a]['coverage']['text_word_types'])
        for k,r in s['null'].items():
            values=[row[k] for row in dd[a]['null']];near(sum(values)/199,r['mean']);near(max(values),r['maximum']);near((1+sum(v>=actual[k]-1e-12 for v in values))/200,r['upper_tail'])
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration235/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'core-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',equivalence_pair_checks=count,profile_null_groups=groups,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
