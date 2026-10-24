"""Unnormalized role log probabilities for a frozen-score ablation."""
import math
import numpy as np
from voynich_smt.dependency_role_proxy import CLASSES


def evidence(carrier,options,probabilities_by_token):
    head=[];type_score=[]
    for h,role in options:
        head.append(math.log(max(1e-6,1-probabilities_by_token[h,0])))
        j=CLASSES.index('other' if role=='direct' else role)
        type_score.append(math.log(max(1e-6,probabilities_by_token[carrier,j])))
    return np.asarray(head),np.asarray(type_score)
