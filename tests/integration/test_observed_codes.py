from dataclasses import asdict, replace
from itertools import product
import pytest
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import substrings, recover_observed_codes
from voynich_smt.solver.recovery import _recover


def request(text='xyx'):
    return HiddenRecoveryRequest(Text.from_string(text),Alphabet(tuple('ab')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','b','ab','ba','aaa','bbb','aba')),
        selection=HomophoneSelection('cycle','text'),dictionary_encoding='trie')


def test_substrings_obey_word_boundaries_and_length_bounds():
    q=request('xy z')
    assert substrings(q.ciphertext,q.bounds)==frozenset((('x',),('y',),('x','y'),('z',)))
    assert substrings(q.ciphertext,Bounds('verbose',2,2,3))==frozenset((('x','y'),))


@pytest.mark.parametrize('reset',['word','text'])
def test_observed_domains_preserve_exhaustive_small_hidden_outcomes(reset):
    for word in product('xy',repeat=3):
        q=replace(request(),ciphertext=Text((word,('x',))),selection=HomophoneSelection('cycle',reset))
        old=q.solve();new=recover_observed_codes(q)
        assert old.status==new.status and old.status!='UNKNOWN'
        assert new.capacity['codeword_domains']=='observed'
        if new.status=='SAT':
            assert new.verified
            actual=[new.encoder.codebook[s][k] for s,k in zip(
                (s for w in new.plaintext.words for s in w),new.choices)]
            assert all(c in substrings(q.ciphertext,q.bounds) for c in actual)


def test_unused_pinned_homophones_and_letters_can_stay_outside_observed_pool():
    q=request('x')
    key=Encoder({'a':(('x',),('y',)),'b':(('z',),)})
    result=_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,1000,
        dictionary=q.dictionary,max_word_length=3,selection=q.selection,dictionary_encoding='trie',
        codeword_domains='observed',guidance={'encoder':key,'pinned_symbols':('a','b'),'rotate':False,
                                           'hint_symbols':(),'word_hints':{},'minimize_core':False})
    assert result.verified and result.encoder.codebook==key.codebook
    assert ('y',) not in substrings(q.ciphertext,q.bounds)


def test_fixed_public_lengths_work_without_oracle_boundaries():
    q=request('xxxy')
    result=recover_observed_codes(q,(2,))
    assert result.verified and len(result.plaintext.words[0])==2
    assert not result.capacity.get('oracle_segmentation')
    with pytest.raises(ValueError):HiddenRecoveryRequest.from_dict({**asdict(q),'codeword_domains':'observed'})


def test_masked_words_are_not_restricted_to_observed_pool():
    q=request()
    with pytest.raises(ValueError):
        _recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,1000,
            dictionary=q.dictionary,max_word_length=3,observed_words=(),codeword_domains='observed')
