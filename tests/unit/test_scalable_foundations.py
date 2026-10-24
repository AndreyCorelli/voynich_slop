from itertools import product
import json
import math

import pytest

from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import CipherStream, generate, tokenize
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import BOS, SparseBigram


@pytest.fixture
def inventory(tmp_path):
    resource = Inventory.build(tmp_path / 'inventory.sqlite', ['walks', 'cat', 'dog', 'cat', 'the'])
    yield resource
    resource.close()


def test_inventory_stable_disk_ids_validation_and_ownership(inventory, tmp_path):
    assert [inventory.word(i) for i in range(inventory.size)] == ['cat', 'dog', 'the', 'walks']
    assert inventory.id('walks') == 3
    same = Inventory.build(tmp_path / 'same.sqlite', ['the', 'dog', 'cat', 'walks'])
    assert same.identity == inventory.identity
    same.close()
    with pytest.raises(FileExistsError):
        Inventory.build(inventory.path, ['different'])
    with pytest.raises(KeyError):
        inventory.id('absent')
    with pytest.raises(ValueError):
        inventory.word(True)
    broken = tmp_path / 'invalid.sqlite'
    with pytest.raises(ValueError):
        Inventory.build(broken, ['UPPER'])
    assert not broken.exists()


def test_public_stream_contains_no_private_key_boundaries_or_provenance(tmp_path):
    words, spans = tokenize("The cat’s here.\n\nTHE dog walks! A-cat 42.")
    assert words == ('the', "cat's", 'here', 'the', 'dog', 'walks', 'a', 'cat')
    assert spans[0] == (0, 3)
    public, truth = generate((words,), seed=8)
    assert public == generate((words,), seed=8)[0]
    assert tuple(truth.decoding[c] for c in public.documents[0]) == words
    path = tmp_path / 'public.json'
    public.save(path)
    assert CipherStream.load(path) == public
    value = json.loads(path.read_text())
    assert set(value) == {'documents', 'type_count', 'format_version', 'tokenization', 'sha256'}
    value['key_seed'] = 8
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='Unexpected'):
        CipherStream.load(path)
    with pytest.raises(ValueError):
        CipherStream(((0, 2),), 3)


@pytest.mark.parametrize('unseen', [False, True])
def test_sparse_probability_mass_dense_equivalence_and_chunks(inventory, unseen):
    documents = [[0, 2, 0, 2], [2, 0]] if unseen else [[0, 1, 2, 3], [3, 2, 1, 0]]
    model = SparseBigram.train(inventory, documents)
    assert sum(model.base_probability(i) for i in range(model.size + 1)) == pytest.approx(1)
    for a in range(BOS, model.size):
        assert sum(model.probability(a, b) for b in range(model.size + 1)) == pytest.approx(1)
        assert all(model.probability(a, b) > 0 for b in range(model.size + 1))
    if unseen:
        assert sum(model.base_probability(i) for i in (1, 3)) == pytest.approx(.01)
    dense = model.dense_hmm()
    for sequence in product(range(model.size), repeat=3):
        assert model.score(sequence) == pytest.approx(dense.joint_log_probability(sequence, sequence))
        assert model.score_chunks((sequence[:1], [], sequence[1:])) == model.score(sequence)
    # Independent reference for a known discounted edge and an unseen context.
    if unseen:
        expected = (model.edges[0, 2] - .5) / model.totals[0] + .5 * model.distinct[0] / model.totals[0] * model.base_probability(2)
        assert model.probability(0, 2) == pytest.approx(expected)
        assert model.probability(1, 0) == model.base_probability(0)


def test_document_boundaries_differ_from_storage_chunks(inventory):
    continuous = SparseBigram.train(inventory, [[0, 1, 2]])
    separated = SparseBigram.train(inventory, [[0], [1, 2]])
    assert continuous.training_sha256 != separated.training_sha256
    assert (0, 1) in continuous.edges and (0, 1) not in separated.edges
    assert continuous.score_chunks([[0], [1], [2]]) == continuous.score([0, 1, 2])
    assert continuous.score([0, 1, 2]) != continuous.score([0]) + continuous.score([1, 2])


def test_sparse_serialization_identity_and_inventory_binding(inventory, tmp_path):
    model = SparseBigram.train(inventory, [[0, 2, 0], [2, 3]], config=ModelConfig(unseen_mass=.03))
    path = tmp_path / 'model.sqlite'
    model.save(path)
    loaded = SparseBigram.load(path, inventory)
    assert loaded.identity == model.identity
    assert loaded.score([0, 1, 3]) == model.score([0, 1, 3])
    other = Inventory.build(tmp_path / 'other.sqlite', ['elsewhere'])
    with pytest.raises(ValueError, match='Inventory'):
        SparseBigram.load(path, other)
    other.close()
    with pytest.raises(ValueError):
        model.score([])
    with pytest.raises(ValueError):
        SparseBigram.train(inventory, [[inventory.size]])
    with pytest.raises(ValueError):
        model.dense_hmm(max_types=2)


@pytest.mark.parametrize('kwargs', [{'discount': 0}, {'discount': 1}, {'unseen_mass': 0},
                                   {'unseen_mass': math.nan}, {'language': 'la'}])
def test_invalid_contract(kwargs):
    with pytest.raises(ValueError):
        ModelConfig(**kwargs)


def test_corpus_adapter_keeps_document_continuity_and_private_sentence_metadata():
    from voynich_smt.word_mapping.scalable.corpora import read_ewt
    source = ['# newdoc id = source-one\n', '# text = The cat.\n',
              '# text = It walks!\n', '# newdoc id = source-two\n', '# text = A dog.\n']
    docs = tuple(read_ewt(source))
    assert docs[0].words == ('the', 'cat', 'it', 'walks')
    assert docs[0].sentence_ends == (2, 4)
    public, truth = generate((d.words for d in docs), seed=9)
    assert len(public.documents) == 2
    assert len(public.documents[0]) == 4
    assert 'source-one' not in str(public)
    assert truth.plaintext[0] == docs[0].words


def test_long_continuous_score_is_stable_and_matches_event_cache(inventory):
    from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer
    from voynich_smt.word_mapping.scalable.state import DictionaryState
    model = SparseBigram.train(inventory, [[0, 2, 0, 2], [2, 0]])
    length, word = 50000, 1  # Unattested form, low per-event probability.
    initial = math.log(model.probability(BOS, word)/(1-model.probability(BOS, model.eos)))
    expected = math.fsum((initial, (length-1)*math.log(model.probability(word,word)),
                          math.log(model.probability(word,model.eos))))
    stream = CipherStream(((0,)*length,), 1)
    state = DictionaryState.create(stream,model,[word])
    scorer = DictionaryScorer(model,stream,state)
    assert abs(model.score([word]*length)-expected) < 1e-8
    assert abs(scorer.validate()-expected) < 1e-8
    assert model.score_chunks(([word]*123, [word]*(length-123))) == model.score([word]*length)


def test_dictionary_only_forms_are_contextually_indistinguishable(inventory):
    from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, full_score
    from voynich_smt.word_mapping.scalable.state import DictionaryState
    model = SparseBigram.train(inventory, [[0, 2, 0, 2], [2, 0]])
    stream = CipherStream(((0, 1, 0, 2),), 3)
    first = DictionaryState.create(stream,model,[1,3,0])
    second = DictionaryState.create(stream,model,[3,1,0])
    assert full_score(model,stream,first) == full_score(model,stream,second)
    assert DictionaryScorer(model,stream,first).swap(0,1).log_delta == 0
