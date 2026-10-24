"""Anonymous type embeddings added to masked-word inputs; spelling stays hidden."""
import random
import numpy as np
import torch
from torch import nn
from voynich_smt.neural_cloze import RepeatedCloze

SLOTS=32

class IdentityCloze(RepeatedCloze):
    def __init__(self,scorer,bank,adapter,*,mode='repeat',seed=941,radius=12):
        super().__init__(scorer,bank,radius=radius)
        if mode not in ('repeat','collapsed','broken'):raise ValueError('Invalid identity mode')
        self.adapter,self.mode,self.seed=adapter,mode,seed

    def job(self,segment,target,center,visible,length):
        ids,positions=super().job(segment,target,center,visible,length)
        window=segment[max(0,center-self.radius):min(len(segment),center+self.radius+1)]
        hidden=sorted(set(window)-set(visible))
        if len(hidden)>SLOTS:raise ValueError('Too many anonymous types')
        # Local permutation depends on occurrence index and seed, never spelling.
        rng=random.Random(self.seed+center*1009)
        slots=list(range(1,SLOTS+1));rng.shuffle(slots)
        mapping=dict(zip(hidden,slots)); identities=[0]
        for word in window:
            if word in visible:identities.extend([0]*len(self.visible_ids(visible[word])))
            else:
                slot=0 if self.mode=='collapsed' else (rng.randint(1,SLOTS) if self.mode=='broken' else mapping[word])
                identities.extend([slot]*(length if word==target else 1))
        identities.append(0)
        assert len(ids)==len(identities)
        return ids,positions,identities

    def distributions(self,jobs):
        results=[]
        for first in range(0,len(jobs),self.scorer.batch_size):
            batch=jobs[first:first+self.scorer.batch_size]
            inputs,attention,identity,rows,places=pack(batch,self.scorer.tokenizer.pad_token_id)
            with torch.inference_mode():
                embeddings=self.scorer.model.roberta.embeddings.word_embeddings(inputs)+self.adapter(identity)
                hidden=self.scorer.model.roberta(inputs_embeds=embeddings,attention_mask=attention).last_hidden_state
                probabilities=torch.log_softmax(self.scorer.model.lm_head(hidden[rows,places]),dim=-1).numpy()
            offset=0
            for _,positions,_ in batch:
                results.append(probabilities[offset:offset+len(positions)].astype(np.float64));offset+=len(positions)
        return results

def pack(jobs,pad):
    width=max(len(j[0]) for j in jobs)
    inputs=torch.full((len(jobs),width),pad,dtype=torch.long)
    attention=torch.zeros_like(inputs);identity=torch.zeros_like(inputs);rows=[];places=[]
    for row,(ids,positions,slots) in enumerate(jobs):
        inputs[row,:len(ids)]=torch.tensor(ids);attention[row,:len(ids)]=1
        identity[row,:len(ids)]=torch.tensor(slots)
        rows.extend([row]*len(positions));places.extend(positions)
    return inputs,attention,identity,rows,places

def adapter_for(model):
    adapter=nn.Embedding(SLOTS+1,model.config.hidden_size,padding_idx=0)
    nn.init.normal_(adapter.weight,std=.02)
    with torch.no_grad():adapter.weight[0].zero_()
    return adapter
