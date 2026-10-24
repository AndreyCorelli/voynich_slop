from dataclasses import asdict, replace
import math
import random

import pytest

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.controls import make_control
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.incremental import IncrementalScorer
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.mutations import MutationCatalog
from voynich_smt.word_mapping.ngram import NgramModel


def resources():
    training = [('in', 'terra', 'est'), ('in', 'terram', 'aqua'),
                ('terra', 'est', 'aqua'), ('aqua', 'est')] * 5
    model = NgramModel.train(training)
    morphology = MorphologyCatalog({word: [{'lemma_id': 'terra' if word in {'terra', 'terram'} else word}]
        for word in model.vocabulary}, {}, model.training_sha256)
    candidates = CandidateCatalog.build(training, morphology, training_sha256=model.training_sha256)
    return model, candidates


def test_incremental_random_joint_swaps_repeated_words_and_rollbacks():
    model, candidates = resources()
    segments = [('x', 'x', 'y', 'z', 'x'), ('z', 'unknown', 'x'), (), ('y', 'x')]
    mapping = WordMapping(candidates.forms, {'x': 0, 'y': 1, 'z': 2, 'unknown': None})
    scorer = IncrementalScorer(model, segments, mapping, collapse_weight=0.7)
    scorer.validate()
    rng = random.Random(29)
    for i in range(1500):
        words = rng.sample(['x', 'y', 'z'], rng.randint(1, 3))
        changes = {word: rng.randrange(len(mapping.forms)) for word in words}
        before = digest(asdict(scorer.mapping))
        proposal = scorer.propose(changes)
        predicted_mapping = WordMapping(mapping.forms, {**scorer.assignments, **changes})
        full = model.score(predicted_mapping.render(segments))
        expected = full.log_likelihood - 0.7 * predicted_mapping.collapse_penalty
        assert scorer.objective + scorer.delta(proposal) == pytest.approx(expected, abs=1e-9)
        assert digest(asdict(scorer.mapping)) == before
        if i % 3:
            scorer.commit(proposal)
            scorer.validate()
        else:
            assert digest(asdict(scorer.mapping)) == before
    assert scorer.mapping.render([['x', 'x']])[0][0] == scorer.mapping.render([['x', 'x']])[0][1]


def test_local_update_deduplicates_windows_and_rejects_stale_proposals():
    model, candidates = resources()
    scorer = IncrementalScorer(model, [('x', 'y', 'z', 'z', 'z', 'z')],
        WordMapping(candidates.forms, {'x': 0, 'y': 1, 'z': 2}))
    single = scorer.propose({'x': 1})
    joint = scorer.propose({'x': 1, 'y': 0})
    assert len(single.event_scores) == 3
    assert len(joint.event_scores) == 4
    scorer.commit(joint)
    with pytest.raises(ValueError, match='Stale'):
        scorer.commit(single)
    with pytest.raises(ValueError, match='inactive'):
        scorer.propose({'new': 0})
    with pytest.raises(ValueError, match='valid surface'):
        scorer.propose({'x': None})


def test_mutations_preserve_lemma_and_allow_lemma_escape():
    model, candidates = resources()
    mapping = WordMapping(candidates.forms, {'x': candidates.forms.index('terra'), 'y': 0})
    scorer = IncrementalScorer(model, [('x', 'y')], mapping)
    proposals = MutationCatalog(mapping, candidates)
    # Limit active words so each proposal targets the known terra assignment.
    proposals.active = ('x',)
    rng = random.Random(8)
    kind, changes = proposals.propose(scorer, rng, 'inflection')
    assert kind == 'inflection' and mapping.forms[changes['x']] == 'terram'
    kind, changes = proposals.propose(scorer, rng, 'lemma')
    assert kind == 'lemma' and mapping.forms[changes['x']] not in {'terra', 'terram'}
    reached = {proposals.propose(scorer, rng, 'replace')[1]['x'] for _ in range(500)}
    assert reached == set(range(len(mapping.forms)))


def test_seeded_search_checkpoint_resume_and_archive(tmp_path):
    model, candidates = resources()
    config = SearchConfig(seed=18, restarts=3, steps_per_restart=150,
                          active_types=3, archive_size=10, collapse_weight=0.1)
    segments = [('x', 'y', 'z'), ('x', 'z'), ('x', 'y', 'z')]
    uninterrupted = Annealer(model, candidates, segments, config)
    uninterrupted.advance()
    interrupted = Annealer(model, candidates, segments, config)
    interrupted.advance(175)  # checkpoint in a later restart
    path = tmp_path / 'checkpoint.json'
    interrupted.checkpoint(path)
    resumed = Annealer(model, candidates, segments, config).resume(path)
    resumed.advance()
    assert resumed.complete
    assert resumed.evaluations == config.restarts * config.steps_per_restart
    assert resumed.archive == uninterrupted.archive
    assert resumed.statistics == uninterrupted.statistics
    assert resumed.best_mapping == uninterrupted.best_mapping
    assert resumed.scorer.objective == uninterrupted.scorer.objective
    assert len(resumed.archive) <= config.archive_size
    assert len({tuple(sorted(row['assignments'].items())) for row in resumed.archive}) == len(resumed.archive)
    resumed.checkpoint(path)
    complete = Annealer(model, candidates, segments, config).resume(path)
    complete.advance()
    assert complete.archive == resumed.archive
    with pytest.raises(ValueError, match='protocol'):
        Annealer(model, candidates, segments, replace(config, seed=19)).resume(path)
    with pytest.raises(ValueError, match='protocol'):
        Annealer(model, candidates, [('x', 'z')], config).resume(path)


def test_exact_recovery_on_small_identifiable_cipher():
    # Tiny synthetic instrument check, not natural-text/generalization evidence.
    plaintext = [('in', 'terra', 'est'), ('aqua', 'est')] * 40
    model = NgramModel.train(plaintext)
    catalog = MorphologyCatalog({word: [] for word in model.vocabulary}, {}, model.training_sha256)
    candidates = CandidateCatalog.build(plaintext, catalog, training_sha256=model.training_sha256)
    public, truth = generate(plaintext, source={'kind': 'instrument'}, seed=77)
    search = Annealer(model, candidates, public.segments,
        SearchConfig(seed=91, restarts=2, steps_per_restart=500, active_types=4))
    search.advance()
    assert recovery(public, truth, search.best_mapping)['exact_token_accuracy'] == 1
    search.scorer.validate()


@pytest.mark.parametrize('kwargs', [{'steps_per_restart': 0}, {'archive_size': 0},
    {'initial_temperature': math.inf}, {'collapse_weight': -1},
    {'mutation_weights': (0, 1, 1, 1)}, {'mutation_weights': (1, 1)}])
def test_invalid_search_configs(kwargs):
    with pytest.raises(ValueError):
        SearchConfig(**kwargs)


@pytest.mark.parametrize('kind', ['within-segment-shuffle', 'position-shuffle', 'bigram-surrogate'])
def test_control_preserved_properties_and_seed(kind):
    segments = [('a', 'b', 'a', 'c', 'a', 'd', 'a'), ('d', 'b', 'c', 'b', 'c'), ()]
    controlled, audit = make_control(segments, kind=kind, seed=9)
    assert (controlled, audit) == make_control(segments, kind=kind, seed=9)
    assert audit['same_unigrams'] and audit['same_segment_lengths']
    if kind == 'position-shuffle':
        assert audit['same_position_unigrams']
    if kind == 'bigram-surrogate':
        assert audit['same_segment_bigrams']


def test_checkpoint_rejects_changed_public_metadata(tmp_path):
    model, candidates = resources()
    config = SearchConfig(steps_per_restart=10)
    first = Annealer(model, candidates, [('x', 'y')], config, input_sha256='source-one')
    first.checkpoint(tmp_path / 'checkpoint.json')
    with pytest.raises(ValueError, match='protocol'):
        Annealer(model, candidates, [('x', 'y')], config,
                 input_sha256='source-two').resume(tmp_path / 'checkpoint.json')
