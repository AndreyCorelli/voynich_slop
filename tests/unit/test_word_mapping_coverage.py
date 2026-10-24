from dataclasses import asdict

import pytest

from benchmarks.word_mapping_ablation import AblationPlan, search_config
from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.corpora import from_segments
from voynich_smt.word_mapping.coverage import screen_complete_segments
from voynich_smt.word_mapping.fixtures import CipherInput


def test_screening_excludes_whole_segments_without_joining_or_adding_candidates():
    stream = from_segments([['a', 'b'], ['a', 'missing'], ['b', None, 'a'], ['b', 'a', 'b']], 'latin', source={})
    candidates = ('a', 'b')
    before = digest(asdict(stream))
    selected, audit = screen_complete_segments(stream, candidates, minimum_words=2)
    assert selected.segments() == (('a', 'b'), ('b', 'a', 'b'))
    assert audit['input_segments'] == 5 and audit['admitted_segments'] == 2
    assert audit['admitted_tokens'] == 5
    assert audit['segments'][1]['missing_forms'] == ['missing']
    assert audit['segments'][1]['excluded_reason'] == 'missing candidates'
    assert digest(asdict(stream)) == before
    assert candidates == ('a', 'b')


def test_all_public_types_are_active_and_controls_use_only_declared_arms():
    plan = AblationPlan(seeds=(1, 2), budgets=(5, 10), fixture_kinds=('one-to-one',),
        arm_names=('baseline', 'trigram', 'collapse-5'), controls=('position-shuffle',),
        control_arm_names=('baseline',), all_types_active=True)
    assert len(plan.jobs()) == 16
    assert all(job['arm']['name'] == 'baseline' for job in plan.jobs() if job['control'] != 'original')
    public = CipherInput((('a', 'b', 'a', 'c'),), {}, {})
    assert search_config(plan, plan.jobs()[0], public).active_types == 3
    with pytest.raises(ValueError, match='public ciphertext'):
        search_config(plan, plan.jobs()[0])
    with pytest.raises(ValueError, match='selected search arms'):
        AblationPlan(arm_names=('baseline',), control_arm_names=('trigram',))
    with pytest.raises(ValueError, match='Unknown selected arm'):
        AblationPlan(arm_names=('unknown',))
