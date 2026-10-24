"""Two-stage explicit marker attachments and parent/marker interactions."""
import math
import numpy as np
from scipy.special import softmax

from .parent_ranking import typed_features
from .predicate_structure import morph_features

MARKER_KINDS=('coordination','subordination','relative')


def marker_features(tokens,position,target,predicates,morph,kinds):
    width=len(morph[0]);local=[]
    for delta in [-1,0,1]:
        i=position+delta;local+=morph[i] if 0<=i<len(tokens) else [0.]*width
    flags=[float(k in kinds) for k in MARKER_KINDS]
    if target is None:
        geometry=[1.,0.,0.,0.,0.,0.,0.];target_morph=[0.]*width
    else:
        distance=abs(position-target);lo,hi=sorted((position,target))
        nearest=min(predicates,key=lambda p:(abs(position-p),p)) if predicates else None
        geometry=[0.,float(target<position),float(target>position),math.log1p(distance),
            float(sum(lo<p<hi for p in predicates)),float(target==nearest),float(position==target)]
        target_morph=morph[target]
    features=[1.]+flags+local+geometry+target_morph
    # A dedicated NULL block allows marker-context evidence to distinguish
    # nominal/nonfinite uses from true finite-clause attachments.
    return features+([1.]+flags+local if target is None else [0.]*(1+len(flags)+len(local)))


def marker_choices(tokens,position,predicates,morph,kinds,boundaries=None):
    # A selected finite-predicate token cannot simultaneously act as a marker.
    allowed=[] if position in predicates else predicates
    if boundaries:
        def region(p):return next(i for i,b in enumerate(boundaries) if p<b)
        allowed=[p for p in allowed if region(p)==region(position)]
    return [{'target':p,'features':marker_features(tokens,position,p,predicates,morph,kinds)} for p in [None]+allowed]


class MarkerModel:
    def __init__(self,vocabulary,ranker):
        self.vocabulary={w:tuple(k) for w,k in vocabulary.items()};self.ranker=ranker

    def predict(self,tokens,predicates,adapter,boundaries=None):
        morph=[morph_features(adapter.analyze(w)) for w in tokens];attachments=[]
        for i,word in enumerate(tokens):
            if word not in self.vocabulary:continue
            kinds=self.vocabulary[word]
            choices=marker_choices(tokens,i,predicates,morph,kinds,boundaries)
            logits=self.ranker.logits([c['features'] for c in choices]);probabilities=softmax(logits)
            # Fixed tie-break: NULL first, then predicate position.
            chosen=int(np.argmax(logits))
            attachments.append({'position':i,'surface':word,'kinds':list(kinds),
                'target':choices[chosen]['target'],'alternatives':[{'target':c['target'],
                    'logit':float(s),'probability':float(p)} for c,s,p in zip(choices,logits,probabilities)]})
        return attachments


def attachment_features(tokens,child,parent,predicates,morph,relation,attachments,interactions):
    base=typed_features(tokens,child,parent,predicates,morph,relation)
    own=[m for m in attachments if m['target']==child]
    other=[m for m in attachments if parent is not None and m['target']==parent]
    flags=[float(any(k in m['kinds'] for m in own)) for k in MARKER_KINDS]
    parent_flags=[float(any(k in m['kinds'] for m in other)) for k in MARKER_KINDS]
    nearest=min(own,key=lambda m:abs(m['position']-child)) if own else None
    features=flags+[float(bool(own)),float(bool(nearest and nearest['position']<child)),
        float(bool(nearest and nearest['position']>child)),
        math.log1p(abs(nearest['position']-child)) if nearest else 0.]
    if interactions:
        between=lambda p:parent is not None and min(child,parent)<p<max(child,parent)
        features+=parent_flags+[
            float(any(between(m['position']) for m in own)),
            float(any(between(m['position']) and 'coordination' in m['kinds'] for m in own)),
            float(any(between(m['position']) and ('subordination' in m['kinds'] or 'relative' in m['kinds']) for m in own)),
            float(any(between(m['position']) and m['target'] not in (None,child,parent) for m in attachments)),
            float(parent is not None and parent>child and bool(flags[1] or flags[2])),
            float(parent is not None and parent<child and bool(flags[0])),
            float(bool(own) and bool(other)),
            float(parent is not None and morph[child][11] and morph[parent][11])]
    # Relation-specific interaction blocks permit learned ROOT/coord/sub effects.
    from .parent_ranking import RELATIONS
    return base+sum([features if r==relation else [0.]*len(features) for r in RELATIONS],[])


class AttachmentRanker:
    """Adapter for the existing typed-forest solver's feature hook."""
    def __init__(self,ranker):self.ranker=ranker
    def logits(self,features):return self.ranker.logits(features)


def infer_attached_links(tokens,predicates,adapter,ranker,marker_model,*,interactions=False,boundaries=None,timeout_ms=2000):
    import z3
    from .parent_ranking import choices
    from .predicate_structure import validate_structure
    tokens=tuple(tokens);predicates=list(predicates);n=len(tokens)
    if predicates!=sorted(set(predicates)) or any(p<0 or p>=n for p in predicates):raise ValueError('Invalid predicate positions')
    if boundaries is not None and (not boundaries or boundaries[-1]!=n or any(a>=b for a,b in zip((0,)+tuple(boundaries),boundaries))):
        raise ValueError('Boundaries must partition every token')
    attachments=marker_model.predict(tokens,predicates,adapter,boundaries)
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    options={};parents={};relations={};status='optimal';score=0
    if predicates:
        opt=z3.Optimize();opt.set(timeout=timeout_ms)
        selected={p:z3.Int(f'arc{p}') for p in predicates};depth={p:z3.Int(f'd{p}') for p in predicates};terms=[]
        for child in predicates:
            rows=choices(tokens,child,predicates,morph,typed=True,boundaries=boundaries,radius=None)
            features=[attachment_features(tokens,child,r['parent'],predicates,morph,r['relation'],attachments,interactions) for r in rows]
            values=ranker.logits(features);normalizer=float(np.logaddexp.reduce(values));options[child]=[]
            for i,(row,value) in enumerate(zip(rows,values)):
                options[child].append({'parent':row['parent'],'relation':row['relation'],'logit':float(value),
                    'conditional_probability':float(math.exp(value-normalizer))})
                terms.append(z3.If(selected[child]==i,round(float(value)*1000000),0))
                if row['parent'] is not None:opt.add(z3.Implies(selected[child]==i,depth[child]>depth[row['parent']]))
            opt.add(selected[child]>=0,selected[child]<len(rows),depth[child]>=0,depth[child]<len(predicates))
        objective=opt.maximize(z3.Sum(terms));answer=opt.check()
        if answer==z3.sat and opt.lower(objective)==opt.upper(objective):
            model=opt.model()
            for child in predicates:
                row=options[child][model.eval(selected[child]).as_long()];parents[child]=row['parent'];relations[child]=row['relation'];score+=round(row['logit']*1000000)
        else:status='unresolved';score=None;parents={p:None for p in predicates};relations={p:None for p in predicates}
    def region(i):return next(j for j,b in enumerate(boundaries) if i<b)
    owners=[]
    for i in range(n):
        allowed=[p for p in predicates if boundaries is None or region(i)==region(p)]
        owners.append(min(allowed,key=lambda p:(abs(p-i),p)) if allowed else None)
    roots=[]
    for p in owners:
        if p is None or status!='optimal':roots.append(None);continue
        while parents[p] is not None:p=parents[p]
        roots.append(p)
    result={'tokens':n,'status':status,'predicates':predicates,'parents':parents,'relations':relations,'arc_candidates':options,
        'token_anchors':owners,'root_groups':roots,'forest_score_integer':score,'known_tokens':sum(bool(adapter.analyze(w)) for w in tokens),
        'inferred_boundaries':[i for i in range(1,n) if roots[i] is not None and roots[i-1] is not None and roots[i]!=roots[i-1]],
        'marker_attachments':attachments}
    validate_structure(result);validate_markers(result,boundaries)
    return result


def validate_markers(prediction,boundaries=None):
    positions=set();predicates=set(prediction['predicates'])
    for marker in prediction['marker_attachments']:
        i=marker['position'];assert i not in positions;positions.add(i)
        assert 0<=i<prediction['tokens'] and (marker['target'] is None or marker['target'] in predicates)
        if i in predicates:assert marker['target'] is None
        assert len({r['target'] for r in marker['alternatives']})==len(marker['alternatives'])
        assert math.isclose(sum(r['probability'] for r in marker['alternatives']),1,abs_tol=1e-9)
        assert marker['target'] in [r['target'] for r in marker['alternatives']]
        if boundaries and marker['target'] is not None:
            region=lambda p:next(j for j,b in enumerate(boundaries) if p<b)
            assert region(i)==region(marker['target'])
    return True
