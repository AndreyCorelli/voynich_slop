"""Restrict a frozen joint-pair bootstrap to a supplied candidate-ID set."""
import numpy as np
from voynich_smt.pair_uncertainty import summarize


def restrict(record,draws,allowed):
    indices=[j for j,p in enumerate(record['pairs']) if set(p['pair'])<=set(allowed)]
    pairs=[record['pairs'][j] for j in indices]
    restricted=np.asarray(draws)[:,indices]
    return dict(case=record['case'],block=record['block'],regime=record['regime'],pairs=pairs,source_pair_indices=indices,features=summarize(pairs,restricted),reference=dict(record['reference']))
