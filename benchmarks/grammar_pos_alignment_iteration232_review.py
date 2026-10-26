"""Scalar contingency and assignment-dual optimality verification."""
from pathlib import Path
from collections import Counter
import json,hashlib,math
import numpy as np
from scipy.optimize import linprog
P=Path('experiments/results/grammar-restoration');O=P/'iteration232'
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-10,rtol=1e-10)
def run():
    pp=read(P/'iteration231/predictions.json');truth=read(P/'iteration231/truth.json');tags=read(P/'iteration231/design-freeze.json')['tags'];groups=read(O/'groups.json');matrices=read(O/'contingencies.json');ss=read(O/'summary.json');old=read(P/'iteration231/summary.json');n=len(tags);checks=0
    constraints=np.zeros((n*n,2*n))
    for i in range(n):
        for j in range(n):constraints[i*n+j,i]=-1;constraints[i*n+j,n+j]=-1
    for a,methods in pp.items():
        y=truth[a]['profiles'];frequency=truth[a]['frequencies']
        for name,p in methods.items():
            group=[max(range(n),key=lambda j:row[j]) for row in p];assert group==groups[a][name];sizes=Counter(group)
            for weighting,ww in [('type_macro',[1]*len(y)),('token_weighted',frequency)]:
                total=sum(ww);matrix=[[sum(ww[k]*y[k][j]/total for k,g in enumerate(group) if g==i) for j in range(n)] for i in range(n)];near(matrix,matrices[a][name][weighting]);m=np.array(matrix);r=ss[a][name][weighting];assert r['nodes']==len(y) and r['nonempty_groups']==len(sizes) and r['group_sizes']=={tags[i]:v for i,v in sizes.items()}
                identity=sum(matrix[i][i] for i in range(n));majority=max(sum(matrix[i][j] for i in range(n)) for j in range(n));purity=sum(max(row) for row in matrix);oracle=sum(ww[i]*max(y[i])/total for i in range(len(y)));near(identity,r['identity']);near(majority,r['target_majority']);near(purity,r['many_to_one_purity']);near(oracle,r['word_profile_oracle'])
                mapping={tags.index(i):tags.index(j) for i,j in r['one_to_one_mapping'].items()};assert set(mapping)==set(sizes) and len(set(mapping.values()))==len(mapping);chosen=sum(matrix[i][j] for i,j in mapping.items());near(chosen,r['one_to_one'])
                # A feasible dual bounds every full one-to-one assignment from above.
                dual=linprog(np.ones(2*n),A_ub=constraints,b_ub=-m.ravel(),bounds=[(None,None)]*(2*n),method='highs');assert dual.success;assert np.all(dual.x[:n,None]+dual.x[None,n:]>=m-1e-9);near(dual.fun,chosen);assert chosen<=purity+1e-10 and purity<=oracle+1e-10
                for i,j in r['purity_mapping'].items():assert matrix[tags.index(i)][tags.index(j)]==max(matrix[tags.index(i)])
                near(r['alignment_gain'],chosen-identity);near(r['aligned_minus_majority'],chosen-majority);near(r['purity_minus_majority'],purity-majority);near(identity,old[a]['methods'][name]['type_macro_top1_mass' if weighting=='type_macro' else 'covered_token_top1_accuracy']);checks+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration231/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'group-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',scalar_contingencies=checks,assignment_dual_certificates=checks,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
