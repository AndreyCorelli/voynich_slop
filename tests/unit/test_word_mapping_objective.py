from dataclasses import replace
import random

import pytest

from benchmarks.word_mapping_ablation import AblationPlan
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.diagnostics import truth_diagnostic
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.incremental import IncrementalScorer
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.mutations import injective_changes
from voynich_smt.word_mapping.ngram import NgramModel
from voynich_smt.word_mapping.objective import frequency_penalty, objective_score


def resources():
    training = [('a', 'b', 'a', 'c'), ('d', 'a', 'b'), ('e', 'b')] * 5
    model = NgramModel.train(training)
    catalog = MorphologyCatalog({w: [] for w in model.vocabulary}, {}, model.training_sha256)
    return model, CandidateCatalog.build(training, catalog, training_sha256=model.training_sha256)


def test_frequency_aggregates_homophones_and_ignores_unknown():
    model, candidates = resources()
    mapping = WordMapping(candidates.forms, {'x': 0, 'y': 0, 'z': 1, 'u': None})
    segments = [('x', 'y', 'z', 'u')]
    assert frequency_penalty(model, segments, mapping) == pytest.approx(
        frequency_penalty(model, [('x', 'x', 'z')], mapping))
    assert frequency_penalty(model, [('u',)], mapping) == 0


def test_frequency_local_deltas_match_independent_full_objective():
    model, candidates = resources()
    segments = [('x', 'x', 'y', 'z'), ('x', 'u', 'z', 'y')]
    scorer = IncrementalScorer(model, segments,
        WordMapping(candidates.forms, {'x': 0, 'y': 1, 'z': 2, 'u': None}),
        collapse_weight=0.7, frequency_weight=3.0)
    rng = random.Random(52)
    for i in range(1200):
        changes = {w: rng.randrange(len(candidates.forms))
                   for w in rng.sample(['x', 'y', 'z'], rng.randint(1, 3))}
        proposed = scorer.propose(changes)
        mapping = WordMapping(candidates.forms, {**scorer.assignments, **changes})
        expected = objective_score(model, segments, mapping, collapse_weight=0.7, frequency_weight=3)
        assert scorer.objective + scorer.delta(proposed) == pytest.approx(expected, abs=1e-9)
        if i % 3:
            scorer.commit(proposed)
        scorer.validate()


@pytest.mark.parametrize('initialization', ['frequency', 'random', 'lemma-aware', 'mixed'])
def test_injective_frequency_search_resume_and_domain(tmp_path, initialization):
    model, candidates = resources()
    segments = [('x', 'y', 'z', 'x'), ('y', 'z', 'x')]
    config = SearchConfig(seed=28, restarts=3, steps_per_restart=100, active_types=3,
                          injective=True, frequency_weight=1, initialization=initialization)
    complete = Annealer(model, candidates, segments, config)
    complete.advance()
    interrupted = Annealer(model, candidates, segments, config)
    for _ in range(121):
        interrupted.advance(1)
        assert interrupted.scorer.penalty == 0
    path = tmp_path / 'checkpoint.json'
    interrupted.checkpoint(path)
    resumed = Annealer(model, candidates, segments, config).resume(path)
    resumed.advance()
    assert resumed.archive == complete.archive
    assert resumed.statistics == complete.statistics
    assert resumed.scorer.objective == complete.scorer.objective
    for row in resumed.archive:
        mapping = WordMapping(candidates.forms, row['assignments'])
        assert not mapping.collapse_penalty
        assert row['score'] == pytest.approx(objective_score(
            model, segments, mapping, injective=True, frequency_weight=1), abs=1e-8)
    with pytest.raises(ValueError, match='protocol'):
        Annealer(model, candidates, segments, replace(config, frequency_weight=2)).resume(path)


def test_injective_invalid_domain_and_homophonic_truth():
    model, candidates = resources()
    with pytest.raises(ValueError, match='candidate per active'):
        Annealer(model, candidates, [('u', 'v', 'w', 'x', 'y', 'z')],
                 SearchConfig(injective=True))
    mapping = WordMapping(candidates.forms, {'x': 0, 'y': 1})
    scorer = IncrementalScorer(model, [('x', 'y')], mapping, injective=True)
    with pytest.raises(ValueError, match='injective'):
        scorer.propose({'x': 1})
    public, truth = generate([('a',) * 30], kind='homophonic', seed=713, source={})
    assignments = {w: 0 for segment in public.segments for w in segment}
    assert len(assignments) > 1
    result = truth_diagnostic(model, candidates, public, truth,
        [{'assignments': assignments, 'score': 0}], injective=True)
    assert not result['active_truth_feasible']
    assert result['diagnosis'] == 'truth_violates_injective_constraint'


def test_injective_replacement_graph_reaches_every_feasible_state():
    # Exhaust the graph, including fully occupied vocabularies where every
    # nontrivial replacement must become a swap.
    import itertools
    for form_count in (3, 4):
        initial = (0, 1, 2)
        seen, pending = {initial}, [initial]
        while pending:
            state = pending.pop()
            assignments = dict(zip(('x', 'y', 'z'), state))
            for word in assignments:
                for form in range(form_count):
                    changes = injective_changes(assignments, {word: form})
                    candidate = {**assignments, **changes}
                    assert len(set(candidate.values())) == 3
                    target = tuple(candidate.values())
                    if target not in seen:
                        seen.add(target)
                        pending.append(target)
        assert seen == set(itertools.permutations(range(form_count), 3))


def test_refinement_plan_limits_constraint_to_declared_one_to_one():
    plan = AblationPlan(frequency_weights=(1, 5), constraint_arms=True,
        arm_names=('baseline', 'frequency-1', 'frequency-5', 'injective', 'injective-frequency-1'))
    jobs = plan.jobs()
    assert any(j['arm'].get('injective') for j in jobs)
    assert all(j['fixture'] == 'one-to-one' for j in jobs if j['arm'].get('injective'))
    for config in [dict(frequency_weight=-1), dict(frequency_weight=float('nan')), dict(injective=1)]:
        with pytest.raises(ValueError):
            SearchConfig(**config)
