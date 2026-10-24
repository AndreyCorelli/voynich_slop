"""Binary case prediction with source-only predicate counts and explicit backoff."""
from collections import Counter,defaultdict


def fit(records,strength=4.):
    if strength<=0:raise ValueError('strength must be positive')
    total=Counter();counts=defaultdict(Counter)
    for row in records:
        if row['case'] not in ('Acc','Abl'):raise ValueError('binary case labels required')
        total[row['case']]+=1
        if row['predicate'] is not None:counts[row['predicate']][row['case']]+=1
    return dict(base=(total['Acc']+.5)/(sum(total.values())+1),strength=strength,counts={k:dict(v) for k,v in counts.items()},tokens=sum(total.values()))


def probability(model,predicate):
    """No target case, morphology, or dependency annotations are accepted."""
    c=model['counts'].get(predicate,{})
    return (c.get('Acc',0)+model['strength']*model['base'])/(sum(c.values())+model['strength'])


def governor(tokens,head):
    """Diagnostic oracle: first verbal ancestor, with cycle protection."""
    seen={head};node=tokens[head]['head'];hops=1
    while node is not None and node not in seen:
        seen.add(node)
        if tokens[node]['pos'] in ('VERB','AUX'):return node,hops
        node=tokens[node]['head'];hops+=1
    return None,None


def nearest(tokens,prep):
    candidates=[i for i,t in enumerate(tokens) if t['pos'] in ('VERB','AUX')]
    return min(candidates,key=lambda i:(abs(i-prep),i)) if candidates else None
