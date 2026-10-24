"""Annotation-dependent diagnostic masks. Never use as restoration inference."""
from copy import deepcopy

MASKS=('baseline','case','finite','case_finite','subject_role','subject_role_finite','exact_edge','exact_edge_no_gate')


def state(value,required):
    if not value:return 'unknown'
    values=value.split(',')
    if len(values)>1:return 'ambiguous_permitted' if required in values else 'ambiguous_excluded'
    return 'permitted' if value==required else 'excluded'


def flags(tokens,subject,predicate,gold):
    s=tokens[subject];v=tokens[predicate]
    case=state(s['features'].get('Case',''),'Nom');finite=state(v['features'].get('VerbForm',''),'Fin')
    return dict(case_state=case,finite_state=finite,case_allowed=case not in ('excluded','ambiguous_excluded'),finite_allowed=finite not in ('excluded','ambiguous_excluded'),subject_role=gold is not None,exact_edge=gold is not None and predicate==gold)


def allows(mask,tokens,subject,predicate,gold):
    if mask not in MASKS:raise ValueError(mask)
    f=flags(tokens,subject,predicate,gold)
    if mask=='baseline':return True
    if mask=='case':return f['case_allowed']
    if mask=='finite':return f['finite_allowed']
    if mask=='case_finite':return f['case_allowed'] and f['finite_allowed']
    if mask=='subject_role':return f['subject_role']
    if mask=='subject_role_finite':return f['subject_role'] and f['finite_allowed']
    return f['exact_edge']


def masked_frame(frame,tokens,mask):
    kept=[j for j,v in enumerate(frame['predicates']) if allows(mask,tokens,frame['subject'],v,frame['gold'])]
    result=deepcopy(frame);result['predicates']=[frame['predicates'][j] for j in kept]
    result['vectors']={arm:[values[j] for j in kept] for arm,values in frame['vectors'].items()}
    return result


def false_positive_class(tokens,subject,predicate,gold):
    f=flags(tokens,subject,predicate,gold)
    if gold is not None:subject_class='finite_subject_wrong_attachment'
    elif f['case_state']=='permitted':subject_class='nominative_not_finite_subject'
    elif f['case_state']=='excluded':subject_class='non_nominative_not_finite_subject'
    else:subject_class='unknown_or_ambiguous_case_not_finite_subject'
    predicate_class={'permitted':'finite','excluded':'nonfinite'}.get(f['finite_state'],'unknown_or_ambiguous')
    return subject_class+'/'+predicate_class
