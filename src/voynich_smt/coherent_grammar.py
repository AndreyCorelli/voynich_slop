"""Bounded coherent dependency analysis; a controlled diagnostic, not full Latin."""
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol
import z3

from .grammar_diagnostic import MorphAnalysis, LatinAdapter


class MorphologyAdapter(Protocol):
    def analyze(self, word: str) -> tuple[MorphAnalysis, ...]: ...
    def government(self, word: str) -> tuple[str, ...]: ...
    def frame(self, word: str) -> str: ...


class CoherentLatinAdapter(LatinAdapter):
    # Small independently specified valency lexicon for the controlled baseline.
    INTRANSITIVE = frozenset('currit currunt ambulat ambulant dormit dormiunt laborat laborant'.split())

    def government(self, word):
        return self.GOVERNMENT.get(word, ())

    def frame(self, word):
        return 'intransitive' if word in self.INTRANSITIVE else 'optional-object'


@dataclass(frozen=True)
class ClauseResult:
    status: str
    tokens: tuple[str, ...]
    analyses: tuple[dict, ...] = ()
    alternative_found: bool | None = False
    reason: str = ''


@dataclass(frozen=True)
class StreamResult:
    status: str
    score: float | None
    boundaries: tuple[int, ...]
    clauses: tuple[ClauseResult, ...]
    covered_tokens: int
    tokens: int
    components: dict
    unresolved_intervals: int = 0


def agrees(a, b, keys):
    return LatinAdapter.agrees(a,b,keys)


def finite(r):
    return r.pos=='V' and r.get('Mood') in {'IND','SUB','IMP'}


class CoherentGrammar:
    ROLES = {'root':0,'subject':1,'object':2,'oblique':3,'modifier':4,'case':5,'genitive':6,'adverb':7}
    NOMINAL = frozenset({'N','PRON','NUM'})
    SUPPORTED = NOMINAL | {'ADJ','VPAR','V','PREP','ADV'}

    def __init__(self, adapter: MorphologyAdapter, max_clause=10, timeout_ms=250):
        self.adapter,self.max_clause,self.timeout_ms=adapter,max_clause,timeout_ms

    @lru_cache(maxsize=8192)
    def clause(self, tokens):
        tokens=tuple(tokens);n=len(tokens)
        if not n or n>self.max_clause:
            return ClauseResult('unsupported',tokens,reason='empty clause or configured length limit')
        readings=[tuple(sorted(set(self.adapter.analyze(w)))) for w in tokens]
        if any(not rr for rr in readings):
            return ClauseResult('unsupported',tokens,reason='missing morphology')
        if any(not any(r.pos in self.SUPPORTED for r in rr) for rr in readings):
            return ClauseResult('unsupported',tokens,reason='unsupported POS/construction')
        # No root can exist regardless of attachment or morphological choice.
        if not any(finite(r) for rr in readings for r in rr):
            return ClauseResult('no_parse',tokens,reason='no supported finite predicate')
        solver=z3.Solver();solver.set(timeout=self.timeout_ms,random_seed=0)
        choice=[z3.Int(f'r{i}') for i in range(n)]
        head=[z3.Int(f'h{i}') for i in range(n)]
        role=[z3.Int(f'role{i}') for i in range(n)]
        depth=[z3.Int(f'd{i}') for i in range(n)]
        root=self.ROLES['root'];subject=self.ROLES['subject'];obj=self.ROLES['object']
        for i in range(n):
            solver.add(choice[i]>=0,choice[i]<len(readings[i]),head[i]>=0,head[i]<n,
                       depth[i]>=0,depth[i]<n)
            options=[]
            for ri,r in enumerate(readings[i]):
                if finite(r):
                    options.append(z3.And(choice[i]==ri,role[i]==root,head[i]==i,depth[i]==0))
                for j in range(n):
                    if i==j:continue
                    for rj,parent in enumerate(readings[j]):
                        common=[choice[i]==ri,choice[j]==rj,head[i]==j,depth[i]>depth[j]]
                        relations=[]
                        if r.pos in self.NOMINAL:
                            case=r.get('Case')
                            if finite(parent):
                                if case=='NOM' and agrees(r,parent,('Number',)):
                                    person=r.get('Person') or '3'
                                    if parent.get('Person') in (None,'0','X',person):relations.append('subject')
                                if case=='ACC' and parent.get('Voice')!='PASSIVE' and self.adapter.frame(tokens[j])!='intransitive':
                                    relations.append('object')
                                if case in {'ACC','ABL'}:relations.append('oblique')
                            if case=='GEN' and parent.pos in self.NOMINAL:relations.append('genitive')
                        if r.pos in {'ADJ','VPAR'} and parent.pos in self.NOMINAL and agrees(r,parent,('Case','Number','Gender')):
                            relations.append('modifier')
                        if r.pos=='PREP' and parent.pos in self.NOMINAL and parent.get('Case') in self.adapter.government(tokens[i]) and i<j:
                            relations.append('case')
                        if r.pos=='ADV' and finite(parent):relations.append('adverb')
                        if relations:options.append(z3.And(*common,z3.Or([role[i]==self.ROLES[v] for v in relations])))
            solver.add(z3.Or(options))
            # Obliques must have exactly one licensed preposition; a preposition
            # cannot discharge the obligations of two separate nominal heads.
            prep_children=[z3.And(head[k]==i,role[k]==self.ROLES['case']) for k in range(n) if k!=i]
            solver.add(z3.Implies(role[i]==self.ROLES['oblique'],z3.Sum([z3.If(c,1,0) for c in prep_children])==1))
            solver.add(z3.Implies(role[i]!=self.ROLES['oblique'],z3.Not(z3.Or(prep_children))))
        solver.add(z3.PbEq([(r==root,1) for r in role],1),
                   z3.PbLe([(r==subject,1) for r in role],1),
                   z3.PbLe([(r==obj,1) for r in role],1))
        status=solver.check()
        if status==z3.unknown:return ClauseResult('unresolved',tokens,reason=solver.reason_unknown())
        if status==z3.unsat:return ClauseResult('no_parse',tokens,reason='no complete analysis in the restricted grammar')
        model=solver.model();selected=[];role_names={v:k for k,v in self.ROLES.items()}
        for i in range(n):
            rr=readings[i][model.eval(choice[i]).as_long()]
            selected.append({'position':i,'surface':tokens[i],'pos':rr.pos,'features':dict(rr.features),
                'head':model.eval(head[i]).as_long(),'role':role_names[model.eval(role[i]).as_long()]})
        # This is an ambiguity flag only; alternative analyses never add reward.
        solver.add(z3.Or([v!=model.eval(v) for v in choice+head+role]))
        alternative=solver.check()
        return ClauseResult('supported',tokens,tuple(selected),None if alternative==z3.unknown else alternative==z3.sat,
            'alternative check unresolved' if alternative==z3.unknown else '')

    def score(self, tokens, *, supplied_boundaries=None):
        tokens=tuple(tokens);n=len(tokens)
        if not n:return StreamResult('unsupported',None,(),(),0,0,{},0)
        if supplied_boundaries is not None:
            ends=tuple(supplied_boundaries)
            if not ends or ends[-1]!=n or any(a>=b for a,b in zip((0,)+ends,ends)):
                raise ValueError('Boundaries must partition every token exactly')
            clauses=[];start=0
            for end in ends:clauses.append(self.clause(tokens[start:end]));start=end
            status='supported' if all(c.status=='supported' for c in clauses) else (
                'unresolved' if any(c.status=='unresolved' for c in clauses) else
                'unsupported' if any(c.status=='unsupported' for c in clauses) else 'no_parse')
            complete=status=='supported'
            return StreamResult(status,-len(clauses) if complete else None,ends,tuple(clauses),
                sum(len(c.tokens) for c in clauses if c.status=='supported'),n,
                {'complete_analysis':0,'boundary':-len(clauses)} if complete else {})
        # Only fully analyzed clauses are edges. There is no skip/UNKNOWN edge.
        best={0:(0,(),())};unresolved=0
        saw_unsupported=False
        for end in range(1,n+1):
            for start in range(max(0,end-self.max_clause),end):
                if start not in best:continue
                clause=self.clause(tokens[start:end])
                unresolved+=clause.status=='unresolved';saw_unsupported|=clause.status=='unsupported'
                if clause.status!='supported':continue
                score,ends,clauses=best[start];candidate=(score-1,ends+(end,),clauses+(clause,))
                if end not in best or candidate[0]>best[end][0]:best[end]=candidate
        if n not in best:
            status='unresolved' if unresolved else 'unsupported' if saw_unsupported else 'no_parse'
            return StreamResult(status,None,(),(),0,n,{},unresolved)
        score,ends,clauses=best[n]
        # A timed-out candidate could alter the optimal segmentation.
        status='unresolved' if unresolved else 'supported'
        return StreamResult(status,score,ends,clauses,n,n,{'complete_analysis':0,'boundary':score},unresolved)


def validate_clause(result, adapter):
    """Check a solver's complete attachment witness without invoking Z3."""
    if result.status!='supported':raise ValueError('A supported witness is required')
    rows=result.analyses;n=len(result.tokens)
    assert len(rows)==n and {r['position'] for r in rows}==set(range(n))
    readings=[MorphAnalysis(r['pos'],tuple(sorted(r['features'].items()))) for r in rows]
    for i,(row,reading) in enumerate(zip(rows,readings)):
        assert row['surface']==result.tokens[i] and row['position']==i
        assert reading in adapter.analyze(result.tokens[i])
    roots=[i for i,r in enumerate(rows) if r['role']=='root']
    assert len(roots)==1
    root=roots[0];assert finite(readings[root]) and rows[root]['head']==root
    assert sum(r['role']=='subject' for r in rows)<=1 and sum(r['role']=='object' for r in rows)<=1
    for i,row in enumerate(rows):
        if i==root:continue
        head=row['head'];assert 0<=head<n and head!=i
        a,b=readings[i],readings[head];role=row['role']
        if role=='subject':
            assert a.pos in CoherentGrammar.NOMINAL and a.get('Case')=='NOM' and head==root
            assert agrees(a,b,('Number',)) and b.get('Person') in (None,'0','X',a.get('Person') or '3')
        elif role=='object':
            assert a.pos in CoherentGrammar.NOMINAL and a.get('Case')=='ACC' and head==root
            assert b.get('Voice')!='PASSIVE' and adapter.frame(result.tokens[head])!='intransitive'
        elif role=='oblique':
            assert a.pos in CoherentGrammar.NOMINAL and a.get('Case') in {'ACC','ABL'} and head==root
        elif role=='modifier':
            assert a.pos in {'ADJ','VPAR'} and b.pos in CoherentGrammar.NOMINAL
            assert agrees(a,b,('Case','Number','Gender'))
        elif role=='case':
            assert a.pos=='PREP' and b.pos in CoherentGrammar.NOMINAL and i<head
            assert b.get('Case') in adapter.government(result.tokens[i])
        elif role=='genitive':
            assert a.pos in CoherentGrammar.NOMINAL and a.get('Case')=='GEN' and b.pos in CoherentGrammar.NOMINAL
        elif role=='adverb':assert a.pos=='ADV' and head==root
        else:raise AssertionError('Unsupported dependency role')
        seen=set();cursor=i
        while cursor!=root:
            assert cursor not in seen;seen.add(cursor);cursor=rows[cursor]['head']
    for i,row in enumerate(rows):
        children=[r for r in rows if r['head']==i and r['role']=='case']
        assert len(children)==(1 if row['role']=='oblique' else 0)
    return True
