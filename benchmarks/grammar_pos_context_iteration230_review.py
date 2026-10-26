"""Independent rational expectations, outer-product POS scoring and null replay."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json,random,hashlib
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration230'
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-11,rtol=1e-11)
def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];ref=read(P/'iteration201/development-references.json');ref['Dante']={'pos':read(P/'iteration200/pos-references.json')['pos_by_stream_position']};lists=read(O/'selections.json');dd=read(O/'edge-values.json');ss=read(O/'summary.json');learn=read(P/'iteration225/selections.json');disjoint=read(P/'iteration226/disjoint-selections.json');raw=read(P/'iteration227/selections.json');dante=read(P/'iteration229/selections.json');checks=groups=0
    for a,selections in lists.items():
        g=gg[a];tags=ref[a]['pos'];buckets=defaultdict(list);counts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p is not None:buckets[g['ids'][i]].append(i);counts[g['ids'][i]][tags[i]]+=1
        prob={w:{t:F(n,sum(c.values())) for t,n in c.items()} for w,c in counts.items()};expected=[float(sum((v*prob[e['b']].get(t,0) for t,v in prob[e['a']].items()),F(0))) for e in g['descriptors']];near(expected,dd[a]['expected']);vocab={t:i for i,t in enumerate(sorted(set(tags)))};original=np.array([vocab[t] for t in tags]);matrix=[original]
        for seed in range(23000,23199):
            rng=random.Random(seed);assignment=original.copy()
            for w,pp in sorted(buckets.items()):
                values=[tags[i] for i in pp];rng.shuffle(values);assignment[pp]=[vocab[t] for t in values];assert Counter(values)==Counter(tags[i] for i in pp)
            matrix.append(assignment)
        matrix=np.array(matrix);columns=[]
        for e in g['descriptors']:
            frames=[]
            for f in e['frames']:frames.append((matrix[:,f['a_positions'],None]==matrix[:,None,f['b_positions']]).mean(axis=(1,2)))
            columns.append(np.mean(frames,axis=0));checks+=200
        values=np.array(columns).T;near(values[0],dd[a]['observed']);near(values[1:],dd[a]['null']);near(values[0]-expected,dd[a]['surplus']);assert dd[a]['sampled_zero_variance']==sum(np.ptp(values[1:],axis=0)<=1e-12)
        actual={'all':list(range(len(g['descriptors'])))};methods=dante if a=='Dante' else {**raw[a],**{name:dict(tied=learn[a][name],disjoint=disjoint[a][name]) for name in learn[a]}}
        for name,modes in methods.items():
            for mode,sets in modes.items():
                for label,ix in sets.items():actual[f'{name}/{mode}/{label}']=ix
        assert actual==selections
        for name,ix in selections.items():
            r=ss[a][name];obs=float(values[0,ix].mean());exp=float(np.array(expected)[ix].mean());null=values[1:,ix].mean(axis=1);assert r['edges']==len(ix);near(obs,r['observed']);near(exp,r['expected']);near(obs-exp,r['surplus']);near(null.mean(),r['null_mean']);near(null.min(),r['null_min']);near(null.max(),r['null_max']);assert r['null_zero_range']==bool(np.ptp(null)<=1e-12);near((1+sum(null>=obs-1e-12))/200,r['upper_tail']);groups+=1
    hashes=0
    frozen=read(O/'design-freeze.json');assert frozen['seeds']==list(range(23000,23199))
    for manifest in [frozen['inputs'],read(P/'iteration229/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',observed_and_null_edge_scores=checks,fixed_list_groups=groups,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
