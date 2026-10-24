"""Counterfactual eligibility and exact contextual-logit traces; no policy change."""
import math
import numpy as np
from voynich_smt import anchor_grammar as ag
from voynich_smt.anchor_class_audit import disagreement
from voynich_smt.paired_anchor_class import target_features


def eligibility_sets(left,right):
    a=set(left);b=set(right)
    return dict(left=sorted(a),right=sorted(b),intersection=sorted(a&b),union=sorted(a|b))


def eligible_pairs(scores,allowed,identity_to_word):
    # Deliberately override the view's count gate for a controlled diagnostic.
    # Absent endpoints are never fabricated; only computed pairs are returned.
    return [dict(r,supported=True) for r in scores if all(i in identity_to_word for i in r['pair']) and {identity_to_word[i] for i in r['pair']}<=set(allowed)]


def trace_pair(public,pair,proposed,model,focus_id,groups):
    rows=target_features(public,set(pair));q=ag.predict([r['features'] for r in rows],model);weights=np.asarray(model['weights']);delta=weights[:,1]-weights[:,0];v=model['vocabulary'];endpoints=[];focus=[];gain=0.
    for opaque in pair:
        indices=[j for j,r in enumerate(rows) if r['word']==opaque];mean=q[indices].mean(axis=0).tolist();margin,_=disagreement(mean,['ADP','CCONJ'],proposed[opaque]);gain+=margin;bygroup={}
        for group in sorted({groups.get(rows[j]['sid'],'extra') for j in indices}):
            js=[j for j in indices if groups.get(rows[j]['sid'],'extra')==group];bygroup[group]=dict(n=len(js),mean=q[js].mean(axis=0).tolist())
        endpoints.append(dict(id=opaque,proposed=proposed[opaque],n=len(indices),mean=mean,groups=bygroup,margin=margin))
        if opaque==focus_id:
            for j in indices:
                r=rows[j];contributions={f:float(delta[v[f]]) for f in sorted(set(r['features'])) if f in v};logit=sum(contributions.values());assert math.isclose(logit,math.log(q[j,1]/q[j,0]),rel_tol=1e-10,abs_tol=1e-12);focus.append(dict(sid=r['sid'],index=r['index'],probabilities=q[j].tolist(),logit=logit,contributions=contributions))
    return dict(pair=sorted(pair),gain=float(gain),endpoints=endpoints,focus_occurrences=focus)


def equal_group_gain(trace):
    gain=0.
    for endpoint in trace['endpoints']:
        mean=np.mean([g['mean'] for g in endpoint['groups'].values()],axis=0).tolist();margin,_=disagreement(mean,['ADP','CCONJ'],endpoint['proposed']);gain+=margin
    return float(gain)
