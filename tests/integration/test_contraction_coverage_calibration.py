from copy import deepcopy
from dataclasses import asdict

from benchmarks.contraction_coverage_calibration import (
    cover_training, balanced_choices, swaps, frequency_score,
)
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text

RULES = [{'id':'et','expansion':'et','position':'whole','units':1},
         {'id':'est','expansion':'est','position':'whole','units':1}]
UNITS = ('<et-part-0>', '<est-part-0>')


def test_wholeword_coverage_requires_seen_plaintext_form():
    fixture = {'train':['a'], 'held':['et'], 'reference_counts':{'et':10,'beta':2}}
    d = cover_training(fixture, RULES)
    assert d['carriers'] == ['et','et']
    assert d['carrier_held_form_overlap'] == ['et']
    assert d['target_occurrences']['<et-part-0>'] == 2


def test_balancing_observes_both_alternatives_without_boundary_input():
    p = Text((('a','b'),('a',),('b','a')))
    choices = balanced_choices(p)
    assert choices == (0,0,1,1,0)
    for u in ('a','b'):
        assert {k for s,k in zip((s for w in p.words for s in w),choices) if s==u} == {0,1}


def tiny():
    encoder = Encoder({UNITS[0]:(('x',),('y',)), UNITS[1]:(('z',),('w',))})
    plain = Text(((UNITS[0],),)*24 + ((UNITS[1],),)*8)
    choices = balanced_choices(plain)
    q = HiddenRecoveryRequest(encoder.encode(plain,choices),Alphabet(UNITS),Alphabet(tuple('xyzw')),
                              Bounds('verbose',2,1,1),WordDictionary(((UNITS[0],),(UNITS[1],))))
    truth = {'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
    p = {'rules':RULES,'expansions':dict(zip(UNITS,('et','est')))}
    return p,q,truth


def test_complete_code_coverage_does_not_identify_wholeword_owners():
    p,q,truth = tiny()
    original = deepcopy(truth)
    alternatives = swaps(truth,p,q)
    assert len(alternatives) == 1
    verify(q,alternatives[0]['result'])
    assert alternatives[0]['result']['plaintext'] != truth['plaintext']
    assert truth == original


def test_frequency_excludes_carriers_truth_and_holdout_metadata():
    p,q,truth = tiny()
    case = {'reference_model':{'counts':{'et':9,'est':1},'tokens':10,'alpha':1},
            'held_plaintext':['est'],'truth':'irrelevant'}
    value = frequency_score(truth,case,p)
    extended = deepcopy(truth)
    extended['plaintext']['words'] = list(extended['plaintext']['words']) + [(UNITS[1],)]*100
    case['held_plaintext'] = ['et']*100
    assert frequency_score(extended,case,p) == value
    alternate = swaps(truth,p,q)[0]['result']
    assert value > frequency_score(alternate,case,p)
