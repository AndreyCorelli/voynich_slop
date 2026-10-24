"""Run reproducible annealing on public word ciphers, then evaluate saved truth."""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
from time import perf_counter

from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.controls import make_control
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.fixtures import CipherInput, CipherTruth
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel
from voynich_smt.word_mapping.objective import objective_score


def resources(foundation):
    foundation = Path(foundation)
    train = WordStream.load(foundation / 'splits/train.json')
    model = NgramModel.load(foundation / 'model.json')
    morphology = MorphologyCatalog.load(foundation / 'morphology-training.json')
    candidates = CandidateCatalog.build(train.segments(), morphology, training_sha256=train.identity)
    if model.training_sha256 != train.identity:
        raise ValueError('Model and training stream differ')
    return model, morphology, candidates


def public_input(path):
    value = json.loads(Path(path).read_text())
    if set(value) != {'segments', 'source', 'encoder', 'format_version'} or value['format_version'] != 1:
        raise ValueError('Invalid public word-cipher schema')
    return CipherInput(tuple(tuple(s) for s in value['segments']), value['source'], value['encoder'])


def optimize(model, candidates, public, config, out, *, resume=False, checkpoint_every=1000):
    if type(checkpoint_every) is not int or checkpoint_every < 1:
        raise ValueError('Checkpoint interval must be positive')
    out = Path(out)
    if (out / 'checkpoint.json').exists() and not resume:
        raise ValueError('Checkpoint exists; use --resume or a new --out directory')
    search = Annealer(model, candidates, public.segments, config, input_sha256=public.identity)
    if resume and (out / 'checkpoint.json').exists():
        search.resume(out / 'checkpoint.json')
    write_json(out / 'public.json', asdict(public))
    initial_evaluations = search.evaluations
    initial_objective = search.initial_objective
    started = perf_counter()
    while not search.complete:
        search.advance(min(checkpoint_every, config.steps_per_restart))
        search.checkpoint(out / 'checkpoint.json')
    seconds = perf_counter() - started
    rows = search.archive
    write_json(out / 'archive.json', {'forms': list(candidates.forms), 'rows': rows})
    result = {'search_sha256': search.identity, 'public_sha256': public.identity,
        'initial_objective': initial_objective, 'best_objective': rows[0]['score'],
        'evaluations': search.evaluations, 'elapsed_seconds_this_invocation': seconds,
        'evaluations_per_second': (search.evaluations - initial_evaluations) / seconds if seconds else None,
        'statistics': search.statistics, 'distinct_mappings': len(rows),
        'score': asdict(model.score(search.best_mapping.render(public.segments)))}
    write_json(out / 'search-report.json', result)
    return search, result


def run(foundation, out, *, kind, config, resume=False, controls=False):
    foundation, out = Path(foundation), Path(out)
    model, morphology, candidates = resources(foundation)
    public = public_input(foundation / f'fixtures/{kind}.json')
    search, report = optimize(model, candidates, public, config, out / 'original', resume=resume)
    exported = search.best_mapping.export(morphology)
    for row in exported:
        word = row['ciphertext']
        assignment = search.best_mapping.assignments[word]
        row['archive_stability'] = sum(r['assignments'].get(word) == assignment for r in search.archive) / len(search.archive)
        row['occurrences'] = sum(s.count(word) for s in public.segments)
    write_json(out / 'best-dictionary.json', exported)
    # Only now load ground truth; it has never entered model/candidates/search.
    value = json.loads((foundation / f'truth/{kind}.json').read_text())
    truth = CipherTruth(value['public_sha256'], tuple(tuple(s) for s in value['plaintext']),
                        value['decoding'], value['deterministic_accuracy_ceiling'])
    eval_morphology = MorphologyCatalog.load(foundation / 'truth/morphology-evaluation.json')
    report['recovery'] = recovery(public, truth, search.best_mapping, morphology=eval_morphology)
    report['candidate_token_coverage'] = sum(w in candidates.form_counts for s in truth.plaintext for w in s) / sum(map(len, truth.plaintext))
    report['controls'] = []
    if controls:
        for control_kind in ('within-segment-shuffle', 'position-shuffle', 'bigram-surrogate'):
            segments, audit = make_control(public.segments, kind=control_kind, seed=config.seed)
            surrogate = CipherInput(segments, {'parent_public_sha256': public.identity}, audit)
            _, result = optimize(model, candidates, surrogate, config, out / control_kind, resume=resume)
            report['controls'].append({'audit': audit, 'search': result})
    report['scope'] = 'development pilot; thresholds and independent multi-seed calibration not yet frozen'
    write_json(out / 'report.json', report)
    return report


def validate(foundation, out, config):
    model, morphology, candidates = resources(foundation)
    out = Path(out)
    report = json.loads((out / 'report.json').read_text())
    original = public_input(out / 'original/public.json')
    original_search = None
    arms = ['original'] + [r['audit']['kind'] for r in report['controls']]
    for arm in arms:
        public = public_input(out / arm / 'public.json')
        search = Annealer(model, candidates, public.segments, config,
                          input_sha256=public.identity).resume(out / arm / 'checkpoint.json')
        if not search.complete or search.evaluations != config.restarts * config.steps_per_restart:
            raise ValueError('Search budget incomplete')
        archive = json.loads((out / arm / 'archive.json').read_text())
        assert digest(archive) == digest({'forms': list(candidates.forms), 'rows': search.archive})
        for row in search.archive:
            mapping = WordMapping(candidates.forms, row['assignments'])
            objective = objective_score(model, public.segments, mapping,
                collapse_weight=config.collapse_weight, frequency_weight=config.frequency_weight,
                injective=config.injective)
            assert math.isclose(objective, row['score'], rel_tol=1e-12, abs_tol=1e-8)
        saved = json.loads((out / arm / 'search-report.json').read_text())
        assert saved['search_sha256'] == search.identity
        assert saved['public_sha256'] == public.identity
        assert saved['statistics'] == search.statistics
        assert saved['score'] == asdict(model.score(search.best_mapping.render(public.segments)))
        if arm == 'original':
            original_search = search
            assert report['public_sha256'] == public.identity
            assert report['statistics'] == search.statistics
            assert report['score'] == saved['score']
            assert report['best_objective'] == search.archive[0]['score']
        else:
            segments, audit = make_control(original.segments, kind=arm, seed=config.seed)
            assert public.segments == segments and public.encoder == audit
            assert next(r for r in report['controls'] if r['audit']['kind'] == arm)['audit'] == audit
    kind = original.encoder['kind']
    value = json.loads((Path(foundation) / f'truth/{kind}.json').read_text())
    truth = CipherTruth(value['public_sha256'], tuple(tuple(s) for s in value['plaintext']),
                        value['decoding'], value['deterministic_accuracy_ceiling'])
    eval_morphology = MorphologyCatalog.load(Path(foundation) / 'truth/morphology-evaluation.json')
    assert recovery(original, truth, original_search.best_mapping, morphology=eval_morphology) == report['recovery']
    assert report['candidate_token_coverage'] == sum(w in candidates.form_counts for s in truth.plaintext for w in s) / sum(map(len, truth.plaintext))
    exported = json.loads((out / 'best-dictionary.json').read_text())
    expected = original_search.best_mapping.export(morphology)
    for row, reference in zip(exported, expected):
        assert {k: row[k] for k in reference} == reference
    assert len(exported) == len(expected)
    result = {'validated': True, 'arms': len(arms), 'budget_per_arm': config.restarts * config.steps_per_restart}
    write_json(out / 'validation.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--foundation', type=Path, default=Path('experiments/results/word-mapping/foundation'))
    parser.add_argument('--out', type=Path, default=Path('experiments/results/word-mapping/recovery-pilot'))
    parser.add_argument('--kind', choices=['one-to-one', 'homophonic', 'frequency-distorting', 'lossy'], default='one-to-one')
    parser.add_argument('--steps', type=int, default=10000)
    parser.add_argument('--restarts', type=int, default=4)
    parser.add_argument('--active-types', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--collapse-weight', type=float, default=0.0)
    parser.add_argument('--frequency-weight', type=float, default=0.0)
    parser.add_argument('--injective', action='store_true')
    parser.add_argument('--controls', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    config = SearchConfig(seed=args.seed, restarts=args.restarts, steps_per_restart=args.steps,
                          active_types=args.active_types, collapse_weight=args.collapse_weight,
                          frequency_weight=args.frequency_weight, injective=args.injective)
    result = validate(args.foundation, args.out, config) if args.validate else run(
        args.foundation, args.out, kind=args.kind, config=config, resume=args.resume, controls=args.controls)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
