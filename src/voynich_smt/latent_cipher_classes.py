"""Fixed-transition HMM induction from anonymous words and ending groups.

Emission priors and all latent inference use observed token IDs only. Gold
classes are accepted solely by the explicitly separate oracle helper.
"""
import numpy as np


def fixed_chain(sequences,k,alpha=.5):
    start=np.full(k,alpha);trans=np.full((k,k),alpha);stop=np.full(k,alpha);occupancy=np.zeros(k)
    for seq in sequences:
        if not seq:continue
        start[seq[0]]+=1;stop[seq[-1]]+=1;np.add.at(occupancy,seq,1)
        for a,b in zip(seq,seq[1:]):trans[a,b]+=1
    denominator=trans.sum(axis=1)+stop
    return dict(start=(start/start.sum()).tolist(),transition=(trans/denominator[:,None]).tolist(),stop=(stop/denominator).tolist(),
        source_occupancy=(occupancy/occupancy.sum()).tolist(),k=k,alpha=alpha)


def batch(sequences):
    lengths=np.asarray([len(s) for s in sequences],dtype=int)
    if not len(lengths) or np.any(lengths==0):raise ValueError('Nonempty sequences required')
    width=int(lengths.max());tokens=np.zeros((len(sequences),width),dtype=int)
    for i,seq in enumerate(sequences):tokens[i,:len(seq)]=seq
    mask=np.arange(width)[None,:]<lengths[:,None]
    return dict(tokens=tokens,mask=mask,lengths=lengths)


def forward_backward(chain,emissions,sequences):
    b=batch(sequences);tokens=b['tokens'];mask=b['mask'];n,width=tokens.shape;k=chain['k']
    transition=np.asarray(chain['transition']);stop=np.asarray(chain['stop']);start=np.asarray(chain['start']);emissions=np.asarray(emissions)
    evidence=np.moveaxis(emissions[:,tokens],0,-1)
    forward=np.zeros((n,width,k));scales=np.ones((n,width));state=start[None,:]*evidence[:,0,:]
    scales[:,0]=state.sum(axis=1);state/=scales[:,0,None];forward[:,0,:]=state
    for t in range(1,width):
        proposal=(state@transition)*evidence[:,t,:];normalizer=proposal.sum(axis=1);active=mask[:,t]
        state=np.where(active[:,None],proposal/np.maximum(normalizer[:,None],1e-300),state)
        scales[:,t]=np.where(active,normalizer,1.);forward[:,t,:]=state
    final=state@stop
    likelihood=float(np.log(np.maximum(scales,1e-300)).sum()+np.log(np.maximum(final,1e-300)).sum())
    backward=np.zeros_like(forward);state=np.broadcast_to(stop,(n,k))/final[:,None];backward[:,-1,:]=state
    for t in range(width-2,-1,-1):
        proposal=(evidence[:,t+1,:]*state)@transition.T/scales[:,t+1,None]
        state=np.where(mask[:,t+1,None],proposal,state);backward[:,t,:]=state
    gamma=forward*backward;gamma/=np.maximum(gamma.sum(axis=2,keepdims=True),1e-300);gamma*=mask[:,:,None]
    return likelihood,[gamma[i,:length].copy() for i,length in enumerate(b['lengths'])]


def word_counts(sequences,posteriors,vocabulary,k):
    ids=np.concatenate([np.asarray(s,dtype=int) for s in sequences]);gamma=np.concatenate(posteriors)
    return np.asarray([np.bincount(ids,weights=gamma[:,j],minlength=vocabulary) for j in range(k)])


def prior_data(sequences,word_endings):
    v=len(word_endings);q=np.bincount(np.concatenate([np.asarray(s,dtype=int) for s in sequences]),minlength=v).astype(float);q/=q.sum()
    endings=np.asarray(word_endings,dtype=int);e=int(endings.max())+1;qe=np.bincount(endings,weights=q,minlength=e);within=q/qe[endings]
    return q,qe,within


def update(counts,word_endings,q,qe,within,sharing=False,alpha_word=.2,alpha_end=1.):
    if not sharing:
        values=counts+alpha_end*q[None,:];return values/values.sum(axis=1,keepdims=True)
    endings=np.asarray(word_endings);end_counts=np.asarray([np.bincount(endings,weights=row,minlength=len(qe)) for row in counts])
    end_prob=(end_counts+alpha_end*qe[None,:])/(end_counts.sum(axis=1,keepdims=True)+alpha_end)
    conditional=(counts+alpha_word*within[None,:])/(end_counts[:,endings]+alpha_word)
    return end_prob[:,endings]*conditional


def log_prior(emissions,word_endings,q,qe,within,sharing=False,alpha_word=.2,alpha_end=1.):
    e=np.maximum(np.asarray(emissions),1e-300)
    if not sharing:return float(alpha_end*np.sum(q[None,:]*np.log(e)))
    endings=np.asarray(word_endings);group=np.asarray([np.bincount(endings,weights=row,minlength=len(qe)) for row in e]);conditional=e/group[:,endings]
    return float(alpha_end*np.sum(qe[None,:]*np.log(group))+alpha_word*np.sum(within[None,:]*np.log(conditional)))


def fit(chain,sequences,word_endings,seed,sharing=False,max_iter=80,tolerance=1e-7,initial=None):
    k=chain['k'];v=len(word_endings);q,qe,within=prior_data(sequences,word_endings)
    rng=np.random.default_rng(seed);emissions=np.asarray(initial,dtype=float).copy() if initial is not None else rng.gamma(2.,1.,size=(k,v))*q[None,:]
    emissions/=emissions.sum(axis=1,keepdims=True);trace=[];converged=False
    for iteration in range(max_iter+1):
        likelihood,gamma=forward_backward(chain,emissions,sequences)
        objective=likelihood+log_prior(emissions,word_endings,q,qe,within,sharing)
        trace.append(dict(iteration=iteration,log_likelihood=likelihood,objective=objective))
        if len(trace)>1:
            improvement=objective-trace[-2]['objective']
            if improvement < -1e-6:raise ValueError('EM objective decreased')
            if improvement<=tolerance*max(1.,abs(trace[-2]['objective'])):converged=True;break
        if iteration==max_iter:break
        counts=word_counts(sequences,gamma,v,k);emissions=update(counts,word_endings,q,qe,within,sharing)
    return dict(emissions=emissions.tolist(),trace=trace,seed=seed,sharing=sharing,converged=converged,iterations=trace[-1]['iteration'],objective=trace[-1]['objective'])


def oracle_emissions(chain,sequences,word_endings,labels,sharing=False):
    """Privileged capacity control, never called by unsupervised fitting."""
    k=chain['k'];q,qe,within=prior_data(sequences,word_endings);gamma=[np.eye(k)[s] for s in labels]
    counts=word_counts(sequences,gamma,len(word_endings),k)
    return update(counts,word_endings,q,qe,within,sharing)


def relation_table(sentences,k,radius=12,alpha=2.):
    counts=np.zeros((12,k,k,5));total=np.zeros(5)
    for s in sentences:
        labels={(c,p):l for c,p,l in s['edges']}
        for c in range(len(s['classes'])):
            for p in range(max(0,c-radius),min(len(s['classes']),c+radius+1)):
                if c==p:continue
                distance=min(6,abs(p-c))-1+(6 if p>c else 0);label=labels.get((c,p),0)
                counts[distance,s['classes'][c],s['classes'][p],label]+=1;total[label]+=1
    prior=(total+.5)/(total.sum()+2.5)
    probability=(counts+alpha*prior)/(counts.sum(axis=3,keepdims=True)+alpha)
    return dict(probabilities=probability.tolist(),prior=prior.tolist(),radius=radius,k=k,alpha=alpha)


def relation_edges(posteriors,model,threshold):
    table=np.asarray(model['probabilities']);edges=[]
    for c,child in enumerate(posteriors):
        candidates=[]
        for p in range(max(0,c-model['radius']),min(len(posteriors),c+model['radius']+1)):
            if p==c:continue
            d=min(6,abs(p-c))-1+(6 if p>c else 0)
            probabilities=np.einsum('i,ijl,j->l',child,table[d],posteriors[p]);label=int(np.argmax(probabilities[1:]))+1
            candidates.append((p,label,float(probabilities[label])))
        if not candidates:continue
        maximum=max(x[2] for x in candidates);best=[x for x in candidates if abs(x[2]-maximum)<1e-12]
        if len(best)!=1 or maximum<threshold:continue
        p,label,confidence=best[0];edges.append([c,p,label,confidence])
    heads={};selected=[]
    for edge in sorted(edges,key=lambda e:(-e[3],e[0],e[1])):
        c,p,label,confidence=edge;current=p;seen={c}
        while current in heads and current not in seen:seen.add(current);current=heads[current]
        if current in seen:continue
        heads[c]=p;selected.append(edge)
    return sorted(selected,key=lambda e:e[0])
