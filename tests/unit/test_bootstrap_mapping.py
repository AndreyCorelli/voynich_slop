from dataclasses import replace
import itertools
import math
import random
import pytest

from voynich_smt.bootstrap_mapping import AgreementModel, AgreementScorer, BootstrapOptions, BootstrapSearch, coordinated_changes
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.incremental import IncrementalScorer
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel


def entries(pos, case, number, gender):
    return [{'lemma_id': 'lemma', 'inflections': [{'part_of_speech': pos,
        'features': {'Case': case, 'Number': number, 'Gender': gender}}]}]


def resources():
    training = [('a', 'b'), ('c', 'd'), ('a', 'e'), ('f', 'd')] * 5
    model = NgramModel.train(training)
    morphology = MorphologyCatalog({
        'a': entries('N', 'NOM', 'S', 'F'), 'b': entries('ADJ', 'NOM', 'S', 'F'),
        'c': entries('N', 'ACC', 'P', 'M'), 'd': entries('ADJ', 'ACC', 'P', 'C'),
        'e': [], 'f': entries('ADJ', 'X', 'X', 'X')}, {}, model.training_sha256)
    catalog = CandidateCatalog.build(training, morphology, training_sha256=model.training_sha256)
    return model, morphology, catalog


def test_ambiguity_common_gender_unknown_and_boundaries():
    _, morphology, _ = resources()
    agreement = AgreementModel(morphology)
    assert agreement.pair('a', 'b') == 1
    assert agreement.pair('c', 'd') == 1
    assert agreement.pair('a', 'd') == -1
    assert agreement.pair('e', 'd') == 0
    assert agreement.pair('a', 'f') == 0  # Missing counterpart features provide no agreement evidence.
    assert agreement.score([('a',), ('b',)]) == 0
    assert agreement.score([('a', None, 'b')]) == 0
    ambiguous = replace(morphology, entries={**morphology.entries,
        'b': morphology.entries['b'] + entries('ADJ', 'ACC', 'P', 'M')})
    assert AgreementModel(ambiguous).pair('a', 'b') == 0
    with_duplicate = replace(ambiguous, entries={**ambiguous.entries,
        'b': ambiguous.entries['b'] * 2})
    assert AgreementModel(with_duplicate).pair('a', 'b') == 0


def test_transactional_joint_deltas_match_full_scores_and_reject_stale():
    model, morphology, catalog = resources()
    segments = [('x', 'y', 'x', 'z'), ('z', 'x', 'u', 'y')]
    base = IncrementalScorer(model, segments, WordMapping(catalog.forms,
        {'x': 0, 'y': 1, 'z': 2, 'u': None}), injective=True, frequency_weight=.4)
    scorer = AgreementScorer(base, AgreementModel(morphology), 2)
    rng = random.Random(71)
    for step in range(300):
        words = rng.sample(['x', 'y', 'z'], 2)
        changes = coordinated_changes({w: f for w, f in scorer.assignments.items() if f is not None},
            dict(zip(words, rng.sample(range(len(catalog.forms)), 2))))
        proposal = scorer.propose(changes)
        new = WordMapping(catalog.forms, {**scorer.assignments, **changes})
        new_base = IncrementalScorer(model, segments, new, injective=True, frequency_weight=.4)
        expected = new_base.objective + 2 * scorer.agreement_model.score(new.render(segments))
        assert scorer.objective + scorer.delta(proposal) == pytest.approx(expected, abs=1e-9)
        if step % 2:
            scorer.commit(proposal)
            with pytest.raises(ValueError, match='Stale'):
                scorer.commit(proposal)
        scorer.validate()


def test_joint_completion_exhaustively_preserves_injectivity():
    assignments = {'x': 0, 'y': 1, 'z': 2, 'w': 3}
    for a, b in itertools.permutations(range(6), 2):
        changes = coordinated_changes(assignments, {'x': a, 'y': b})
        result = {**assignments, **changes}
        assert result['x'] == a and result['y'] == b
        assert len(set(result.values())) == len(result)
    with pytest.raises(ValueError, match='injective'):
        coordinated_changes(assignments, {'x': 1, 'y': 1})


@pytest.mark.parametrize('options', [BootstrapOptions(), BootstrapOptions(shortlist_probability=.6),
    BootstrapOptions(agreement_weight=2), BootstrapOptions(joint_probability=.25),
    BootstrapOptions(shortlist_probability=.6, agreement_weight=2, joint_probability=.25)])
def test_seeded_resume_and_archive_objectives(tmp_path, options):
    model, morphology, catalog = resources()
    segments = [('x', 'y', 'z', 'x'), ('z', 'y')]
    config = SearchConfig(seed=44, restarts=3, steps_per_restart=100, initialization='mixed',
        active_types=3, injective=True, archive_size=10, archive_min_distance=2)
    complete = BootstrapSearch(model, catalog, morphology, segments, config, options)
    complete.advance()
    partial = BootstrapSearch(model, catalog, morphology, segments, config, options)
    partial.advance(131)
    path = tmp_path / 'checkpoint.json'
    partial.checkpoint(path)
    resumed = BootstrapSearch(model, catalog, morphology, segments, config, options).resume(path)
    resumed.advance()
    assert resumed.archive == complete.archive
    assert resumed.statistics == complete.statistics
    assert resumed.scorer.objective == complete.scorer.objective
    agreement = AgreementModel(morphology)
    for row in complete.archive:
        mapping = WordMapping(catalog.forms, row['assignments'])
        assert mapping.collapse_penalty == 0
        expected = model.score(mapping.render(segments)).log_likelihood + options.agreement_weight * agreement.score(mapping.render(segments))
        assert row['score'] == pytest.approx(expected, abs=1e-8)
    assert all(not row['locked'] for row in complete.hypotheses().values())
    changed = replace(options, agreement_weight=options.agreement_weight + 1)
    with pytest.raises(ValueError, match='protocol'):
        BootstrapSearch(model, catalog, morphology, segments, config, changed).resume(path)


@pytest.mark.parametrize('kwargs', [{'shortlist_probability': 1}, {'joint_probability': -.1},
    {'agreement_weight': math.nan}, {'shortlist_size': True}])
def test_invalid_options(kwargs):
    with pytest.raises(ValueError):
        BootstrapOptions(**kwargs)


def test_restarts_have_identical_initial_dictionaries_across_arms():
    model, morphology, catalog = resources()
    segments = [('x', 'y', 'z')]
    config = SearchConfig(seed=71, restarts=3, steps_per_restart=30, active_types=3,
        initialization='mixed', injective=True)
    traces = []
    for options in (BootstrapOptions(), BootstrapOptions(shortlist_probability=.6, joint_probability=.25, agreement_weight=2)):
        search = BootstrapSearch(model, catalog, morphology, segments, config, options)
        initial = [dict(search.scorer.assignments)]
        for _ in range(2):
            search.advance(30)
            initial.append(dict(search.scorer.assignments))
        traces.append(initial)
    assert traces[0] == traces[1]


def test_pair_can_improve_agreement_when_neither_single_change_does():
    morphology = MorphologyCatalog({
        'a': entries('N', 'NOM', 'S', 'F'), 'b': entries('ADJ', 'ACC', 'P', 'M'),
        'c': entries('N', 'GEN', 'P', 'F'), 'd': entries('ADJ', 'GEN', 'P', 'F')}, {}, 'train')
    agreement = AgreementModel(morphology)
    initial = agreement.score([('a', 'b')])
    assert agreement.score([('c', 'b')]) == initial
    assert agreement.score([('a', 'd')]) == initial
    assert agreement.score([('c', 'd')]) > initial
