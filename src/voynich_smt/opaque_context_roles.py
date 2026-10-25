"""Second-order directional role similarity from opaque word adjacency alone."""
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix, diags, hstack


def statistics(ids, wanted):
    """Cosine between mean context profiles of left and right neighbors.

    All inputs form one word stream; no sentence boundaries or labels are used.
    Each word's role profile concatenates its empirical left/right distributions.
    """
    vocab=sorted(set(ids));index={w:i for i,w in enumerate(vocab)};n=len(vocab)
    if not n:return {}
    pairs=Counter((index[a],index[b]) for a,b in zip(ids,ids[1:]))
    row=[a for a,b in pairs];col=[b for a,b in pairs]
    forward=csr_matrix(([float(v) for v in pairs.values()],(row,col)),shape=(n,n))
    def normalize(matrix):
        mass=np.asarray(matrix.sum(axis=1)).ravel();return diags(1/np.maximum(mass,1))@matrix
    left=normalize(forward.T.tocsr());right=normalize(forward);roles=hstack([left,right],format='csr')
    present=sorted(set(wanted)&set(index));ix=[index[w] for w in present]
    a=left[ix]@roles;b=right[ix]@roles;dot=np.asarray(a.multiply(b).sum(axis=1)).ravel();na=np.sqrt(np.asarray(a.multiply(a).sum(axis=1)).ravel());nb=np.sqrt(np.asarray(b.multiply(b).sum(axis=1)).ravel());counts=Counter(ids);result={}
    for j,w in enumerate(present):
        valid=bool(na[j]>0 and nb[j]>0);result[w]=dict(n=counts[w],supported=valid,role_similarity=float(np.clip(dot[j]/(na[j]*nb[j]),0,1)) if valid else 0.)
    return result
