from itertools import product
import pytest
import z3
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.dictionary_encoding import membership


@pytest.mark.parametrize('words', [(),('a',),('a','ab','aba','abb','ba','bbb'),('ab','ba','aa','bb')])
def test_trie_formula_is_equivalent_including_inactive_padding(words):
    alphabet=Alphabet(tuple('ab'))
    candidates=tuple(tuple(w) for w in words)
    symbols=[z3.Int(f'p{i}') for i in range(max(map(len,candidates),default=0))]
    size=z3.Int('size')
    s=z3.Solver()
    s.add(z3.Xor(membership(candidates,symbols,size,alphabet,'flat'),
                 membership(candidates,symbols,size,alphabet,'trie')))
    assert s.check()==z3.unsat


def test_unknown_dictionary_encoding_rejected():
    with pytest.raises(ValueError):membership((('a',),),[z3.Int('p')],z3.Int('s'),Alphabet(('a',)),'bad')


def test_trie_roundtrip_and_cycle_outcomes_match_flat():
    from dataclasses import asdict,replace
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.settings import HomophoneSelection
    from voynich_smt.models.text import Text
    q=HiddenRecoveryRequest(Text.from_string('x'),Alphabet(tuple('ab')),Alphabet(tuple('xy')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('a','ab','aba','abb','ba','bbb')),
        selection=HomophoneSelection('cycle'),dictionary_encoding='trie')
    assert HiddenRecoveryRequest.from_dict(asdict(q))==q
    for word in product('xy',repeat=4):
        request=replace(q,ciphertext=Text((word,word)))
        flat=replace(request,dictionary_encoding='flat').solve()
        trie=request.solve()
        assert flat.status==trie.status
        assert trie.status!='SAT' or trie.verified
        assert trie.capacity['dictionary_encoding']=='trie'


@pytest.mark.parametrize('setting', ['nulls','optimization'])
@pytest.mark.parametrize('encoding', ['trie','entry'])
def test_factored_encodings_require_feasibility_without_nulls(setting,encoding):
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.text import Text
    from voynich_smt.models.settings import NullBounds,Optimization
    value=NullBounds(True,1,1,1) if setting=='nulls' else Optimization(True)
    with pytest.raises(ValueError,match='null-free feasibility'):
        HiddenRecoveryRequest(Text.from_string('x'),Alphabet(('a',)),Alphabet(tuple('xy')),
            Bounds('verbose',2,1,3),WordDictionary.from_strings(('a',)),
            dictionary_encoding=encoding,**{setting:value})


@pytest.mark.parametrize('words', [(),('a',),('a','ab','aba','abb','ba','bbb'),('ab','ba','aa','bb')])
def test_entry_formula_projects_to_exact_flat_membership(words):
    alphabet=Alphabet(tuple('ab'))
    candidates=tuple(tuple(w) for w in words)
    symbols=[z3.Int(f'entry_p{i}') for i in range(max(map(len,candidates),default=0)+1)]
    size,entry=z3.Ints('entry_size entry_id')
    formula=membership(candidates,symbols,size,alphabet,'entry',entry)
    projected=z3.Or([z3.substitute(formula,(entry,z3.IntVal(i))) for i in range(len(candidates))])
    solver=z3.Solver()
    solver.add(z3.Xor(membership(candidates,symbols,size,alphabet,'flat'),projected))
    assert solver.check()==z3.unsat
    for invalid in (-1,len(candidates)):
        solver=z3.Solver();solver.add(formula,entry==invalid)
        assert solver.check()==z3.unsat


def test_entry_hidden_recovery_matches_trie_and_roundtrips():
    from dataclasses import asdict,replace
    from voynich_smt.cipher.base import Bounds
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    from voynich_smt.language.dictionary import WordDictionary
    from voynich_smt.models.settings import HomophoneSelection
    from voynich_smt.models.text import Text
    q=HiddenRecoveryRequest(Text.from_string('x'),Alphabet(tuple('ab')),Alphabet(tuple('xy')),
        Bounds('verbose',2,1,2),WordDictionary.from_strings(('a','ab','ba','aba','bbb')),
        selection=HomophoneSelection('cycle'),dictionary_encoding='entry')
    assert HiddenRecoveryRequest.from_dict(asdict(q))==q
    for word in product('xy',repeat=3):
        request=replace(q,ciphertext=Text((word,word,('x',))))
        entry=request.solve();trie=replace(request,dictionary_encoding='trie').solve()
        assert entry.status==trie.status and entry.status!='UNKNOWN'
        assert entry.status!='SAT' or entry.verified
        assert entry.capacity['dictionary_encoding']=='entry'
