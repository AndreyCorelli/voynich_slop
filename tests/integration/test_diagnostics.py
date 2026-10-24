from dataclasses import replace
import pytest
from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.diagnostics import recover_observations


def request(text='a a a x'):
    return HiddenRecoveryRequest(Text.from_string(text), Alphabet(('a',)), Alphabet(tuple('axy')),
        Bounds('verbose',2,1,2), WordDictionary.from_strings(('a',)), selection=HomophoneSelection('cycle'))


def test_dropped_observations_preserve_occurrence_counters():
    q=request()
    assert q.solve().status=='UNSAT'
    assert recover_observations(q, range(4)).status=='UNSAT'
    r=recover_observations(q, (0,2,3))
    assert r.status=='SAT' and r.verified
    assert r.encoder.encode(r.plaintext,r.choices)==Text.from_string('a x a x')
    assert replace(q,ciphertext=Text.from_string('a a x')).solve().status=='UNSAT'
    assert r.capacity['observed_word_indices']==[0,2,3]
    assert 'context retained' in r.capacity['verification_scope']


def test_empty_observation_mask_retains_shape_but_no_glyph_evidence():
    r=recover_observations(request(), ())
    assert r.status=='SAT' and r.verified
    assert r.capacity['observed_word_indices']==[]


@pytest.mark.parametrize('indices', [(0,0),(-1,), (4,), (True,)])
def test_bad_observation_indices(indices):
    with pytest.raises(ValueError):recover_observations(request(),indices)


def test_mask_rejects_other_representations():
    with pytest.raises(ValueError):recover_observations(replace(request(),representation='ite'),(0,))


@pytest.mark.parametrize('encoding', ['flat', 'trie'])
def test_masks_match_independent_exhaustive_two_letter_oracle(encoding):
    from itertools import permutations, product
    from voynich_smt.cipher.base import Encoder
    from voynich_smt.cipher.selection import choose
    legal=set()
    for order in permutations('axy'):
        for sizes in ((1,1),(1,2),(2,1)):
            a,b=sizes
            key=Encoder({'a':tuple((x,) for x in order[:a]),
                         'b':tuple((x,) for x in order[a:a+b])})
            for letters in product('ab',repeat=4):
                plain=Text(tuple((x,) for x in letters))
                legal.add(key.encode(plain,choose(plain,key,HomophoneSelection('cycle'))).words)
    q=replace(request('a a x y'),plaintext_alphabet=Alphabet(tuple('ab')),
              dictionary=WordDictionary.from_strings(('a','b')),bounds=Bounds('homophonic',2,1,1),
              dictionary_encoding=encoding)
    for keep in product((False,True),repeat=4):
        mask=tuple(i for i,value in enumerate(keep) if value)
        expected=any(all(w[i]==q.ciphertext.words[i] for i in mask) for w in legal)
        result=recover_observations(q,mask)
        assert result.status==('SAT' if expected else 'UNSAT')
        assert result.status!='SAT' or result.verified
