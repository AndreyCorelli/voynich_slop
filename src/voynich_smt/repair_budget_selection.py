"""Choose a repair budget by labeled calibration gain and a spoil constraint."""
import numpy as np


def edit_counts(baseline,prediction,gold):
    a=np.asarray(baseline);b=np.asarray(prediction);y=np.asarray(gold)
    corrected=int(((a!=y)&(b==y)).sum());spoiled=int(((a==y)&(b!=y)).sum())
    return dict(tokens=len(y),baseline_correct=int((a==y).sum()),corrected=corrected,spoiled=spoiled,net=corrected-spoiled)


def select_budget(records,risk=.01):
    if not 0<=risk<=1:raise ValueError('risk must be in [0,1]')
    budgets=sorted(set(float(b) for r in records for b in r['predictions']))
    if 0. not in budgets:raise ValueError('No-update budget0 is required')
    candidates=[]
    for budget in budgets:
        total=None
        for r in records:
            predictions={float(b):p for b,p in r['predictions'].items()};c=edit_counts(r['baseline'],predictions[budget],r['gold'])
            total=c if total is None else {k:total[k]+c[k] for k in c}
        total.update(budget=budget,feasible=total['spoiled']<=risk*total['baseline_correct']);candidates.append(total)
    feasible=[c for c in candidates if c['feasible']];best=max(feasible,key=lambda c:(c['net'],-c['spoiled'],-c['budget']))
    return dict(budget=best['budget'],risk=risk,calibration=best,candidates=candidates)
