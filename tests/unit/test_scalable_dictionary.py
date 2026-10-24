from dataclasses import replace
from itertools import permutations, product
import random

import pytest

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, EventIndex, full_score
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.state import CandidateConflict, DictionaryState


@pytest.fixture
def resources(tmp_path):
    inventory = Inventory.build(tmp_path / 'inventory.sqlite', ['a', 'b', 'c', 'd'])
    model = SparseBigram.train(inventory, [[0, 1, 0, 2, 0], [1, 2, 1], [2]])
    yield inventory, model
    inventory.close()


def test_complete_state_identity_binding_and_random_initialization(resources):
    _, model = resources
    stream = CipherStream(((0, 1, 2),), 3)
    state = DictionaryState.random(stream, model, seed=3)
    assert state == DictionaryState.random(stream, model, seed=3)
    assert len(set(state.assignments)) == 3
    with pytest.raises(ValueError, match='injective'):
        DictionaryState.create(stream, model, [0, 0, 1])
    with pytest.raises(ValueError):
        DictionaryState.create(stream, model, [0, 1])
    with pytest.raises(ValueError):
        DictionaryState.create(stream, model, [0, True, 2])
    with pytest.raises(ValueError):
        replace(state, cipher_sha256='wrong').bind(stream, model)
    with pytest.raises(ValueError, match='smaller'):
        DictionaryState.random(CipherStream(((0, 1, 2, 3, 4),), 5), model, seed=3)


def test_sparse_matching_agrees_with_exhaustive_feasibility(resources):
    _, model = resources
    stream = CipherStream(((0, 1, 2),), 3)
    subsets = [tuple(i for i in range(3) if mask & (1 << i)) for mask in range(8)]
    for rows in product(subsets, repeat=3):
        possible = [key for key in permutations(range(3)) if all(w in row for w, row in zip(key, rows))]
        if possible:
            state = DictionaryState.from_candidates(stream, model, rows)
            assert state.assignments in possible
        else:
            with pytest.raises(CandidateConflict):
                DictionaryState.from_candidates(stream, model, rows)
    assert DictionaryState.from_candidates(stream, model, [(0, 1), (0,), (1, 2)]).assignments == (1, 0, 2)
    with pytest.raises(CandidateConflict):
        DictionaryState.from_candidates(stream, model, [(0,), (0,), (1, 2)])


@pytest.mark.parametrize('documents', [((0,),), ((0, 0, 0, 0),),
    ((0, 1, 0, 1, 0),), ((0, 1, 1, 0), (1,), (0, 0, 1))])
def test_exhaustive_local_deltas_and_overlap_match_full_rescoring(resources, documents):
    _, model = resources
    stream = CipherStream(documents, len({w for d in documents for w in d}))
    for key in permutations(range(model.size), stream.type_count):
        state = DictionaryState.create(stream, model, key)
        scorer = DictionaryScorer(model, stream, state)
        before = scorer.score
        assert before == pytest.approx(full_score(model, stream, state), abs=1e-12)
        assert sum(n for _, _, n in scorer.index.events) == sum(map(len, documents)) + len(documents)
        for cipher in range(stream.type_count):
            for word in range(model.size):
                move = scorer.assign_or_swap(cipher, word)
                changed = list(key)
                for c, w in move.changes:
                    changed[c] = w
                after = full_score(model, stream, DictionaryState.create(stream, model, changed))
                assert before + move.log_delta == pytest.approx(after, abs=1e-12)
                assert scorer.state == state  # Rejected/uncommitted proposals have no effect.
                assert scorer.score == before


def test_transactions_ownership_cycles_stale_and_foreign_moves(resources):
    _, model = resources
    stream = CipherStream(((0, 1, 2, 0, 0, 1),), 3)
    state = DictionaryState.create(stream, model, (0, 1, 2))
    scorer = DictionaryScorer(model, stream, state)
    swap = scorer.swap(0, 1)
    replacement = scorer.replace(0, 3)
    other = DictionaryScorer(model, stream, state)
    with pytest.raises(ValueError, match='foreign'):
        other.commit(swap)
    scorer.commit(swap)
    assert scorer.state.assignments == (1, 0, 2)
    assert scorer.owner(1) == 0 and scorer.owner(0) == 1
    with pytest.raises(ValueError, match='Stale'):
        scorer.commit(replacement)
    cycle = scorer.propose({0: 0, 1: 2, 2: 1})
    scorer.commit(cycle)
    assert scorer.state.assignments == (0, 2, 1)
    scorer.validate()
    old = scorer.state
    with pytest.raises(ValueError, match='occupied'):
        scorer.replace(0, 2)
    with pytest.raises(ValueError, match='injectivity'):
        scorer.propose({0: 3, 1: 3})
    with pytest.raises(ValueError):
        scorer.replace(True, 3)
    assert scorer.state == old
    noop = scorer.swap(1, 1)
    assert not noop.changes and noop.log_delta == 0
    scorer.commit(noop)
    scorer.validate()


def test_randomized_accept_reject_sequence_has_no_drift(resources):
    _, model = resources
    rng = random.Random(31)
    docs = (tuple(rng.randrange(3) for _ in range(300)), (2, 2, 0))
    stream = CipherStream(docs, 3)
    scorer = DictionaryScorer(model, stream, DictionaryState.random(stream, model, seed=2))
    for _ in range(1000):
        before = scorer.state
        move = scorer.assign_or_swap(rng.randrange(3), rng.randrange(model.size))
        if rng.random() < .5:
            scorer.commit(move)
        else:
            assert scorer.state == before
        assert scorer.score == pytest.approx(scorer.validate(), abs=1e-8)


@pytest.mark.parametrize('vocabulary_size', [3, 4])
def test_replacement_and_swap_moves_reach_all_small_injective_keys(resources, vocabulary_size):
    _, model = resources
    stream = CipherStream(((0, 1, 2),), 3)
    initial = (0, 1, 2)
    discovered, queue = {initial}, [initial]
    for key in queue:
        scorer = DictionaryScorer(model, stream, DictionaryState.create(stream, model, key))
        for cipher in range(3):
            for word in range(vocabulary_size):
                move = scorer.assign_or_swap(cipher, word)
                next_key = list(key)
                for c, w in move.changes:
                    next_key[c] = w
                next_key = tuple(next_key)
                if next_key not in discovered:
                    discovered.add(next_key)
                    queue.append(next_key)
    assert discovered == set(permutations(range(vocabulary_size), 3))


def test_event_index_can_be_shared_without_sharing_dictionary_mutations(resources):
    _, model = resources
    stream = CipherStream(((0, 0, 1),), 2)
    index = EventIndex.build(stream)
    state = DictionaryState.create(stream, model, (0, 1))
    first = DictionaryScorer(model, stream, state, event_index=index)
    second = DictionaryScorer(model, stream, state, event_index=index)
    assert first.index is second.index
    first.commit(first.swap(0, 1))
    assert second.state == state
    second.validate()
    different = CipherStream(((0, 1, 1),), 2)
    with pytest.raises(ValueError, match='different cipher'):
        DictionaryScorer(model, different, DictionaryState.create(different, model, (0, 1)), event_index=index)


def test_matching_long_augmenting_path_does_not_use_recursive_stack():
    from types import SimpleNamespace
    count = 1500
    stream = CipherStream((tuple(range(count)),), count)
    model = SimpleNamespace(size=count, inventory_sha256='test-only-identity')
    rows = [(i, i + 1) for i in range(count - 1)] + [(0,)]
    state = DictionaryState.from_candidates(stream, model, rows)
    assert state.assignments == tuple(range(1, count)) + (0,)


def test_frequency_initialization_uses_counts_with_stable_id_ties(resources):
    _, model = resources
    stream = CipherStream(((2, 2, 2, 1, 0),), 3)
    # Model word counts: 0=3, 1=3, 2=3, 3=0; ties use ascending ID.
    state = DictionaryState.frequency(stream, model)
    assert state.assignments == (1, 2, 0)
    assert state == DictionaryState.initialize(stream, model, method='frequency', seed=999)
    assert len(set(state.assignments)) == stream.type_count
    with pytest.raises(ValueError, match='initialization'):
        DictionaryState.initialize(stream, model, method='unknown')
    with pytest.raises(ValueError, match='smaller'):
        DictionaryState.frequency(CipherStream(((0, 1, 2, 3, 4),), 5), model)
