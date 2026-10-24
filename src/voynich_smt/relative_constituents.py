"""Bounded nominal constituency and one-step nonfinite relative bridges.

This is an explicit construction grammar, not a complete Latin parser. All
lexical additions are declared below; none comes from evaluation annotations.
"""
from dataclasses import asdict
from functools import lru_cache
from itertools import product
from .grammar_diagnostic import MorphAnalysis, LatinAdapter
from .relative_bridge import RELATIVES, finite

# First dictionary roots, not surface-form guesses. X remains unsupported except
# for these declared construction frames. Modal licenses are a separate inventory.
OBJECT_ROOTS = frozenset(('hab', 'loc'))
MODAL_ROOTS = frozenset(('deb', 'poss'))


class ConstituentAdapter(LatinAdapter):
    @lru_cache(maxsize=100000)
    def analyze(self, word):
        try:
            parsed = self.analyzer.engine.parse(word)
        except KeyError as error:
            if error.args != ('PACK',):
                raise
            return ()
        result = set()
        for form in parsed.forms:
            for analysis in form.analyses.values():
                lexeme = analysis.lexeme
                for inflection in analysis.inflections:
                    features = {k: v.name for k,v in inflection.features.items()}
                    if inflection.wordType.name in ('V','VPAR'):
                        features['VerbKind'] = (getattr(lexeme,'form',None) or ['UNKNOWN'])[0]
                        features['VerbRoot'] = lexeme.roots[0] if lexeme.roots else ''
                    result.add(MorphAnalysis(inflection.wordType.name,tuple(sorted(features.items()))))
        return tuple(sorted(result))


def compatible(adapter, a, b):
    return adapter.agrees(a,b,('Case','Number','Gender'))


def _grounded_phrases(tokens, marker, head, noun, adapter, allowed_gap=(), radius=16):
    """A single head, agreeing modifiers, genitives and simple PP modifiers.

    At most three tokens precede the head. The span ends at the marker, or
    immediately before a gap consisting solely of the specified governors.
    Conjunctions join modifiers, not an unbounded set of competing nominal heads.
    Returned token analyses are joint witnesses; no independently mixed readings.
    """
    lattice = [adapter.analyze(w) for w in tokens]
    lower = max(0, marker-radius)
    # An adjectival homograph immediately after a compatible unambiguous noun
    # cannot discard that noun and claim to be the head of the suffix alone.
    if head and any(r.pos in ('ADJ','VPAR','NUM') and compatible(adapter,r,noun) for r in lattice[head]):
        previous=lattice[head-1]
        if (not any(r.pos in ('ADJ','VPAR','NUM') for r in previous) and
                any(r.pos=='N' and compatible(adapter,r,noun) for r in previous)):
            return []
    results = []
    for end in range(head+1,marker+1):
        if not set(range(end,marker)).issubset(set(allowed_gap)):
            continue
        for start in range(max(lower,head-3),head+1):
            argument_prep = None
            first = start
            if start<head and tokens[start] in adapter.GOVERNMENT and any(r.pos=='PREP' for r in lattice[start]):
                if noun.get('Case') not in adapter.GOVERNMENT[tokens[start]]:
                    continue
                argument_prep = start
                first += 1
            if first>head:
                continue
            # Prefix: only agreeing determiners/adjectives/participles or genitives.
            chosen = {head:noun}
            if argument_prep is not None:
                chosen[argument_prep] = next(r for r in lattice[argument_prep] if r.pos=='PREP')
            good = True
            agreeing_support = False
            for pos in range(first,head):
                candidates = [r for r in lattice[pos] if r.pos in ('ADJ','NUM','PRON','VPAR') and compatible(adapter,r,noun)]
                if candidates:
                    chosen[pos]=candidates[0];agreeing_support=True
                else:
                    candidates=[r for r in lattice[pos] if r.pos=='N' and r.get('Case')=='GEN']
                    if not candidates:
                        good=False;break
                    chosen[pos]=candidates[0]
            if not good:
                continue
            # Suffix has no alternate full nominal head: genitive nouns only.
            pos=head+1
            while pos<end:
                if tokens[pos] in ('et','uel','que'):
                    if pos==head+1 or pos+1==end or tokens[pos-1] in ('et','uel','que'):
                        good=False;break
                    readings=[r for r in lattice[pos] if r.pos=='CONJ']
                    if not readings:
                        good=False;break
                    chosen[pos]=readings[0];pos+=1;continue
                candidates=[r for r in lattice[pos] if r.pos in ('ADJ','NUM','PRON','VPAR') and compatible(adapter,r,noun)]
                if candidates:
                    chosen[pos]=candidates[0];agreeing_support=True;pos+=1;continue
                candidates=[r for r in lattice[pos] if r.pos=='N' and r.get('Case')=='GEN']
                if candidates:
                    chosen[pos]=candidates[0];pos+=1;continue
                if tokens[pos] in adapter.GOVERNMENT and pos+1<end:
                    preps=[r for r in lattice[pos] if r.pos=='PREP']
                    objects=[r for r in lattice[pos+1] if r.pos=='N' and r.get('Case') in adapter.GOVERNMENT[tokens[pos]]]
                    if preps and objects:
                        chosen[pos]=preps[0];chosen[pos+1]=objects[0];pos+=2;continue
                good=False;break
            if not good:
                continue
            # PREP/CONJ/ADV homographs need positive modifier support for N usage.
            if any(r.pos in ('PREP','CONJ','ADV') for r in lattice[head]) and not agreeing_support:
                continue
            results.append({'start':start,'end':end,'head':head,'argument_preposition':argument_prep,
                'analyses':{str(p):asdict(r) for p,r in sorted(chosen.items())}})
    return results


def noun_phrases(tokens, marker, head, noun, adapter, allowed_gap=(), radius=16, pronoun=None):
    """Bind wildcard/common genders once across the entire nominal constituent."""
    gender=lambda r: {'M','F'} if r.get('Gender')=='C' else {'M','F','N'} if r.get('Gender') in (None,'X','0') else {r.get('Gender')}
    number=lambda r: {'S','P'} if r.get('Number') in (None,'X','0') else {r.get('Number')}
    genders=gender(noun);numbers=number(noun)
    if pronoun is not None:
        genders &= gender(pronoun);numbers &= number(pronoun)
    result=[]
    for g,n in product(sorted(genders),sorted(numbers)):
        features=dict(noun.features);features.update(Gender=g,Number=n)
        bound=MorphAnalysis(noun.pos,tuple(sorted(features.items())))
        for phrase in _grounded_phrases(tokens,marker,head,bound,adapter,allowed_gap,radius):
            phrase['analyses'][str(head)]=asdict(noun)
            phrase['agreement']={'Gender':g,'Number':n}
            result.append(phrase)
    return result


def argument(noun, verb, tokens, head, adapter, *, prep=None, object_frames=False):
    if prep is not None:
        if noun.get('Case') in adapter.GOVERNMENT.get(tokens[prep],()):
            return 'prepositional_oblique'
        return None
    person = '1' if tokens[head] in ('ego','nos') else '2' if tokens[head] in ('tu','uos','vos') else '3'
    if finite(verb) and noun.get('Case')=='NOM' and noun.get('Number')==verb.get('Number') and verb.get('Person')==person:
        return 'subject'
    transitive = verb.get('VerbKind')=='TRANS' or (object_frames and verb.get('VerbRoot') in OBJECT_ROOTS)
    if noun.get('Case')=='ACC' and transitive and verb.get('Voice')=='ACTIVE':
        return 'object'
    if noun.get('Case')=='ABL' and verb.get('Voice')=='PASSIVE' and verb.get('VerbKind')!='DEP':
        return 'passive_instrument'
    return None


def infer(tokens, predicates, marker, child, adapter, *, scopes=(), boundaries=(),
          constituents=True, nonfinite=False, object_frames=False, radius=16):
    """Return all feasible head/path pairs; do not break ties using annotations."""
    empty=lambda status:{'status':status,'parents':[],'antecedents':[],'chains':[]}
    if tokens[marker] not in RELATIVES or marker>=child or child not in predicates:
        return empty('unsupported')
    lattice=[adapter.analyze(w) for w in tokens]
    segment=lambda p:sum(p>=end for end in boundaries)
    island=lambda p:marker<=p<=child
    other=[(min(m,c),max(m,c)) for m,c in scopes if (m,c)!=(marker,child)]
    witnesses={}
    for head in range(max(0,marker-radius),marker):
        if head in predicates or tokens[head] in RELATIVES or segment(head)!=segment(marker):
            continue
        nouns=[r for r in lattice[head] if r.pos in ('N','PRON')]
        for parent in predicates:
            if island(parent) or segment(parent)!=segment(marker):
                continue
            if any((lo<=head<=hi)!=(lo<=parent<=hi) for lo,hi in other):
                continue
            if any(min(head,parent)<p<max(head,parent) and not island(p) for p in predicates):
                continue
            paths=[(None,None)]
            if nonfinite:
                for via in range(max(0,min(head,parent)-radius),min(len(tokens),max(head,parent)+radius+1)):
                    if island(via) or segment(via)!=segment(marker) or via in predicates:
                        continue
                    if any((lo<=head<=hi)!=(lo<=via<=hi) for lo,hi in other):
                        continue
                    if any(min(via,parent)<p<max(via,parent) and not island(p) for p in predicates):
                        continue
                    for reading in lattice[via]:
                        if reading.pos=='VPAR' and reading.get('Case')=='NOM' and reading.get('Voice')=='ACTIVE':
                            paths.append((via,reading))
                        elif reading.pos=='V' and reading.get('Mood')=='INF' and reading.get('Voice')=='ACTIVE':
                            paths.append((via,reading))
            for pron,noun,cv,pv in product(lattice[marker],nouns,lattice[child],lattice[parent]):
                if pron.pos!='PRON' or not finite(cv) or not finite(pv) or not adapter.agrees(pron,noun,('Gender','Number')):
                    continue
                relative_prep=marker-1 if marker and tokens[marker-1] in adapter.GOVERNMENT else None
                relative_role=argument(pron,cv,tokens,marker,adapter,prep=relative_prep,object_frames=object_frames)
                if not relative_role:
                    continue
                for via,vr in paths:
                    if via is not None:
                        if vr.pos=='VPAR':
                            if vr.get('Number')!=pv.get('Number') or pv.get('Person')!='3':
                                continue
                            # Explicit shared nominative; the same chosen subject
                            # agrees with the participle and finite governor.
                            subjects=[(p,r) for p in range(max(0,via-8),min(len(tokens),via+9))
                                if p!=head and p!=via and p not in predicates and not island(p) and segment(p)==segment(parent)
                                and not any(min(p,parent)<f<max(p,parent) and not island(f) for f in predicates)
                                for r in lattice[p] if r.pos in ('N','PRON') and r.get('Case')=='NOM'
                                and adapter.agrees(r,vr,('Number','Gender'))
                                and argument(r,pv,tokens,p,adapter)=='subject']
                            if not subjects:
                                continue
                        else:
                            if pv.get('VerbRoot') not in MODAL_ROOTS:
                                continue
                            subjects=[(None,None)]
                        governing_verb=vr
                    else:
                        subjects=[(None,None)];governing_verb=pv
                    phrases=(noun_phrases(tokens,marker,head,noun,adapter,
                        allowed_gap=(parent,) if via is None else (parent,via),radius=radius,pronoun=pron) if constituents else
                        [{'start':head,'end':head+1,'head':head,'argument_preposition':head-1 if head and tokens[head-1] in adapter.GOVERNMENT else None,
                          'analyses':{str(head):asdict(noun)}}])
                    for phrase in phrases:
                        # A governor cannot simultaneously be selected as a noun
                        # modifier inside this very witness.
                        if any(phrase['start']<=p<phrase['end'] for p in (*predicates,via) if p is not None):
                            continue
                        governing_role=argument(noun,governing_verb,tokens,head,adapter,
                            prep=phrase['argument_preposition'],object_frames=object_frames)
                        if not governing_role:
                            continue
                        for subject,sr in subjects:
                            if subject is not None and phrase['start']<=subject<phrase['end']:
                                continue
                            key=(head,via,parent,phrase['start'],phrase['end'],subject,tuple(sorted(phrase.get('agreement',{}).items())))
                            witnesses.setdefault(key,{'antecedent':head,'via':via,'parent':parent,'noun':asdict(noun),
                                'pronoun':asdict(pron),'child_verb':asdict(cv),'parent_verb':asdict(pv),
                                'nonfinite_verb':asdict(vr) if vr else None,'subject':subject,'subject_reading':asdict(sr) if sr else None,
                                'phrase':phrase,'relative_role':relative_role,'governing_role':governing_role})
    chains=list(witnesses.values());parents=sorted({w['parent'] for w in chains});heads=sorted({w['antecedent'] for w in chains})
    return {'status':'unique_chain' if len({(w['antecedent'],w['via'],w['parent']) for w in chains})==1 else 'ambiguous' if chains else 'no_bridge',
        'parents':parents,'antecedents':heads,'chains':chains}
