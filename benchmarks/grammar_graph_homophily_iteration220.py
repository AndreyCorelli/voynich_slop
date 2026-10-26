"""Frequency-stratified graph homophily diagnostic, not grammar inference."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random
P=Path('experiments/results/grammar-restoration');O=P/'iteration220'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def band(n):return 0 if n<10 else 1 if n<20 else 2 if n<50 else 3 if n<100 else 4
def agreement(edges,y):return sum(y[e['a']]==y[e['b']] for e in edges)/len(edges)
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration201/development-references.json','iteration207/features.json','iteration211/predictions.json','iteration216/predictions.json','iteration219/verification-manifest.json']]
    save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22000,22199)),frequency_bins=['5-9','10-19','20-49','50-99','100+'],primary='unweighted edge binary Case-bearing agreement'))
    for p,h in read(P/'iteration219/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');ff=read(P/'iteration207/features.json');nodes={};components={}
    for a in ff:
        g=graphs[a];counts=Counter(g['ids']);adj=defaultdict(set)
        for e in g['descriptors']:adj[e['a']].add(e['b']);adj[e['b']].add(e['a'])
        nodes[a]=[dict(word=w,frequency=counts[w],bin=band(counts[w]),degree=len(adj[w]),neighbors=sorted(adj[w])) for w in sorted(adj)];seen=set();cc=[]
        for w in sorted(adj):
            if w in seen:continue
            todo=[w];seen.add(w);members=[]
            while todo:
                v=todo.pop();members.append(v)
                for u in sorted(adj[v]):
                    if u not in seen:seen.add(u);todo.append(u)
            cc.append(sorted(members))
        components[a]=cc
    save(O/'nodes.json',nodes);save(O/'components.json',components);save(O/'graph-freeze.json',{n:sha(O/n) for n in ['nodes.json','components.json']})
    refs=read(P/'iteration201/development-references.json');baseline=read(P/'iteration211/predictions.json');balanced=read(P/'iteration216/predictions.json');labels={};details={};summary={};mistakes={}
    for a,nn in nodes.items():
        g=graphs[a];ref=refs[a];casewords={g['ids'][i] for i,p in enumerate(g['positions']) if p and ref['case'][i]};y={r['word']:int(r['word'] in casewords) for r in nn};labels[a]=y;edges=g['descriptors'];actual=agreement(edges,y);buckets=defaultdict(list)
        for r in nn:buckets[r['bin']].append(r['word'])
        null=[]
        for seed in range(22000,22199):
            rng=random.Random(seed);permuted={}
            for b,words in sorted(buckets.items()):
                values=[y[w] for w in words];rng.shuffle(values);permuted.update(zip(words,values))
            null.append(agreement(edges,permuted))
        comp=[dict(words=cc,size=len(cc),case_bearing=sum(y[w] for w in cc),mixed=0<sum(y[w] for w in cc)<len(cc)) for cc in components[a]];mix=Counter('both_case' if y[e['a']] and y[e['b']] else 'neither_case' if not y[e['a']] and not y[e['b']] else 'mixed' for e in edges);details[a]=dict(null_agreement=null,components=comp)
        summary[a]=dict(nodes=len(nn),edges=len(edges),case_bearing=sum(y.values()),edge_types=dict(mix),agreement=actual,null_mean=sum(null)/len(null),null_max=max(null),upper_tail=(1+sum(v>=actual-1e-12 for v in null))/200,components=len(comp),mixed_components=sum(c['mixed'] for c in comp),nodes_in_mixed_components=sum(c['size'] for c in comp if c['mixed']),by_degree={name:dict(nodes=sum(test(r) for r in nn),case_bearing=sum(y[r['word']] for r in nn if test(r))) for name,test in [('degree1',lambda r:r['degree']==1),('degree2plus',lambda r:r['degree']>=2)]})
        index={r['word']:r for r in nn};mistakes[a]={}
        for name,pp in [('baseline',baseline[a]['full12']['applicability']),('balanced',balanced[a]['balanced'][a])]:
            rr=[]
            for i,(f,p) in enumerate(zip(ff[a],pp)):
                w=f['word'];n=index[w];same=sum(y[v]==y[w] for v in n['neighbors']);rr.append(dict(index=i,word=w,truth=y[w],predicted=int(p>=.5),error=int(p>=.5)!=y[w],degree=n['degree'],same_label_neighbors=same,same_fraction=same/n['degree']))
            mistakes[a][name]=rr;summary[a][name]={group:dict(n=len(selected),mean_same_fraction=sum(r['same_fraction'] for r in selected)/len(selected) if selected else None) for group,selected in [('correct',[r for r in rr if not r['error']]),('false_positive',[r for r in rr if r['error'] and r['predicted']]),('false_negative',[r for r in rr if r['error'] and not r['predicted']])]}
    for n,v in [('labels',labels),('details',details),('mistakes',mistakes),('summary',summary)]:save(O/(n+'.json'),v)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
