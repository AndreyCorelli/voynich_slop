"""Corrected oracle constraints: coordination never narrows unknown morphology.

The original frozen iteration-64 implementation remains preserved.
"""
from collections import defaultdict
import numpy as np
from voynich_smt.copular_head_oracle import clause_anchor,DEPENDENTS
from voynich_smt.typed_predicate_units import select

# All variants are fixed diagnostics, not calibration choices.
ARMS={
    'baseline':{},
    'shared':dict(shared=True),
    'assigned_global':dict(roles='assigned_global'),
    'assigned_clause':dict(roles='assigned_clause'),
    'gold_role_clause':dict(roles='gold_clause'),
    'joint':dict(shared=True,roles='assigned_clause'),
    'oracle_joint':dict(shared=True,roles='gold_clause'),
    'phrase_clause':dict(unary=True),
    'phrase_clause_joint':dict(unary=True,shared=True,roles='assigned_clause'),
    'sv_strict':dict(sv='strict'),
    'sv_coord':dict(sv='coord'),
    'adjective_strict':dict(adjective='strict'),
    'adjective_coord':dict(adjective='coord'),
    'oracle_full':dict(unary=True,shared=True,roles='gold_clause',sv='coord',adjective='coord'),
}


def coordination(tokens,index):
    adjacency=defaultdict(set)
    for i,t in enumerate(tokens):
        if t['rel'].split(':')[0]=='conj' and t['head'] is not None:
            adjacency[i].add(t['head']);adjacency[t['head']].add(i)
    seen={index};pending=[index]
    while pending:
        for j in adjacency[pending.pop()]-seen:seen.add(j);pending.append(j)
    return seen


def context(tokens):
    return dict(anchors=[clause_anchor(tokens,i) for i in range(len(tokens))],subjects={i for i,t in enumerate(tokens) if t['pos'] in ('NOUN','PROPN','PRON') and t['rel'].split(':')[0]=='nsubj'},coordination=[coordination(tokens,i) for i in range(len(tokens))])


def values(token,feature):
    value=token['features'].get(feature,'')
    if feature=='Person' and not value and token['pos'] in ('NOUN','PROPN'):return {'3'}
    return set(value.split(',')) if value else set()


def compatible(a,b):
    # Unknown morphology imposes no restriction.
    return not a or not b or bool(a&b)


def subject_values(tokens,subject,feature,ctx,permissive):
    result=values(tokens[subject],feature)
    if not result:return set()
    if permissive and len(ctx['coordination'][subject])>1:
        if feature=='Number':result=result|{'Plur'}
        elif feature=='Gender':return set()
        elif feature=='Person':
            people=set().union(*(values(tokens[j],feature) for j in ctx['coordination'][subject]))
            if people:result=result|{min(people)}
    return result


def reasons(frame,option,tokens,ctx,config,assigned):
    h,role=option;s=frame['subject'];v=frame['carrier'];result=[]
    kind=config.get('roles')
    if kind:
        subjects=ctx['subjects'] if kind=='gold_clause' else assigned
        if h in subjects and h!=s:
            if kind=='assigned_global':result.append('role_reuse')
            elif ctx['anchors'][h] is not None and ctx['anchors'][v] is not None and ctx['anchors'][h]==ctx['anchors'][v]:result.append('role_reuse')
    if config.get('unary'):
        if tokens[h]['rel'].split(':')[0] in DEPENDENTS:result.append('phrase')
        a,b=ctx['anchors'][h],ctx['anchors'][v]
        if a is not None and b is not None and a!=b:result.append('clause')
    if config.get('sv'):
        for feature in ('Number','Person'):
            if not compatible(subject_values(tokens,s,feature,ctx,config['sv']=='coord'),values(tokens[v],feature)):result.append('sv_'+feature)
    if config.get('adjective') and role=='cop' and tokens[h]['pos']=='ADJ':
        for feature in ('Number','Gender','Case'):
            if not compatible(subject_values(tokens,s,feature,ctx,config['adjective']=='coord'),values(tokens[h],feature)):result.append('adjective_'+feature)
    return result


def allowed_indices(frames,tokens,ctx,config):
    assigned={r['subject'] for r in frames}
    return {r['subject']:[j for j,option in enumerate(r['options']) if not reasons(r,option,tokens,ctx,config,assigned)] for r in frames}


def decode(frames,allowed,shared=False):
    """Exact score maximization for mandatory frames, optionally sharing a head/type.

    There is no new NONE score. Empty domains or tied maxima abstain; for shared
    groups an empty intersection/tie abstains for the whole group. No gold unit
    is read. With shared=False this is the frozen independent decision rule.
    """
    output={};stats=dict(groups=0,multiple_frame_groups=0,empty_groups=0,tied_groups=0)
    groups=defaultdict(list)
    for r in frames:groups[r['carrier'] if shared else r['subject']].append(r)
    for group in groups.values():
        stats['groups']+=1;stats['multiple_frame_groups']+=len(group)>1
        domains=[{r['options'][j]:j for j in allowed[r['subject']]} for r in group]
        common=set(domains[0]).intersection(*domains[1:])
        if not common:
            stats['empty_groups']+=1
            for r in group:output[r['subject']]=None
            continue
        options=sorted(common);scores=np.asarray([sum(r['scores'][d[option]] for r,d in zip(group,domains)) for option in options])
        winner=select(scores,options,group[0]['subject'],group[0]['carrier'])
        if winner is None:stats['tied_groups']+=1
        for r in group:output[r['subject']]=[r['subject'],winner[1],r['carrier'],winner[3]] if winner else None
    return output,stats


def shared_gold_conflicts(frames):
    """Identify gold frames incompatible with others under shared-head equality."""
    groups=defaultdict(list)
    for r in frames:groups[r['carrier']].append(r)
    conflicts=[]
    for group in groups.values():
        choices={tuple(r['gold'][1::2]) for r in group}
        if len(choices)>1:
            conflicts.append(dict(carrier=group[0]['carrier'],subjects=[r['subject'] for r in group],reason='different_gold_heads_or_types'))
    return conflicts
