from dataclasses import replace
import pytest
from voynich_smt.coherent_grammar import CoherentGrammar,validate_clause
from voynich_smt.grammar_diagnostic import MorphAnalysis


def reading(pos,**features):return MorphAnalysis(pos,tuple(sorted(features.items())))


class Adapter:
    def __init__(self):
        self.lexicon={
            'noun':[reading('N',Case='NOM',Number='S',Gender='F')],
            'ambiguous':[reading('N',Case='NOM',Number=n,Gender='F') for n in ['S','P']],
            'adj':[reading('ADJ',Case='NOM',Number='S',Gender='F')],
            'verb':[reading('V',Mood='IND',Person='3',Number='S',Voice='ACTIVE')],
            'plural':[reading('V',Mood='IND',Person='3',Number='P',Voice='ACTIVE')],
            'acc':[reading('N',Case='ACC',Number='S',Gender='F')],
            'abl':[reading('N',Case='ABL',Number='S',Gender='F')],
            'gen':[reading('N',Case='GEN',Number='S',Gender='F')],
            'prep':[reading('PREP')],
            'participle':[reading('VPAR',Case='NOM',Number='S',Gender='F')],
            'first':[reading('V',Mood='IND',Person='1',Number='S',Voice='ACTIVE')],
            'ego':[reading('PRON',Case='NOM',Number='S',Person='1')],
        }
    def analyze(self,w):return tuple(self.lexicon.get(w,()))
    def government(self,w):return ('ACC',) if w=='prep' else ()
    def frame(self,w):return 'optional-object'


def grammar():return CoherentGrammar(Adapter())


def test_single_consistent_reading_prevents_independent_agreement_escape():
    g=grammar()
    assert g.clause(('ambiguous','adj','verb')).status=='supported'
    # Each constraint is independently satisfiable, but no one reading of
    # ambiguous can agree with both the singular modifier and plural verb.
    assert g.clause(('ambiguous','adj','plural')).status=='no_parse'


def test_parse_witness_and_tampering():
    g=grammar();r=g.clause(('noun','adj','verb'))
    assert validate_clause(r,g.adapter)
    changed=[dict(a) for a in r.analyses];changed[1]['head']=1
    with pytest.raises(AssertionError):validate_clause(replace(r,analyses=tuple(changed)),g.adapter)


def test_government_cannot_share_one_preposition_or_nominal_head():
    g=grammar()
    assert g.clause(('noun','prep','acc','verb')).status=='supported'
    assert g.clause(('noun','prep','abl','verb')).status=='no_parse'
    assert g.clause(('noun','prep','prep','acc','verb')).status=='no_parse'
    assert g.clause(('noun','abl','verb')).status=='no_parse'


def test_no_predicate_or_unattached_fragment_cannot_be_dropped():
    g=grammar()
    assert g.score(('noun','participle')).status=='no_parse'
    assert g.score(('noun','plural')).status=='no_parse'
    assert g.score(('unknown','verb')).status=='unsupported'
    assert g.score(('noun','noun','verb')).status=='no_parse'


def test_full_coverage_latent_segmentation_and_supplied_partition():
    g=grammar();tokens=('noun','verb','noun','verb')
    for result in [g.score(tokens),g.score(tokens,supplied_boundaries=[2,4])]:
        assert result.status=='supported' and result.covered_tokens==4
        assert result.boundaries==(2,4) and result.score==-2
        assert tuple(w for c in result.clauses for w in c.tokens)==tokens
    for boundaries in [[2],[2,2,4],[0,4],[5]]:
        with pytest.raises(ValueError):g.score(tokens,supplied_boundaries=boundaries)


def test_omitted_subject_and_person_agreement():
    g=grammar()
    assert g.clause(('verb',)).status=='supported'
    assert g.clause(('ego','first')).status=='supported'
    assert g.clause(('noun','first')).status=='no_parse'
    assert g.clause(('ego','verb')).status=='no_parse'


def test_duplicate_analyses_have_no_reward_and_alternative_is_reported():
    g=grammar();old=g.score(('noun','adj','verb'))
    g.adapter.lexicon['noun']*=10;g.clause.cache_clear()
    new=g.score(('noun','adj','verb'))
    assert new.score==old.score and new.boundaries==old.boundaries
    g.adapter.lexicon['adj'].append(reading('ADJ',Case='NOM',Number='S',Gender='X'))
    g.clause.cache_clear()
    assert g.clause(('noun','adj','verb')).alternative_found


def test_cycle_prevention_and_length_limit():
    g=grammar()
    # Two genitives cannot attach to each other as a disconnected cycle.
    assert g.clause(('gen','gen','verb')).status=='no_parse'
    assert g.clause(('verb',)*11).status=='unsupported'
    assert g.score(()).status=='unsupported'
