from itertools import product
import pytest
from voynich_smt.solver import length_search as runner
from voynich_smt.solver.recovery import Recovery
from tests.integration.test_segmented_recovery import request


def test_ordered_vectors_are_complete_unique_and_shortest_first():
    domains=((2,4,7),(1,3),(2,5))
    expected=sorted(product(*domains),key=lambda v:(sum(v),v))
    assert list(runner.ordered_vectors(domains))==expected
    assert list(runner.ordered_vectors(((2,2,1),(3,))))==[(1,3),(2,3)]
    assert list(runner.ordered_vectors(((),(1,))))==[]


def test_public_domains_keep_all_lengths_and_no_truth_required():
    q=request('xxxy')
    domains,graph=runner.public_domains(q)
    assert domains==((2,3),)
    assert list(runner.admissible_vectors(domains,graph))==[(2,),(3,)]
    result=runner.search(q,max_branches=2)
    assert result['status']=='SAT' and result['verified']
    assert result['attempts'][0]['word_lengths']==(2,)


@pytest.mark.parametrize('statuses,limit,status,exhausted',[
    (('UNSAT','UNSAT'),2,'UNSAT',True),
    (('UNKNOWN','UNSAT'),2,'UNKNOWN',True),
    (('UNSAT','UNKNOWN'),2,'UNKNOWN',True),
    (('UNSAT',),1,'UNKNOWN',False),
    (('UNKNOWN',),1,'UNKNOWN',False)])
def test_only_exhaustive_proved_rejections_mean_unsat(monkeypatch,statuses,limit,status,exhausted):
    outcomes=iter(statuses)
    monkeypatch.setattr(runner,'recover_with_word_lengths',lambda *a:Recovery(next(outcomes),0))
    result=runner.search(request('xxxy'),limit)
    assert result['status']==status and result['exhausted']==exhausted
    assert len(result['attempts'])==limit


def test_unknown_branch_does_not_prevent_later_verified_sat(monkeypatch):
    q=request('xyx')
    real=runner.recover_with_word_lengths
    visited=[]
    def recover(public,vector):
        visited.append(vector)
        return Recovery('UNKNOWN',0) if len(visited)==1 else real(public,vector)
    monkeypatch.setattr(runner,'recover_with_word_lengths',recover)
    result=runner.search(q,2)
    assert visited==[(1,),(2,)]
    assert result['status']=='SAT' and result['verified']


def test_public_equal_and_prefix_length_relations():
    q=request('x xx x')
    domains,graph=runner.public_domains(q)
    actual=list(runner.admissible_vectors(domains,graph))
    expected=[v for v in runner.ordered_vectors(domains) if v[0]==v[2] and v[0]<v[1]]
    assert actual==expected


def test_unverified_sat_is_rejected(monkeypatch):
    monkeypatch.setattr(runner,'recover_with_word_lengths',lambda *a:Recovery('SAT',0))
    with pytest.raises(RuntimeError):runner.search(request('xxxy'),1)


@pytest.mark.parametrize('domains', [((2,4,7),(1,3),(2,5)), ((1,),(2,3,5)), ((1,2),), ((),(1,))])
def test_diverse_products_remain_complete_and_unique(domains):
    expected=set(product(*domains))
    for actual in (list(runner.balanced_vectors(domains)),list(runner.ranked_vectors(domains))):
        assert set(actual)==expected and len(actual)==len(expected)
    if expected:
        balanced=list(runner.balanced_vectors(domains))
        assert balanced[0]==tuple(d[0] for d in domains)
        if any(len(d)>1 for d in domains):
            assert balanced[1]==tuple(d[min(1,len(d)-1)] for d in domains)


def test_candidate_rich_uses_public_candidate_counts_and_preserves_all_vectors():
    from voynich_smt.language.dictionary import CandidateGraph
    candidates=(tuple(tuple(w) for w in ('a','ab','ba','aaa','aab','aba','abb')),
                tuple(tuple(w) for w in ('a','b','ab')))
    graph=CandidateGraph(candidates,(),0)
    domains=((1,2,3),(1,2))
    actual=list(runner.admissible_vectors(domains,graph,'candidate_rich'))
    assert actual[0]==(3,1)
    assert set(actual)==set(product(*domains)) and len(actual)==6


@pytest.mark.parametrize('ordering',['balanced','candidate_rich'])
@pytest.mark.parametrize('statuses,limit,status,exhausted',[
    (('UNSAT','UNSAT'),2,'UNSAT',True),
    (('UNKNOWN','UNSAT'),2,'UNKNOWN',True),
    (('UNSAT','UNKNOWN'),2,'UNKNOWN',True),
    (('UNSAT',),1,'UNKNOWN',False),
    (('UNKNOWN',),1,'UNKNOWN',False)])
def test_diverse_orderings_retain_safe_result_classification(monkeypatch,ordering,statuses,limit,status,exhausted):
    outcomes=iter(statuses)
    monkeypatch.setattr(runner,'recover_with_word_lengths',lambda *a:Recovery(next(outcomes),0))
    result=runner.search(request('xxxy'),limit,ordering=ordering)
    assert result['status']==status and result['exhausted']==exhausted


def test_all_orderings_keep_public_length_relations():
    q=request('x xx x')
    domains,graph=runner.public_domains(q)
    expected=set(runner.admissible_vectors(domains,graph))
    for ordering in ('balanced','candidate_rich'):
        assert set(runner.admissible_vectors(domains,graph,ordering))==expected
    with pytest.raises(ValueError):runner.search(q,ordering='bad')
