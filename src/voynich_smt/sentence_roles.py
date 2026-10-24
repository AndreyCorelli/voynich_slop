"""Sentence-wide expected roles with strictly target-excluding recurrent context."""
import hashlib
import numpy as np
import torch
from torch import nn


def bucket(text,size):
    return int.from_bytes(hashlib.blake2b(text.encode(),digest_size=8).digest(),'little')%size


def head_bin(tokens,i):
    head=tokens[i]['head']
    if head==0:return 0
    positions={t['id']:j for j,t in enumerate(tokens)}
    if head not in positions:return -100
    d=positions[head]-i
    if d==0:return -100
    magnitude=1 if abs(d)==1 else 2 if abs(d)<=3 else 3 if abs(d)<=7 else 4
    return magnitude+(4 if d>0 else 0)


class SentenceRoles(nn.Module):
    def __init__(self,labels,relations,morphology,dimension=64):
        super().__init__();self.labels=[tuple(x) for x in labels];self.relations=relations;self.morphology=morphology
        self.word=nn.Embedding(16384,dimension);self.suffix=nn.Embedding(2048,dimension)
        self.morph=nn.Linear(len(morphology),dimension,bias=False)
        self.drop=nn.Dropout(.2)
        self.forward_rnn=nn.GRU(dimension,dimension,batch_first=True)
        self.backward_rnn=nn.GRU(dimension,dimension,batch_first=True)
        self.role_head=nn.Linear(2*dimension,len(labels))
        self.relation_head=nn.Linear(2*dimension,len(relations));self.head_head=nn.Linear(2*dimension,9)

    def forward(self,words,suffixes,morphology,lengths):
        x=self.drop(self.word(words)+self.suffix(suffixes)+self.morph(morphology))
        packed=nn.utils.rnn.pack_padded_sequence(x,lengths.cpu(),batch_first=True,enforce_sorted=False)
        f,_=self.forward_rnn(packed);f,_=nn.utils.rnn.pad_packed_sequence(f,batch_first=True,total_length=x.shape[1])
        rev=torch.zeros_like(x)
        for i,n in enumerate(lengths.tolist()):rev[i,:n]=x[i,:n].flip(0)
        packed=nn.utils.rnn.pack_padded_sequence(rev,lengths.cpu(),batch_first=True,enforce_sorted=False)
        b,_=self.backward_rnn(packed);b,_=nn.utils.rnn.pad_packed_sequence(b,batch_first=True,total_length=x.shape[1])
        back=torch.zeros_like(b)
        for i,n in enumerate(lengths.tolist()):back[i,:n]=b[i,:n].flip(0)
        # At position i, use forward state i-1 and backward state i+1.
        # Each state excludes target input i, including its dictionary readings.
        left=torch.cat((torch.zeros_like(f[:,:1]),f[:,:-1]),dim=1)
        right=torch.cat((back[:,1:],torch.zeros_like(back[:,:1])),dim=1)
        h=self.drop(torch.cat((left,right),dim=-1))
        return self.role_head(h),self.relation_head(h),self.head_head(h)


def reading_features(entries,word):
    features=set()
    for entry in entries.get(word,[]):
        if entry.get('enclitic'):continue
        for inf in entry['inflections']:
            features.add('POS:'+inf['part_of_speech'])
            for k in ('Case','Number','Gender','Person','VerbForm','Tense','Mood'):
                if k in inf['features']:features.add(k+':'+str(inf['features'][k]))
    if not features:features.add('UNKNOWN')
    return features


class Encoder:
    def __init__(self,entries,morphology):
        self.entries=entries;self.morphology=morphology;self.index={x:i for i,x in enumerate(morphology)};self.cache={}
    def word(self,w):
        if w not in self.cache:
            m=np.zeros(len(self.morphology),dtype=np.float32)
            fs=reading_features(self.entries,w)
            for f in fs:
                if f in self.index:m[self.index[f]]=1
            # Preserve ambiguity: union of analyses, not annotation-selected tags.
            self.cache[w]=(bucket(w,16384),bucket(w[-3:],2048),m)
        return self.cache[w]
    def batch(self,sentences):
        lengths=torch.tensor([len(s) for s in sentences]);n=int(lengths.max());b=len(sentences)
        w=np.zeros((b,n),dtype=np.int64);s=w.copy();m=np.zeros((b,n,len(self.morphology)),dtype=np.float32)
        for i,words in enumerate(sentences):
            for j,word in enumerate(words):w[i,j],s[i,j],m[i,j]=self.word(word)
        return torch.from_numpy(w),torch.from_numpy(s),torch.from_numpy(m),lengths
