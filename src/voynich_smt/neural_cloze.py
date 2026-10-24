"""Candidate-length-hypothesized cloze with repeated types and hidden spelling.

Only supplied visible surfaces enter model inputs. The candidate bank supplies
label pieces, never the proposed spelling in the context. Other hidden types
occupy one mask; every occurrence of the target uses the hypothesized piece count.
"""
from collections import defaultdict
import math
import numpy as np


class ClozeCandidateBank:
    def __init__(self, tokenizer, forms):
        self.forms=tuple(forms)
        if not self.forms or len(set(self.forms))!=len(self.forms):
            raise ValueError('Unique candidate forms required')
        if any(not w or any(c.isspace() for c in w) for w in self.forms):
            raise ValueError('Candidates must be nonempty words')
        encoded=tokenizer(list(self.forms),add_special_tokens=False)['input_ids']
        forbidden=set(tokenizer.all_special_ids)
        self.groups={};self.excluded=[]
        groups=defaultdict(list)
        for i,pieces in enumerate(encoded):
            if not pieces or any(p in forbidden for p in pieces):
                self.excluded.append(i)
            else:groups[len(pieces)].append((i,pieces))
        for length,items in sorted(groups.items()):
            self.groups[length]=(np.asarray([i for i,_ in items],dtype=np.int32),
                                 np.asarray([p for _,p in items],dtype=np.int32))
        if not self.groups:raise ValueError('No scoreable candidate forms')

    def scores(self, log_probabilities):
        result=np.full(len(self.forms),-np.inf,dtype=np.float64)
        for length,(indices,pieces) in self.groups.items():
            values=np.asarray(log_probabilities[length])
            if values.ndim!=2 or values.shape[0]!=length:
                raise ValueError('Incorrect cloze distribution shape')
            result[indices]=values[np.arange(length)[None,:],pieces].mean(axis=1)
        return result


class RepeatedCloze:
    def __init__(self, scorer, bank, *, radius=12):
        if type(radius) is not int or radius<0:raise ValueError('Nonnegative word radius required')
        self.scorer,self.bank,self.radius=scorer,bank,radius
        self.visible_cache={}

    def visible_ids(self, word):
        if word not in self.visible_cache:
            ids=self.scorer.tokenizer(word,add_special_tokens=False)['input_ids']
            if not ids or any(i in self.scorer.tokenizer.all_special_ids for i in ids):
                raise ValueError('Visible words must tokenize without special/unknown pieces')
            self.visible_cache[word]=ids
        return self.visible_cache[word]

    def job(self, segment, target, center, visible, length):
        if not 0<=center<len(segment) or segment[center]!=target or target in visible or length<1:
            raise ValueError('Invalid hidden target')
        tok=self.scorer.tokenizer
        ids=[tok.bos_token_id];positions=None
        first=max(0,center-self.radius);last=min(len(segment),center+self.radius+1)
        for i in range(first,last):
            cipher=segment[i]
            if cipher==target:
                if i==center:positions=tuple(range(len(ids),len(ids)+length))
                ids.extend([tok.mask_token_id]*length)
            elif cipher in visible:ids.extend(self.visible_ids(visible[cipher]))
            else:ids.append(tok.mask_token_id)
        ids.append(tok.eos_token_id)
        if len(ids)>self.scorer.max_length:raise ValueError('Cloze window exceeds context limit')
        return ids,positions

    def distributions(self,jobs):
        import torch
        results=[]
        for first in range(0,len(jobs),self.scorer.batch_size):
            batch=jobs[first:first+self.scorer.batch_size]
            width=max(len(ids) for ids,_ in batch)
            inputs=torch.full((len(batch),width),self.scorer.tokenizer.pad_token_id,dtype=torch.long)
            attention=torch.zeros_like(inputs);rows=[];places=[]
            for row,(ids,positions) in enumerate(batch):
                inputs[row,:len(ids)]=torch.tensor(ids);attention[row,:len(ids)]=1
                rows.extend([row]*len(positions));places.extend(positions)
            with torch.inference_mode():
                hidden=self.scorer.model.roberta(input_ids=inputs,attention_mask=attention).last_hidden_state
                logits=self.scorer.model.lm_head(hidden[rows,places])
                probabilities=torch.log_softmax(logits,dim=-1).cpu().numpy()
            offset=0
            for _,positions in batch:
                results.append(probabilities[offset:offset+len(positions)].astype(np.float64))
                offset+=len(positions)
            self.scorer.inference_rows+=len(batch)
        return results

    def rank_scores(self,segments,target,visible):
        occurrences=[(segment,i) for segment in segments for i,c in enumerate(segment) if c==target]
        if not occurrences:raise ValueError('Target has no occurrences')
        pooled={};first={}
        for length in self.bank.groups:
            jobs=[self.job(segment,target,i,visible,length) for segment,i in occurrences]
            values=self.distributions(jobs)
            pooled[length]=np.mean(values,axis=0)
            first[length]=values[0]
        return {'pooled':self.bank.scores(pooled),'first_occurrence':self.bank.scores(first),
                'occurrences':len(occurrences)}
