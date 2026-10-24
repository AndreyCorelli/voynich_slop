"""Experimental pairwise scorer; scores are preferences, never probabilities of truth."""
from collections import Counter
from functools import lru_cache
import hashlib
import math

import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit


@lru_cache(maxsize=262144)
def bucket(feature, dimension):
    raw = hashlib.blake2b(feature.encode(), digest_size=8).digest()
    value = int.from_bytes(raw, 'little')
    return value % dimension, 1 if value >> 63 else -1


def features(words, *, context=True, dimension=65536):
    """Length-normalized lexical and suffix contexts; no sentence or cipher IDs."""
    if not words:
        raise ValueError('Empty reconstruction')
    counts = Counter('w:' + w for w in words)
    if context:
        for distance in (1, 2, 4, 8):
            for a, b in zip(words, words[distance:]):
                if distance <= 2:
                    counts[f'p{distance}:{a}|{b}'] += 1
                for size in (2, 3):
                    counts[f's{size}d{distance}:{a[-size:]}|{b[-size:]}'] += 1
        for a,b,c in zip(words, words[1:], words[2:]):
            counts[f't:{a}|{b}|{c}'] += 1
    values = Counter()
    for name, count in counts.items():
        index, sign = bucket(name, dimension)
        values[index] += sign * count / math.sqrt(len(words))
    return sparse.csr_matrix((list(values.values()), ([0]*len(values), list(values))), shape=(1,dimension))


def fit_preferences(differences, *, regularization=1., maxiter=200):
    """Fit positive-minus-negative pairs, with fixed L2 regularization."""
    matrix = sparse.vstack(differences).tocsr()
    def objective(weights):
        margins = matrix @ weights
        loss = np.logaddexp(0, -margins).sum() + regularization * (weights @ weights) / 2
        gradient = -(matrix.T @ expit(-margins)) + regularization * weights
        return float(loss), np.asarray(gradient)
    result = minimize(objective, np.zeros(matrix.shape[1]), jac=True, method='L-BFGS-B',
                      options={'maxiter':maxiter, 'gtol':1e-5})
    if not result.success:
        raise RuntimeError('Scorer optimization failed: '+str(result.message))
    return result.x, {'pairs':matrix.shape[0], 'iterations':int(result.nit), 'loss':float(result.fun)}


def score(words, weights, *, context=True, window=256):
    if not words:
        raise ValueError('Empty reconstruction')
    # Disjoint windows: same boundaries for every reconstruction of this cipher.
    total = 0.
    for start in range(0,len(words),window):
        part = words[start:start+window]
        total += len(part) * float((features(part, context=context, dimension=len(weights)) @ weights)[0])
    return total/len(words)
