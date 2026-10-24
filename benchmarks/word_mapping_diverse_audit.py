"""Evaluation-only diversity/recovery audit after neural selection is frozen."""
import json
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_recovery import public_input
from benchmarks.word_mapping_diverse_candidates import ROOT, MODES, SEEDS
from benchmarks.word_mapping_neural_probe import PARENT
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.evaluation import recovery

OUT = Path('experiments/results/word-mapping/diverse-neural-rerank')


def audit(out=OUT, parent=PARENT, root=ROOT):
    out, parent, root = map(Path, (out, parent, root))
    report = json.loads((out / 'report.json').read_text())
    selection = json.loads((out / 'selection.json').read_text())
    manifest = json.loads((out / 'manifest.json').read_text())
    if digest(selection) != manifest['protocol']['selection_sha256'] or report['manifest_sha256'] != manifest['sha256']:
        raise ValueError('Selection/report changed')
    rows = []
    for job, result in zip(selection, report['runs'], strict=True):
        bundle = job['bundle']
        study = parent / bundle / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        truth = load_truth(study, 'one-to-one')
        pool = []
        paths = [(study / f'runs/one-to-one/injective/seed-{seed}/budget-50000/original/archive.json', f'saved-frequency-{seed}') for seed in (11, 22, 33)]
        paths += [(root / bundle / f'{mode}-{seed}/archive.json', f'{mode}-{seed}') for mode in MODES for seed in SEEDS]
        for path, label in paths:
            archive = json.loads(path.read_text())
            if digest(archive) != job['source_sha256'][label]:
                raise ValueError('Pool source changed')
            for candidate in archive['rows']:
                metric = recovery(public, truth, WordMapping(archive['forms'], candidate['assignments']))
                pool.append((label, metric['exact_token_accuracy']))
        candidates = job['candidates']
        keys = list(candidates[0]['assignments'])
        distances = [sum(a['assignments'][w] != b['assignments'][w] for w in keys) / len(keys)
            for i, a in enumerate(candidates) for b in candidates[i+1:]]
        scored = [json.loads((out / 'scores' / f"{job['id']}-{c['rank']}.json").read_text())['row'] for c in candidates]
        rows.append({'bundle': bundle, 'pool_dictionaries': len(pool),
            'distinct_pool_dictionaries': job['distinct_pool_dictionaries'],
            'shortlist_mean_pairwise_type_distance': mean(distances),
            'ngram_accuracy': result['before']['exact_token_accuracy'],
            'neural_accuracy': result['after']['exact_token_accuracy'],
            'neural_selected_origin': candidates[result['selected_rank']]['origin'],
            'shortlist_oracle_accuracy': result['archive_oracle_exact_token_accuracy'],
            'pool_oracle_accuracy': max(v for _, v in pool),
            'best_by_origin': {label: max(v for name, v in pool if name == label) for _, label in paths},
            'scoring_seconds': sum(r['seconds'] for r in scored),
            'masked_words': sum(r['masked_words'] for r in scored)})
    result = {'evaluation_only': True, 'neural_report_sha256': digest(report), 'rows': rows,
        'scope': 'oracle and recovery computed after selection; no new optimization or test scoring'}
    write_json(out / 'diversity-audit.json', result)
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    audit()
