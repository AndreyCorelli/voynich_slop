"""A fixed contextual classifier; opaque IDs only group and mask occurrences."""
import numpy as np
from voynich_smt import anchor_grammar as ag
from voynich_smt.masked_anchor_class import masked_type_features,CLASSES
from voynich_smt.anchor_class_audit import disagreement

ARMS=('context','prior','shuffle0','shuffle1','shuffle2')


def predict_records(public,candidates,models):
    result={arm:[] for arm in ARMS}
    for opaque_id,proposed in candidates.items():
        rows=masked_type_features(public,set(),opaque_id);xx=[r['features'] for r in rows];n=len(rows);sentences=len({r['sid'] for r in rows})
        for arm in ARMS:
            probability=models['prior'] if arm=='prior' else ag.predict(xx,models[arm]).mean(axis=0).tolist()
            margin,mass=disagreement(probability,list(CLASSES),proposed)
            result[arm].append(dict(anchor_id=opaque_id,proposed=proposed,n=n,sentences=sentences,mean=probability,disagreement=margin,class_mass=mass,supported=n>=5 and sentences>=3))
    return result
