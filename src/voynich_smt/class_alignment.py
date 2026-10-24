"""Exact small-class alignment from source distributions; no target labels.

Bijective class relabeling and small many-to-one proxy maps are enumerated in
full. Ties produce set-valued class assignments rather than index tie-breaks.
"""
from functools import lru_cache
from itertools import permutations,product
import numpy as np

COARSE=('nominal','verbal','function_other')
FINE=('noun','adjective','pronoun_determiner','verb','adverb','adposition','conjunction','other')


def tag_class(upos,family):
    if family=='coarse':return 0 if upos in ('NOUN','PROPN','PRON','DET','ADJ','NUM') else 1 if upos in ('VERB','AUX') else 2
    return 0 if upos in ('NOUN','PROPN') else 1 if upos=='ADJ' else 2 if upos in ('PRON','DET') else 3 if upos in ('VERB','AUX') else 4 if upos=='ADV' else 5 if upos=='ADP' else 6 if upos in ('CCONJ','SCONJ') else 7


def statistics(sequences,k):
    u=np.zeros(k);t=np.zeros((k,k));start=np.zeros(k);end=np.zeros(k)
    for seq in sequences:
        if not seq:continue
        np.add.at(u,np.asarray(seq,dtype=int),1);start[seq[0]]+=1;end[seq[-1]]+=1
        for a,b in zip(seq,seq[1:]):t[a,b]+=1
    return dict(unigram=u,transition=t,start=start,end=end)


def fit_source(sequences,k,alpha=.5):
    counts=statistics(sequences,k)
    norm=lambda x:(x+alpha)/(x.sum()+alpha*x.size)
    return dict(unigram=norm(counts['unigram']).tolist(),joint=norm(counts['transition']).tolist(),
        transition=((counts['transition']+alpha)/(counts['transition'].sum(axis=1,keepdims=True)+alpha*k)).tolist(),
        start=norm(counts['start']).tolist(),end=norm(counts['end']).tolist(),k=k,alpha=alpha)


@lru_cache(None)
def maps(observed,k,bijective):
    if bijective:
        if observed!=k:raise ValueError('A bijection requires equal inventory sizes')
        return np.asarray(list(permutations(range(k))),dtype=np.int16)
    return np.asarray(list(product(range(k),repeat=observed)),dtype=np.int16)


def encode(sequences,k,key,noise=0.,noise_seed=2501):
    rng=np.random.default_rng(noise_seed);corrupted=[]
    for seq in sequences:
        seq=np.asarray(seq,dtype=int).copy();positions=rng.random(len(seq))<noise
        shifts=rng.integers(1,k,size=len(seq));seq[positions]=(seq[positions]+shifts[positions])%k;corrupted.append(seq.tolist())
    permutation=np.random.default_rng(key).permutation(k)
    anonymous=[[int(permutation[c]) for c in seq] for seq in corrupted]
    inverse=np.argsort(permutation).tolist()
    return anonymous,inverse


def shuffle_context(sequences,seed=2502):
    rng=np.random.default_rng(seed);result=[]
    for seq in sequences:
        values=list(seq);rng.shuffle(values);result.append(values)
    return result


def js_rows(p,q):
    p=np.asarray(p);q=np.asarray(q);m=(p+q)/2
    # Inputs are smoothed probability vectors, so logarithms stay finite.
    return .5*np.sum(p*np.log(p/m)+q*np.log(q/m),axis=1)


def score_maps(source,sequences,observed,bijective):
    k=source['k'];mapping=maps(observed,k,bijective);counts=statistics(sequences,observed);logs={name:np.log(np.asarray(source[name])) for name in ('unigram','transition','start','end')}
    if bijective:
        unigram=np.sum(counts['unigram'][None,:]*logs['unigram'][mapping],axis=1)
        transitions=np.zeros(len(mapping))
        for a in range(observed):
            for b in range(observed):
                if counts['transition'][a,b]:transitions+=counts['transition'][a,b]*logs['transition'][mapping[:,a],mapping[:,b]]
        boundary=np.sum(counts['start'][None,:]*logs['start'][mapping]+counts['end'][None,:]*logs['end'][mapping],axis=1)
        total=max(1,float(counts['unigram'].sum()));events=max(1,float(counts['transition'].sum()+counts['start'].sum()+counts['end'].sum()))
        return mapping,dict(frequency=unigram/total,markov=(transitions+boundary)/events,
            joint=.5*unigram/total+.5*(transitions+boundary)/events),dict(unigram=unigram/total,transitions=transitions/events,boundary=boundary/events)
    # Small many-to-one proxy: likelihood alone can collapse all groups onto a
    # frequent state. Compare aggregate distributions instead, with a separately
    # reported ordinary Markov control.
    onehot=np.eye(k)[mapping];u=np.einsum('ami,m->ai',onehot,counts['unigram']);t=np.einsum('ami,mn,anj->aij',onehot,counts['transition'],onehot,optimize=True)
    starts=np.einsum('ami,m->ai',onehot,counts['start']);ends=np.einsum('ami,m->ai',onehot,counts['end'])
    smooth=lambda x:(x+.5)/(x.sum(axis=1,keepdims=True)+.5*x.shape[1])
    frequency=-js_rows(smooth(u),np.asarray(source['unigram'])[None,:])
    transition=-js_rows(smooth(t.reshape(len(mapping),-1)),np.asarray(source['joint']).reshape(1,-1))
    boundary=-.25*(js_rows(smooth(starts),np.asarray(source['start'])[None,:])+js_rows(smooth(ends),np.asarray(source['end'])[None,:]))
    markov=(np.sum(t*np.asarray(logs['transition'])[None,:,:],axis=(1,2))+np.sum(starts*logs['start']+ends*logs['end'],axis=1))/max(1,float(counts['unigram'].sum()))
    return mapping,dict(frequency_fit=frequency,joint_fit=frequency+transition+boundary,markov=markov),dict(unigram=frequency,transitions=transition,boundary=boundary)


def align(source,sequences,observed,bijective=True,tolerance=1e-10):
    mapping,scores,parts=score_maps(source,sequences,observed,bijective);result={}
    used=statistics(sequences,observed)['unigram']>0
    for name,values in scores.items():
        best=float(values.max());optimal=np.flatnonzero(values>=best-tolerance);options=[sorted(set(int(x) for x in mapping[optimal,j])) for j in range(observed)]
        assignment=[v[0] if len(v)==1 else None for v in options]
        lower=values[values<best-tolerance]
        result[name]=dict(mapping=assignment,options=options,score=best,optimal_maps=len(optimal),
            score_gap_to_next=float(best-lower.max()) if len(lower) else None,
            observed_class_count=int(used.sum()),components={part:float(v[optimal[0]]) for part,v in parts.items()})
    return result
