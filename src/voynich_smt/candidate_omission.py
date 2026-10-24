"""Remove one repair candidate without altering cached context evidence."""
import numpy as np
from voynich_smt.pair_uncertainty import summarize


def omit(record,draws,opaque):
    indices=[j for j,p in enumerate(record['pairs']) if opaque not in p['pair']]
    pairs=[record['pairs'][j] for j in indices]
    # Ranking, gap and winning frequency must be recomputed after removal.
    features=summarize(pairs,np.asarray(draws)[:,indices])
    reference=dict(record['reference'])
    reference['supported']=any(p['supported'] and p['pair']==reference['pair'] for p in pairs)
    return dict(features=features,pairs=pairs,source_pair_indices=indices,reference=reference)
