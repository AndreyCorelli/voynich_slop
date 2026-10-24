"""Capacity-preserving search over emission classes, with optional supplied anchors."""
from collections import Counter
import ctypes
import hashlib
import math
from pathlib import Path
import random
import subprocess
import tempfile

import numpy as np
from .structural_language import BOS, EOS


class ProfileScorer:
    def __init__(self, model, profiles, segments, assignments):
        source=Path(__file__).with_name('structural_search_kernel.cpp')
        sha=hashlib.sha256(source.read_bytes()).hexdigest()
        library=Path(tempfile.gettempdir())/f'voynich-structural-{sha}.dylib'
        if not library.exists():
            subprocess.run(['c++','-O3','-std=c++17','-shared','-fPIC',str(source),'-o',str(library)],check=True,capture_output=True)
        self.kernel=ctypes.CDLL(str(library)).score_segments
        ip=ctypes.POINTER(ctypes.c_int);dp=ctypes.POINTER(ctypes.c_double)
        self.kernel.argtypes=[ip,ip,ip,ip,ip,ctypes.c_int,ip,ip,dp,dp,ctypes.c_int,ctypes.c_int,ctypes.c_int,dp]
        self.kernel.restype=None
        states=sorted(model.states,key=repr)+[BOS,('OUTSIDE',)]
        ids={s:i for i,s in enumerate(states)}
        self.size=len(states);self.bos=ids[BOS];self.eos=ids[EOS]
        self.transition=np.asarray([[math.exp(model.log_transition(a,b)) for b in states] for a in states],dtype=np.float64)
        # BOS is never emitted; the extra column is irrelevant to the kernel.
        offsets=[0];flat=[];weights=[]
        for profile in profiles:
            counts=Counter(ids.get(s,ids[('OUTSIDE',)]) for s in profile)
            for s,count in sorted(counts.items()):
                flat.append(s);weights.append(count/len(profile))
            offsets.append(len(flat))
        self.offsets=np.asarray(offsets,dtype=np.int32)
        self.states=np.asarray(flat,dtype=np.int32);self.weights=np.asarray(weights,dtype=np.float64)
        self.keys=tuple(sorted({w for s in segments for w in s}));self.ids={w:i for i,w in enumerate(self.keys)}
        self.assignments=np.asarray([assignments[w] for w in self.keys],dtype=np.int32)
        words=[];starts=[];ends=[];self.affected=[set() for _ in self.keys]
        for i,segment in enumerate(segments):
            starts.append(len(words))
            for w in segment:
                index=self.ids[w];words.append(index);self.affected[index].add(i)
            ends.append(len(words))
        self.words=np.asarray(words,dtype=np.int32)
        self.starts=np.asarray(starts,dtype=np.int32);self.ends=np.asarray(ends,dtype=np.int32)
        self.scores=self.evaluate(range(len(segments)))
        self.score=float(self.scores.sum())

    def evaluate(self, indices):
        selected=np.asarray(tuple(indices),dtype=np.int32)
        result=np.empty(len(selected),dtype=np.float64)
        def ip(a):return a.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
        def dp(a):return a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        self.kernel(ip(self.assignments),ip(self.words),ip(self.starts),ip(self.ends),ip(selected),len(selected),
                    ip(self.offsets),ip(self.states),dp(self.weights),dp(self.transition),self.size,self.bos,self.eos,dp(result))
        return result

    def propose(self, changes):
        if any(not 0<=i<len(self.assignments) or not 0<=p<len(self.offsets)-1 for i,p in changes.items()):
            raise ValueError('Invalid profile assignment')
        indices=sorted(set().union(*(self.affected[i] for i in changes))) if changes else []
        old={i:int(self.assignments[i]) for i in changes}
        for i,p in changes.items():self.assignments[i]=p
        scores=self.evaluate(indices)
        for i,p in old.items():self.assignments[i]=p
        delta=float(scores.sum()-self.scores[indices].sum())
        return delta,indices,scores

    def commit(self, changes, proposal):
        delta,indices,scores=proposal
        for i,p in changes.items():self.assignments[i]=p
        self.scores[indices]=scores;self.score+=delta

    def validate(self):
        full=self.evaluate(range(len(self.scores)))
        if not np.allclose(full,self.scores,atol=1e-8,rtol=1e-12) or not math.isclose(float(full.sum()),self.score,abs_tol=1e-7):
            raise ValueError('Incremental profile score drift')


class ProfileSearch:
    def __init__(self, scorer, capacities, training_mass, anchors, *, seed, steps):
        self.scorer=scorer;self.capacities=tuple(capacities)
        self.training_mass=tuple(training_mass);self.anchors=dict(anchors)
        import itertools
        self.cumulative_mass=tuple(itertools.accumulate(training_mass))
        self.has_mass=bool(self.cumulative_mass and self.cumulative_mass[-1]>0)
        self.rng=random.Random(seed);self.steps=steps;self.step=0
        self.active=tuple(i for i in range(len(scorer.keys)) if i not in anchors)
        self.owners=Counter(map(int,scorer.assignments))
        if any(self.owners[p]>capacity for p,capacity in enumerate(capacities)):
            raise ValueError('Initialization exceeds profile capacity')
        if any(int(scorer.assignments[i])!=p for i,p in anchors.items()):
            raise ValueError('Incorrect supplied anchors')
        self.initial_score=self.best_score=scorer.score
        self.initial=scorer.assignments.copy();self.best=self.initial.copy()
        self.statistics=Counter()
        self.trace=[{'step':0,'score':scorer.score,'best_score':self.best_score}]

    def advance(self, budget):
        for _ in range(min(budget,self.steps-self.step)):
            changes={}
            if self.active:
                a=self.rng.choice(self.active)
                draw=self.rng.random()
                if draw<.2 and len(self.active)>1:
                    a,b=self.rng.sample(self.active,2)
                    changes={a:int(self.scorer.assignments[b]),b:int(self.scorer.assignments[a])}
                else:
                    if draw<.8 and self.has_mass:
                        p=self.rng.choices(range(len(self.capacities)),cum_weights=self.cumulative_mass)[0]
                    else:p=self.rng.randrange(len(self.capacities))
                    old=int(self.scorer.assignments[a])
                    if p!=old and self.owners[p]>=self.capacities[p]:
                        # Capacity-preserving swap with an unanchored owner.
                        eligible=[b for b in self.active if int(self.scorer.assignments[b])==p and b!=a]
                        if eligible:
                            b=self.rng.choice(eligible);changes={a:p,b:old}
                    else:changes={a:p}
            proposal=self.scorer.propose(changes)
            self.statistics['proposed']+=1
            temperature=2.*(.02/2.)**(self.step/max(1,self.steps-1))
            delta=proposal[0]
            if delta>=0 or math.log(max(self.rng.random(),1e-300))<delta/temperature:
                for i in changes:self.owners[int(self.scorer.assignments[i])]-=1
                self.scorer.commit(changes,proposal)
                for p in changes.values():self.owners[p]+=1
                self.statistics['accepted']+=1
                if self.scorer.score>self.best_score+1e-9:
                    self.best_score=self.scorer.score;self.best=self.scorer.assignments.copy()
            self.step+=1
        self.scorer.validate()
        if any(int(self.scorer.assignments[i])!=p for i,p in self.anchors.items()):
            raise ValueError('Anchor changed')
        if self.owners!=Counter(map(int,self.scorer.assignments)):
            raise ValueError('Capacity cache drift')
        self.trace.append({'step':self.step,'score':self.scorer.score,'best_score':self.best_score})
