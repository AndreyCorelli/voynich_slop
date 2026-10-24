"""Provide class information without revealing a target's lexical anchor name."""


def inject(public, target_ids, assignments=None):
    assignments={} if assignments is None else assignments
    if not set(assignments)<=set(target_ids):raise ValueError('assignment outside target catalogue')
    if any(tag not in ('ADP','CCONJ') for tag in assignments.values()):raise ValueError('invalid inferred class')
    return [dict(s,tokens=[dict(t,anchor=None,tag=assignments.get(t['id'],'X')) if t['id'] in target_ids else dict(t) for t in s['tokens']]) for s in public]
