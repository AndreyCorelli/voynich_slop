"""Frozen test-side replication of the source-calibration context-length probe."""
import hashlib


def test_blocks(ids):
    """Preserve one 400-sentence census at 100/200/400; add larger endpoints."""
    if len(ids)<700:raise ValueError('Need at least 700 unique sentences')
    if len(set(ids))!=len(ids):raise ValueError('Duplicate sentence IDs')
    ordered=sorted(ids,key=lambda sid:hashlib.sha256(('cal98|'+sid).encode()).hexdigest());result={}
    for n in (100,200,400):
        for i in range(400//n):result[str(n)+'-'+str(i)]=ordered[n*i:n*(i+1)]
    result['700-0']=ordered[:700];result[str(len(ids))+'-0']=list(ids)
    return result
