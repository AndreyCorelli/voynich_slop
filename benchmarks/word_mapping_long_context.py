"""Disjoint-book Caesar training, larger covered bundles, and local oracle audits."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import hashlib
import json
import multiprocessing
from pathlib import Path
import re

from benchmarks.expanded_medieval_latin import Paragraphs
from benchmarks.word_mapping_ablation import AblationPlan, load_truth, validate as validate_study
from benchmarks.word_mapping_parallel import run as run_searches
from benchmarks.word_mapping_recovery import public_input, resources
from voynich_smt.data.corpus import Corpus, digest, write_json
from voynich_smt.word_mapping.corpora import WordStream, from_corpus, validate_splits
from voynich_smt.word_mapping.coverage import screen_complete_segments
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.word_mapping.neighborhood import audit_neighborhood
from voynich_smt.word_mapping.ngram import NgramModel

BOOKS = ('gall5', 'gall6', 'gall7', 'bc1', 'bc2', 'bc3')
SOURCE_ROOT = Path('data/raw/word-mapping-caesar')
PARENT = Path('experiments/results/word-mapping/foundation-calibration')


def extension_stream(book):
    path = SOURCE_ROOT / f'voinich-caesar-{book}.html'
    raw = path.read_bytes()
    parser = Paragraphs()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    paragraphs, chapters = [], []
    for row in parser.rows:
        if row['classes']:
            continue
        match = re.match(r'^\s*\[\s*(\d+)\s*\]\s*', row['text'])
        if match:
            chapters.append(int(match[1]))
            paragraphs.append(row['text'][match.end():])
    if not chapters or chapters != list(range(1, len(chapters) + 1)):
        raise ValueError('Caesar chapter extraction incomplete or unordered')
    body = '\n\n'.join(paragraphs)
    source = {'url': f'https://www.thelatinlibrary.com/caesar/{book}.shtml' if book.startswith('gall')
              else f'https://www.thelatinlibrary.com/caesar/civil/{book}.shtml',
              'raw_sha256': hashlib.sha256(raw).hexdigest(), 'extracted_sha256': digest(body),
              'book': book, 'chapters': len(chapters), 'encoding': 'utf-8'}
    records = tuple({'raw': m[0], 'tokens': list(m[0].lower()),
        'char_start': m.start(), 'char_end': m.end(), 'excluded_reason': None}
        for m in re.finditer(r'[^\W\d_]+', body))
    corpus = Corpus('latin', source, {'preserve_spaces': True,
        'policy': 'numbered prose paragraphs only; editorial numeric labels ignored; punctuation retained'}, records)
    return from_corpus(corpus, f'caesar-extension-{book}', raw_text=body)


def prepare(out, *, resume=False, write=True):
    out = Path(out)
    streams = [extension_stream(book) for book in BOOKS]
    train = WordStream(tuple(r for s in streams for r in s.records),
        {'policy': 'Gallic V-VII and Civil I-III only', 'sources': [s.provenance for s in streams]})
    test = WordStream.load(PARENT / 'splits/test.json')
    full = WordStream.load(PARENT / 'corpora/caesar-full.json')
    blocked = {(r.source_id, r.record_index) for r in test.records if r.surface is not None}
    development = full.select(lambda r: (r.source_id, r.record_index) not in blocked,
        description={'policy': 'original Gallic I-IV source except original final test positions'})
    validate_splits({'train': train, 'development': development, 'test': test})
    model = NgramModel.train(train.segments(), training_sha256=train.identity)
    morphology = WhitakerAnnotator(Path('data/vendor/whitakers-words')).catalog(
        model.vocabulary, training_sha256=train.identity)
    candidates = CandidateCatalog.build(train.segments(), morphology, training_sha256=train.identity)
    covered, audit = screen_complete_segments(development, candidates.forms, minimum_words=5)
    # Assign entire original scored segments to chronological thirds before
    # selecting covered records. Never cut a sentence at a length target.
    keys = list(dict.fromkeys((r.source_id, r.segment_id) for r in full.records))
    bundle_for = {key: min(2, i * 3 // len(keys)) for i, key in enumerate(keys)}
    bundles = {f'bundle-{i + 1}': covered.select(
        lambda r, i=i: bundle_for[r.source_id, r.segment_id] == i,
        description={'policy': 'whole original segments in chronological third', 'third': i + 1}) for i in range(3)}
    if any(sum(map(len, s.segments())) < 150 for s in bundles.values()):
        raise ValueError('Long-context calibration has insufficient fully covered natural text')
    validate_splits(bundles)
    bundles['pooled'] = covered
    code = [Path(__file__), Path('src/voynich_smt/word_mapping/neighborhood.py'),
            Path('src/voynich_smt/word_mapping/coverage.py')]
    protocol = {'training_sha256': train.identity, 'model_sha256': model.identity,
        'candidate_sha256': digest(asdict(candidates)), 'morphology_sha256': morphology.identity,
        'test_sha256': test.identity, 'development_sha256': development.identity,
        'coverage_sha256': digest(audit), 'bundles': {n: s.identity for n, s in bundles.items()},
        'source_sha256': {book: s.provenance['source']['raw_sha256'] for book, s in zip(BOOKS, streams)},
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in code},
        'scope': 'same-author disjoint books; screened segment bundles; final test unscored; pooled overlaps bundles'}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    path = out / 'manifest.json'
    if path.exists():
        if not resume or json.loads(path.read_text()) != json.loads(json.dumps(manifest)):
            raise ValueError('Long-context foundation exists or inputs/code changed')
    if write:
        write_json(path, manifest)
        write_json(out / 'coverage-audit.json', audit)
        for name, stream in bundles.items():
            base = out / name / 'foundation'
            train.save(base / 'splits/train.json')
            stream.save(base / 'splits/development.json')
            test.save(base / 'splits/test.json')
            write_json(base / 'splits/manifest.json', validate_splits({'train': train, 'development': stream, 'test': test}))
            model.save(base / 'model.json')
            morphology.save(base / 'morphology-training.json')
            write_json(base / 'candidates.json', asdict(candidates))
        write_json(out / 'foundation-report.json', {'train_tokens': sum(map(len, train.segments())),
            'candidate_forms': len(candidates.forms), 'input_tokens': audit['input_tokens'],
            'admitted_tokens': audit['admitted_tokens'], 'admitted_segments': audit['admitted_segments'],
            'bundles': {n: {'tokens': sum(map(len, s.segments())), 'segments': len(s.segments())} for n, s in bundles.items()}})
    else:
        if digest(json.loads((out / 'coverage-audit.json').read_text())) != digest(audit):
            raise ValueError('Coverage audit differs from reconstruction')
        for name, stream in bundles.items():
            base = out / name / 'foundation'
            for split, expected in [('train', train), ('development', stream), ('test', test)]:
                if WordStream.load(base / f'splits/{split}.json').identity != expected.identity:
                    raise ValueError('Saved foundation stream differs from reconstruction')
            if NgramModel.load(base / 'model.json').identity != model.identity:
                raise ValueError('Saved model differs from reconstruction')
            if digest(json.loads((base / 'candidates.json').read_text())) != digest(asdict(candidates)):
                raise ValueError('Saved candidates differ from reconstruction')
    return manifest, bundles


def _neighborhood_worker(study, profile, write=True):
    study = Path(study)
    model = NgramModel.load(study / f'models/{profile}.json')
    value = json.loads((study / 'candidates.json').read_text())
    value['forms'] = tuple(value['forms'])
    candidates = CandidateCatalog(**value)
    public = public_input(study / 'fixtures/one-to-one.json')
    truth = load_truth(study, 'one-to-one')
    def progress(done, total):
        print(f'Oracle audit {study.parent.name}/{profile}: {done}/{total} types', flush=True)
    result = audit_neighborhood(model, candidates, public, truth, progress=progress)
    if write:
        write_json(study.parent / f'neighborhood-{profile}.json', {'report': result, 'sha256': digest(result)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/long-context-calibration'))
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    manifest, bundles = prepare(args.out, resume=args.resume or args.validate, write=not args.validate)
    if args.prepare_only:
        print((args.out / 'foundation-report.json').read_text())
        return
    if args.validate:
        for name in bundles:
            print(json.dumps({name: validate_study(args.out / name / 'study')}), flush=True)
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as pool:
            futures = {pool.submit(_neighborhood_worker, args.out / name / 'study', profile, False): (name, profile)
                       for name in bundles for profile in ('mixture', 'trigram')}
            for future in as_completed(futures):
                name, profile = futures[future]
                saved = json.loads((args.out / name / f'neighborhood-{profile}.json').read_text())
                if digest(saved['report']) != saved['sha256']:
                    raise ValueError('Neighborhood report checksum changed')
                actual = future.result()
                if saved['report'] != actual:
                    raise ValueError('Neighborhood report differs from exhaustive reconstruction')
                print(f'Validated exhaustive oracle audit {name}/{profile}', flush=True)
        write_json(args.out / 'validation.json', {'validated': True, 'bundles': len(bundles),
            'manifest_sha256': manifest['sha256']})
        return
    plan = AblationPlan(seeds=(11, 22, 33), budgets=(10000, 50000), restarts=2,
        fixture_kinds=('one-to-one',), all_types_active=True, constraint_arms=True,
        arm_names=('baseline', 'trigram', 'injective'), archive_size=30)
    for name in bundles:
        report = run_searches(args.out / name / 'foundation', args.out / name / 'study', plan,
                             workers=args.workers, resume=args.resume)
        print(json.dumps({'bundle': name, 'search_diagnoses': report['diagnoses']}), flush=True)
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('spawn')) as pool:
        futures = {pool.submit(_neighborhood_worker, args.out / name / 'study', profile): (name, profile)
                   for name in bundles for profile in ('mixture', 'trigram')}
        for future in as_completed(futures):
            result = future.result()
            print(json.dumps({'oracle_audit': futures[future], 'tokens': result['tokens'],
                'types': result['active_types'], 'counts': result['counts']}), flush=True)


if __name__ == '__main__':
    main()
