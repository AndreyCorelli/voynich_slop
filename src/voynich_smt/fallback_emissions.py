"""Normalized candidate emissions plus a fixed state-independent fallback.

A latent mixture channel gives a proper EM update, rather than clipping an
unconstrained update or applying an unnormalized candidate penalty.
"""
import numpy as np
from voynich_smt.latent_cipher_classes import forward_backward,word_counts
from voynich_smt.supported_emissions import supported_update


def mixture(component,frequency,epsilon):
    if not 0<=epsilon<1:raise ValueError('epsilon must be in [0,1)')
    return (1-epsilon)*np.asarray(component)+epsilon*np.asarray(frequency)[None,:]


def mixture_step(chain,component,sequences,prior,frequency,epsilon,sharing=False):
    emission=mixture(component,frequency,epsilon);_,gamma=forward_backward(chain,emission,sequences)
    counts=word_counts(sequences,gamma,len(frequency),chain['k'])
    responsibility=np.divide((1-epsilon)*component,emission,out=np.zeros_like(emission),where=emission>0)
    return supported_update(counts*responsibility,prior,sharing)


def fallback_posteriors(component,frequency,epsilon,sequences,gamma):
    e=mixture(component,frequency,epsilon);ratio=np.divide(epsilon*np.asarray(frequency)[None,:],e,out=np.zeros_like(e),where=e>0)
    return np.concatenate([np.sum(g*ratio[:,seq].T,axis=1) for seq,g in zip(sequences,gamma)])
