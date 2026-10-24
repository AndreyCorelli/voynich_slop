"""Public contextual-profile initialization, with no lexical/annotation access.

Only observed source forms need feature vectors. Unobserved inventory forms have
no context profile and remain eligible through full-inventory search and fallback.
No target word labels, spelling, topic, boundaries, or grammatical tags are used.
"""
from collections import Counter, defaultdict
import math
import random

PROFILE_VERSION = 'context-profile-v1'
NEIGHBORS = 64
JITTER = .025


def raw_profiles(counts, edges):
    """Nine frequency/diversity/entropy/neighbor-frequency features per type."""
    total=sum(counts.values())
    if not total: raise ValueError('Empty profile counts')
    left,right=defaultdict(Counter),defaultdict(Counter)
    for (a,b),n in edges.items():
        if a in counts and b in counts:
            right[a][b]+=n; left[b][a]+=n
    # Frequency-selected reference set, not a supplied function-word dictionary.
    cutoff=sorted(counts.values(),reverse=True)[min(31,len(counts)-1)]
    common={w for w,n in counts.items() if n>=cutoff}
    result={}
    for word,n in counts.items():
        features=[math.log(n/total)]
        for neighbors in (left[word],right[word]):
            mass=sum(neighbors.values()); distinct=len(neighbors)
            if mass:
                entropy=math.log(mass)-sum(k*math.log(k) for k in neighbors.values())/mass
                mean=sum(k*math.log(counts[w]/total) for w,k in neighbors.items())/mass
                fraction=sum(k for w,k in neighbors.items() if w in common)/mass
            else: entropy,mean,fraction=0.,0.,0.
            features.extend((math.log1p(distinct)/math.log1p(n),
                             entropy/math.log1p(distinct) if distinct else 0.,mean,fraction))
        result[word]=tuple(features)
    return result


def percentile_profiles(profiles):
    """Within-corpus midrank transforms reduce absolute corpus-size dependence."""
    import numpy as np
    from scipy.stats import rankdata
    ids=tuple(sorted(profiles))
    values=np.asarray([profiles[w] for w in ids],dtype=float)
    for column in range(values.shape[1]):
        values[:,column]=(rankdata(values[:,column],method='average')-.5)/len(ids)
    # Frequency is useful, but must not dominate contextual features.
    values[:,0]*=.5
    return ids,values


def initialize_profile(stream,model,*,seed):
    import numpy as np
    from scipy.spatial import cKDTree
    from .state import DictionaryState
    if model.size<stream.type_count: raise ValueError('Inventory smaller than cipher')
    source=getattr(model,'_profile_source',None)
    if source is None:
        counts={w:n for w,n in enumerate(model.counts[:-1]) if n}
        ids,features=percentile_profiles(raw_profiles(counts,model.edges))
        source=ids,cKDTree(features)
        model._profile_source=source
    source_ids,tree=source
    counts=Counter(c for d in stream.documents for c in d)
    edges=Counter((a,b) for d in stream.documents for a,b in zip(d,d[1:]))
    target_ids,features=percentile_profiles(raw_profiles(counts,edges))
    rng=random.Random(seed+4000037)
    queries=features+np.asarray([[rng.gauss(0,JITTER) for _ in range(features.shape[1])] for _ in target_ids])
    k=min(NEIGHBORS,len(source_ids))
    distances,neighbors=tree.query(queries,k=k,workers=1)
    if k==1:
        neighbors=neighbors.reshape((-1,1));distances=distances.reshape((-1,1))
    assignments=[None]*stream.type_count; used=set()
    positions={c:i for i,c in enumerate(target_ids)}
    for cipher in sorted(counts,key=lambda c:(-counts[c],c)):
        row=positions[cipher]
        ranked=sorted(zip(distances[row],neighbors[row]),key=lambda x:(x[0],source_ids[int(x[1])]))
        word=next((source_ids[int(i)] for _,i in ranked if source_ids[int(i)] not in used),None)
        if word is None:
            # Conflicts do not make any form permanently unavailable. Full-range
            # rejection sampling is normally short (U much smaller than V).
            word=rng.randrange(model.size)
            while word in used: word=rng.randrange(model.size)
        assignments[cipher]=word;used.add(word)
    return DictionaryState.create(stream,model,assignments)
