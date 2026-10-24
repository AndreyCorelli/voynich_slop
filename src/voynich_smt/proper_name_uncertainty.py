"""Conservative, fit-support-only expansion of proper-name number sets."""
from voynich_smt.construction_interventions import readings_key

POLICIES=('baseline','proper_unseen','proper_sparse5','proper_all')


def candidates(word,pos,original,model,policy):
    if policy not in POLICIES:
        raise ValueError(policy)
    support=sum(model['words'].get('number/'+readings_key(dict(word=word,pos=pos)),{}).values())
    widen=pos=='PROPN' and (policy=='proper_all' or policy=='proper_unseen' and support==0 or policy=='proper_sparse5' and support<5)
    result=set(original)
    if widen:
        for state in original:
            if state!='OTHER':
                _,person=state.split(':')
                result.update(number+':'+person for number in ('Sing','Plur'))
    return sorted(result)
