"""Fixed untrained anonymous pair rankings, no label-guided choice."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,math
P=Path('experiments/results/grammar-restoration');O=P/'iteration227';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def tied(s,k):
    cut=sorted(s,reverse=True)[min(k,len(s))-1];return [i for i,v in enumerate(s) if v>=cut]
def disjoint(s,edges,k):
    used=set();ix=[]
    for i in sorted(range(len(s)),key=lambda i:(-s[i],i)):
        e=edges[i]
        if used.isdisjoint([e['a'],e['b']]):ix.append(i);used.update([e['a'],e['b']])
        if len(ix)==k:break
    return ix

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration223/details.json','iteration225/summary.json','iteration226/summary.json','iteration226/verification-manifest.json']];save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration226/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');features={};scores={};sel={}
    for a in AA:
        g=gg[a];counts=Counter(g['ids']);frames=defaultdict(set)
        for i in range(1,len(g['ids'])-1):
            if all(g['positions'][j] is not None for j in [i-1,i,i+1]):frames[g['ids'][i]].add((g['ids'][i-1],g['ids'][i+1]))
        rows=[]
        for e in g['descriptors']:
            u=frames[e['a']];v=frames[e['b']];assert len(u&v)==e['shared_frames'];rows.append(dict(a=e['a'],b=e['b'],frequency_a=counts[e['a']],frequency_b=counts[e['b']],frames_a=len(u),frames_b=len(v),shared=len(u&v),union=len(u|v)))
        features[a]=rows;scores[a]=dict(support=[r['shared'] for r in rows],frequency_high=[(math.log(r['frequency_a'])+math.log(r['frequency_b']))/2 for r in rows],frequency_low=[-(math.log(r['frequency_a'])+math.log(r['frequency_b']))/2 for r in rows],jaccard=[r['shared']/r['union'] for r in rows]);sel[a]={name:{mode:{f'top{k}':tied(s,k) if mode=='tied' else disjoint(s,g['descriptors'],k) for k in [10,20]} for mode in ['tied','disjoint']} for name,s in scores[a].items()}
    for n,v in [('features',features),('scores',scores),('selections',sel)]:save(O/(n+'.json'),v)
    save(O/'selection-freeze.json',{n:sha(O/n) for n in ['features.json','scores.json','selections.json']})
    labels=read(P/'iteration223/details.json');learned=read(P/'iteration225/summary.json');robust=read(P/'iteration226/summary.json');summary={}
    for a in AA:
        y=labels[a]['edge_values'];edges=gg[a]['descriptors'];totaltypes=len({e[k] for e in edges for k in ['a','b']});summary[a]=dict(all=learned[a]['all'],rankings={},learned={name:dict(tied=r['lists'],disjoint={k:robust[a][name][k]['disjoint'] for k in ['top10','top20']}) for name,r in learned[a]['models'].items()})
        for name,modes in sel[a].items():
            summary[a]['rankings'][name]={}
            for mode,lists in modes.items():
                summary[a]['rankings'][name][mode]={}
                for label,ix in lists.items():
                    endpoints={edges[i][k] for i in ix for k in ['a','b']};summary[a]['rankings'][name][mode][label]=dict(edges=len(ix),requested=int(label[3:]),shortfall=max(0,int(label[3:])-len(ix)),mean_compatibility=sum(y[i] for i in ix)/len(ix) if ix else None,endpoints=len(endpoints),endpoint_coverage=len(endpoints)/totaltypes)
    save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{n:{mode:{k:(r['edges'],round(r['mean_compatibility'],4)) for k,r in lists.items()} for mode,lists in mm.items()} for n,mm in v['rankings'].items()})
if __name__=='__main__':run()
