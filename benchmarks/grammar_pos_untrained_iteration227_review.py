"""Independent full-context counts, deterministic selections and metric audit."""
from pathlib import Path
from collections import Counter,defaultdict
import json,math,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration227'
def read(p):return json.loads(p.read_text())
def near(a,b):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
def run():
    gg=read(P/'iteration193/graphs.json');features=read(O/'features.json');scores=read(O/'scores.json');sel=read(O/'selections.json');ss=read(O/'summary.json');labels=read(P/'iteration223/details.json');old=read(P/'iteration225/summary.json');robust=read(P/'iteration226/summary.json');count=lists=0
    for a,rows in features.items():
        g=gg[a];frequency=Counter(g['ids']);frames=defaultdict(set)
        for i in range(1,len(g['ids'])-1):
            if all(g['positions'][j] is not None for j in [i-1,i,i+1]):frames[g['ids'][i]].add((g['ids'][i-1],g['ids'][i+1]))
        for r,e in zip(rows,g['descriptors']):
            u,v=e['a'],e['b'];assert r==dict(a=u,b=v,frequency_a=frequency[u],frequency_b=frequency[v],frames_a=len(frames[u]),frames_b=len(frames[v]),shared=len(frames[u]&frames[v]),union=len(frames[u]|frames[v]));count+=1
        expected=dict(support=[r['shared'] for r in rows],frequency_high=[math.log(r['frequency_a']*r['frequency_b'])/2 for r in rows],frequency_low=[-math.log(r['frequency_a']*r['frequency_b'])/2 for r in rows],jaccard=[r['shared']/r['union'] for r in rows]);totaltypes=len({e[k] for e in g['descriptors'] for k in ['a','b']})
        assert ss[a]['all']==old[a]['all']
        for name in ['rich19','control3']:assert ss[a]['learned'][name]==dict(tied=old[a]['models'][name]['lists'],disjoint={k:robust[a][name][k]['disjoint'] for k in ['top10','top20']})
        for name,values in scores[a].items():
            for x,y in zip(values,expected[name]):near(x,y)
            for mode in ['tied','disjoint']:
                for k in [10,20]:
                    if mode=='tied':
                        cut=sorted(values,reverse=True)[k-1];ix=[i for i,v in enumerate(values) if v>=cut]
                    else:
                        used=set();ix=[]
                        for i in sorted(range(len(values)),key=lambda i:(-values[i],i)):
                            e=g['descriptors'][i];ends={e['a'],e['b']}
                            if not used.intersection(ends):ix.append(i);used.update(ends)
                            if len(ix)==k:break
                    label=f'top{k}';assert ix==sel[a][name][mode][label];v=ss[a]['rankings'][name][mode][label];ends={g['descriptors'][i][s] for i in ix for s in ['a','b']};assert v['edges']==len(ix) and v['endpoints']==len(ends) and v['requested']==k and v['shortfall']==max(0,k-len(ix));near(v['mean_compatibility'],sum(labels[a]['edge_values'][i] for i in ix)/len(ix));near(v['endpoint_coverage'],len(ends)/totaltypes);lists+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration226/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',edge_feature_rows=count,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
