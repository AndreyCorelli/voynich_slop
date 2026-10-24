"""Case-free occurrence context and ridge logistic residuals over lexical priors."""
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from voynich_smt.predicate_case import fit as lexical_fit,probability as lexical_probability


def context(tokens,head,predicate):
    """Exclude entire target nominal subtree; never read any token's case.

    Reference topology, POS, and lemmas remain privileged inputs. Only predicate
    verbal morphology is read, explicitly excluding Case/Number/Gender.
    """
    f={'bias':1.}
    if predicate is None:return f
    children={i:[] for i in range(len(tokens))}
    for i,t in enumerate(tokens):
        if t['head'] is not None:children[t['head']].append(i)
    excluded=set();todo=[head]
    while todo:
        i=todo.pop()
        if i in excluded:continue
        excluded.add(i);todo.extend(children[i])
    if predicate in excluded:return f
    t=tokens[predicate]
    f['predicate_pos:'+t['pos']]=1.
    for key in ('VerbForm','Mood','Tense','Voice','Person'):
        if t.get('features',{}).get(key):f[f'verb:{key}:{t["features"][key]}']=1.
    for i in children[predicate]:
        if i in excluded:continue
        child=tokens[i];rel=child['rel'];pos=child['pos']
        if rel in ('punct','discourse'):continue
        f[f'frame:{rel}:{pos}']=1.
        if child['lemma']:f[f'child:{rel}:{child["lemma"]}']=1.
        # Only immediate grandchildren; discard the target subtree everywhere.
        for j in children[i]:
            if j in excluded:continue
            grandchild=tokens[j]
            if grandchild['pos']=='ADP':f[f'other_prep:{rel}:{grandchild["lemma"]}']=1.
    parent=t['head']
    if parent is not None and parent not in excluded:
        f['parent_pos:'+tokens[parent]['pos']]=1.
        if tokens[parent]['lemma']:f['parent_lemma:'+tokens[parent]['lemma']]=1.
    return f


def design(features,vocabulary):
    return np.array([[f.get(k,0.) for k in vocabulary] for f in features],dtype=float)


def fit(records,features,arm='context',ridge=1.):
    lexical=lexical_fit(records,4.);df=Counter(k for f in features for k in f)
    vocabulary=['bias'] if arm=='calibration' else sorted(k for k,n in df.items() if n>=2 or k=='bias')
    x=design(features,vocabulary);y=np.array([r['case']=='Acc' for r in records],dtype=float);offset=[]
    # Leave-sentence-out priors prevent own labels from helping residual fitting.
    priors={sid:lexical_fit([r for r in records if r['sent_id']!=sid],4.) for sid in {r['sent_id'] for r in records}}
    for r in records:
        m=priors[r['sent_id']];p=m['base'] if arm=='context_only' else lexical_probability(m,r['predicate']);offset.append(np.log(p/(1-p)))
    offset=np.array(offset)
    def objective(w):
        z=offset+x@w;loss=float(np.sum(np.logaddexp(0,z)-y*z)+.5*ridge*(w@w));grad=x.T@(expit(z)-y)+ridge*w
        return loss,grad
    result=minimize(objective,np.zeros(len(vocabulary)),jac=True,method='L-BFGS-B',options=dict(maxiter=1000,ftol=1e-12,gtol=1e-7))
    if not result.success:raise RuntimeError(result.message)
    return dict(lexical=lexical,vocabulary=vocabulary,weights=result.x.tolist(),arm=arm,ridge=ridge,objective=float(result.fun),gradient_max=float(np.max(np.abs(result.jac))),iterations=int(result.nit))


def predict(model,features,predicates):
    base=np.array([model['lexical']['base'] if model['arm']=='context_only' else lexical_probability(model['lexical'],p) for p in predicates]);offset=np.log(base/(1-base));return expit(offset+design(features,model['vocabulary'])@np.array(model['weights'])).tolist()
