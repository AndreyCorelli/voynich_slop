"""A complete, source-inventory-defined bank of previously unused class swaps."""
from itertools import product


def remaining_bank(anchors,previous):
    used={frozenset(m) for m in previous.values() if m and len({anchors[w] for w in m})>1}
    adps=sorted(w for w,p in anchors.items() if p=='ADP');conjs=sorted(w for w,p in anchors.items() if p=='CCONJ')
    result={'correct':{}}
    for a,c in product(adps,conjs):
        if frozenset((a,c)) not in used:result['swap_'+a+'__'+c]={a:c,c:a}
    result['same_adp']=previous['same_adp'];result['same_conjunction']=previous['same_conjunction']
    return result
