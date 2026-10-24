"""Exact finite joint word/reading/parse inference for an explicit toy grammar.

This is a synthetic identifiability instrument, not a grammar of unrestricted Latin.
"""
from dataclasses import dataclass
from itertools import permutations, product
import time
import z3


@dataclass(frozen=True)
class Reading:
    pos: str
    case: str = '_'
    number: str = '_'
    gender: str = '_'
    valency: str = '_'
    government: str = '_'


@dataclass(frozen=True)
class Parse:
    roles: tuple
    heads: tuple
    requirements: tuple
    agreements: tuple
    governments: tuple


def syntax(length, max_adjectives=2, allow_pp=True, noun_attachment=False):
    """All constituent permutations and internal adjective positions; no gold tree."""
    results={}
    for kind in ('transitive','intransitive','copular'):
        core=('S','O','V') if kind=='transitive' else ('S','V') if kind=='intransitive' else ('S','A','V')
        for pp in (False,True) if allow_pp else (False,):
            parts=core+(('P',) if pp else ())
            nominal=[x for x in parts if x in ('S','O','P')]
            for sizes in product(range(1,max_adjectives+2),repeat=len(nominal)):
                sizes=dict(zip(nominal,sizes)); widths={p:sizes[p]+(p=='P') if p in sizes else 1 for p in parts}
                if sum(widths.values())!=length:continue
                for order in permutations(parts):
                    spans={};offset=0
                    for p in order:spans[p]=list(range(offset,offset+widths[p]));offset+=widths[p]
                    for choices in product(*(range(sizes[p]) for p in nominal)):
                        noun={p:spans[p][(p=='P')+i] for p,i in zip(nominal,choices)};root=spans['V'][0]
                        attachments=[root]
                        if pp and noun_attachment:attachments += [noun[p] for p in ('S','O') if p in noun]
                        for attachment in attachments:
                            roles=['']*length;heads=[-1]*length;requirements=[];agreements=[];governments=[]
                            roles[root]='root';requirements.append((root,'V','_',kind))
                            for p in nominal:
                                h=noun[p];roles[h]={'S':'nsubj','O':'obj','P':'obl' if attachment==root else 'nmod'}[p];heads[h]=attachment if p=='P' else root
                                case={'S':'NOM','O':'ACC','P':'_'}[p];requirements.append((h,'N',case,'_'))
                                for j in spans[p][(p=='P'):]:
                                    if j!=h:
                                        roles[j]='amod';heads[j]=h;requirements.append((j,'ADJ','_','_'));agreements.append((j,h,('case','number','gender')))
                                if p=='P':
                                    prep=spans[p][0];roles[prep]='case';heads[prep]=h;requirements.append((prep,'ADP','_','_'));governments.append((prep,h))
                            agreements.append((root,noun['S'],('number',)))
                            if kind=='copular':
                                a=spans['A'][0];roles[a]='xcomp';heads[a]=root;requirements.append((a,'ADJ','NOM','_'));agreements.append((a,noun['S'],('number','gender')))
                            parse=Parse(tuple(roles),tuple(heads),tuple(requirements),tuple(agreements),tuple(governments))
                            results[(parse.roles,parse.heads,parse.requirements)]=parse
    return list(results.values())


class JointGrammar:
    def __init__(self, lexicon, sentences, candidates=None, shared=True, injective=True,
                 max_adjectives=2, allow_pp=True, noun_attachment=False, timeout_ms=10000):
        self.lexicon=lexicon;self.sentences=sentences;self.solver=z3.Solver();self.solver.set(timeout=timeout_ms)
        self.words=sorted(lexicon);self.word_index={w:i for i,w in enumerate(self.words)}
        self.readings=sorted(set(r for rr in lexicon.values() for r in rr),key=repr)
        attrs=('pos','case','number','gender','valency','government')
        values={a:{v:i for i,v in enumerate(sorted({getattr(r,a) for r in self.readings}))} for a in attrs}
        self.mapping={};self.occurrences=[];self.structures=[];self.parse_counts=[]
        for si,sentence in enumerate(sentences):
            keys=[t if shared else (si,t) for t in sentence];variables=[]
            for key,t in zip(keys,sentence):
                if key not in self.mapping:
                    var=z3.Int('word_'+str(len(self.mapping)));self.mapping[key]=var
                    pool=self.words if candidates is None else candidates[t]
                    self.solver.add(z3.Or([var==self.word_index[w] for w in pool]))
                variables.append(self.mapping[key])
            if not shared and injective:self.solver.add(z3.Distinct([self.mapping[k] for k in set(keys)]))
            occ=[]
            for j,var in enumerate(variables):
                fields={a:z3.Int(f'{a}_{si}_{j}') for a in attrs};analysis=z3.Int(f'analysis_{si}_{j}')
                options=[]
                for w in self.words:
                    for r in lexicon[w]:
                        options.append(z3.And(var==self.word_index[w],analysis==self.readings.index(r),*[fields[a]==values[a][getattr(r,a)] for a in attrs]))
                self.solver.add(z3.Or(options));occ.append({'reading':analysis,**fields})
            self.occurrences.append(occ)
            parses=syntax(len(sentence),max_adjectives,allow_pp,noun_attachment);branches=[];rolevars=[z3.Int(f'role_{si}_{j}') for j in range(len(sentence))];headvars=[z3.Int(f'head_{si}_{j}') for j in range(len(sentence))]
            rolelabels=('root','nsubj','obj','amod','case','obl','nmod','xcomp')
            for parse in parses:
                clauses=[];possible=True
                for j,pos,case,valency in parse.requirements:
                    for attr,value in (('pos',pos),('case',case),('valency',valency)):
                        if value=='_':continue
                        if value not in values[attr]:possible=False;break
                        clauses.append(occ[j][attr]==values[attr][value])
                if not possible:continue
                for a,b,features in parse.agreements:
                    clauses.extend(occ[a][f]==occ[b][f] for f in features)
                for prep,noun in parse.governments:
                    # Government uses the selected prep analysis and selected noun case.
                    opts=[]
                    for case in ('ACC','ABL'):
                        if case in values['case'] and case in values['government']:
                            opts.append(z3.And(occ[prep]['government']==values['government'][case],occ[noun]['case']==values['case'][case]))
                    clauses.append(z3.Or(opts))
                clauses.extend(rolevars[j]==rolelabels.index(parse.roles[j]) for j in range(len(sentence)))
                clauses.extend(headvars[j]==parse.heads[j] for j in range(len(sentence)))
                branches.append(z3.And(clauses))
            self.solver.add(z3.Or(branches));self.parse_counts.append(len(branches));self.structures.extend(rolevars+headvars)
        if shared and injective:self.solver.add(z3.Distinct(list(self.mapping.values())))
        self.shared=shared;self.rolelabels=rolelabels

    def example(self, model):
        mapping={str(k):self.words[model.eval(v).as_long()] for k,v in self.mapping.items()};sentences=[];offset=0
        for si,s in enumerate(self.sentences):
            n=len(s);vs=self.structures[offset:offset+2*n];offset+=2*n
            words=[mapping[str(t if self.shared else (si,t))] for t in s]
            sentences.append({'words':words,'roles':[self.rolelabels[model.eval(v).as_long()] for v in vs[:n]],'heads':[model.eval(v).as_long() for v in vs[n:]],'readings':[self.readings[model.eval(o['reading']).as_long()].__dict__ for o in self.occurrences[si]]})
        return {'mapping':mapping,'sentences':sentences}

    def enumerate(self, projection='structure', limit=10000):
        variables=self.structures if projection=='structure' else list(self.mapping.values())
        self.solver.push();count=0;examples=[];started=time.perf_counter();status='limit';allvalues=[]
        while count<limit:
            result=self.solver.check()
            if result!=z3.sat:
                status='complete' if result==z3.unsat else 'unknown';break
            model=self.solver.model();vals=tuple(model.eval(v).as_long() for v in variables);allvalues.append(vals);count+=1
            if len(examples)<12:examples.append(self.example(model))
            self.solver.add(z3.Or([v!=value for v,value in zip(variables,vals)]))
        self.solver.pop()
        return {'count':count,'status':status,'elapsed_seconds':time.perf_counter()-started,'examples':examples,'projections':allvalues}

    def query_structure(self, roles, heads, different=False):
        vals=[]
        for rr,hh in zip(roles,heads):vals.extend(self.rolelabels.index(r) for r in rr);vals.extend(hh)
        assert len(vals)==len(self.structures)
        self.solver.push();conditions=[v==x for v,x in zip(self.structures,vals)]
        self.solver.add(z3.Not(z3.And(conditions)) if different else z3.And(conditions))
        result=self.solver.check();example=self.example(self.solver.model()) if result==z3.sat else None;self.solver.pop()
        return {'status':str(result),'example':example}

    def query_mapping(self, mapping):
        self.solver.push();self.solver.add(*[v==self.word_index[mapping[k]] for k,v in self.mapping.items()]);result=self.solver.check();self.solver.pop();return str(result)
