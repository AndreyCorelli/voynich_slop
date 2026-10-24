"""Fixed old emissions with a bounded, new-pairs-only repair channel."""
import numpy as np
from voynich_smt.latent_cipher_classes import forward_backward,word_counts


def repair_prior(frequency,new_pairs):
    mask=np.asarray(new_pairs,dtype=bool);values=mask*np.asarray(frequency)[None,:];totals=values.sum(axis=1,keepdims=True)
    return np.divide(values,totals,out=np.zeros_like(values),where=totals>0)


def anchored_emission(base,repair,budget):
    if not 0<=budget<1:raise ValueError('budget must be in [0,1)')
    base=np.asarray(base);repair=np.asarray(repair);active=repair.sum(axis=1)>0;mass=budget*active[:,None]
    return (1-mass)*base+mass*repair


def repair_log_prior(repair,prior,alpha=1.):
    return float(alpha*np.sum(np.asarray(prior)*np.log(np.maximum(repair,1e-300))))


def repair_update(counts,prior,alpha=1.):
    values=counts+alpha*prior;totals=values.sum(axis=1,keepdims=True)
    return np.divide(values,totals,out=np.zeros_like(values),where=totals>0)


def repair_step(chain,base,repair,sequences,prior,budget):
    emission=anchored_emission(base,repair,budget);_,gamma=forward_backward(chain,emission,sequences);counts=word_counts(sequences,gamma,emission.shape[1],chain['k'])
    mass=budget*(np.asarray(prior).sum(axis=1)>0)[:,None];responsibility=mass*repair/emission
    return repair_update(counts*responsibility,prior)
