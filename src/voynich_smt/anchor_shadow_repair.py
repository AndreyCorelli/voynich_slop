"""Apply a blind pair recommendation to public assignments, preserving type IDs."""


def swap_assignments(public,pair):
    if pair is None:return [dict(s,tokens=[dict(t) for t in s['tokens']]) for s in public]
    if len(pair)!=2 or len(set(pair))!=2:raise ValueError('Expected two distinct opaque type IDs')
    assignments={}
    for sentence in public:
        for token in sentence['tokens']:
            if token['id'] in pair:
                value=(token['anchor'],token['tag'])
                if token['id'] in assignments and assignments[token['id']]!=value:raise ValueError('Inconsistent type assignment')
                assignments[token['id']]=value
    if set(assignments)!=set(pair):raise ValueError('Recommended type absent')
    if {value[1] for value in assignments.values()}!={'ADP','CCONJ'}:raise ValueError('Expected proposed ADP/CCONJ pair')
    left,right=pair;replacement={left:assignments[right],right:assignments[left]};result=[]
    for sentence in public:
        tokens=[]
        for token in sentence['tokens']:
            changed=dict(token)
            if token['id'] in replacement:changed['anchor'],changed['tag']=replacement[token['id']]
            tokens.append(changed)
        result.append(dict(sentence,tokens=tokens))
    return result
