"""Apply a context-level anchor swap to a scored prefix, allowing absent types."""
from voynich_smt.anchor_shadow_repair import swap_assignments


def repair_prefix(query,context,pair):
    if query!=context[:len(query)]:raise ValueError('Scored query must be the identical context prefix')
    if pair is None:return swap_assignments(query,None)
    # Validate global assignments even if an endpoint never occurs in the query.
    inventory=[t for s in context for t in s['tokens'] if t['id'] in pair]
    repaired=swap_assignments([dict(sent_id='inventory',tokens=inventory)],pair)
    assignments={t['id']:(t['anchor'],t['tag']) for t in repaired[0]['tokens']}
    return [dict(s,tokens=[dict(t,anchor=assignments[t['id']][0],tag=assignments[t['id']][1]) if t['id'] in assignments else dict(t) for t in s['tokens']]) for s in query]
