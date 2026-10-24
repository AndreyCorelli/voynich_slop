from dataclasses import asdict, replace
import pytest
from benchmarks.clean_latin_suffix import suffix_witness, validate_row
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import choose, accepts
from voynich_smt.data.corpus import digest
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


@pytest.mark.parametrize('alternatives',[2,3])
@pytest.mark.parametrize('start',[0,1,2,3,4])
def test_suffix_rotation_preserves_ciphertext_and_phase_zero_cycles(alternatives,start):
    key=Encoder({'a':tuple((c,) for c in 'xyw'[:alternatives]),
                 'b':tuple((c,) for c in 'zvu'[:alternatives])})
    plain=Text.from_string('ab a ab b a');selection=HomophoneSelection('cycle','text')
    choices=choose(plain,key,selection);cipher=key.encode(plain,choices)
    original={'plaintext':asdict(plain),'encoder':asdict(key),'choices':list(choices),
              'segmentation':[[0,*range(1,len(w)+1)] for w in plain.words]}
    rotated=suffix_witness(original,start)
    new_key=Encoder(rotated['encoder']['codebook'])
    new_plain=Text(tuple(rotated['plaintext']['words']));new_choices=tuple(rotated['choices'])
    assert new_key.encode(new_plain,new_choices)==Text(cipher.words[start:])
    assert new_key.decode(Text(cipher.words[start:]))==new_plain
    assert accepts(new_plain,new_key,new_choices,selection)
    assert original['encoder']==asdict(key)
    assert original['choices']==list(choices)


def test_cached_prefix_cannot_be_mistaken_for_suffix():
    base=HiddenRecoveryRequest(Text.from_string('x y z'),Alphabet(tuple('ab')),
        Alphabet(tuple('xyz')),Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','b')),
        selection=HomophoneSelection('cycle','text'))
    wrong=replace(base,ciphertext=Text.from_string('x y'))
    row={'word_count':2,'request':asdict(wrong),
         'input_sha256':digest({'request':asdict(wrong),'codeword_domains':'observed'}),
         'result':{'status':'UNKNOWN'}}
    with pytest.raises(ValueError,match='contiguous suffix'):validate_row(row,base)
