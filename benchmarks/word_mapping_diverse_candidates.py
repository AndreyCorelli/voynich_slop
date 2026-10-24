"""Preserve independent initialization basins for bounded neural reranking."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

from benchmarks.word_mapping_recovery import optimize, public_input, resources
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.annealing import Annealer, SearchConfig
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.objective import objective_score

ROOT = Path('experiments/results/word-mapping/diverse-candidates')
MODES = ('frequency', 'random', 'lemma-aware')
SEEDS = (101, 202)


def diverse_select(rows, limit):
    """Keep the ngram winner, then maximize minimum unweighted type distance."""
    if type(limit) is not int or limit < 1:
        raise ValueError('Positive shortlist size required')
    seen = {}
    for row in sorted(rows, key=lambda r: (-r['score'], digest(r['assignments']))):
        seen.setdefault(digest(row['assignments']), row)
    remaining = list(seen.values())
    if not remaining:
        raise ValueError('Empty pool')
    keys = set(remaining[0]['assignments'])
    if any(set(r['assignments']) != keys for r in remaining):
        raise ValueError('Dictionary domains differ')
    selected = [remaining.pop(0)]
    while remaining and len(selected) < limit:
        index = max(range(len(remaining)), key=lambda i: (
            min(sum(remaining[i]['assignments'][w] != s['assignments'][w] for w in keys) for s in selected),
            remaining[i]['score'], -i))
        selected.append(remaining.pop(index))
    return selected


def generate(root=ROOT, parent=PARENT, *, validate=False, resume=False):
    root, parent = Path(root), Path(parent)
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    parent_validation = json.loads((parent / 'validation.json').read_text())
    if digest(parent_manifest['protocol']) != parent_manifest['sha256'] or not parent_validation['validated'] or parent_validation['manifest_sha256'] != parent_manifest['sha256']:
        raise ValueError('Validated parent required')
    code = [Path(__file__), Path('benchmarks/word_mapping_recovery.py'), *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'version': 1, 'parent_sha256': parent_manifest['sha256'], 'modes': list(MODES),
        'seeds': list(SEEDS), 'steps': 20000, 'archive_size': 10, 'injective': True,
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in code}}
    manifest = {'protocol': protocol, 'sha256': digest(protocol)}
    if (root / 'manifest.json').exists():
        if not (resume or validate) or json.loads((root / 'manifest.json').read_text()) != manifest:
            raise ValueError('Generation exists or protocol changed')
    elif validate:
        raise ValueError('Missing generation')
    else:
        write_json(root / 'manifest.json', manifest)
    hashes = {}
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3', 'pooled'):
        model, _, candidates = resources(parent / bundle / 'foundation')
        if model.identity != parent_manifest['protocol']['model_sha256'] or digest(asdict(candidates)) != parent_manifest['protocol']['candidate_sha256']:
            raise ValueError('Parent training resources changed')
        public = public_input(parent / bundle / 'study/fixtures/one-to-one.json')
        if public.identity != json.loads((parent / bundle / 'study/manifest.json').read_text())['protocol']['fixture_sha256']['one-to-one']:
            raise ValueError('Parent public fixture changed')
        hashes[f'{bundle}/public'] = public.identity
        hashes[f'{bundle}/model'] = model.identity
        hashes[f'{bundle}/candidates'] = digest(asdict(candidates))
        for mode in MODES:
            for seed in SEEDS:
                config = SearchConfig(seed=seed, restarts=1, steps_per_restart=20000,
                    active_types=len({w for s in public.segments for w in s}),
                    initialization=mode, injective=True, archive_size=10)
                directory = root / bundle / f'{mode}-{seed}'
                if validate:
                    search = Annealer(model, candidates, public.segments, config, input_sha256=public.identity).resume(directory / 'checkpoint.json')
                    if not search.complete or search.evaluations != 20000:
                        raise ValueError('Incomplete search')
                    archive = json.loads((directory / 'archive.json').read_text())
                    if digest(archive) != digest({'forms': list(candidates.forms), 'rows': search.archive}):
                        raise ValueError('Archive differs from checkpoint')
                    for row in archive['rows']:
                        value = objective_score(model, public.segments, WordMapping(candidates.forms, row['assignments']), injective=True)
                        if not math.isclose(value, row['score'], abs_tol=1e-8, rel_tol=1e-12):
                            raise ValueError('Objective differs')
                else:
                    optimize(model, candidates, public, config, directory, resume=resume, checkpoint_every=20000)
                    archive = json.loads((directory / 'archive.json').read_text())
                hashes[f'{bundle}/{mode}-{seed}'] = digest(archive)
                print(f"{'Validated' if validate else 'Generated'} {bundle}/{mode}-{seed}", flush=True)
    report = {'manifest_sha256': manifest['sha256'], 'source_sha256': hashes,
        'searches': 24, 'mutations': 480000, 'scope': 'development only; no truth loaded; final test untouched'}
    if validate:
        if json.loads((root / 'report.json').read_text()) != report:
            raise ValueError('Generation report differs')
        write_json(root / 'validation.json', {'validated': True, **report})
    else:
        write_json(root / 'report.json', report)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    generate(resume=args.resume, validate=args.validate)
