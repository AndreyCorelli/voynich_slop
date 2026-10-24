"""Token-only, language-neutral structural diagnostic with latent boundaries.

Independent obligation compatibility is a relaxation, not a dependency parse.
Scores are explicit unnormalized penalties; no parse-count marginal is claimed.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import math
from typing import Protocol


@dataclass(frozen=True, order=True)
class MorphAnalysis:
    pos: str
    features: tuple[tuple[str, str], ...] = ()

    def get(self, key):
        return dict(self.features).get(key)


class LanguageAdapter(Protocol):
    def analyze(self, word: str) -> tuple[MorphAnalysis, ...]: ...
    def obligations(self, tokens: tuple[str, ...], radius: int) -> list: ...


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    components: dict
    boundaries: tuple[int, ...]
    known_tokens: int
    tokens: int
    approximation: str = 'independent-obligation relaxation; exact bounded segmentation DP'


class LatinAdapter:
    GOVERNMENT = {'ad': ('ACC',), 'apud': ('ACC',), 'per': ('ACC',), 'contra': ('ACC',),
        'inter': ('ACC',), 'post': ('ACC',), 'ante': ('ACC',), 'propter': ('ACC',),
        'sine': ('ABL',), 'de': ('ABL',), 'ex': ('ABL',), 'e': ('ABL',),
        'ab': ('ABL',), 'a': ('ABL',), 'pro': ('ABL',), 'cum': ('ABL',),
        'in': ('ACC','ABL'), 'sub': ('ACC','ABL')}
    NOMINAL = {'N','PRON','NUM'}

    def __init__(self, analyzer):
        self.analyzer = analyzer

    @lru_cache(maxsize=100000)
    def analyze(self, word):
        return tuple(sorted({MorphAnalysis(i['part_of_speech'],tuple(sorted(i['features'].items())))
            for a in self.analyzer.annotate(word) for i in a['inflections']}))

    @staticmethod
    def agrees(left, right, keys):
        for key in keys:
            a,b = left.get(key), right.get(key)
            if a in (None,'X','0') or b in (None,'X','0'):
                continue
            if key=='Gender' and (a=='C' or b=='C') and {a,b} <= {'M','F','C'}:
                continue
            if a != b:
                return False
        return True

    def obligations(self, tokens, radius):
        lattice = [self.analyze(w) for w in tokens]
        result=[]
        for i, readings in enumerate(lattice):
            if not readings:
                continue
            poses = {r.pos for r in readings}
            neighbors = [(j,r) for j in range(max(0,i-radius),min(len(tokens),i+radius+1))
                         if j!=i for r in lattice[j]]
            # Ambiguous adjectives can be substantival; no required modifier reading.
            if poses <= {'ADJ','VPAR'}:
                targets = tuple(sorted({j for j,r in neighbors if r.pos in self.NOMINAL and
                    any(self.agrees(a,r,('Case','Number','Gender')) for a in readings)}))
                result.append((i,'modifier',targets,.25))
            if poses == {'PREP'} and tokens[i] in self.GOVERNMENT:
                targets = tuple(sorted({j for j,r in neighbors if j>i and r.pos in self.NOMINAL | {'ADJ'}
                    and r.get('Case') in self.GOVERNMENT[tokens[i]]}))
                result.append((i,'government',targets,1.0))
            finite = tuple(r for r in readings if r.pos=='V' and r.get('Mood') in {'IND','SUB','IMP'})
            if finite and len(finite)==len(readings):
                nominatives = [(j,r) for j,r in neighbors if r.pos in self.NOMINAL and r.get('Case')=='NOM']
                compatible = tuple(sorted({j for j,r in nominatives if any(
                    self.agrees(v,r,('Number',)) and v.get('Person') in (None,'X','0','3') for v in finite)}))
                # Omitted subjects allowed: charge only when an expressed candidate exists.
                result.append((i,'subject',compatible,.5,tuple(sorted({j for j,_ in nominatives}))))
        return lattice,result


class BoundaryModel:
    def __init__(self, mean_length, max_length=24):
        self.max_length = max_length
        self.mean_length = mean_length
        weights = {n: math.exp(-((n-mean_length)/max(mean_length,1))**2/2)
                   for n in range(4,max_length+1)}
        total=sum(weights.values())
        self.log_prior={n:math.log(w/total) for n,w in weights.items()}


class GrammarScorer:
    def __init__(self, adapter: LanguageAdapter, boundary: BoundaryModel, radius=8):
        self.adapter,self.boundary,self.radius=adapter,boundary,radius

    def score(self, tokens, *, latent=True):
        tokens=tuple(tokens)
        if not tokens:
            return ScoreBreakdown(0,{},(),0,0)
        lattice,obligations=self.adapter.obligations(tokens,self.radius)
        def region(start,end):
            components={'modifier':0.,'government':0.,'subject':0.,'predicate':0.,'boundary':0.}
            for item in obligations:
                i,kind,targets,penalty,*extra=item
                if not start<=i<end: continue
                if not any(start<=j<end for j in targets):
                    if kind!='subject' or any(start<=j<end for j in extra[0]):
                        components[kind]-=penalty
            if not any(r.pos=='V' for rr in lattice[start:end] for r in rr):
                components['predicate']-=.25  # soft ellipsis allowance, not a hard finite-clause rule
            if latent:
                components['boundary']=self.boundary.log_prior.get(end-start,
                    min(self.boundary.log_prior.values())-4)
            return components
        if not latent:
            components=region(0,len(tokens)); boundaries=(len(tokens),)
        else:
            n=len(tokens); dp=[-math.inf]*(n+1); dp[0]=0; previous={}
            for end in range(1,n+1):
                for start in range(max(0,end-self.boundary.max_length),end):
                    length=end-start
                    if length<4 and not (start==0 and end==n): continue
                    if not math.isfinite(dp[start]):continue
                    components=region(start,end); value=dp[start]+sum(components.values())
                    if value>dp[end]: dp[end]=value;previous[end]=(start,components)
            components={}; ends=[]; end=n
            while end:
                start,parts=previous[end];ends.append(end)
                for k,v in parts.items():components[k]=components.get(k,0)+v
                end=start
            boundaries=tuple(reversed(ends))
        return ScoreBreakdown(sum(components.values()),components,boundaries,
            sum(bool(r) for r in lattice),len(tokens))
