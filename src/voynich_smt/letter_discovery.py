"""Compact permutation-key discovery with incremental character/word evidence."""
from collections import Counter
from functools import lru_cache
import math
import numpy as np
from numba import njit
# Canonical j->i, v->u; retain every other ASCII letter.
ALPHABET=''.join(c for c in 'abcdefghijklmnopqrstuvwxyz' if c not in 'jv')
SPACE=len(ALPHABET);BASE=SPACE+1


def pattern(word):
    seen={};return tuple(seen.setdefault(c,len(seen)) for c in word)


def encode_text(text):
    ids={c:i for i,c in enumerate(ALPHABET)};ids[' ']=SPACE
    return np.asarray([ids[c] for c in text],dtype=np.int64)


def decode_text(cipher,key):
    return ''.join(' ' if c==SPACE else ALPHABET[int(key[c])] for c in cipher)


def language_model(sentences,order=4):
    counts=np.zeros(BASE**order,dtype=np.float64);unigram=np.zeros(SPACE)
    for words in sentences:
        text=encode_text(' '.join(words));chars=text[text!=SPACE];unigram+=np.bincount(chars,minlength=SPACE)
        if len(text)<order:continue
        codes=np.zeros(len(text)-order+1,dtype=np.int64)
        for k in range(order):codes=codes*BASE+text[k:k+len(codes)]
        counts+=np.bincount(codes,minlength=len(counts))
    # Fixed smoothed joint character n-gram likelihood, no target fitting.
    logs=np.log((counts+.1)/(counts.sum()+.1*len(counts)))
    return logs.astype(np.float64),unigram/unigram.sum()


def trie(words):
    nodes=[np.full(SPACE,-1,dtype=np.int32)];terminal=[-1];ids={c:i for i,c in enumerate(ALPHABET)}
    for wi,w in enumerate(words):
        state=0
        for c in w:
            k=ids[c];nextstate=int(nodes[state][k])
            if nextstate<0:nextstate=len(nodes);nodes[state][k]=nextstate;nodes.append(np.full(SPACE,-1,dtype=np.int32));terminal.append(-1)
            state=nextstate
        terminal[state]=wi
    return np.asarray(nodes),np.asarray(terminal,dtype=np.int32)


@lru_cache(maxsize=2)
def candidate_groups(dictionary_words):
    groups={}
    for i,w in enumerate(dictionary_words):groups.setdefault(pattern(w),[]).append(i)
    return groups


def prepare(cipher_words,dictionary_words):
    unique=sorted(set(cipher_words));typeid={w:i for i,w in enumerate(unique)};frequency=Counter(cipher_words);wordmax=max(map(len,unique));wordarray=np.full((len(unique),wordmax),-1,dtype=np.int64);lengths=np.asarray([len(w) for w in unique],dtype=np.int64)
    for i,w in enumerate(unique):wordarray[i,:len(w)]=encode_text(w)
    groups=candidate_groups(tuple(dictionary_words))
    ptr=[0];candidates=[]
    for w in unique:candidates.extend(groups.get(pattern(w),[]));ptr.append(len(candidates))
    affectedwords=np.full((SPACE,len(unique)),-1,dtype=np.int64);wordcounts=np.zeros(SPACE,dtype=np.int64)
    for c in range(SPACE):
        indices=np.flatnonzero((wordarray==c).any(axis=1));affectedwords[c,:len(indices)]=indices;wordcounts[c]=len(indices)
    return {'unique':unique,'words':wordarray,'lengths':lengths,'frequency':np.asarray([frequency[w] for w in unique],dtype=np.float64),'ptr':np.asarray(ptr,dtype=np.int64),'candidate_ids':np.asarray(candidates,dtype=np.int64),'affected_words':affectedwords,'affected_word_counts':wordcounts}


def gram_positions(cipher,order):
    n=len(cipher)-order+1;positions=np.full((SPACE,n),-1,dtype=np.int64);counts=np.zeros(SPACE,dtype=np.int64)
    for c in range(SPACE):
        mask=np.zeros(n,dtype=bool)
        for j in range(order):mask|=cipher[j:j+n]==c
        indices=np.flatnonzero(mask);positions[c,:len(indices)]=indices;counts[c]=len(indices)
    return positions,counts


@njit
def word_value(w,key,words,lengths,nodes,terminal,ptr,candidate_ids,scores,unknown):
    state=0
    for j in range(lengths[w]):
        state=nodes[state,key[words[w,j]]]
        if state<0:return unknown[w]
    target=terminal[state]
    if target<0:return unknown[w]
    lo=ptr[w];hi=ptr[w+1]
    while lo<hi:
        mid=(lo+hi)//2
        if candidate_ids[mid]<target:lo=mid+1
        else:hi=mid
    if lo<ptr[w+1] and candidate_ids[lo]==target:return scores[lo]
    return unknown[w]


@njit
def gram_value(i,cipher,key,logs,order,base,space):
    code=0
    for j in range(order):
        c=cipher[i+j];code=code*base+(space if c==space else key[c])
    return logs[code]


@njit
def merge(a,na,b,nb,result):
    i=j=n=0
    while i<na or j<nb:
        if j>=nb or (i<na and a[i]<b[j]):x=a[i];i+=1
        elif i>=na or b[j]<a[i]:x=b[j];j+=1
        else:x=a[i];i+=1;j+=1
        result[n]=x;n+=1
    return n


@njit
def search(cipher,initial,logs,order,positions,pcounts,words,lengths,frequency,nodes,terminal,ptr,candidate_ids,scores,unknown,waffected,wcounts,weight,steps,seed):
    np.random.seed(seed);key=initial.copy();ng=len(cipher)-order+1;nw=len(lengths);totalwords=frequency.sum();space=len(key);base=space+1
    grams=np.asarray([gram_value(i,cipher,key,logs,order,base,space) for i in range(ng)])
    values=np.asarray([word_value(i,key,words,lengths,nodes,terminal,ptr,candidate_ids,scores,unknown) for i in range(nw)])
    gsum=grams.sum();wsum=(values*frequency).sum();current=gsum/ng+weight*wsum/totalwords;best=current;bestkey=key.copy();accepted=0
    affectedg=np.empty(ng,dtype=np.int64);affectedw=np.empty(nw,dtype=np.int64);newg=np.empty(ng);neww=np.empty(nw)
    checkpoint_steps=np.asarray([0,100,1000,steps]);checkpoints=np.zeros((4,3));checkpoints[0]=np.asarray([0.,current,best]);ci=1
    for step in range(1,steps+1):
        a=np.random.randint(space);b=np.random.randint(space-1)
        if b>=a:b+=1
        key[a],key[b]=key[b],key[a]
        gn=merge(positions[a],pcounts[a],positions[b],pcounts[b],affectedg);wn=0 if weight==0 else merge(waffected[a],wcounts[a],waffected[b],wcounts[b],affectedw)
        dg=dw=0.
        for j in range(gn):
            i=affectedg[j];v=gram_value(i,cipher,key,logs,order,base,space);newg[j]=v;dg+=v-grams[i]
        for j in range(wn):
            i=affectedw[j];v=word_value(i,key,words,lengths,nodes,terminal,ptr,candidate_ids,scores,unknown);neww[j]=v;dw+=(v-values[i])*frequency[i]
        delta=dg/ng+weight*dw/totalwords
        # Fixed cyclic annealing; archived key chosen only by discovery objective.
        phase=((step-1)%2000)/1999.;temperature=.05*(.001/.05)**phase
        if delta>=0 or np.random.random()<np.exp(delta/temperature):
            gsum+=dg;wsum+=dw;current=gsum/ng+weight*wsum/totalwords;accepted+=1
            for j in range(gn):grams[affectedg[j]]=newg[j]
            for j in range(wn):values[affectedw[j]]=neww[j]
            if current>best:best=current;bestkey=key.copy()
        else:key[a],key[b]=key[b],key[a]
        if ci<4 and step==checkpoint_steps[ci]:checkpoints[ci]=np.asarray([step,current,best]);ci+=1
    return bestkey,best,accepted,checkpoints


def full_score(cipher,key,logs,order,prepared,nodes,terminal,scores,unknown,weight):
    grams=[gram_value(i,cipher,key,logs,order,BASE,SPACE) for i in range(len(cipher)-order+1)]
    vals=[word_value(i,key,prepared['words'],prepared['lengths'],nodes,terminal,prepared['ptr'],prepared['candidate_ids'],scores,unknown) for i in range(len(prepared['unique']))]
    return float(np.mean(grams)+weight*np.average(vals,weights=prepared['frequency']))


def initialization(cipher,frequency,seed):
    rng=np.random.default_rng(seed);counts=np.bincount(cipher[cipher!=SPACE],minlength=SPACE);key=np.zeros(SPACE,dtype=np.int64);key[np.argsort(-counts)]=np.argsort(-frequency)
    # Equal randomized initial perturbation for every experimental arm.
    for _ in range(6):a,b=rng.choice(SPACE,2,replace=False);key[a],key[b]=key[b],key[a]
    return key
