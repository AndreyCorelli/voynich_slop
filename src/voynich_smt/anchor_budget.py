"""Source-frozen function-anchor budgets and conservative calibration diagnostic."""
from collections import Counter
from scipy.stats import beta
from voynich_smt.pooled_grammar import counts

def budgets(sentences,inventory):
    freq=Counter(t['word'] for s in sentences for t in s['tokens']);eligible=sorted((w for w,p in inventory.items() if p in ('ADP','CCONJ','SCONJ')),key=lambda w:(-freq[w],w))
    return {str(n):{w:inventory[w] for w in eligible[:n]} for n in (0,5,10,20,len(eligible))}

def precision_lower(k,n,alpha=.05/101):
    return float(beta.ppf(alpha,k,n-k+1)) if k and n else 0.

def conservative_policy(rows,arm):
    eligible=[]
    for i in range(101):
        threshold=i/100;c=counts(rows,'pp',arm,threshold);types=len({r['word'] for r in rows if r['scores'][arm]['pp']>=threshold});lower=precision_lower(c['tp'],c['predicted'])
        if c['predicted']>=20 and types>=10 and lower>=.9:eligible.append(dict(threshold=threshold,calibration=c,types=types,precision_lower=lower))
    return max(eligible,key=lambda r:(r['calibration']['tp'],r['precision_lower'],r['threshold'])) if eligible else None
