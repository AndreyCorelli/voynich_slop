"""Reference-only soft POS compatibility, frequency-stratified profile null."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random
P=Path('experiments/results/grammar-restoration');O=P/'iteration223'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def dot(u,v):return sum(x*v.get(k,0) for k,x in u.items())
def average(values):return sum(values)/len(values) if values else None
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration201/development-references.json','iteration220/nodes.json','iteration220/labels.json','iteration222/verification-manifest.json']]
    save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22300,22499)),strata=['5-9','10-19','20-49','50-99','100+'],primary='mean edge global word-POS profile dot product'))
    for p,h in read(P/'iteration222/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');nodes=read(P/'iteration220/nodes.json');anonymous={a:dict(nodes=nn,edges=[[e['a'],e['b']] for e in graphs[a]['descriptors']]) for a,nn in nodes.items()};save(O/'anonymous-graphs.json',anonymous);save(O/'graph-freeze.json',{'anonymous-graphs.json':sha(O/'anonymous-graphs.json')})
    refs=read(P/'iteration201/development-references.json');case=read(P/'iteration220/labels.json');profiles={};details={};summary={}
    for a,anon in anonymous.items():
        g=graphs[a];cc=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p:cc[g['ids'][i]][refs[a]['pos'][i]]+=1
        prob={r['word']:{tag:n/sum(cc[r['word']].values()) for tag,n in cc[r['word']].items()} for r in anon['nodes']};profiles[a]=prob;edges=anon['edges'];groups={'all':list(range(len(edges)))}
        for kind in ['both_case','mixed','neither_case']:groups[kind]=[i for i,(u,v) in enumerate(edges) if ('both_case' if case[a][u]+case[a][v]==2 else 'neither_case' if case[a][u]+case[a][v]==0 else 'mixed')==kind]
        actual=[dot(prob[u],prob[v]) for u,v in edges];buckets=defaultdict(list)
        for r in anon['nodes']:buckets[r['bin']].append(r['word'])
        null={name:[] for name in groups}
        for seed in range(22300,22499):
            rng=random.Random(seed);perm={}
            for b,words in sorted(buckets.items()):
                source=words.copy();rng.shuffle(source);perm.update({w:prob[v] for w,v in zip(words,source)})
            values=[dot(perm[u],perm[v]) for u,v in edges]
            for name,ix in groups.items():null[name].append(average([values[i] for i in ix]))
        contributions={tag:average([prob[u].get(tag,0)*prob[v].get(tag,0) for u,v in edges]) for tag in sorted({t for pp in prob.values() for t in pp})};details[a]=dict(groups=groups,edge_values=actual,null=null,pos_contributions=contributions);summary[a]={}
        for name,ix in groups.items():
            value=average([actual[i] for i in ix]);nn=null[name];summary[a][name]=dict(edges=len(ix),agreement=value,null_mean=average(nn),null_min=min(nn) if ix else None,null_max=max(nn) if ix else None,upper_tail=(1+sum(v>=value-1e-12 for v in nn))/200 if ix else None)
    for n,v in [('profiles',profiles),('details',details),('summary',summary)]:save(O/(n+'.json'),v)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
