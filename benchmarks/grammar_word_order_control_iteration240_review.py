"""Independent word shuffles, graphs, clustering and oracle-score audit."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,hashlib,random
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import linear_sum_assignment,linprog
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
from benchmarks.grammar_pos_text_robustness_iteration237_review import lloyd
P=Path('experiments/results/grammar-restoration');O=P/'iteration240'
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-8,rtol=1e-8)
def describe(v):return dict(minimum=min(v),mean=sum(v)/len(v),maximum=max(v)) if v else None
def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];graphs=read(O/'graphs.json');parts=read(O/'partitions.json');audit=read(O/'shuffle-audit.json');dd=read(O/'details.json');ss=read(O/'summary.json');baseline=read(P/'iteration237/baselines.json');ref=read(P/'iteration201/development-references.json');ref['Dante']={'pos':read(P/'iteration200/pos-references.json')['pos_by_stream_position']};tags=read(P/'iteration231/design-freeze.json')['tags'];nchecks=geometries=metrics=certs=0;constraints=np.zeros((289,34))
    for i in range(17):
        for j in range(17):constraints[17*i+j,i]=-1;constraints[17*i+j,17+j]=-1
    for a,records in graphs.items():
        g=gg[a];sentences=defaultdict(list);profiles=defaultdict(Counter);freq=Counter()
        for i,p in enumerate(g['positions']):
            if p is not None:sentences[tuple(p[:2])].append(i);profiles[g['ids'][i]][ref[a]['pos'][i]]+=1;freq[g['ids'][i]]+=1
        prob={w:[c[t]/sum(c.values()) for t in tags] for w,c in profiles.items()}
        def evaluate(part,cert=False):
            nonlocal metrics,certs
            if not part['clusterable']:return None
            y=np.array([prob[w] for w in part['words']]);output={}
            for name,weights in [('type_macro',np.ones(len(y))),('token_weighted',np.array([freq[w] for w in part['words']]))]:
                w=weights/weights.sum();m=np.zeros((17,17));np.add.at(m,part['labels'],w[:,None]*y);r,c=linear_sum_assignment(-m);output[name]=dict(one_to_one=float(m[r,c].sum()),purity=float(m.max(1).sum()),majority=float((w@y).max()),profile_oracle=float(w@y.max(1)));metrics+=1
                if cert:
                    dual=linprog(np.ones(34),A_ub=constraints,b_ub=-m.ravel(),bounds=[(None,None)]*34,method='highs');assert dual.success;near(dual.fun,output[name]['one_to_one']);certs+=1
            return output
        actual=evaluate(baseline[a]['partition'],True)
        for name,v in actual.items():
            for k,z in v.items():near(z,ss[a]['original_scores'][name][k])
        for j,record in enumerate(records):
            seed=24000+j;rng=random.Random(seed);ids=g['ids'].copy();changed=0
            for sentence,ix in sorted(sentences.items()):
                values=[g['ids'][i] for i in ix];rng.shuffle(values);assert Counter(values)==Counter(g['ids'][i] for i in ix)
                for i,w in zip(ix,values):changed+=w!=g['ids'][i];ids[i]=w
            assert Counter(ids)==Counter(g['ids']);assert all(ids[i]==g['ids'][i] for i,p in enumerate(g['positions']) if p is None);assert audit[a][j]==dict(seed=seed,sentences=len(sentences),lexical_positions=sum(map(len,sentences.values())),changed_positions=changed)
            frames=defaultdict(lambda:defaultdict(list))
            for i in range(1,len(ids)-1):
                if all(g['positions'][k] is not None for k in [i-1,i,i+1]) and freq[ids[i]]>=5:frames[(ids[i-1],ids[i+1])][ids[i]].append(i)
            pairs=defaultdict(list)
            for f,words in sorted(frames.items()):
                for u,v in combinations(sorted(words),2):pairs[(u,v)].append(dict(frame=list(f),a_positions=words[u],b_positions=words[v]))
            edges=[dict(a=u,b=v,shared_frames=len(ff),frames=ff) for (u,v),ff in sorted(pairs.items()) if len(ff)>=2];assert edges==record['descriptors'];p=parts[a][j];words=sorted({e[k] for e in edges for k in ['a','b']});assert p['words']==words and p['seed']==seed;nchecks+=1
            if len(words)>=17:
                assert p['clusterable'];embedded=cluster({'descriptors':edges});x=np.array(embedded['embedding']);labels,initial,iterations=lloyd(x);assert labels==p['labels'] and initial==p['initial_center_indices'] and iterations==p['iterations']
                if j in [0,99,198]:
                    index={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
                    for e in edges:u,v=index[e['a']],index[e['b']];adj[u,v]=adj[v,u]=1
                    degree=adj.sum(1);ev,vec=eigh(np.eye(len(words))-np.diag(degree**-.5)@adj@np.diag(degree**-.5),driver='evr');dim=min(len(words),sum(ev<=1e-10)+17);boundary=dim-1
                    while dim<len(words) and abs(ev[dim]-ev[boundary])<=1e-10:dim+=1
                    z=vec[:,:dim];z/=np.linalg.norm(z,axis=1)[:,None];near(z@z.T,x@x.T);geometries+=1
            else:assert not p['clusterable']
            expected=evaluate(p,j in [0,99,198]);r=dd[a][j];assert r['seed']==seed and r['edges']==len(edges) and r['nodes']==len(words) and r['clusterable']==p['clusterable']
            if expected:
                for name,v in expected.items():
                    for k,z in v.items():near(z,r['scores'][name][k])
            else:assert r['scores'] is None
        s=ss[a];assert s['original_edges']==baseline[a]['edges'] and s['original_nodes']==len(baseline[a]['partition']['words']);assert s['clusterable_runs']==sum(r['clusterable'] for r in dd[a]) and s['zero_edge_runs']==sum(r['edges']==0 for r in dd[a]);near(s['edge_count_upper_tail'],(1+sum(r['edges']>=s['original_edges'] for r in dd[a]))/200)
        for name,key in [('null_edges','edges'),('null_nodes','nodes')]:
            for k,z in describe([r[key] for r in dd[a]]).items():near(z,s[name][k])
        for weighting,mm in s['conditional_scores'].items():
            for metric,value in mm.items():
                expected=describe([r['scores'][weighting][metric] for r in dd[a] if r['clusterable']])
                if expected:
                    for k,z in expected.items():near(z,value[k])
                else:assert value is None
    hashes=0
    manifests=[read(O/'design-freeze.json')['inputs'],read(P/'iteration239/verification-manifest.json'),read(P/'iteration231/verification-manifest.json'),read(P/'iteration237/design-freeze.json')['inputs']]
    for manifest in manifests:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'graph-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',shuffle_graph_partition_replays=nchecks,independent_geometry_samples=geometries,oracle_metric_groups=metrics,assignment_dual_certificates=certs,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
