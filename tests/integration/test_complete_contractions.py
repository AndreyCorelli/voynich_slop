import pytest

from voynich_smt.language.contractions import expand_units, tokenizations, tokenize_dictionary
from benchmarks.latin_contractions import unitizations


def test_equal_length_paths_survive_and_optional_overlaps_are_complete():
    rules = [{'id':'ae','expansion':'ae','position':'any'},
             {'id':'ea','expansion':'ea','position':'any'}]
    paths = tokenizations('aea',rules)
    assert set(paths)=={('a','e','a'),('<ae>','a'),('a','<ea>')}
    assert all(expand_units(p,rules)=='aea' for p in paths)
    assert {len(p) for p in paths}==set(unitizations('aea',rules))
    with pytest.raises(ValueError,match='exceeds'):
        tokenizations('aea',rules,max_variants=2)


def test_positions_and_dictionary_round_trips():
    rules=[{'id':'con','expansion':'con','position':'initial'},
           {'id':'rum','expansion':'rum','position':'final'},
           {'id':'et','expansion':'et','position':'whole'}]
    words=('conrum','acon','ruma','et','eta')
    paths=tokenize_dictionary(words,rules)
    assert {expand_units(p,rules) for p in paths}==set(words)
    assert ('<con>','<rum>') in paths
    assert tokenizations('acon',rules)==(tuple('acon'),)
    assert tokenizations('ruma',rules)==(tuple('ruma'),)
    assert tokenizations('eta',rules)==(tuple('eta'),)
    with pytest.raises(ValueError,match='Unknown'):
        expand_units(('<unknown>',),rules)


def test_duplicate_ids_and_invalid_inputs_rejected():
    rule={'id':'ae','expansion':'ae','position':'any'}
    with pytest.raises(ValueError,match='Duplicate'):
        tokenizations('ae',[rule,rule])
    with pytest.raises(ValueError):
        tokenizations('a e',[rule])


def test_hidden_recovery_requires_contraction_for_one_glyph_word():
    from dataclasses import asdict
    from benchmarks.l3_conflict import verify
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.alphabet import Alphabet
    from voynich_smt.models.text import Text
    from voynich_smt.solver.observed_codes import recover_observed_codes

    rules=[{'id':'ae','expansion':'ae','position':'any'}]
    def request(words):
        return HiddenRecoveryRequest(Text.from_string('x'),Alphabet(('a','e','<ae>')),
            Alphabet(tuple('xyz')),Bounds('verbose',2,1,3),WordDictionary(words),timeout_ms=1000)
    bare=request((tuple('ae'),))
    assert recover_observed_codes(bare).status=='UNSAT'
    mixed=request(tokenize_dictionary(('ae',),rules))
    result=asdict(recover_observed_codes(mixed))
    assert result['status']=='SAT'
    verify(mixed,result)
    assert result['plaintext']['words']==(('<ae>',),)
    assert expand_units(result['plaintext']['words'][0],rules)=='ae'
