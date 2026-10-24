"""Lexical-frequency-free finite-predicate and clause-skeleton inference.

Target annotations are not an inference input. Morphology and source-trained
weights supply evidence; unresolved tokens/alternatives stay explicit.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import minimize
import z3

from .coherent_grammar import finite

CATEGORIES=('N','PRON','ADJ','V','VPAR','PREP','CONJ','ADV','NUM')


def morph_features(readings):
    # Existence flags avoid rewarding duplicate dictionary analyses.
    rr=set(readings)
    return [float(any(r.pos==p for r in rr)) for p in CATEGORIES]+[
        float(any(finite(r) for r in rr)),float(any(r.pos=='V' and not finite(r) for r in rr)),
        float(any(r.get('Mood')=='SUB' for r in rr)),float(any(r.get('Case')=='NOM' for r in rr)),
        float(any(r.get('Person')=='3' for r in rr)),float(not rr)]


def sentence_features(tokens,adapter):
    local=[morph_features(adapter.analyze(w)) for w in tokens]
    width=len(local[0]) if local else len(morph_features(()))
    # A fixed morphological window; boundary markers/punctuation never appear.
    return np.array([sum([local[j] if 0<=j<len(tokens) else [0.]*width
                        for j in range(i-2,i+3)],[]) for i in range(len(tokens))],dtype=float)


@dataclass
class Logistic:
    weights: list
    mean: list
    scale: list

    @classmethod
    def fit(cls,x,y):
        x=np.asarray(x);y=np.asarray(y);mu=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1
        a=np.column_stack([np.ones(len(x)),(x-mu)/scale])
        def objective(w):
            z=a@w
            p=1/(1+np.exp(-np.clip(z,-40,40)))
            value=np.mean(np.logaddexp(0,z)-y*z)+.01*np.dot(w[1:],w[1:])/2
            gradient=a.T@(p-y)/len(y);gradient[1:]+=.01*w[1:]
            return value,gradient
        result=minimize(objective,np.zeros(a.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':200})
        if not result.success:raise ValueError('Source classifier did not converge: '+result.message)
        return cls(result.x.tolist(),mu.tolist(),scale.tolist())

    def logits(self,x):
        x=np.asarray(x)
        if not len(x):return np.array([])
        return np.column_stack([np.ones(len(x)),(x-np.asarray(self.mean))/np.asarray(self.scale)])@np.asarray(self.weights)

    def probability(self,x):return 1/(1+np.exp(-np.clip(self.logits(x),-40,40)))


def parent_features(child,parent,predicates,morph):
    width=len(morph[0]);root=parent is None
    cindex=predicates.index(child);pindex=predicates.index(parent) if not root else -1
    lo,hi=sorted((child,parent)) if not root else (child,child)
    gap=morph[lo+1:hi]
    between=np.max(gap,axis=0).tolist() if gap else [0.]*width
    before=morph[max(0,child-3):child]
    before=np.max(before,axis=0).tolist() if before else [0.]*width
    return [float(root),float(not root and parent<child),float(not root and parent>child),
        math.log1p(abs(child-parent)) if not root else 0.,
        abs(cindex-pindex) if not root else 0.,float(cindex==0),float(cindex==len(predicates)-1),
        child/max(1,len(morph)-1)]+morph[child]+(morph[parent] if not root else [0.]*width)+between+before


def candidate_parents(child,predicates,boundaries=None):
    index=predicates.index(child)
    result=[None]+predicates[max(0,index-3):index]+predicates[index+1:index+4]
    if boundaries:
        def region(p):return next(i for i,b in enumerate(boundaries) if p<b)
        result=[p for p in result if p is None or region(p)==region(child)]
    return result


class StructureModel:
    def __init__(self,adapter,finite_model,parent_model,threshold=.5):
        self.adapter,self.finite_model,self.parent_model,self.threshold=adapter,finite_model,parent_model,threshold

    def infer(self,tokens,supplied_boundaries=None,*,any_finite=False):
        tokens=tuple(tokens);n=len(tokens)
        if supplied_boundaries is not None and (not supplied_boundaries or supplied_boundaries[-1]!=n or
                any(a>=b for a,b in zip((0,)+tuple(supplied_boundaries),supplied_boundaries))):
            raise ValueError('Supplied boundaries must partition the stream')
        lattice=[tuple(set(self.adapter.analyze(w))) for w in tokens]
        x=sentence_features(tokens,self.adapter)
        probabilities=self.finite_model.probability(x)
        candidates=[i for i,r in enumerate(lattice) if any(finite(a) for a in r)]
        predicates=[i for i in candidates if any_finite or probabilities[i]>=self.threshold]
        morph=[morph_features(r) for r in lattice]
        arc_candidates={};parents={};status='optimal'
        if predicates:
            options={c:candidate_parents(c,predicates,supplied_boundaries) for c in predicates}
            opt=z3.Optimize();opt.set(timeout=1000)
            var={c:z3.Int(f'head{c}') for c in predicates};depth={c:z3.Int(f'depth{c}') for c in predicates}
            terms=[]
            for c in predicates:
                rows=[]
                for p in options[c]:
                    score=float(self.parent_model.logits([parent_features(c,p,predicates,morph)])[0])
                    rows.append({'parent':p,'logit':score})
                    terms.append(z3.If(var[c]==(-1 if p is None else p),round(score*1000000),0))
                    if p is not None:opt.add(z3.Implies(var[c]==p,depth[c]>depth[p]))
                arc_candidates[c]=rows
                opt.add(z3.Or([var[c]==(-1 if p is None else p) for p in options[c]]),depth[c]>=0,depth[c]<len(predicates))
            objective=opt.maximize(z3.Sum(terms));answer=opt.check()
            if answer==z3.sat and opt.lower(objective)==opt.upper(objective):
                solution=opt.model()
                parents={c:(None if solution.eval(var[c]).as_long()==-1 else solution.eval(var[c]).as_long()) for c in predicates}
            else:
                status='unresolved';parents={c:None for c in predicates}
        # Partial clause membership: nearest predicted finite anchor within the
        # supplied region, if any. No token is silently removed.
        owners=[]
        for i in range(n):
            allowed=[p for p in predicates if supplied_boundaries is None or
                next(j for j,b in enumerate(supplied_boundaries) if p<b)==next(j for j,b in enumerate(supplied_boundaries) if i<b)]
            owners.append(min(allowed,key=lambda p:(abs(p-i),p)) if allowed else None)
        root_groups=[]
        for owner in owners:
            if owner is None or status!='optimal':root_groups.append(None);continue
            while parents[owner] is not None:owner=parents[owner]
            root_groups.append(owner)
        # A deliberately weak sentence-cut hypothesis from changes in forest root.
        inferred=[i for i in range(1,n) if root_groups[i] is not None and root_groups[i-1] is not None and root_groups[i]!=root_groups[i-1]]
        result={'status':status,'tokens':n,'predicates':predicates,'parents':parents,
            'predicate_probabilities':probabilities.tolist(),'finite_candidates':candidates,
            'reading_alternatives':[[{'pos':a.pos,'features':dict(a.features)} for a in sorted(r)] for r in lattice],
            'arc_candidates':arc_candidates,'token_anchors':owners,'root_groups':root_groups,
            'inferred_boundaries':inferred,'known_tokens':sum(bool(r) for r in lattice)}
        validate_structure(result)
        return result


def validate_structure(result):
    n=result['tokens'];pred=set(result['predicates']);parents={int(k):v for k,v in result['parents'].items()}
    assert len(result['token_anchors'])==len(result['root_groups'])==n
    assert set(parents)==pred and all(0<=p<n for p in pred)
    assert all(p is None or p in pred for p in result['token_anchors'])
    for child in pred:
        seen=set();p=child
        while p is not None:
            assert p not in seen;seen.add(p);p=parents[p]
        if result['status']=='optimal':
            rows=result['arc_candidates'].get(child,result['arc_candidates'].get(str(child),[]))
            assert parents[child] in [r['parent'] for r in rows]
    return True
