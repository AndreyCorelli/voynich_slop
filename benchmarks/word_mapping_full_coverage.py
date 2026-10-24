"""Large-budget, fully covered natural-segment calibration with all types active."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from benchmarks.word_mapping_ablation import AblationPlan, validate as validate_ablation
from benchmarks.word_mapping_parallel import run as run_parallel
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.corpora import WordStream, validate_splits
from voynich_smt.word_mapping.coverage import screen_complete_segments
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.word_mapping.ngram import NgramModel


def prepare_foundation(parent, out, *, minimum_words=5, resume=False, write=True):
    parent, out = Path(parent), Path(out)
    full = WordStream.load(parent / 'corpora/caesar-full.json')
    development = WordStream.load(parent / 'splits/development.json')
    test = WordStream.load(parent / 'splits/test.json')
    # Expand from source positions independently of held-out word identities.
    blocked = {(r.source_id, r.record_index) for stream in (development, test)
               for r in stream.records if r.surface is not None}
    train = full.select(lambda r: (r.source_id, r.record_index) not in blocked,
        description={'policy': 'all cached source positions except declared development/test positions',
            'development_sha256': development.identity, 'test_sha256': test.identity})
    validate_splits({'train': train, 'development': development, 'test': test})
    model = NgramModel.train(train.segments(), training_sha256=train.identity)
    # Candidate vocabulary and morphology are fixed before admission screening.
    annotator = WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    morphology = annotator.catalog(model.vocabulary, training_sha256=train.identity)
    candidates = CandidateCatalog.build(train.segments(), morphology, training_sha256=train.identity)
    covered, audit = screen_complete_segments(development, candidates.forms, minimum_words=minimum_words)
    if not covered.segments():
        raise ValueError('No complete covered development segments; candidates will not be augmented from truth')
    splits = validate_splits({'train': train, 'development': covered, 'test': test})
    code_paths = [Path(__file__), Path('src/voynich_smt/word_mapping/coverage.py')]
    protocol = {'version': 1, 'parent': str(parent.resolve()), 'parent_full_sha256': full.identity,
        'original_development_sha256': development.identity, 'test_sha256': test.identity,
        'splits': splits, 'model_sha256': model.identity, 'morphology_sha256': morphology.identity,
        'candidate_sha256': digest(asdict(candidates)), 'coverage_audit_sha256': digest(audit),
        'minimum_words': minimum_words,
        'code_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in code_paths},
        'scope': 'coverage-screened natural development segments; training-disjoint; final test unscored'}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    path = out / 'manifest.json'
    if path.exists():
        if not resume:
            raise ValueError('Covered foundation exists; use --resume or a new output directory')
        if json.loads(path.read_text()) != json.loads(json.dumps(manifest)):
            raise ValueError('Covered foundation inputs/policy/code changed')
    if write:
        write_json(path, manifest)
        for name, stream in [('train', train), ('development', covered), ('test', test)]:
            stream.save(out / f'splits/{name}.json')
        write_json(out / 'splits/manifest.json', splits)
        model.save(out / 'model.json')
        morphology.save(out / 'morphology-training.json')
        write_json(out / 'candidates.json', asdict(candidates))
        write_json(out / 'coverage-audit.json', audit)
        write_json(out / 'report.json', {'train_tokens': sum(map(len, train.segments())),
            'candidate_forms': len(candidates.forms), 'development_tokens': audit['input_tokens'],
            'development_segments': audit['input_segments'], 'admitted_tokens': audit['admitted_tokens'],
            'admitted_segments': audit['admitted_segments'], 'scope': protocol['scope']})
    return manifest, audit


def validate_foundation(out):
    out = Path(out)
    saved = json.loads((out / 'manifest.json').read_text())
    if digest(saved['protocol']) != saved['sha256']:
        raise ValueError('Covered foundation manifest changed')
    protocol = saved['protocol']
    manifest, audit = prepare_foundation(protocol['parent'], out, minimum_words=protocol['minimum_words'],
                                       resume=True, write=False)
    streams = {name: WordStream.load(out / f'splits/{name}.json') for name in ('train', 'development', 'test')}
    if validate_splits(streams) != manifest['protocol']['splits']:
        raise ValueError('Covered foundation split changed')
    if digest(json.loads((out / 'coverage-audit.json').read_text())) != digest(audit):
        raise ValueError('Coverage audit changed')
    if NgramModel.load(out / 'model.json').identity != protocol['model_sha256']:
        raise ValueError('Covered training model changed')
    result = {'validated': True, 'admitted_tokens': audit['admitted_tokens'],
              'admitted_segments': audit['admitted_segments'], 'manifest_sha256': saved['sha256']}
    write_json(out / 'validation.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=Path('experiments/results/word-mapping/foundation-calibration'))
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/full-coverage-large'))
    parser.add_argument('--seeds', type=int, nargs='+', default=[11, 22, 33, 44, 55])
    parser.add_argument('--budgets', type=int, nargs='+', default=[10000, 200000])
    parser.add_argument('--restarts', type=int, default=2)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--minimum-words', type=int, default=5)
    parser.add_argument('--checkpoint-every', type=int, default=10000)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    if args.validate:
        print(json.dumps({'foundation': validate_foundation(args.out / 'foundation'),
                          'search': validate_ablation(args.out / 'study')}, indent=2))
        return
    _, audit = prepare_foundation(args.parent, args.out / 'foundation',
                                 minimum_words=args.minimum_words, resume=args.resume)
    if args.prepare_only:
        print(json.dumps({key: audit[key] for key in ('input_segments', 'admitted_segments', 'input_tokens', 'admitted_tokens')}, indent=2))
        return
    plan = AblationPlan(seeds=tuple(args.seeds), budgets=tuple(args.budgets), restarts=args.restarts,
        fixture_kinds=('one-to-one', 'homophonic'), all_types_active=True,
        arm_names=('baseline', 'trigram', 'collapse-5'),
        controls=('position-shuffle',), control_arm_names=('baseline',))
    print(json.dumps({'runs': len(plan.jobs()), 'total_evaluations': sum(
        plan.restarts * job['budget'] for job in plan.jobs()), 'admitted_tokens': audit['admitted_tokens'],
        'all_types_active': True, 'workers': args.workers}), flush=True)
    report = run_parallel(args.out / 'foundation', args.out / 'study', plan, workers=args.workers,
                          resume=args.resume, checkpoint_every=args.checkpoint_every)
    print(json.dumps({key: report[key] for key in ('completed_runs', 'total_evaluations', 'diagnoses')}, indent=2))


if __name__ == '__main__':
    main()
