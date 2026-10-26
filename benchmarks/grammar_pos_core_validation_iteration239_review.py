"""Independent masked graph and retention audit, geometry samples and replay."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,hashlib,random
import numpy as np
from scipy.linalg import eigh
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
P=Path('experiments/results/grammar-restoration');O=P/'iteration239'
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-8,rtol=1e-8)
def lloyd(x):
    chosen=[random.Random(23500).randrange(len(x))]
    while len(chosen)<17:
        d=np.sum((x[:,None,:]-x[chosen][None,:,:])**2,axis=2).min(1);d[chosen]=-1;chosen.append(int(np.argmax(d)))
    centers=x[chosen].copy();previous=None
    for iteration in range(300):
        labels=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);new=centers.copy()
        for k in range(17):
            if any(labels==k):new[k]=x[labels==k].mean(0)
        movement=max(np.linalg.norm(new-centers,axis=1));centers=new
        if previous is not None and np.array_equal(previous,labels) or movement<=1e-10:break
        previous=labels.copy()
    return np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1).tolist(),chosen,iteration+1

def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];graphs=read(O/'graphs.json');parts=read(O/'partitions.json');baselines=read(P/'iteration237/baselines.json');cores=read(P/'iteration238/cores.json');dd=read(O/'details.json');ss=read(O/'summary.json');old=read(P/'iteration235/runs.json');graphchecks=geometry=0
    originalgraphs=graphs;originalparts=parts;originaldetails=dd;originalsummary=ss
    originalgg=gg;originalcores=cores;originalbaselines=baselines;originalold=old
    graphs={};parts={};dd={};ss={};gg={};cores={};baselines={};old={};fractions={}
    for author,levels in originalgraphs.items():
        for fraction,records in levels.items():
            key=author+'/'+fraction;graphs[key]=records;parts[key]=originalparts[author][fraction];dd[key]=originaldetails[author][fraction];ss[key]=originalsummary[author][fraction];gg[key]=originalgg[author];cores[key]=originalcores[author];baselines[key]=originalbaselines[author];old[key]=originalold[author];fractions[key]=float(fraction)
    for a,records in graphs.items():
        g=gg[a];sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None});assert baselines[a]['edges']==len(g['descriptors']) and baselines[a]['partition']['labels']==old[a][0]['labels'];cc=[c for c in cores[a] if c['size']>1];pairs=[(u,v) for c in cc for u,v in combinations(c['words'],2)];nodes={w for c in cc for w in c['words']}
        for j,record in enumerate(records):
            seed=23900+j;assert record['seed']==seed and record['total_sentences']==len(sentences);removed=set(random.Random(seed).sample(sentences,int(fractions[a]*len(sentences))));assert record['deleted_sentences']==[list(v) for v in sorted(removed)];valid=[p is not None and tuple(p[:2]) not in removed for p in g['positions']];freq=Counter(w for w,ok in zip(g['ids'],valid) if ok);frames=defaultdict(lambda:defaultdict(list))
            for i in range(1,len(valid)-1):
                if valid[i-1] and valid[i] and valid[i+1] and freq[g['ids'][i]]>=5:frames[(g['ids'][i-1],g['ids'][i+1])][g['ids'][i]].append(i)
            joins=defaultdict(list)
            for f,words in sorted(frames.items()):
                for u,v in combinations(sorted(words),2):joins[(u,v)].append(dict(frame=list(f),a_positions=words[u],b_positions=words[v]))
            expected=[dict(a=u,b=v,shared_frames=len(ff),frames=ff) for (u,v),ff in sorted(joins.items()) if len(ff)>=2];assert expected==record['descriptors'];part=parts[a][j];words=sorted({e[k] for e in expected for k in ['a','b']});assert words==part['words'] and part['seed']==seed;graphchecks+=1
            if len(words)>=17:
                assert part['clusterable'];embedded=cluster({'descriptors':expected});x=np.array(embedded['embedding']);labels,initial,iterations=lloyd(x);assert labels==part['labels'] and initial==part['initial_center_indices'] and iterations==part['iterations'];assert part['embedding_dimension']==embedded['embedding_dimension'] and part['zero_eigenvalues']==embedded['zero_eigenvalues']
                if j in [0,15,30]:
                    ix={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
                    for e in expected:u,v=ix[e['a']],ix[e['b']];adj[u,v]=adj[v,u]=1
                    degree=adj.sum(1);lap=np.eye(len(words))-np.diag(degree**-.5)@adj@np.diag(degree**-.5);ev,vec=eigh(lap,driver='evr');zero=sum(ev<=1e-10);dim=min(len(words),zero+17);boundary=dim-1
                    while dim<len(words) and abs(ev[dim]-ev[boundary])<=1e-10:dim+=1
                    z=vec[:,:dim];z/=np.linalg.norm(z,axis=1)[:,None];near(z@z.T,x@x.T);geometry+=1
            else:assert not part['clusterable'] and part['labels'] is None
            labels=dict(zip(words,part['labels'])) if part['clusterable'] else {};survive=[(u,v) for u,v in pairs if u in words and v in words];retained=sum(part['clusterable'] and labels[u]==labels[v] for u,v in survive);intact=sum(all(w in labels for w in c['words']) and len({labels[w] for w in c['words']})==1 for c in cc);r=dd[a][j];assert r['seed']==seed and r['clusterable']==part['clusterable'] and r['edges']==len(expected) and r['graph_nodes']==len(words);assert r['original_pairs']==len(pairs) and r['surviving_pairs']==len(survive) and r['retained_pairs']==retained and r['intact_cores']==intact and r['original_cores']==len(cc);
            if pairs:near(r['unconditional_retention'],retained/len(pairs));near(r['pair_survival'],len(survive)/len(pairs))
            else:assert r['unconditional_retention'] is None and r['pair_survival'] is None
            if survive:near(r['conditional_retention'],retained/len(survive))
            else:assert r['conditional_retention'] is None
        s=ss[a];assert s['original_pairs']==len(pairs) and s['unclusterable_runs']==sum(not p['clusterable'] for p in parts[a])
        for metric in ['unconditional_retention','conditional_retention','pair_survival','intact_cores']:
            values=[r[metric] for r in dd[a] if r[metric] is not None]
            if not values:assert s[metric] is None;continue
            expected=dict(minimum=min(values),mean=sum(values)/len(values),maximum=max(values))
            for k,v in expected.items():near(v,s[metric][k])
    corestats=read(O/'core-statistics.json')
    for author,levels in originalparts.items():
        nonsingleton=[c for c in originalcores[author] if c['size']>1]
        for fraction,records in levels.items():
            expected=[]
            for c in nonsingleton:
                available=intact=0
                for p in records:
                    present=set(p['words']);labels=dict(zip(p['words'],p['labels'])) if p['clusterable'] else {}
                    available+=all(w in present for w in c['words']);intact+=all(w in labels for w in c['words']) and len({labels[w] for w in c['words']})==1
                expected.append(dict(words=c['words'],size=c['size'],all_endpoints_survive=available,intact=intact))
            assert expected==corestats[author][fraction]
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration238/verification-manifest.json'),read(P/'iteration237/design-freeze.json')['inputs']]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'partition-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',graph_and_partition_replays=graphchecks,independent_geometry_samples=geometry,retention_groups=310,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
