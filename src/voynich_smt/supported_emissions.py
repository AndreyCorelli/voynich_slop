"""Emission EM under an explicitly supplied word/class support mask.

The mask may be privileged in diagnostics. No labels enter updates once supplied.
Priors are conditioned separately within each state's permitted support.
"""
import numpy as np
from voynich_smt.latent_cipher_classes import forward_backward,word_counts,prior_data


def supported_prior(sequences,endings,support):
    support=np.asarray(support,dtype=bool);q,_,_=prior_data(sequences,endings);endings=np.asarray(endings);groups=int(endings.max())+1
    if support.shape[1]!=len(endings) or not np.all(support.any(axis=0)) or not np.all(support.any(axis=1)):raise ValueError('Every word and state requires support')
    word=q[None,:]*support;word/=word.sum(axis=1,keepdims=True)
    end=np.asarray([np.bincount(endings,weights=row,minlength=groups) for row in word]);within=word/np.maximum(end[:,endings],1e-300)
    return dict(word=word,end=end,within=within,support=support,endings=endings)


def supported_update(counts,prior,sharing=False,alpha_word=.2,alpha_end=1.):
    counts=np.asarray(counts);mask=prior['support'];endings=prior['endings']
    if np.any(counts[~mask]>1e-10):raise ValueError('Counts outside support')
    counts=np.where(mask,counts,0.)
    if not sharing:
        values=counts+alpha_end*prior['word'];return values/values.sum(axis=1,keepdims=True)
    ec=np.asarray([np.bincount(endings,weights=row,minlength=prior['end'].shape[1]) for row in counts])
    ep=(ec+alpha_end*prior['end'])/(ec.sum(axis=1,keepdims=True)+alpha_end)
    conditional=(counts+alpha_word*prior['within'])/(ec[:,endings]+alpha_word)
    return ep[:,endings]*conditional


def supported_log_prior(emissions,prior,sharing=False,alpha_word=.2,alpha_end=1.):
    e=np.asarray(emissions);safe=np.maximum(e,1e-300)
    if not sharing:return float(alpha_end*np.sum(prior['word']*np.log(safe)))
    endings=prior['endings'];groups=np.asarray([np.bincount(endings,weights=row,minlength=prior['end'].shape[1]) for row in e])
    conditional=e/np.maximum(groups[:,endings],1e-300)
    return float(alpha_end*np.sum(prior['end']*np.log(np.maximum(groups,1e-300)))+alpha_word*np.sum(prior['within']*np.log(np.maximum(conditional,1e-300))))


def supported_step(chain,emissions,sequences,prior,sharing=False):
    _,gamma=forward_backward(chain,emissions,sequences)
    counts=word_counts(sequences,gamma,len(prior['endings']),chain['k'])
    return supported_update(counts,prior,sharing)
