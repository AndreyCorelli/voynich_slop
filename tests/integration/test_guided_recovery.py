from dataclasses import replace
import pytest
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.guided import recover_guided


def request(text, words=('a','b'), maximum=1):
    return HiddenRecoveryRequest(Text.from_string(text),Alphabet(tuple('ab')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,maximum),WordDictionary.from_strings(words),selection=HomophoneSelection('cycle'))


def test_exact_pins_can_keep_unused_letters_and_unvisited_alternatives():
    q=request('x',('a',),maximum=3)
    key=Encoder({'a':(('x',),('y',)), 'b':(('z',),)})
    r=recover_guided(q,key,('a','b'))
    assert r.status=='SAT' and r.verified
    assert r.encoder.codebook==key.codebook
    assert r.capacity['pinned_symbols']==['a','b']


def test_rotations_align_suffix_key_with_earlier_cycle_phase():
    q=request('y x',('a',))
    key=Encoder({'a':(('x',),('y',)), 'b':(('z',),)})
    r=recover_guided(q,key,('a','b'))
    assert r.status=='UNSAT' and r.capacity['pinned_unsat_core']==['a']
    r=recover_guided(q,key,('a','b'),rotate=True)
    assert r.status=='SAT' and r.verified
    assert r.encoder.codebook['a']==(('y',),('x',))
    assert r.choices==(0,1)


def test_releasing_a_mapping_can_restore_a_full_verified_fit():
    q=request('x z',('a',))
    key=Encoder({'a':(('x',),('y',)), 'b':(('z',),)})
    assert recover_guided(q,key,('a','b'),rotate=True).status=='UNSAT'
    r=recover_guided(q,key,(),hint_symbols=('a',),word_hints={1:('a',)})
    assert r.status=='SAT' and r.verified
    assert r.capacity['pinned_symbols']==[]
    assert r.capacity['initial_value_hints']>0
    assert r.encoder.codebook['a']==(('x',),('z',))


def test_complete_text_cycle_can_fail_when_two_blocks_fit_separately():
    q=request('x y x',('a',))
    key=Encoder({'a':(('x',),('y',)), 'b':(('z',),)})
    assert recover_guided(q,key,('a','b')).verified
    bad=request('x x y',('a',))
    assert recover_guided(bad,key,('a','b'),rotate=True).status=='UNSAT'


@pytest.mark.parametrize('pins', [('a','a'),('c',)])
def test_bad_pins_rejected(pins):
    with pytest.raises(ValueError):recover_guided(request('x'),Encoder({'a':(('x',),),'b':(('y',),)}),pins)


def test_inadmissible_hints_and_guidance_modes_rejected():
    key=Encoder({'a':(('x',),),'b':(('y',),)})
    q=request('x')
    for kwargs in ({'word_hints':{-1:('a',)}},{'word_hints':{True:('a',)}}, {'word_hints':{0:('z',)}}):
        with pytest.raises(ValueError):recover_guided(q,key,**kwargs)
    with pytest.raises(ValueError):recover_guided(replace(q,representation='ite'),key)
    with pytest.raises(ValueError):recover_guided(replace(q,selection=HomophoneSelection()),key)


def test_guided_outcomes_match_independent_exhaustive_key_oracle():
    from itertools import permutations,product
    from voynich_smt.cipher.selection import choose
    keys=[]
    for order in permutations('xyz'):
        for a,b in ((1,1),(1,2),(2,1)):
            key=Encoder({'a':tuple((s,) for s in order[:a]),'b':tuple((s,) for s in order[a:a+b])})
            for letters in product('ab',repeat=3):
                plain=Text(tuple((s,) for s in letters))
                text=key.encode(plain,choose(plain,key,HomophoneSelection('cycle')))
                keys.append((key,text))
    seed=Encoder({'a':(('x',),('y',)),'b':(('z',),)})
    for pins in ((),('a',),('b',),('a','b')):
        for rotate in (False,True):
            def matches(key):
                for s in pins:
                    original=seed.codebook[s]
                    rotations=range(len(original)) if rotate else (0,)
                    if not any(key.codebook[s]==original[i:]+original[:i] for i in rotations):return False
                return True
            legal={text for key,text in keys if matches(key)}
            for ciphertext in product('xyz',repeat=3):
                q=request(' '.join(ciphertext))
                result=recover_guided(q,seed,pins,rotate=rotate,hint_symbols=('a','b'))
                assert result.status==('SAT' if q.ciphertext in legal else 'UNSAT')
                assert result.status!='SAT' or result.verified
                if result.status=='UNSAT' and pins:
                    core=result.capacity['pinned_unsat_core']
                    assert set(core)<=set(pins)
                    assert recover_guided(q,seed,core,rotate=rotate).status=='UNSAT'


def test_forced_cycle_certificate_is_rotation_independent_and_conservative():
    from voynich_smt.solver.guided import forced_cycle_conflicts
    key=Encoder({'a':(('x',),('y',)), 'b':(('z',),)})
    q=request('y x y y')
    certificates=forced_cycle_conflicts(q.ciphertext,key,('a',))
    assert certificates==[{'symbol':'a','word_indices':[0,1,2,3],
        'code_indices':[1,0,1,1],'codes':[['y'],['x'],['y'],['y']],
        'reason':'forced word-start appearances violate every cyclic rotation'}]
    assert recover_guided(q,key,('a',),rotate=True).status=='UNSAT'
    # Internal raw occurrences may be crossed by an unknown code: no certificate.
    assert forced_cycle_conflicts(Text.from_string('zx y x y y'),key,('a',))==[]
    assert forced_cycle_conflicts(Text.from_string('y x y x'),key,('a',))==[]


def test_word_reset_does_not_use_text_wide_cycle_pruning():
    key=Encoder({'a':(('x',),('y',)),'b':(('z',),)})
    q=replace(request('x x x',('a',)),selection=HomophoneSelection('cycle','word'))
    r=recover_guided(q,key,('a',))
    assert r.status=='SAT' and r.verified
    assert r.capacity['forced_cycle_conflicts']==[]
