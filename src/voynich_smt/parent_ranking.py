"""Conditional parent choice and typed acyclic predicate forests."""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
import z3

from .predicate_structure import Logistic,morph_features,parent_features,validate_structure

RELATIONS=('root','coordination','subordination')
COORDINATION=frozenset('et atque ac aut uel nec neque sed'.split())
RELATIVE_FORMS=frozenset('qui quae quod quem quam cui cuius quorum quarum quibus quos quas quo qua'.split())
SUBORDINATION=frozenset('ut ne cum quod quia si nisi quamquam quoniam dum ubi postquam antequam quam'.split())


def parents_for(child,predicates,boundaries=None,radius=3):
    i=predicates.index(child)
    candidates=[None]+([p for p in predicates if p!=child] if radius is None else
        predicates[max(0,i-radius):i]+predicates[i+1:i+radius+1])
    if boundaries:
        def region(p):return next(j for j,b in enumerate(boundaries) if p<b)
        candidates=[p for p in candidates if p is None or region(p)==region(child)]
    return candidates


def typed_features(tokens,child,parent,predicates,morph,relation):
    base=parent_features(child,parent,predicates,morph)
    before=tokens[max(0,child-4):child]
    between=tokens[min(child,parent)+1:max(child,parent)] if parent is not None else ()
    cues=[float(any(w in COORDINATION for w in before)),float(any(w in SUBORDINATION for w in before)),
          float(any(w in COORDINATION for w in between)),float(any(w in SUBORDINATION for w in between)),
          float(morph[child][11]),float(any(morph[i][1] for i in range(max(0,child-4),child))),
          float(any(w in RELATIVE_FORMS for w in before))]
    # Relation-specific feature blocks allow the same evidence to support
    # coordination or subordination differently, including ROOT alternatives.
    all_features=[1.]+base+cues
    return sum([all_features if relation==r else [0.]*len(all_features) for r in RELATIONS],[])


@dataclass
class ConditionalRanker(Logistic):
    @classmethod
    def fit_groups(cls,groups):
        if not groups:raise ValueError('At least one training group is required')
        x=np.asarray([row for features,_ in groups for row in features],dtype=float)
        mu=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1
        a=(x-mu)/scale
        lengths=[len(features) for features,_ in groups]
        starts=np.cumsum([0]+lengths[:-1]);gold=np.array([start+index for start,(_,index) in zip(starts,groups)])
        def objective(w):
            logits=a@w;gradient_logits=np.zeros(len(x));loss=0.
            for start,length,target in zip(starts,lengths,gold):
                segment=logits[start:start+length];normalizer=logsumexp(segment)
                loss+=normalizer-logits[target]
                gradient_logits[start:start+length]=np.exp(segment-normalizer)
                gradient_logits[target]-=1
            loss=loss/len(groups)+.01*np.dot(w,w)/2
            gradient=a.T@gradient_logits/len(groups)+.01*w
            return loss,gradient
        result=minimize(objective,np.zeros(a.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':300})
        if not result.success:raise ValueError('Conditional ranking failed: '+result.message)
        # A common intercept cancels within a choice set; keep it exactly zero.
        return cls([0.]+result.x.tolist(),mu.tolist(),scale.tolist())


def choices(tokens,child,predicates,morph,typed=False,boundaries=None,radius=3):
    rows=[]
    for parent in parents_for(child,predicates,boundaries,radius):
        labels=['root'] if parent is None else ['coordination','subordination'] if typed else ['untyped']
        for relation in labels:
            feature=typed_features(tokens,child,parent,predicates,morph,relation) if typed else parent_features(child,parent,predicates,morph)
            rows.append({'parent':parent,'relation':relation,'features':feature})
    return rows


def infer_links(tokens,predicates,adapter,ranker,*,typed=False,boundaries=None,radius=3,timeout_ms=2000):
    """Link caller-supplied positions; benchmark must label their provenance.

    This generic linker has no annotation argument. The detected pipeline supplies
    model positions; explicit oracle diagnostics supply reference positions.
    """
    tokens=tuple(tokens);predicates=list(predicates);n=len(tokens)
    if predicates!=sorted(set(predicates)) or any(p<0 or p>=n for p in predicates):
        raise ValueError('Predicate positions must be unique, sorted and in range')
    if boundaries is not None and (not boundaries or boundaries[-1]!=n or
            any(a>=b for a,b in zip((0,)+tuple(boundaries),boundaries))):
        raise ValueError('Boundaries must cover the stream exactly')
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    options={};parents={};relations={};status='optimal';score=0
    if predicates:
        solver=z3.Optimize();solver.set(timeout=timeout_ms)
        selected={p:z3.Int(f'arc{p}') for p in predicates};depth={p:z3.Int(f'd{p}') for p in predicates};terms=[]
        for child in predicates:
            rows=choices(tokens,child,predicates,morph,typed,boundaries,radius)
            logits=ranker.logits([r['features'] for r in rows]);normalizer=float(logsumexp(logits))
            options[child]=[]
            for i,(row,value) in enumerate(zip(rows,logits)):
                options[child].append({'parent':row['parent'],'relation':row['relation'],
                    'logit':float(value),'conditional_probability':float(math.exp(value-normalizer))})
                terms.append(z3.If(selected[child]==i,round(float(value)*1000000),0))
                if row['parent'] is not None:solver.add(z3.Implies(selected[child]==i,depth[child]>depth[row['parent']]))
            solver.add(selected[child]>=0,selected[child]<len(rows),depth[child]>=0,depth[child]<len(predicates))
        objective=solver.maximize(z3.Sum(terms));answer=solver.check()
        if answer==z3.sat and solver.lower(objective)==solver.upper(objective):
            model=solver.model()
            for child in predicates:
                row=options[child][model.eval(selected[child]).as_long()]
                parents[child]=row['parent'];relations[child]=row['relation'];score+=round(row['logit']*1000000)
        else:status='unresolved';parents={p:None for p in predicates};relations={p:None for p in predicates};score=None
    owners=[]
    for i in range(n):
        allowed=[p for p in predicates if boundaries is None or
            next(j for j,b in enumerate(boundaries) if p<b)==next(j for j,b in enumerate(boundaries) if i<b)]
        owners.append(min(allowed,key=lambda p:(abs(p-i),p)) if allowed else None)
    roots=[]
    for p in owners:
        if p is None or status!='optimal':roots.append(None);continue
        while parents[p] is not None:p=parents[p]
        roots.append(p)
    result={'tokens':n,'status':status,'predicates':predicates,'parents':parents,'relations':relations,
        'arc_candidates':options,'token_anchors':owners,'root_groups':roots,'forest_score_integer':score,
        'inferred_boundaries':[i for i in range(1,n) if roots[i] is not None and roots[i-1] is not None and roots[i]!=roots[i-1]],
        'known_tokens':sum(bool(adapter.analyze(w)) for w in tokens)}
    validate_structure(result)
    return result
