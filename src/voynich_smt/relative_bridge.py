"""Bounded local relative bridge; feasibility witnesses, not complete parses.

Inputs contain tokens, finite positions and marker-to-child scopes only. No gold
nominal heads or parent arcs enter inference. Unknown valency abstains on objects.
"""
from dataclasses import asdict
from functools import lru_cache
from itertools import product
from .grammar_diagnostic import LatinAdapter, MorphAnalysis

RELATIVES = frozenset('qui quae quod quem quam cuius cui quo qua quorum quarum quibus quos quas'.split())


class BridgeAdapter(LatinAdapter):
    @lru_cache(maxsize=100000)
    def analyze(self, word):
        result = set()
        try:
            parsed = self.analyzer.engine.parse(word)
        except KeyError as error:
            if error.args != ('PACK',):
                raise
            return ()
        for form in parsed.forms:
            for analysis in form.analyses.values():
                kind = (getattr(analysis.lexeme, 'form', None) or ['UNKNOWN'])[0]
                for inflection in analysis.inflections:
                    features = {k: v.name for k, v in inflection.features.items()}
                    if inflection.wordType.name == 'V':
                        features['VerbKind'] = kind
                    result.add(MorphAnalysis(inflection.wordType.name, tuple(sorted(features.items()))))
        return tuple(sorted(result))


def finite(r):
    return r.pos == 'V' and r.get('Mood') in ('IND', 'SUB', 'IMP')


def role(reading, verb, tokens, position, adapter):
    """A deliberately partial argument inventory; unknown is not evidence."""
    case = reading.get('Case')
    if position and tokens[position-1] in adapter.GOVERNMENT:
        if case in adapter.GOVERNMENT[tokens[position-1]] and any(r.pos == 'PREP' for r in adapter.analyze(tokens[position-1])):
            return 'prepositional_oblique'
        return None
    person = '1' if tokens[position] in ('ego','nos') else '2' if tokens[position] in ('tu','uos','vos') else '3'
    if case == 'NOM' and reading.get('Number') == verb.get('Number') and verb.get('Person') == person:
        return 'subject'
    if case == 'ACC' and verb.get('VerbKind') == 'TRANS' and verb.get('Voice') == 'ACTIVE':
        return 'object'
    if case == 'ABL' and verb.get('Voice') == 'PASSIVE' and verb.get('VerbKind') != 'DEP':
        return 'passive_instrument'
    return None


def bridge(tokens, predicates, marker, child, adapter, *, scopes=(), boundaries=(), radius=8, consistent=True):
    """Enumerate witnesses; publish a parent only when all witnesses agree.

    Minimal marker..child intervals are opaque, not inferred complete clauses.
    A direct nominal governor cannot cross another exposed finite predicate.
    `consistent=False` is the explicit mixed-reading diagnostic ablation.
    """
    if tokens[marker] not in RELATIVES or child not in predicates or marker >= child:
        return {'status': 'unsupported', 'parents': [], 'bridges': []}
    inside = lambda i, lo, hi: lo <= i <= hi
    island = (marker, child)
    other = [(min(m,c),max(m,c)) for m,c in scopes if (m,c) != (marker,child)]
    segment = lambda i: sum(i >= end for end in boundaries)
    readings = [adapter.analyze(w) for w in tokens]
    witnesses = {}
    for ant in range(max(0,marker-radius),marker):
        if tokens[ant] in RELATIVES or segment(ant) != segment(marker):
            continue
        for governor in predicates:
            if inside(governor,*island) or segment(governor) != segment(marker):
                continue
            if any(inside(ant,*span) != inside(governor,*span) for span in other):
                continue
            if any(min(ant,governor) < p < max(ant,governor) and not inside(p,*island) for p in predicates):
                continue
            for pron, noun, cv, gv in product(readings[marker],readings[ant],readings[child],readings[governor]):
                if pron.pos != 'PRON' or noun.pos not in ('N','PRON') or not finite(cv) or not finite(gv):
                    continue
                if not adapter.agrees(pron,noun,('Gender','Number')):
                    continue
                relative_role = role(pron,cv,tokens,marker,adapter)
                if not relative_role:
                    continue
                governing_readings = (noun,) if consistent else [r for r in readings[ant] if r.pos in ('N','PRON')]
                for governing_noun in governing_readings:
                    governing_role = role(governing_noun,gv,tokens,ant,adapter)
                    if governing_role:
                        witnesses.setdefault((ant,governor),{'antecedent':ant,'governor':governor,
                            'pronoun':asdict(pron),'nominal':asdict(noun),'governing_nominal':asdict(governing_noun),
                            'child_verb':asdict(cv),'governing_verb':asdict(gv),
                            'relative_role':relative_role,'governing_role':governing_role})
    parents = sorted({g for a,g in witnesses})
    return {'status':'unique_parent' if len(parents)==1 else 'ambiguous' if parents else 'no_bridge',
        'parents':parents,'bridges':list(witnesses.values())}
