"""Target-gold label alignment diagnostic; never deployed inference."""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
from scipy.optimize import linear_sum_assignment
P=Path('experiments/results/grammar-restoration');O=P/'iteration232'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration231/predictions.json','iteration231/truth.json','iteration231/features.json','iteration231/design-freeze.json','iteration231/summary.json','iteration231/verification-manifest.json']];save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration231/verification-manifest.json').items():assert sha(Path(p))==h
    pred=read(P/'iteration231/predictions.json');tags=read(P/'iteration231/design-freeze.json')['tags'];groups={a:{name:np.argmax(pp,axis=1).tolist() for name,pp in methods.items()} for a,methods in pred.items()};save(O/'groups.json',groups);save(O/'group-freeze.json',{'groups.json':sha(O/'groups.json')})
    truth=read(P/'iteration231/truth.json');previous=read(P/'iteration231/summary.json');contingencies={};summary={}
    for a,methods in groups.items():
        y=np.array(truth[a]['profiles']);frequency=np.array(truth[a]['frequencies']);summary[a]={};contingencies[a]={}
        for name,group in methods.items():
            group=np.array(group);summary[a][name]={};contingencies[a][name]={};sizes=Counter(group.tolist())
            for weighting,ww in [('type_macro',np.ones(len(y))),('token_weighted',frequency)]:
                w=ww/ww.sum();matrix=np.zeros((len(tags),len(tags)))
                for i,j in enumerate(group):matrix[j]+=w[i]*y[i]
                rows,cols=linear_sum_assignment(-matrix);mapping=dict(zip(rows.tolist(),cols.tolist()));identity=float(np.trace(matrix));aligned=float(matrix[rows,cols].sum());purity=float(matrix.max(axis=1).sum());majority=float((w@y).max());profile_ceiling=float(w@y.max(axis=1));summary[a][name][weighting]=dict(nodes=len(group),nonempty_groups=len(sizes),group_sizes={tags[k]:n for k,n in sizes.items()},identity=identity,target_majority=majority,one_to_one=aligned,many_to_one_purity=purity,word_profile_oracle=profile_ceiling,alignment_gain=aligned-identity,aligned_minus_majority=aligned-majority,purity_minus_majority=purity-majority,one_to_one_mapping={tags[k]:tags[v] for k,v in mapping.items() if k in sizes},purity_mapping={tags[k]:tags[int(matrix[k].argmax())] for k in sizes});contingencies[a][name][weighting]=matrix.tolist()
                baseline=previous[a]['methods'][name]['type_macro_top1_mass' if weighting=='type_macro' else 'covered_token_top1_accuracy'];assert abs(identity-baseline)<1e-12
    save(O/'contingencies.json',contingencies);save(O/'summary.json',summary)
    for a,methods in summary.items():print(a,{n:{w:{k:round(d[k],4) if isinstance(d[k],float) else d[k] for k in ['nonempty_groups','identity','target_majority','one_to_one','many_to_one_purity']} for w,d in metrics.items()} for n,metrics in methods.items()})
if __name__=='__main__':run()
