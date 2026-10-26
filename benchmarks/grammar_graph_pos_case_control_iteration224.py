"""Case-and-frequency conditioned POS-profile permutation control."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,random
P=Path('experiments/results/grammar-restoration');O=P/'iteration224'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def mean(v):return sum(v)/len(v) if v else None
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration223/anonymous-graphs.json','iteration223/profiles.json','iteration223/details.json','iteration223/summary.json','iteration223/verification-manifest.json','iteration220/labels.json']]
    save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22400,22599)),strata='frequency bin x global recognized Case-bearing status'))
    for p,h in read(P/'iteration223/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration223/anonymous-graphs.json');profiles=read(P/'iteration223/profiles.json');old=read(P/'iteration223/details.json');oldsummary=read(P/'iteration223/summary.json');case=read(P/'iteration220/labels.json');strata={};details={};summary={}
    for a,g in graphs.items():
        buckets=defaultdict(list)
        for r in g['nodes']:buckets[(r['bin'],case[a][r['word']])].append(r['word'])
        strata[a]=[dict(frequency_bin=b,case_bearing=c,words=sorted(words),size=len(words),distinct_profiles=len({json.dumps(profiles[a][w],sort_keys=True) for w in words})) for (b,c),words in sorted(buckets.items())];null={k:[] for k in old[a]['groups']}
        for seed in range(22400,22599):
            rng=random.Random(seed);permuted={}
            for key,words in sorted(buckets.items()):
                words=sorted(words);source=words.copy();rng.shuffle(source);assert all(case[a][w]==case[a][v] for w,v in zip(words,source));permuted.update({w:profiles[a][v] for w,v in zip(words,source)})
            values=[sum(v*permuted[y].get(tag,0) for tag,v in permuted[x].items()) for x,y in g['edges']]
            for name,ix in old[a]['groups'].items():null[name].append(mean([values[i] for i in ix]))
        details[a]=dict(null=null);summary[a]={}
        for name,ix in old[a]['groups'].items():
            actual=mean([old[a]['edge_values'][i] for i in ix]);assert actual==oldsummary[a][name]['agreement'];nn=null[name];summary[a][name]=dict(edges=len(ix),agreement=actual,frequency_only_null_mean=oldsummary[a][name]['null_mean'],conditioned_null_mean=mean(nn),conditioned_null_min=min(nn) if ix else None,conditioned_null_max=max(nn) if ix else None,upper_tail=(1+sum(v>=actual-1e-12 for v in nn))/200 if ix else None)
    for n,v in [('strata',strata),('details',details),('summary',summary)]:save(O/(n+'.json'),v)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
