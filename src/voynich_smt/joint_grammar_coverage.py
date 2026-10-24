"""Coverage variants of the finite joint grammar; original experiment stays frozen."""
from dataclasses import dataclass
from functools import lru_cache
import z3
from voynich_smt.joint_grammar import JointGrammar,Parse,syntax

ROLE_LABELS=('root','nsubj','obj','amod','case','obl','nmod','xcomp','nmod:gen','cc','conj')


@dataclass(frozen=True)
class CandidateParse:
    parse: Parse
    features: tuple=()


def insert_genitive(parse,head,index):
    shift=lambda j:j+(j>=index) if j>=0 else j
    roles=list(parse.roles);roles.insert(index,'nmod:gen')
    heads=[shift(h) for h in parse.heads];heads.insert(index,shift(head))
    req=tuple((shift(j),*rest) for j,*rest in parse.requirements)+((index,'N','GEN','_'),)
    agree=tuple((shift(a),shift(b),f) for a,b,f in parse.agreements)
    gov=tuple((shift(a),shift(b)) for a,b in parse.governments)
    return Parse(tuple(roles),tuple(heads),req,agree,gov)


def omit_subject(parse):
    sub=parse.roles.index('nsubj');root=parse.roles.index('root')
    if any(h==sub for h in parse.heads) or any(r=='xcomp' for r in parse.roles):return None
    shift=lambda j:j-(j>sub) if j>=0 else j
    roles=tuple(r for i,r in enumerate(parse.roles) if i!=sub);heads=tuple(shift(h) for i,h in enumerate(parse.heads) if i!=sub)
    req=tuple((shift(j),*rest) for j,*rest in parse.requirements if j!=sub)
    agree=tuple((shift(a),shift(b),f) for a,b,f in parse.agreements if sub not in (a,b))
    gov=tuple((shift(a),shift(b)) for a,b in parse.governments if sub not in (a,b))
    return Parse(roles,heads,req,agree,gov)


def coordinate_subject(parse):
    sub=parse.roles.index('nsubj');root=parse.roles.index('root')
    # Predicate agreement for a coordinated group needs separate gender rules.
    # This fragment supports coordinated transitive/intransitive subjects only.
    if any(h==sub for h in parse.heads) or 'xcomp' in parse.roles:return None
    shift=lambda j:j+2*(j>sub) if j>=0 else j
    roles=list(parse.roles);roles[sub+1:sub+1]=['cc','conj']
    heads=[shift(h) for h in parse.heads];heads[sub+1:sub+1]=[sub+2,sub]
    req=tuple((shift(j),*rest) for j,*rest in parse.requirements)+((sub+1,'CC','_','_'),(sub+2,'N','NOM','_'))
    agree=tuple((shift(a),shift(b),f) for a,b,f in parse.agreements if (a,b)!=(root,sub))
    gov=tuple((shift(a),shift(b)) for a,b in parse.governments)
    return CandidateParse(Parse(tuple(roles),tuple(heads),req,agree,gov),((shift(root),'number','P'),))


@lru_cache(maxsize=128)
def coverage_syntax(length,broad=False,max_adjectives=0,allow_pp=False,noun_attachment=False):
    result=[CandidateParse(p) for p in syntax(length,max_adjectives,allow_pp,noun_attachment)]
    if broad:
        if length>=2:
            for p in syntax(length-1,max_adjectives,allow_pp,noun_attachment):
                for h,r in enumerate(p.roles):
                    if r in ('nsubj','obj','obl','nmod'):
                        for i in (h,h+1):result.append(CandidateParse(insert_genitive(p,h,i)))
        for p in syntax(length+1,max_adjectives,allow_pp,noun_attachment):
            omitted=omit_subject(p)
            if omitted is not None:result.append(CandidateParse(omitted))
        if length>=3:
            for p in syntax(length-2,max_adjectives,allow_pp,noun_attachment):
                coordinated=coordinate_subject(p)
                if coordinated is not None:result.append(coordinated)
    return tuple(dict.fromkeys(result))


class CoverageGrammar(JointGrammar):
    """Reuse projection/query methods; compile broader concrete parse candidates."""
    def __init__(self,lexicon,sentences,broad=False,max_adjectives=0,allow_pp=False,noun_attachment=False,timeout_ms=10000):
        self.lexicon=lexicon;self.sentences=sentences;self.shared=True;self.rolelabels=ROLE_LABELS
        self.words=sorted(lexicon);self.word_index={w:i for i,w in enumerate(self.words)}
        self.readings=sorted(set(r for rr in lexicon.values() for r in rr),key=repr)
        attrs=('pos','case','number','gender','valency','government')
        values={a:{v:i for i,v in enumerate(sorted({getattr(r,a) for r in self.readings}))} for a in attrs}
        self.mapping={};self.occurrences=[];self.structures=[];self.parse_counts=[]
        self.solver=z3.Solver();self.solver.set(timeout=timeout_ms)
        for si,s in enumerate(sentences):
            variables=[]
            for t in s:
                if t not in self.mapping:
                    self.mapping[t]=z3.Int('word_'+str(len(self.mapping)))
                    self.solver.add(self.mapping[t]>=0,self.mapping[t]<len(self.words))
                variables.append(self.mapping[t])
            occ=[]
            for j,var in enumerate(variables):
                fields={a:z3.Int(f'{a}_{si}_{j}') for a in attrs};analysis=z3.Int(f'analysis_{si}_{j}')
                options=[]
                for w in self.words:
                    for r in lexicon[w]:options.append(z3.And(var==self.word_index[w],analysis==self.readings.index(r),*[fields[a]==values[a][getattr(r,a)] for a in attrs]))
                self.solver.add(z3.Or(options));occ.append({'reading':analysis,**fields})
            self.occurrences.append(occ)
            rolevars=[z3.Int(f'role_{si}_{j}') for j in range(len(s))];headvars=[z3.Int(f'head_{si}_{j}') for j in range(len(s))];branches=[]
            for candidate in coverage_syntax(len(s),broad,max_adjectives,allow_pp,noun_attachment):
                p=candidate.parse;conditions=[];possible=True
                requirements=[(j,a,v) for j,pos,case,val in p.requirements for a,v in (('pos',pos),('case',case),('valency',val)) if v!='_']+list(candidate.features)
                for j,a,v in requirements:
                    if v not in values[a]:possible=False;break
                    conditions.append(occ[j][a]==values[a][v])
                if not possible:continue
                for a,b,fs in p.agreements:conditions.extend(occ[a][f]==occ[b][f] for f in fs)
                for prep,noun in p.governments:
                    opts=[z3.And(occ[prep]['government']==values['government'][case],occ[noun]['case']==values['case'][case]) for case in ('ACC','ABL') if case in values['government'] and case in values['case']]
                    conditions.append(z3.Or(opts))
                conditions.extend(v==self.rolelabels.index(r) for v,r in zip(rolevars,p.roles));conditions.extend(v==h for v,h in zip(headvars,p.heads));branches.append(z3.And(conditions))
            self.solver.add(z3.Or(branches));self.parse_counts.append(len(branches));self.structures.extend(rolevars+headvars)
        self.solver.add(z3.Distinct(list(self.mapping.values())))
