from dataclasses import asdict
import pytest
from benchmarks import public_length_key_uniqueness as b
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from benchmarks.l3_conflict import verify


def fixture(plain_string):
    plain=Text.from_string(plain_string)
    enc=Encoder({'a':(('x',),),'b':(('y','z'),)})
    q=HiddenRecoveryRequest(enc.encode(plain,(0,)*plain.size),Alphabet(tuple('ab')),
        Alphabet(tuple('xyz')),Bounds('verbose',1,1,3),
        WordDictionary.from_strings(('ab','ba','a','b')),timeout_ms=5000)
    case={'truth':{'encoder':asdict(enc)},'holdout_plaintext':asdict(Text.from_string('ba'))}
    return plain,q,b.exclusion(case)


def test_alternative_mapping_sat_when_training_does_not_identify_boundary():
    plain,q,rule=fixture('ab')
    result=asdict(b.solve(plain,q,rule));verify(q,result)
    assert result['status']=='SAT' and result['verified']
    assert b.changed_mappings(result,rule)
    assert result['plaintext']['words']==plain.words


def test_mapping_exclusion_unsat_when_training_identifies_codes():
    plain,q,rule=fixture('a b ab')
    assert b.solve(plain,q,rule).status=='UNSAT'


def test_solver_receives_only_known_training_and_one_joint_exclusion(monkeypatch):
    plain,q,rule=fixture('ab');received=[];sentinel=object()
    def spy(*args,**kwargs):received.append((args,kwargs));return sentinel
    monkeypatch.setattr(b,'_recover',spy)
    assert b.solve(plain,q,rule) is sentinel
    args,kwargs=received[0]
    assert args==(plain,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000)
    assert kwargs=={'representation':q.representation,'selection':q.selection,
                    'codeword_domains':'observed','key_exclusions':(rule,)}
    assert {s['symbol'] for s in rule['segments']}=={'a','b'}


def test_saved_diagnostic_validates_and_resume_skips_fits(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    r=b.run()
    assert all(row['result']['status']=='UNSAT' and row['conclusion']=='HELD_OUT_MAPPINGS_FORCED' for row in r['cases'])
    assert all('prediction' not in row for row in r['cases'])
    b.validate()
    def unexpected(*args):raise AssertionError('Repeated fit')
    monkeypatch.setattr(b,'solve',unexpected)
    from voynich_smt.data.corpus import digest
    assert digest(b.run())==digest(r)
