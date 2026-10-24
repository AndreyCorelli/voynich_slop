"""Localize hidden-recovery difficulty by truncating one fixed synthetic text."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3
from benchmarks.cycle_performance import solve
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text


def prefix_truth(truth, word_count):
    words = truth['plaintext']['words'][:word_count]
    return {'plaintext': {'words': words}, 'encoder': truth['encoder'],
            'choices': truth['choices'][:sum(map(len, words))], 'nulls': [],
            'source_generator': truth.get('generator'), 'prefix_word_count': word_count}


def summarize(experiments):
    sat = [r['word_count'] for r in experiments if r['result']['status'] == 'SAT']
    unknown = [r['word_count'] for r in experiments if r['result']['status'] == 'UNKNOWN']
    return {'verified_sat_word_counts': sat, 'unknown_word_counts': unknown,
            'first_sampled_unknown': min(unknown) if unknown else None,
            'interpretation': 'A sampled solver-budget boundary, not an UNSAT boundary; runtime need not be monotonic'}


def run(config, output, artifacts, resume=False):
    if (set(config) != {'source_report', 'seed', 'word_counts', 'timeout_ms'}
            or type(config['seed']) is not int or not config['word_counts']
            or any(type(n) is not int or n <= 0 for n in config['word_counts'])
            or config['word_counts'] != sorted(set(config['word_counts']))
            or type(config['timeout_ms']) is not int or config['timeout_ms'] <= 0):
        raise ValueError('Invalid synthetic prefix configuration')
    source = json.loads(Path(config['source_report']).read_text())
    candidates = [r for r in source['experiments'] if r['seed'] == config['seed'] and r['cycle_encoding'] == 'state']
    if not source['complete'] or not candidates:
        raise ValueError('Completed source with matching controls required')
    baseline = max(candidates, key=lambda r: r['vocabulary_size'])
    payload = json.loads(Path(baseline['public_input']).read_text())
    if digest(payload) != baseline['input_sha256']:
        raise ValueError('Source input hash mismatch')
    original = HiddenRecoveryRequest.from_dict(payload['request'])
    if (original.nulls.enabled or original.optimization.enabled or original.bounds.max_homophones != 2
            or original.bounds.max_code_length != 3 or original.selection.mode != 'cycle'
            or original.selection.reset != 'text' or original.dictionary_encoding != 'trie'):
        raise ValueError('Expected null-free H2/L3 trie control with text-wide cycles')
    if config['word_counts'][-1] > len(original.ciphertext.words):
        raise ValueError('Requested prefix exceeds saved control')
    truth = json.loads(Path(baseline['truth']).read_text())
    if len(truth['plaintext']['words']) != len(original.ciphertext.words):
        raise ValueError('Truth must describe the entire saved control')
    verify(original, dict(status='SAT', verified=True, **{k: truth[k] for k in ('encoder', 'plaintext', 'choices')}))
    report = {'config': config, 'config_sha256': digest(config), 'source_sha256': digest(source),
        'source_input_sha256': digest(payload), 'source_truth_sha256': digest(truth),
        'source_input': baseline['public_input'], 'source_truth': baseline['truth'],
        'environment': {'python': platform.python_version(), 'z3': z3.get_version_string()},
        'implementation_sha256': {str(p): digest(p.read_text()) for p in map(Path, (
            'src/voynich_smt/solver/recovery.py', 'src/voynich_smt/solver/selection.py',
            'src/voynich_smt/solver/dictionary_encoding.py', 'src/voynich_smt/language/dictionary.py',
            'benchmarks/synthetic_prefix.py', 'benchmarks/cycle_performance.py'))},
        'semantics': 'Fresh independent hidden solves; same full vocabulary and key-generated text; only prefix length varies',
        'experiments': [], 'complete': False}
    if resume and output.exists():
        previous = json.loads(output.read_text())
        for key in ('config_sha256', 'source_sha256', 'source_input_sha256', 'source_truth_sha256',
                    'environment', 'implementation_sha256'):
            if previous[key] != report[key]:
                raise ValueError('Resume requires identical source, configuration, environment and implementation')
        report = previous
    done = {r['word_count']: r for r in report['experiments']}
    for count in config['word_counts']:
        request = replace(original, ciphertext=Text(original.ciphertext.words[:count]), timeout_ms=config['timeout_ms'])
        wrapped = {'request': asdict(request), 'cycle_encoding': 'state'}
        prefix = prefix_truth(truth, count)
        verify(request, dict(status='SAT', verified=True, **{k: prefix[k] for k in ('encoder', 'plaintext', 'choices')}))
        if count in done:
            row = done[count]
            if (row['input_sha256'] != digest(wrapped)
                    or digest(json.loads(Path(row['public_input']).read_text())) != digest(wrapped)):
                raise ValueError('Saved prefix input changed')
            verify(request, row['result'])
            if row['result']['status'] == 'UNSAT':
                raise RuntimeError('Known positive control incorrectly UNSAT')
            continue
        name = f'seed-{config["seed"]}-words-{count:02d}'
        path = artifacts / 'inputs' / f'{name}.json'
        truth_path = artifacts / 'truth' / f'{name}.json'
        write_json(path, wrapped); write_json(truth_path, prefix)
        print(f'{name}: {len(request.dictionary.words)} vocabulary entries, {request.timeout_ms}ms budget', flush=True)
        begin = perf_counter(); result = asdict(solve(request, 'state')); verify(request, result)
        row = {'id': name, 'word_count': count, 'ciphertext_tokens': request.ciphertext.size,
            'public_input': str(path), 'input_sha256': digest(wrapped), 'truth': str(truth_path),
            'truth_sha256': digest(prefix), 'wall_seconds': perf_counter()-begin, 'result': result}
        report['experiments'].append(row)
        report['summary'] = summarize(report['experiments']); write_json(output, report)
        print(f'  {result["status"]}: solver={result["runtime_seconds"]:.3f}s wall={row["wall_seconds"]:.3f}s', flush=True)
        if result['status'] == 'UNSAT':
            raise RuntimeError('Known positive control incorrectly UNSAT')
    report.update(complete=True, summary=summarize(report['experiments']))
    write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='experiments/configs/synthetic-prefix.json')
    parser.add_argument('--output', default='experiments/results/synthetic-prefix.json')
    parser.add_argument('--artifacts', default='data/generated/synthetic-prefix')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    run(json.loads(Path(args.config).read_text()), Path(args.output), Path(args.artifacts), args.resume)


if __name__ == '__main__': main()
