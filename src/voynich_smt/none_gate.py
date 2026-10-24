"""Calibrate a unique best edge against NONE without changing attachment scores."""
import numpy as np
from voynich_smt.multi_link_attachment import edge_metrics

CUTOFFS=(-1000000.,-8.,-6.,-4.,-3.,-2.,-1.5,-1.,-.5,0.,.5,1.,1.5,2.,3.,4.,6.,8.,1000000.)


def best_edge(frame,model):
    if not frame['predicates']:return dict(predicate=None,margin=None)
    scores=np.asarray(frame['vectors'][model['arm']])@np.asarray(model['weights'])
    assert np.isfinite(scores).all() and np.abs(scores).max()<1000000
    maximum=float(scores.max());winners=np.flatnonzero(np.isclose(scores,maximum,rtol=0,atol=1e-10))
    return dict(predicate=frame['predicates'][int(winners[0])] if len(winners)==1 else None,margin=maximum)


def accept(proposal,cutoff):
    return proposal['predicate'] is not None and proposal['margin']>cutoff+1e-10


def calibrate(frames,proposals,mode):
    if mode not in ('map','free'):raise ValueError(mode)
    assert len(frames)==len(proposals)
    gold={(r['sid'],r['subject'],r['gold']) for r in frames if r['gold'] is not None};records=[]
    for cutoff in CUTOFFS:
        if mode=='map' and cutoff<0:continue
        predicted={(r['sid'],r['subject'],p['predicate']) for r,p in zip(frames,proposals) if accept(p,cutoff)}
        records.append(dict(cutoff=cutoff,**edge_metrics(gold,predicted)))
    f1=max(records,key=lambda r:(r['f1'],-r['predicted']))
    eligible=[r for r in records if r['predicted']>=20 and r['precision'] is not None and r['precision']>=.9]
    high=max(eligible,key=lambda r:(r['tp'],-r['fp'])) if eligible else dict(cutoff=1000000.,predicted=0,note='No calibration cutoff achieved precision90 with20 predictions')
    return dict(f1=f1,precision90=high,grid=records)
