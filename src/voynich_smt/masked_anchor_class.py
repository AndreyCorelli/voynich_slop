"""Whole-type masked features and type-blocked contextual class diagnostics."""
import hashlib
import math
import numpy as np
from voynich_smt import anchor_grammar as ag

CLASSES=('ADP','CCONJ')


def type_fold(word):
    return int(hashlib.sha256(('class92|'+word).encode()).hexdigest()[:8],16)%3


def masked_type_features(public,held_ids,target_id):
    hidden=set(held_ids)|{target_id}
    masked=[dict(s,tokens=[dict(t,anchor=None,tag='X') if t['id'] in hidden else dict(t) for t in s['tokens']]) for s in public]
    return [r for r in ag.public_features(masked) if r['word']==target_id]


def cap_rows(rows,limit=20):
    return sorted(rows,key=lambda r:hashlib.sha256((r['sid']+'|'+str(r['index'])).encode()).hexdigest())[:limit]


def type_summary(records,arm):
    supported=[r for r in records if r['n']>=5 and r['sentences']>=3]
    def calc(rs):
        if not rs:return dict(n=0,accuracy=None,nll=None)
        return dict(n=len(rs),accuracy=sum(int(np.argmax(r['probabilities'][arm]))==r['gold'] for r in rs)/len(rs),nll=sum(-math.log(max(1e-12,r['probabilities'][arm][r['gold']])) for r in rs)/len(rs))
    return dict(all=calc(records),supported=calc(supported))
