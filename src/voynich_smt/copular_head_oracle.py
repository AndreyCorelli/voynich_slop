"""Gold morphology/parse diagnostics for copular heads; not inference features."""
from itertools import combinations

CUES=('case','adp','phrase','clause')
DEPENDENTS=frozenset(('amod','det','nmod','appos','flat','fixed','compound','case'))
CLAUSAL=frozenset(('root','ccomp','xcomp','advcl','acl','parataxis','csubj'))
MASKS={('none' if not selected else '+'.join(selected)):selected for n in range(len(CUES)+1) for selected in combinations(CUES,n)}


def case_allowed(token):
    case=token['features'].get('Case','')
    return not case or 'Nom' in case.split(',')


def in_adp_phrase(tokens,index):
    seen=set()
    while index is not None and index not in seen:
        seen.add(index)
        if any(t['head']==index and t['rel'].split(':')[0]=='case' and t['pos']=='ADP' for t in tokens):return True
        if tokens[index]['rel'].split(':')[0] not in DEPENDENTS:break
        index=tokens[index]['head']
    return False


def clause_anchor(tokens,index):
    seen=set()
    while index is not None and index not in seen:
        seen.add(index);t=tokens[index];rel=t['rel'].split(':')[0]
        if rel in CLAUSAL or t['head'] is None:return index
        if rel=='conj' and (t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin' or any(u['head']==index and u['rel'].split(':')[0] in ('cop','aux') and u['features'].get('VerbForm')=='Fin' for u in tokens)):return index
        index=t['head']
    return None


def flags(tokens,head,carrier):
    h=clause_anchor(tokens,head);v=clause_anchor(tokens,carrier)
    return dict(case=case_allowed(tokens[head]),adp=not in_adp_phrase(tokens,head),phrase=tokens[head]['rel'].split(':')[0] not in DEPENDENTS,clause=h is None or v is None or h==v)


def indices(options,head_flags,mask,mode):
    if mask not in MASKS or mode not in ('free_type','cop_type'):raise ValueError((mask,mode))
    # Apply the head masks to every candidate role consistently. Source finite
    # carriers generally pass morphology/phrase masks in their direct option.
    return [j for j,(head,role) in enumerate(options) if (mode=='free_type' or role=='cop') and all(head_flags[head][cue] for cue in MASKS[mask])]
