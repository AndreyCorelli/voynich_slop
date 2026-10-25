"""Directional opaque-neighbor overlap and an exact count-conditioned null mean."""
from collections import Counter, defaultdict
import math
from scipy.stats import hypergeom


def statistics(public, wanted=None):
    counts=Counter();left=defaultdict(Counter);right=defaultdict(Counter)
    for s in public:
        ids=[t['id'] for t in s['tokens']]
        for i,w in enumerate(ids):
            counts[w]+=1
            if i:left[w][ids[i-1]]+=1
            if i+1<len(ids):right[w][ids[i+1]]+=1
    result={}
    for w,n in counts.items():
        if wanted is not None and w not in wanted:continue
        a=left[w];b=right[w];nl=sum(a.values());nr=sum(b.values());overlap=expected=0.
        if nl and nr:
            total=nl+nr
            for k in sorted(set(a)|set(b)):
                mass=a[k]+b[k];overlap+=min(a[k]/nl,b[k]/nr)
                for j in range(max(0,mass-nr),min(mass,nl)+1):
                    expected+=float(hypergeom.pmf(j,total,mass,nl))*min(j/nl,(mass-j)/nr)
        result[w]=dict(n=n,left_n=nl,right_n=nr,supported=bool(nl and nr),overlap=overlap,null_mean=expected,corrected=overlap-expected,frequency=math.log1p(n))
    return result
