"""Offline foundation audit, not annealing or a manuscript recovery claim."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
from time import perf_counter

from voynich_smt.data.corpus import Corpus, digest, write_json
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.corpora import WordStream, from_corpus, from_segments, validate_splits
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.morphology import MorphologyCatalog, WhitakerAnnotator
from voynich_smt.word_mapping.ngram import NgramModel

DEFAULT_OUT = Path('experiments/results/word-mapping/foundation')
VENDOR = Path('data/vendor/whitakers-words')


def caesar_stream():
    corpus = Corpus.load('data/processed/caesar-latin-v2.json')
    manifest = json.loads(Path('data/raw/pg218.txt.manifest.json').read_text())
    raw = Path('data/raw/pg218.txt').read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['sha256']:
        raise ValueError('Caesar raw source checksum mismatch')
    if corpus.source.get('sha256') != manifest['sha256']:
        raise ValueError('Processed Caesar and raw source differ')
    return from_corpus(corpus, 'caesar', raw_text=raw.decode(manifest['encoding']))


def cached_medieval_streams():
    # Existing audited loaders use local source() reads; never invoke fetch/run.
    from benchmarks.expanded_medieval_latin import WORKS, load_work
    from benchmarks.historical_word_lengths import latin_segments
    streams = {}
    for name, filename, incipit in [
        ('aquinas', 'latin-aquinas-ente.html', 'Quia parvus error'),
        ('caroli', 'latin-caroli.html', 'Secundis sedentibus')]:
        # Source file names/incipits are taken from the existing source catalog.
        segments, manifest = latin_segments(filename, incipit)
        streams[name] = from_segments(segments, name, source=manifest)
    for work in WORKS:
        segments, manifests, audit = load_work(work)
        streams[work['id']] = from_segments(segments, work['id'],
            source={'manifests': manifests, 'extraction_audit': audit})
    return streams


def partition(stream, max_words):
    """Contiguous complete segments; cuts are chosen without plaintext scoring."""
    accepted = 0
    last_segment = None
    records = []
    for record in stream.records:
        if accepted >= max_words and record.segment_id != last_segment:
            break
        records.append(record)
        accepted += record.surface is not None
        last_segment = record.segment_id
    selected = WordStream(tuple(records), {**stream.provenance,
        'parent_sha256': stream.identity, 'selection': {'max_words': max_words,
            'cut_policy': 'finish current segment'}})
    segment_ids = list(dict.fromkeys(r.segment_id for r in records if r.surface is not None))
    if len(segment_ids) < 3:
        raise ValueError('Need at least three complete segments for splits')
    train_end = max(1, min(len(segment_ids) - 2, int(len(segment_ids) * 0.7)))
    dev_end = max(train_end + 1, min(len(segment_ids) - 1, int(len(segment_ids) * 0.85)))
    groups = {'train': set(segment_ids[:train_end]), 'development': set(segment_ids[train_end:dev_end]),
              'test': set(segment_ids[dev_end:])}
    splits = {name: selected.select(lambda r, ids=ids: r.segment_id in ids,
        description={'split': name, 'segment_ids': sorted(ids), 'strategy': 'contiguous 70/15/15 segments'})
        for name, ids in groups.items()}
    return selected, splits


def run(out, *, max_words=2000, seed=42, medieval=False, prepare_only=False):
    started = perf_counter()
    out = Path(out)
    config = {'version': 1, 'max_words': max_words, 'seed': seed, 'medieval': medieval}
    if prepare_only:
        config['prepare_only'] = True
    if (out / 'config.json').exists() and json.loads((out / 'config.json').read_text()) != config:
        raise ValueError('Existing output uses another config; select a new --out directory')
    write_json(out / 'config.json', config)
    caesar = caesar_stream()
    caesar.save(out / 'corpora/caesar-full.json')
    eva = from_corpus(Corpus.load('data/processed/zl-eva.json'), 'zl-eva')
    eva.save(out / 'corpora/voynich.json')
    if medieval:
        for name, stream in cached_medieval_streams().items():
            stream.save(out / f'corpora/{name}.json')
    selected, splits = partition(caesar, max_words)
    selected.save(out / 'corpora/caesar-selected.json')
    split_hashes = validate_splits(splits)
    for name, stream in splits.items():
        stream.save(out / f'splits/{name}.json')
    write_json(out / 'splits/manifest.json', split_hashes)
    train = splits['train']
    model = NgramModel.train(train.segments(), training_sha256=train.identity)
    model.save(out / 'model.json')
    annotator = WhitakerAnnotator(VENDOR)
    morphology = annotator.catalog(model.vocabulary, training_sha256=train.identity)
    morphology.save(out / 'morphology-training.json')
    candidates = CandidateCatalog.build(train.segments(), morphology, training_sha256=train.identity)
    write_json(out / 'candidates.json', asdict(candidates))
    if prepare_only:
        report = {'config': config, 'python': platform.python_version(), 'splits': split_hashes,
            'model_sha256': model.identity, 'morphology_sha256': morphology.identity,
            'candidate_forms': len(candidates.forms), 'rows': [],
            'unrecognized_training_forms': sum(not a for a in morphology.entries.values()),
            'elapsed_seconds': perf_counter() - started,
            'scope': 'preparation only; no development/test scoring or test fixtures'}
        write_json(out / 'report.json', report)
        return report
    # Truth annotations are evaluation-only and never enlarge candidate sets.
    test = splits['test']
    evaluation_morphology = annotator.catalog(
        set(model.vocabulary) | {w for s in test.segments() for w in s},
        training_sha256=test.identity)
    evaluation_morphology.save(out / 'truth/morphology-evaluation.json')
    rows = []
    for kind in ('one-to-one', 'homophonic', 'frequency-distorting', 'lossy'):
        public, truth = generate(test.segments(), source={'source_id': 'caesar-test',
            'stream_sha256': test.identity}, seed=seed, kind=kind)
        write_json(out / f'fixtures/{kind}.json', asdict(public))
        write_json(out / f'truth/{kind}.json', asdict(truth))
        mapping = candidates.initialize(public.segments, active_types=300, seed=seed)
        write_json(out / f'dictionaries/{kind}-frequency.json', mapping.export(morphology))
        rows.append({'kind': kind, 'public_sha256': public.identity,
            'candidate_token_coverage': sum(w in candidates.form_counts for s in truth.plaintext for w in s)
                / sum(map(len, truth.plaintext)),
            'frequency_baseline': recovery(public, truth, mapping, morphology=evaluation_morphology),
            'score': asdict(model.score(mapping.render(public.segments)))})
    report = {'config': config, 'python': platform.python_version(),
        'splits': split_hashes, 'model_sha256': model.identity,
        'morphology_sha256': morphology.identity, 'candidate_forms': len(candidates.forms),
        'unrecognized_training_forms': sum(not a for a in morphology.entries.values()),
        'development_score': asdict(model.score(splits['development'].segments())),
        'test_score': asdict(model.score(test.segments())), 'rows': rows,
        'elapsed_seconds': perf_counter() - started,
        'scope': 'foundation/frequency baseline only; no search or decipherment inference'}
    write_json(out / 'report.json', report)
    return report


def validate(out):
    out = Path(out)
    streams = {name: WordStream.load(out / f'splits/{name}.json')
               for name in ('train', 'development', 'test')}
    report = json.loads((out / 'report.json').read_text())
    assert validate_splits(streams) == report['splits']
    model = NgramModel.load(out / 'model.json')
    reference = NgramModel.train(streams['train'].segments(), model.config,
                                training_sha256=streams['train'].identity)
    assert reference.identity == model.identity == report['model_sha256']
    annotator = WhitakerAnnotator(VENDOR)
    catalog = MorphologyCatalog.load(out / 'morphology-training.json', expected_resource=annotator.resource)
    assert catalog.identity == report['morphology_sha256']
    for word in sorted(catalog.entries)[::max(1, len(catalog.entries) // 32)]:
        assert annotator.annotate(word) == catalog.entries[word]
    candidates = CandidateCatalog.build(streams['train'].segments(), catalog,
                                        training_sha256=streams['train'].identity)
    assert digest(asdict(candidates)) == digest(json.loads((out / 'candidates.json').read_text()))
    prepare_only = report['config'].get('prepare_only', False)
    eval_catalog = None if prepare_only else MorphologyCatalog.load(out / 'truth/morphology-evaluation.json',
                                         expected_resource=annotator.resource)
    for row in report['rows']:
        kind = row['kind']
        public, truth = generate(streams['test'].segments(), source={
            'source_id': 'caesar-test', 'stream_sha256': streams['test'].identity},
            seed=report['config']['seed'], kind=kind)
        assert digest(asdict(public)) == digest(json.loads((out / f'fixtures/{kind}.json').read_text()))
        assert digest(asdict(truth)) == digest(json.loads((out / f'truth/{kind}.json').read_text()))
        mapping = candidates.initialize(public.segments, active_types=300, seed=report['config']['seed'])
        assert recovery(public, truth, mapping, morphology=eval_catalog) == row['frequency_baseline']
        assert asdict(reference.score(mapping.render(public.segments))) == row['score']
    if not prepare_only:
        for name in ('development', 'test'):
            assert asdict(reference.score(streams[name].segments())) == report[f'{name}_score']
    else:
        assert not report['rows'] and not (out / 'truth').exists() and not (out / 'fixtures').exists()
    # Validate all exported corpora, including optional medieval adapters.
    for path in (out / 'corpora').glob('*.json'):
        WordStream.load(path)
    result = {'validated': True, 'model_sha256': model.identity, 'fixture_count': len(report['rows'])}
    write_json(out / 'validation.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--max-words', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--medieval', action='store_true', help='Also export cached medieval streams')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--prepare-only', action='store_true', help='Freeze splits/models without evaluating held-out text')
    args = parser.parse_args()
    if args.max_words < 1:
        parser.error('--max-words must be positive')
    result = validate(args.out) if args.validate else run(args.out,
        max_words=args.max_words, seed=args.seed, medieval=args.medieval, prepare_only=args.prepare_only)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
