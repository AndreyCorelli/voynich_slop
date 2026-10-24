from dataclasses import replace
import pytest
from benchmarks.vocabulary_restoration import variant_request
from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


def requests():
    old=HiddenRecoveryRequest(Text.from_string('xy xy'),Alphabet(tuple('aiv')),Alphabet(tuple('xy')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('iv','a','i','aa')),
        selection=HomophoneSelection('cycle','text'),dictionary_encoding='trie')
    return replace(old,dictionary=WordDictionary.from_strings(('a','aa'))),old


def test_restoration_changes_only_selected_vocabulary_and_timeout():
    clean,old=requests()
    q=variant_request(clean,old,('i',),30000)
    assert q.dictionary.words==tuple(map(tuple,('a','i','aa')))
    assert replace(q,dictionary=clean.dictionary,timeout_ms=clean.timeout_ms)==clean
    assert q.timeout_ms==30000
    assert clean.dictionary.words==tuple(map(tuple,('a','aa')))


@pytest.mark.parametrize('additions',[(),('a',),('v',)])
def test_restoration_rejects_empty_existing_or_nonoriginal_entries(additions):
    clean,old=requests()
    with pytest.raises(ValueError):
        variant_request(clean,old,additions,30000)
