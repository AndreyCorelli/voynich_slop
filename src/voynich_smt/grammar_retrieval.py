"""Analysis-set projections for controlled morphological candidate constraints."""

def project(profile,fields):
    """Preserve analyses and their correlations; discard lexical identity."""
    if fields is None:return frozenset(profile)
    return frozenset((pos,tuple((k,v) for k,v in features if k in fields)) for pos,enclitic,features in profile)

def admits(candidate,reference,fields):
    # Empty reference is unknown, not evidence that every candidate is wrong.
    if not reference:return True
    return bool(project(candidate,fields)&project(reference,fields))
