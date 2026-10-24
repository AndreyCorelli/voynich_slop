"""Keep uncertain proposed ADP classes unknown; never assert the opposite class."""


def assignments(probabilities, threshold):
    result={}
    for opaque,p_conjunction in probabilities.items():
        if p_conjunction>.5:result[opaque]='CCONJ'
        elif threshold is None or 1-p_conjunction>=threshold:result[opaque]='ADP'
    return result


def choose(rows):
    baseline=next(r for r in rows if r['threshold']==0.)['metrics'];eligible=[]
    for r in rows:
        m=r['metrics'];qualified=(m['precision'] is not None and m['precision']>=.9 and m['tp']>=.8*baseline['tp'])
        r['qualified']=qualified
        if qualified:eligible.append(r)
    return max(eligible,key=lambda r:(r['metrics']['tp'],-r['metrics']['fp'],r['threshold'])) if eligible else dict(threshold=None,qualified=False)
