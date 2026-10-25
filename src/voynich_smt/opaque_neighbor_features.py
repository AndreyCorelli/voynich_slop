"""Identity-invariant frequency and recurrence features from opaque token IDs."""
from collections import Counter, defaultdict
import math


def bucket(value, boundaries):
    return str(sum(value > edge for edge in boundaries))


def features(public, relational=True):
    """Return one feature list per token, using no anchor/tag/plaintext fields."""
    counts=Counter(t['id'] for s in public for t in s['tokens'])
    total=sum(counts.values()); neighbors={side:defaultdict(Counter) for side in [-1,1]}
    for s in public:
        ts=s['tokens']
        for i,t in enumerate(ts):
            for side in [-1,1]:
                j=i+side
                if 0<=j<len(ts):neighbors[side][t['id']][ts[j]['id']]+=1
    result=[]
    for s in public:
        ts=s['tokens']
        for i,t in enumerate(ts):
            identity=t['id'];out=['opaque:frequency:'+bucket(counts[identity]/total,[.0001,.0005,.001,.0025,.005,.01,.025,.05])]
            for side,name in [(-1,'left'),(1,'right')]:
                prefix='opaque:'+name+':'
                j=i+side
                if not 0<=j<len(ts):out.append(prefix+'edge');continue
                other=ts[j]['id'];out.append(prefix+'frequency:'+bucket(counts[other]/total,[.0001,.0005,.001,.0025,.005,.01,.025,.05]))
                if relational:
                    c=neighbors[side][identity];n=sum(c.values());probs=[v/n for v in c.values()];entropy=-sum(p*math.log(p) for p in probs)/math.log(n) if n>1 else 0.
                    out.extend([prefix+'diversity:'+bucket(len(c)/n,[.25,.5,.75]),prefix+'entropy:'+bucket(entropy,[.25,.5,.75]),prefix+'concentration:'+bucket(max(c.values())/n,[.1,.25,.5,.75]),prefix+'pairshare:'+bucket(c[other]/n,[.05,.1,.25,.5]),prefix+'pairrepeat:'+str(c[other]>=2)])
            if relational:out.append('opaque:flank_equal:'+str(i>0 and i+1<len(ts) and ts[i-1]['id']==ts[i+1]['id']))
            result.append(out)
    return result
