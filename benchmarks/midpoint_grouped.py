"""Equivalent midpoint enumeration with repeated ciphertext words grouped."""
from heapq import heappop,heappush
from voynich_smt.solver.length_search import public_domains


def vectors(domains,words,span,relations):
    groups={}
    for i,w in enumerate(words):groups.setdefault(tuple(w),[]).append(i)
    groups=list(groups.values());choices=[]
    for indices in groups:
        common=set(domains[indices[0]])
        for i in indices[1:]:common.intersection_update(domains[i])
        ranks={i:{n:r for r,n in enumerate(sorted(domains[i],key=lambda n:(abs(n*span-2*len(words[i])),n)))} for i in indices}
        ordered=sorted(common,key=lambda n:(sum(ranks[i][n] for i in indices),n))
        if not ordered:return
        choices.append(tuple((n,sum(ranks[i][n] for i in indices)) for n in ordered))
    def item(state):
        vector=[0]*len(words);cost=0
        for indices,options,k in zip(groups,choices,state):
            n,weight=options[k];cost+=weight
            for i in indices:vector[i]=n
        return cost,tuple(vector),state
    if not groups:return
    state=(0,)*len(groups);queue=[item(state)];seen={state}
    while queue:
        _,vector,state=heappop(queue)
        if not any((r.prefix=='equal' and vector[r.left]!=vector[r.right])
                   or (r.prefix=='left' and vector[r.left]>=vector[r.right])
                   or (r.prefix=='right' and vector[r.left]<=vector[r.right]) for r in relations):
            yield vector
        for i,k in enumerate(state):
            if k+1==len(choices[i]):continue
            adjacent=state[:i]+(k+1,)+state[i+1:]
            if adjacent in seen:continue
            seen.add(adjacent);heappush(queue,item(adjacent))


def proposals(q):
    domains,graph=public_domains(q)
    yield from vectors(domains,q.ciphertext.words,q.bounds.min_code_length+q.bounds.max_code_length,graph.relations)
