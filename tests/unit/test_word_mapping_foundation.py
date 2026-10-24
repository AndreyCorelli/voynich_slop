from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import random

import pytest

from voynich_smt.data.corpus import digest
from voynich_smt.data.latin import normalize as latin
from voynich_smt.data.voynich import normalize as eva
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.corpora import Normalization, WordStream, from_corpus, from_segments, validate_splits
from voynich_smt.word_mapping.evaluation import frozen_holdout, recovery
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.mapping import WordMapping, occurrence_index
from voynich_smt.word_mapping.morphology import MorphologyCatalog, WhitakerAnnotator
from voynich_smt.word_mapping.ngram import BOS, EOS, OOV, NgramConfig, NgramModel


def test_latin_raw_spelling_offsets_boundaries_and_exclusion(tmp_path):
    raw = ('*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\n'
           'GALLIA est omnis. Jūlius vivit xxw aqua! terra\n\nest\n'
           '*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    corpus = latin({'sha256': 'example'}, raw)
    stream = from_corpus(corpus, 'caesar', raw_text=raw)
    assert stream.segments() == (('gallia', 'est', 'omnis'), ('iulius', 'uiuit'), ('aqua',), ('terra',), ('est',))
    assert stream.records[3].original == 'Jūlius'
    assert stream.records[3].metadata['char_start'] == raw.index('Jūlius')
    assert stream.records[5].surface is None
    stream.save(tmp_path / 'stream.json')
    loaded = WordStream.load(tmp_path / 'stream.json')
    assert loaded.identity == stream.identity
    assert loaded.segments() == stream.segments()
    with pytest.raises(ValueError, match='offsets'):
        from_corpus(corpus, 'caesar', raw_text=raw.replace('Jūlius', 'Iūlius'))
    with pytest.raises(ValueError, match='boundaries'):
        from_corpus(replace(corpus, normalization={'preserve_spaces': False}), 'caesar')


def test_eva_locus_folio_metadata_and_missing_currier():
    raw = ('#=IVTFF Eva- 2.0\n<f1r> <! $I=H $L=A>\n'
           '<f1r.1,@P0> ar.or.d?n.ar\n<f1r.2,@P0> ar.ol\n'
           '<f1v> <! $I=S>\n<f1v.1,@P0> ar')
    corpus = eva({}, raw)
    stream = from_corpus(corpus, 'eva')
    assert stream.segments() == (('ar', 'or'), ('ar',), ('ar', 'ol'), ('ar',))
    assert stream.records[0].metadata['page_variables']['L'] == 'A'
    assert stream.records[-1].metadata['page_variables'].get('L') is None
    assert from_corpus(corpus, 'eva', cross_locus=True).segments() == (
        ('ar', 'or'), ('ar', 'ar', 'ol'), ('ar',))


def test_cached_stream_and_selection_do_not_join_gaps():
    stream = from_segments([['in', 'terra', None, 'est'], ['aqua', 'est']], 'latin', source={})
    assert stream.segments() == (('in', 'terra'), ('est',), ('aqua', 'est'))
    selected = stream.select(lambda r: r.surface != 'terra', description='omit terra')
    assert selected.segments() == (('in',), ('est',), ('aqua', 'est'))
    assert 'sentence-unavailable' in stream.provenance['boundary_policy']
    assert Normalization().apply('Jūlius vivit') == 'iulius uiuit'


def test_split_overlap_and_duplicated_passages():
    stream = from_segments([['a', 'b', 'c']], 'one', source={})
    train = stream.select(lambda r: r.record_index < 2, description='train')
    test = stream.select(lambda r: r.record_index == 2, description='test')
    assert validate_splits({'train': train, 'test': test})['train'] == train.identity
    with pytest.raises(ValueError, match='overlap'):
        validate_splits({'train': stream, 'test': test})
    words = [f'w{i}' for i in range(10)]
    with pytest.raises(ValueError, match='Duplicated passage'):
        validate_splits({'a': from_segments([words], 'a', source={}),
                         'b': from_segments([words], 'b', source={})})


def test_stream_tampering_and_duplicate_records_rejected(tmp_path):
    stream = from_segments([['terra']], 'one', source={})
    with pytest.raises(ValueError, match='Duplicate'):
        WordStream(stream.records * 2, {})
    path = tmp_path / 'stream.json'
    stream.save(path)
    value = json.loads(path.read_text())
    value['records'][0]['surface'] = 'aqua'
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='checksum'):
        WordStream.load(path)


def test_hand_calculated_smoothed_conditionals_and_normalization():
    model = NgramModel.train([['in', 'terra']], NgramConfig(alpha=1, backoff_strength=1))
    i, t = model.form_ids['in'], model.form_ids['terra']
    # Three training events, four possible outputs (two words, EOS, OOV).
    p1 = 2 / 7
    p2 = (1 + p1) / 2
    p3 = (1 + p2) / 2
    assert model.probability(BOS, BOS, i) == pytest.approx((p2 + p3) / 2)
    assert model.probability(BOS, i, t) == pytest.approx((p2 + p3) / 2)
    for a, b in [(BOS, BOS), (BOS, i), (i, t), (t, t), (OOV, OOV)]:
        assert sum(model.probability(a, b, c) for c in range(1, 5)) == pytest.approx(1)
    with pytest.raises(ValueError):
        model.probability(BOS, BOS, BOS)


def test_unknown_barriers_source_boundaries_and_oov_are_distinct():
    model = NgramModel.train([['in', 'terra'], ['est']])
    broken = model.score([['in', None, 'terra']])
    separated = model.score([['in'], ['terra']])
    assert broken.log_likelihood == separated.log_likelihood
    assert broken.covered_tokens == 2 and broken.total_tokens == 3
    assert broken.prediction_events == 4 and broken.coverage == 2 / 3
    assert model.score([[None, None]]).per_token is None
    assert model.score([['unseen']]).oov_tokens == 1
    assert model.score([['unseen']]).covered_tokens == 1
    assert (model.form_ids['terra'], model.form_ids['est']) not in model.bigram
    assert model.score([['in', 'terra']]).prediction_events == 3


def test_ngram_round_trip_and_tampering(tmp_path):
    model = NgramModel.train([['terra', 'est'], ['aqua', 'est']], NgramConfig(min_count=2))
    assert model.vocabulary == ('est',)
    assert model.unigram[OOV] == 2
    path = tmp_path / 'model.json'
    model.save(path)
    loaded = NgramModel.load(path)
    assert loaded.identity == model.identity
    assert loaded.score([['est', 'aqua']]) == model.score([['est', 'aqua']])
    value = json.loads(path.read_text())
    value['unigram'][0][1] += 1
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='checksum'):
        NgramModel.load(path)


@pytest.mark.parametrize('kwargs', [{'min_count': 0}, {'alpha': 0},
    {'backoff_strength': -1}, {'bigram_weight': 2}, {'alpha': math.nan}])
def test_bad_ngram_config(kwargs):
    with pytest.raises(ValueError):
        NgramConfig(**kwargs)


def test_randomized_smoothed_probability_distributions():
    rng = random.Random(23)
    for _ in range(20):
        sequences = [rng.choices(['a', 'b', 'c'], k=rng.randint(1, 15)) for _ in range(5)]
        model = NgramModel.train(sequences)
        for _ in range(10):
            a, b = rng.choices(range(len(model.vocabulary) + 3), k=2)
            probabilities = [model.probability(a, b, c) for c in range(1, len(model.vocabulary) + 3)]
            assert all(0 < p <= 1 for p in probabilities)
            assert sum(probabilities) == pytest.approx(1)


def test_deterministic_dictionary_many_to_one_and_exports():
    mapping = WordMapping(('terrae', 'est'), {'a': 0, 'b': 0, 'c': 1, 'd': None})
    assert mapping.render([['a', 'c', 'b', 'd', 'unseen']]) == (('terrae', 'est', 'terrae', None, None),)
    assert mapping.collapse_penalty == 1
    assert occurrence_index([['a', 'b', 'a'], ['a']])['a'] == ((0, 0), (0, 2), (1, 0))
    assert mapping.export()[0]['surface'] == 'terrae'
    with pytest.raises(ValueError):
        WordMapping(('terra',), {'a': True})


@pytest.fixture
def annotator():
    vendor = Path('data/vendor/whitakers-words')
    if not vendor.exists():
        pytest.skip('Pinned morphology resource not cached')
    return WhitakerAnnotator(vendor)


def test_real_morphology_retains_inflections_and_surface(annotator, tmp_path):
    catalog = annotator.catalog(['terrae', 'terra', 'est', 'notalatinwordxyz'], training_sha256='train')
    features = {tuple(sorted(i['features'].items())) for a in catalog.entries['terrae'] for i in a['inflections']}
    assert len(features) >= 3
    cases = {i['features'].get('Case') for a in catalog.entries['terrae'] for i in a['inflections']}
    assert {'GEN', 'DAT', 'NOM'} <= cases
    assert not catalog.entries['notalatinwordxyz']
    assert catalog.lemma_ids('terra') & catalog.lemma_ids('terrae')
    assert WordMapping(('terrae',), {'x': 0}).export(catalog)[0]['surface'] == 'terrae'
    path = tmp_path / 'morphology.json'
    catalog.save(path)
    assert MorphologyCatalog.load(path, expected_resource=annotator.resource).identity == catalog.identity
    with pytest.raises(ValueError, match='resource changed'):
        MorphologyCatalog.load(path, expected_resource={})


def test_training_candidates_and_ambiguity_weights():
    catalog = MorphologyCatalog({'a': [{'lemma_id': 'L1'}, {'lemma_id': 'L2'}],
                                'b': [{'lemma_id': 'L1'}], 'unrecognized': []}, {}, 'train')
    segments = [['a', 'a', 'b', 'unrecognized']]
    candidates = CandidateCatalog.build(segments, catalog, training_sha256='train')
    assert candidates.lemma_counts == {'L1': 2.0, 'L2': 1.0}
    assert 'unrecognized' in candidates.forms
    for mode in ('frequency', 'random', 'lemma-aware'):
        first = candidates.initialize([['x', 'y', 'x', 'z']], active_types=2, seed=4, mode=mode)
        assert first == candidates.initialize([['x', 'y', 'x', 'z']], active_types=2, seed=4, mode=mode)
        assert set(first.assignments) == {'x', 'y'}
        assert first.render([['z']]) == ((None,),)
    with pytest.raises(ValueError, match='training inputs'):
        CandidateCatalog.build(segments, catalog, training_sha256='test')


@pytest.mark.parametrize('kind', ['one-to-one', 'homophonic', 'frequency-distorting', 'lossy'])
def test_synthetic_truth_separation_directions_and_ceiling(kind):
    plaintext = [['terra', 'est', 'terra', 'aqua'] * 20]
    public, truth = generate(plaintext, source={'source_id': 'heldout'}, seed=7, kind=kind)
    assert (public, truth) == generate(plaintext, source={'source_id': 'heldout'}, seed=7, kind=kind)
    assert 'plaintext' not in asdict(public) and 'decoding' not in asdict(public)
    assert 'terra' not in json.dumps(asdict(public))
    forms = tuple(sorted(set(truth.decoding.values())))
    mapping = WordMapping(forms, {c: forms.index(p) for c, p in truth.decoding.items()})
    result = recovery(public, truth, mapping)
    assert result['exact_token_accuracy'] == truth.deterministic_accuracy_ceiling
    assert result['coverage'] == 1
    if kind == 'lossy':
        assert truth.deterministic_accuracy_ceiling < 1
    else:
        assert result['exact_type_accuracy'] == 1
        if kind != 'one-to-one':
            assert mapping.collapse_penalty > 0
    with pytest.raises(ValueError, match='another fixture'):
        recovery(public, replace(truth, public_sha256='wrong'), mapping)


def test_exact_vs_lemma_recovery_and_frozen_holdout(annotator):
    public, truth = generate([['terra', 'terra']], source={}, seed=3)
    catalog = annotator.catalog(['terra', 'terram'], training_sha256='evaluation')
    word = public.segments[0][0]
    mapping = WordMapping(('terram',), {word: 0})
    result = recovery(public, truth, mapping, morphology=catalog)
    assert result['exact_token_accuracy'] == 0
    assert result['lemma_token_accuracy'] == 1
    before = digest(asdict(mapping))
    model = NgramModel.train([['terram', 'terra']])
    score = frozen_holdout(model, mapping, [[word, 'new', word]])
    assert score.coverage == 2 / 3
    assert score.log_likelihood == model.score([['terram'], ['terram']]).log_likelihood
    assert digest(asdict(mapping)) == before
