from dataclasses import replace

import pytest

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, full_score
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import CandidateRetriever, ContextIndex, RetrievalConfig
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram
from voynich_smt.word_mapping.scalable.state import DictionaryState


@pytest.fixture
def scorer(tmp_path):
    inventory = Inventory.build(tmp_path / 'inventory.sqlite', ['a', 'b', 'c', 'd', 'e'])
    model = SparseBigram.train(inventory, [[0, 1, 0, 2, 0]] * 3 + [[1, 2, 1]])
    stream = CipherStream(((0, 1, 0, 2), (2, 1)), 3)
    scorer = DictionaryScorer(model, stream, DictionaryState.create(stream, model, (0, 1, 2)))
    yield scorer
    inventory.close()


def test_context_indexes_equal_exhaustive_full_inventory_top_k(scorer):
    model = scorer.model
    index = ContextIndex(model, limit=3, cache_queries=2)
    for count in (1, 2, 3):
        for left in range(BOS, model.size):
            expected = tuple(sorted(range(model.size), key=lambda w: (-model.probability(left, w), w))[:count])
            assert index.query('successors', left, count=count) == expected
        for right in range(model.size + 1):
            expected = tuple(sorted(range(model.size), key=lambda w: (-model.probability(w, right), w))[:count])
            assert index.query('predecessors', right, count=count) == expected
    assert len(index._cache) <= 2
    index.query('successors', 0)
    before = index.cache_hits
    index.query('successors', 0)
    assert index.cache_hits == before + 1
    with pytest.raises(ValueError):
        index.query('successors', 0, count=4)


def test_candidate_scores_are_full_swap_deltas_and_refresh_after_changes(scorer):
    config = RetrievalConfig(active_limit=5, total_entries=10, per_context=3, random_candidates=1)
    retriever = CandidateRetriever(scorer, config=config, seed=9)
    row = retriever.get(0)
    original = scorer.state
    for candidate in row.candidates:
        move = scorer.assign_or_swap(0, candidate.word_id)
        key = list(original.assignments)
        for c, w in move.changes:
            key[c] = w
        expected = full_score(scorer.model, scorer.stream,
                              DictionaryState.create(scorer.stream, scorer.model, key))
        assert candidate.log_delta == pytest.approx(expected - scorer.score)
    assert scorer.state == original
    scorer.commit(scorer.swap(1, 2))
    refreshed = retriever.get(0)
    assert refreshed.generation == scorer.generation != row.generation
    assert all(c.log_delta == pytest.approx(scorer.assign_or_swap(0, c.word_id).log_delta)
               for c in refreshed.candidates)
    assert scorer.assignment(0) in {c.word_id for c in refreshed.candidates}


def test_budgets_archive_reintroduction_and_replay(scorer):
    config = RetrievalConfig(active_limit=2, total_entries=4, per_context=3, archive_per_type=2)
    first = CandidateRetriever(scorer, config=config, seed=7)
    second = CandidateRetriever(scorer, config=config, seed=7)
    for c in (0, 1, 2, 0, 1):
        row = first.refresh(c)
        assert row == second.refresh(c)
        assert len(row.candidates) <= 2 and row.pool_size <= config.pool_limit
        assert first.entry_count <= 4
        assert len(first.archives) <= 2
    # A bounded archive contributes evicted IDs back into the scored pool.
    archived = first.archives[1]
    assert archived
    config_wide = replace(config, active_limit=5, total_entries=10)
    first.config = config_wide
    row = first.refresh(1)
    assert any('archive' in c.sources for c in row.candidates if c.word_id in archived)


def test_starved_shortlist_does_not_block_full_inventory_exploration(scorer):
    config = RetrievalConfig(active_limit=1, total_entries=2, per_context=1,
                             random_candidates=1, exploration_probability=1.)
    retriever = CandidateRetriever(scorer, config=config, seed=2)
    row = retriever.get(0)
    assert [c.word_id for c in row.candidates] == [scorer.assignment(0)]
    seen = set()
    for _ in range(100):
        move, source = retriever.propose(0)
        assert source == 'exploration'
        key = dict(move.changes)
        seen.add(key.get(0, scorer.assignment(0)))
    assert seen == set(range(scorer.model.size))  # Includes unattested inventory forms.
    scorer.validate()


@pytest.mark.parametrize('kwargs', [{'active_limit': 0}, {'pool_limit': 10},
                                   {'exploration_probability': 0}, {'total_entries': 1}])
def test_invalid_retrieval_contract(kwargs):
    with pytest.raises(ValueError):
        RetrievalConfig(**kwargs)


@pytest.mark.parametrize('discount, reserve', [(.1, .01), (.5, .2), (.9, .4)])
def test_context_exactness_across_random_sparse_models(scorer, discount, reserve):
    import random
    from types import SimpleNamespace
    from voynich_smt.word_mapping.scalable.config import ModelConfig
    rng = random.Random(45)
    inventory = SimpleNamespace(size=5, identity=scorer.model.inventory_sha256)
    for _ in range(10):
        docs = [[rng.randrange(4) for _ in range(rng.randrange(1, 9))] for _ in range(4)]
        model = SparseBigram.train(inventory, docs, config=ModelConfig(discount=discount, unseen_mass=reserve))
        index = ContextIndex(model, limit=2, cache_queries=2)
        for neighbor in range(BOS, model.size):
            assert index.query('successors', neighbor) == tuple(sorted(range(5), key=lambda w: (-model.probability(neighbor, w), w))[:2])
        for neighbor in range(model.size + 1):
            assert index.query('predecessors', neighbor) == tuple(sorted(range(5), key=lambda w: (-model.probability(w, neighbor), w))[:2])


def test_tight_global_budgets_include_archive_cap(scorer):
    config = RetrievalConfig(active_limit=1, total_entries=2, per_context=3, archive_per_type=32)
    retriever = CandidateRetriever(scorer, config=config, seed=7)
    for cipher in (0, 1, 2, 0):
        retriever.refresh(cipher)
        assert retriever.entry_count == sum(len(r.candidates) for r in retriever.rows.values()) <= 2
        assert retriever.archive_entry_count == sum(map(len, retriever.archives.values())) <= 2


def test_attested_mixture_preserves_unseen_support_and_expected_mass(scorer):
    retriever=CandidateRetriever(scorer,config=RetrievalConfig(attested_mix=.5),seed=83)
    samples=[retriever.random_word() for _ in range(5000)]
    assert set(samples)==set(range(scorer.model.size))
    fraction=sum(bool(scorer.model.counts[w]) for w in samples)/len(samples)
    # Three observed forms in a five-form inventory: .5 + .5*(3/5) = .8.
    assert .77 < fraction < .83
    original=CandidateRetriever(scorer,config=RetrievalConfig(),seed=83)
    import random
    expected=random.Random(83)
    assert [original.random_word() for _ in range(100)]==[expected.randrange(scorer.model.size) for _ in range(100)]
    for value in (-.1,1.,float('nan')):
        with pytest.raises(ValueError): RetrievalConfig(attested_mix=value)
