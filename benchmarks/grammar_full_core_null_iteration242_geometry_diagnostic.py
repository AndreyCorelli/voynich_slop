from pathlib import Path
import gzip,json,numpy as np
from scipy.linalg import eigh
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
out=Path('experiments/results/grammar-restoration/iteration242');records=[]
for path in [out/'real.json.gz']+[out/f'null-{s}.json.gz' for s in range(24000,24199)]:
 d=json.loads(gzip.decompress(path.read_bytes()))
 for stage,edges in [('initial',d['initial_graph']),('deletion15',d['deletions'][15]['graph'])]:
  c=cluster({'descriptors':edges});x=np.array(c['embedding']);words=c['words'];ix={w:i for i,w in enumerate(words)};a=np.zeros((len(words),len(words)))
  for e in edges:i,j=ix[e['a']],ix[e['b']];a[i,j]=a[j,i]=1
  degree=a.sum(1);lap=np.eye(len(words))-np.diag(degree**-.5)@a@np.diag(degree**-.5)
  ev,v=eigh(lap,driver='evr');dim=min(len(words),sum(ev<=1e-10)+17);boundary=dim-1
  while dim<len(words) and abs(ev[dim]-ev[boundary])<=1e-10:dim+=1
  z=v[:,:dim].copy();z/=np.linalg.norm(z,axis=1)[:,None]
  if not np.allclose(z@z.T,x@x.T,atol=1e-8,rtol=1e-8):
   record=dict(trial=path.name,stage=stage,dimension=int(dim),expected_dimension=c['embedding_dimension'],evr_orthogonality=float(np.max(abs(v.T@v-np.eye(len(words))))),evr_gram_error=float(np.max(abs(z@z.T-x@x.T))))
   ev,v=eigh(lap,driver='evd');z=v[:,:dim].copy();z/=np.linalg.norm(z,axis=1)[:,None];record['evd_gram_error']=float(np.max(abs(z@z.T-x@x.T)));record['evd_orthogonality']=float(np.max(abs(v.T@v-np.eye(len(words)))));assert np.allclose(z@z.T,x@x.T,atol=1e-8,rtol=1e-8);records.append(record);print(record,flush=True)
(out/'geometry-diagnostic.json').write_text(json.dumps(records,indent=2)+'\n')
print('complete',len(records))
