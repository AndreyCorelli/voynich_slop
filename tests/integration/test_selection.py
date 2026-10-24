from dataclasses import asdict
from itertools import permutations, product

import pytest

from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import choose
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection, NullBounds, Optimization
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover, recover_dictionary


def test_concrete_per_letter_cycles_and_resets():
    key = Encoder({'a': (('x',), ('y',)), 'b': (('z',), ('w',), ('v',))})
    plain = Text.from_string('abab aabb')
    assert choose(plain, key, HomophoneSelection('cycle')) == (0,0,1,1,0,1,2,0)
    assert choose(plain, key, HomophoneSelection('cycle','word')) == (0,0,1,1,0,1,0,1)


@pytest.mark.parametrize('representation', ['finite','ite','array','interval','chunk'])
def test_cycle_accepts_non_lexical_key_order(representation):
    r = recover(Text.from_string('aaa'), Text.from_string('xzy'), Alphabet(('a',)), Alphabet(tuple('xyz')),
                Bounds('homophonic',3,1,1), representation=representation, selection=HomophoneSelection('cycle'))
    assert r.status == 'SAT' and r.verified
    assert r.encoder.codebook['a'] == (('x',),('z',),('y',))
    assert r.choices == (0,1,2)


def test_cycle_is_stricter_than_free_selection():
    args = (Text.from_string('aaa'), Text.from_string('xyy'), Alphabet(('a',)), Alphabet(tuple('xy')),
            Bounds('homophonic',2,1,1))
    assert recover(*args).status == 'SAT'
    assert recover(*args, selection=HomophoneSelection('cycle')).status == 'UNSAT'


def test_cycle_count_continues_across_spaces_unless_explicit_reset():
    args = (Text.from_string('a a'), Text.from_string('x y'), Alphabet(('a',)), Alphabet(tuple('xy')),
            Bounds('homophonic',2,1,1))
    assert recover(*args, selection=HomophoneSelection('cycle')).verified
    assert recover(*args, selection=HomophoneSelection('cycle','word')).status == 'UNSAT'


@pytest.mark.parametrize('optimization', [Optimization(), Optimization(True)])
def test_cycle_with_nulls_and_full_codebook_optimization(optimization):
    r = recover_dictionary(Text.from_string('xnynx'), Alphabet(('a',)), Alphabet(tuple('xyn')),
                           Bounds('homophonic',2,1,1), WordDictionary.from_strings(('aaa',)),
                           nulls=NullBounds(True,1,2,1), optimization=optimization,
                           selection=HomophoneSelection('cycle'))
    assert r.status == 'SAT' and r.verified
    assert r.choices == (0,1,0) and len(r.nulls) == 2
    if optimization.enabled:
        assert r.optimization['optimality_proven']


def test_hidden_variable_word_length_slots_do_not_count_as_occurrences():
    r = recover_dictionary(Text.from_string('x yz x'), Alphabet(tuple('ab')), Alphabet(tuple('xyz')),
                           Bounds('homophonic',2,1,1), WordDictionary.from_strings(('a','b','ab','ba')),
                           selection=HomophoneSelection('cycle'))
    assert r.status == 'SAT' and r.verified
    assert choose(r.plaintext, r.encoder, HomophoneSelection('cycle')) == r.choices


def test_tiny_cycle_outcomes_match_independent_exhaustive_oracle():
    codes = tuple('xyz')
    # Five appearances, at most three distinct length-one codes; order is arbitrary.
    legal = {''.join(key[i % count] for i in range(5))
             for count in range(1,4) for key in permutations(codes,count)}
    samples = [''.join(w) for w in product(codes, repeat=5)]
    for observed in samples[::5] + sorted(legal):
        r = recover(Text.from_string('aaaaa'), Text.from_string(observed), Alphabet(('a',)), Alphabet(codes),
                    Bounds('homophonic',3,1,1), selection=HomophoneSelection('cycle'))
        assert (r.status == 'SAT') == (observed in legal)
        if r.status == 'SAT':
            assert r.verified


def test_serialized_cycle_and_seeded_generation():
    template = HiddenRecoveryRequest(Text(()), Alphabet(tuple('ab')), Alphabet(tuple('xyz')),
               Bounds('verbose',2,1,2), WordDictionary.from_strings(('aaaa','abab','bbbb')),
               selection=HomophoneSelection('cycle'))
    public, truth = generate(template, 3, 7)
    assert HiddenRecoveryRequest.from_dict(asdict(public)).selection == template.selection
    assert public.solve().verified
    assert truth['generator']['selection'] == {'mode':'cycle','reset':'text'}
    assert generate(template, 3, 7) == (public,truth)
    malformed = asdict(public)
    malformed['selection']['initial_phase'] = 3
    with pytest.raises(ValueError):
        HiddenRecoveryRequest.from_dict(malformed)


@pytest.mark.parametrize('mode,reset', [('random','text'),('cycle','line'),('free','word')])
def test_invalid_selection(mode,reset):
    with pytest.raises(ValueError):
        HomophoneSelection(mode,reset)


def test_cycles_count_recovered_symbols_in_partial_domains():
    r = recover(Text.from_string('aaa'), Text.from_string('xyz'), Alphabet(tuple('ab')), Alphabet(tuple('xyz')),
                Bounds('homophonic',2,1,1), domains={1:('a','b'),2:('a','b')},
                selection=HomophoneSelection('cycle'))
    assert r.status=='SAT' and r.verified
    assert choose(r.plaintext,r.encoder,HomophoneSelection('cycle'))==r.choices


def test_two_letter_cycles_match_independent_ownership_oracle():
    glyphs=tuple('xyz')
    plaintext='ababa'
    legal=set()
    for na,nb in [(1,1),(1,2),(2,1)]:
        for allocation in permutations(glyphs,na+nb):
            code={'a':allocation[:na],'b':allocation[na:]}
            counters={'a':0,'b':0}; word=[]
            for p in plaintext:
                word.append(code[p][counters[p]%len(code[p])]);counters[p]+=1
            legal.add(''.join(word))
    for observed in [''.join(w) for w in product(glyphs,repeat=5)][::9]+sorted(legal):
        r=recover(Text.from_string(plaintext),Text.from_string(observed),Alphabet(tuple('ab')),Alphabet(glyphs),
                  Bounds('homophonic',2,1,1),selection=HomophoneSelection('cycle'))
        assert (r.status=='SAT') == (observed in legal)
        if r.status=='SAT':
            assert r.verified
