from dataclasses import asdict
from itertools import combinations

import pytest

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.neighborhood import audit_neighborhood
from voynich_smt.word_mapping.ngram import NgramModel


def test_exhaustive_neighborhood_matches_full_scoring_and_preserves_inputs():
    training = [('a', 'b', 'c', 'a'), ('d', 'a', 'b')] * 20
    plaintext = [('a', 'b', 'c', 'a'), ('b', 'a')]
    model = NgramModel.train(training)
    morphology = MorphologyCatalog({w: [] for w in model.vocabulary}, {}, model.training_sha256)
    candidates = CandidateCatalog.build(training, morphology, training_sha256=model.training_sha256)
    public, truth = generate(plaintext, seed=4, source={})
    initial = digest((asdict(candidates), asdict(public), asdict(truth)))
    actual = audit_neighborhood(model, candidates, public, truth, top=100)
    assignments = {w: candidates.forms.index(f) for w, f in truth.decoding.items()}
    mapping = WordMapping(candidates.forms, assignments)
    baseline = model.score(mapping.render(public.segments)).log_likelihood
    expected = {'replacement': [], 'injective_replacement': [], 'swap': []}
    for word, old in assignments.items():
        for form in range(len(candidates.forms)):
            if form == old:
                continue
            changed = WordMapping(candidates.forms, {**assignments, word: form})
            delta = model.score(changed.render(public.segments)).log_likelihood - baseline
            expected['replacement'].append(delta)
            if not changed.collapse_penalty:
                expected['injective_replacement'].append(delta)
    for a, b in combinations(assignments, 2):
        changed = WordMapping(candidates.forms, {**assignments, a: assignments[b], b: assignments[a]})
        expected['swap'].append(model.score(changed.render(public.segments)).log_likelihood - baseline)
    for kind, deltas in expected.items():
        counts = actual['counts'][kind]
        assert counts['evaluated'] == len(deltas)
        assert counts.get('improving', 0) == sum(d > 1e-8 for d in deltas)
        assert sorted(e['objective_delta'] for e in actual['examples'][kind]) == pytest.approx(sorted(deltas))
        for example in actual['examples'][kind]:
            assert sum(t['log_delta'] for t in example['terms']) == pytest.approx(example['objective_delta'])
    assert digest((asdict(candidates), asdict(public), asdict(truth))) == initial


def test_neighborhood_rejects_missing_candidates_instead_of_augmenting_truth():
    model = NgramModel.train([('a', 'b')])
    morphology = MorphologyCatalog({w: [] for w in model.vocabulary}, {}, model.training_sha256)
    candidates = CandidateCatalog.build([('a', 'b')], morphology, training_sha256=model.training_sha256)
    public, truth = generate([('a', 'missing')], seed=2, source={})
    with pytest.raises(ValueError, match='fully covered'):
        audit_neighborhood(model, candidates, public, truth)


def test_caesar_html_adapter_excludes_navigation_and_preserves_boundaries(tmp_path, monkeypatch):
    from benchmarks import word_mapping_long_context as runner
    monkeypatch.setattr(runner, 'SOURCE_ROOT', tmp_path)
    (tmp_path / 'voinich-caesar-gall5.html').write_text('''<h1>HEADER</h1>
      <p class="internal_navigation">1 2 footer</p>
      <p>[<a name="1">1</a>] In terra est. <font size=2>2</font> Aqua est.</p>
      <p>[2] Terra bona est.</p><p>FOOTER</p>''')
    stream = runner.extension_stream('gall5')
    assert stream.segments() == (('in', 'terra', 'est'), ('aqua', 'est'), ('terra', 'bona', 'est'))
    assert stream.provenance['source']['chapters'] == 2


def test_known_morphology_failure_is_recorded_and_other_errors_raise(tmp_path):
    from voynich_smt.word_mapping.morphology import WhitakerAnnotator
    class Engine:
        def parse(self, word):
            raise KeyError('PACK' if word == 'qu' else 'OTHER')
    annotator = object.__new__(WhitakerAnnotator)
    annotator.engine, annotator.resource, annotator.annotation_failures = Engine(), {}, {}
    catalog = annotator.catalog(['qu'], training_sha256='train')
    assert catalog.entries['qu'] == []
    assert catalog.annotation_failures['qu']
    path = tmp_path / 'morphology.json'
    catalog.save(path)
    assert MorphologyCatalog.load(path).identity == catalog.identity
    with pytest.raises(KeyError, match='OTHER'):
        annotator.annotate('other')


def test_long_foundation_disjoint_bundles_untouched_test_and_validation(tmp_path, monkeypatch):
    from pathlib import Path
    from benchmarks import word_mapping_long_context as runner
    from voynich_smt.word_mapping.corpora import WordStream, from_segments, validate_splits
    if not Path('data/vendor/whitakers-words').exists():
        pytest.skip('Pinned morphology resource not cached')
    sources, parent = tmp_path / 'sources', tmp_path / 'parent'
    sources.mkdir()
    monkeypatch.setattr(runner, 'SOURCE_ROOT', sources)
    monkeypatch.setattr(runner, 'PARENT', parent)
    for book in runner.BOOKS:
        (sources / f'voinich-caesar-{book}.html').write_text(
            '<p>[1] In terra est aqua bona terra.</p>')
    full = from_segments([('in', 'terra', 'est', 'aqua', 'bona', 'terra')] * 90, 'caesar', source={})
    test = full.select(lambda r: r.segment_id == '89', description={'test': True})
    full.save(parent / 'corpora/caesar-full.json')
    test.save(parent / 'splits/test.json')
    out = tmp_path / 'output'
    manifest, bundles = runner.prepare(out)
    assert sum(map(len, bundles['pooled'].segments())) == 534
    assert sum(sum(map(len, s.segments())) for n, s in bundles.items() if n != 'pooled') == 534
    validate_splits({n: s for n, s in bundles.items() if n != 'pooled'})
    for name, stream in bundles.items():
        base = out / name / 'foundation'
        assert WordStream.load(base / 'splits/test.json').identity == test.identity
        train = WordStream.load(base / 'splits/train.json')
        validate_splits({'train': train, 'development': stream, 'test': test})
    assert runner.prepare(out, resume=True, write=False)[0] == manifest
    altered = bundles['pooled'].select(lambda r: r.segment_id == '1', description={})
    altered.save(out / 'pooled/foundation/splits/development.json')
    with pytest.raises(ValueError, match='differs from reconstruction'):
        runner.prepare(out, resume=True, write=False)
