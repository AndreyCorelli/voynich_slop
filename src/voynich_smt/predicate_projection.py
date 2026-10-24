"""Versioned, annotation-only clause projection for structural benchmarks.

This module consumes UD annotations to construct references; it is not a parser
and must never provide gold clause complexes to ordinary decoder inference.
"""
from copy import deepcopy

VERSION='predicate-complex-v1'


def project_sentence(sentence,deprels):
    """Contract supported head/finite-auxiliary edges, preserving finite nodes.

    Unique direct finite aux/cop constructions are supported. Ambiguous or
    unsupported components are left uncontracted and explicitly recorded.
    """
    result=deepcopy(sentence);n=len(sentence['tokens']);heads=sentence['heads']
    if len(deprels)!=n:raise ValueError('One dependency relation per token required')
    finite=set(sentence['finite']);deps=[r.split(':')[0] for r in deprels]
    children={}
    issues=[]
    for p in sorted(finite):
        if sentence['upos'][p]!='AUX':continue
        h=heads[p]
        if h is None:continue
        if deps[p] not in {'aux','cop'}:
            if deps[p] not in {'root','conj'}:issues.append({'kind':'unsupported_auxiliary_relation','position':p,'head':h,'deprel':deprels[p]})
            continue
        children.setdefault(h,[]).append(p)
    complex_map={}
    for h,aux in sorted(children.items()):
        if len(aux)!=1:
            issues.append({'kind':'multiple_finite_auxiliaries','head':h,'positions':aux});continue
        p=aux[0]
        if h in finite:
            issues.append({'kind':'finite_head_with_finite_auxiliary','head':h,'positions':aux});continue
        if sentence['upos'][h] not in {'VERB','AUX'} and deps[p]!='cop':
            issues.append({'kind':'unsupported_auxiliary_head','head':h,'positions':aux});continue
        complex_map[h]=p
        if sentence['upos'][h]=='AUX':issues.append({'kind':'nonfinite_auxiliary_chain_partial','head':h,'positions':aux})
    def representative(node,exclude=None):
        """Nearest finite or contracted head on the upward dependency path."""
        seen=set()
        while node is not None:
            if node in seen:raise ValueError('Dependency cycle')
            seen.add(node)
            p=complex_map.get(node,node if node in finite else None)
            if p is not None and p!=exclude:return p
            node=heads[node]
        return None
    inverse={p:h for h,p in complex_map.items()};parents={};relations={}
    for p in sorted(finite):
        origin=inverse.get(p,p);cursor=heads[origin];path=[deps[origin]];seen=set()
        parent=None
        while cursor is not None:
            if cursor in seen:raise ValueError('Dependency cycle')
            seen.add(cursor)
            candidate=complex_map.get(cursor,cursor if cursor in finite else None)
            if candidate is not None and candidate!=p:parent=candidate;break
            path.append(deps[cursor]);cursor=heads[cursor]
        parents[p]=parent
        relations[p]='root' if parent is None else 'coordination' if 'conj' in path else 'subordination'
    markers={}
    for i,dep in enumerate(deps):
        h=heads[i]
        if dep in {'mark','cc'} and (h in finite or h in complex_map):
            markers[i]={'target':complex_map.get(h,h),'kind':'coordination' if dep=='cc' else 'subordination'}
        elif sentence['upos'][i] in {'PRON','DET'} and sentence['features'][i].get('PronType')=='Rel':
            target=representative(i)
            if target is not None:markers[i]={'target':target,'kind':'relative'}
    for start in finite:
        seen=set();node=start
        while node is not None:
            if node in seen:raise ValueError('Projected predicate cycle')
            seen.add(node);node=parents[node]
    result.update(parents=parents,relations=relations,markers=markers,anchors=[representative(i) for i in range(n)],
        reference_version=VERSION,predicate_complexes=[{'head':h,'representative':p,'deprel':deprels[p]} for h,p in sorted(complex_map.items())],
        projection_issues=issues)
    return result


def projection_changes(old,new):
    """Explicit sentence-local changes; no denominators are silently dropped."""
    def keyed(d):return {int(k):v for k,v in d.items()}
    def differences(key):
        a,b=keyed(old[key]),keyed(new[key])
        return [{'position':i,'old':a.get(i),'new':b.get(i)} for i in sorted(set(a)|set(b)) if a.get(i)!=b.get(i)]
    assert old['tokens']==new['tokens'] and old['finite']==new['finite']
    return {'sent_id':old['sent_id'],'parents':differences('parents'),'relations':differences('relations'),
        'markers':differences('markers'),'anchors':[{'position':i,'old':a,'new':b} for i,(a,b) in enumerate(zip(old['anchors'],new['anchors'])) if a!=b],
        'complexes':new['predicate_complexes'],'issues':new['projection_issues']}
