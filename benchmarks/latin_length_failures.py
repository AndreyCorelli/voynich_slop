"""Rank remaining Latin passage length failures; pure analysis, no solver calls."""
from collections import Counter, deque
import csv
import hashlib
import json
from pathlib import Path

from benchmarks.latin_contractions import CONFIG, checksum, unitizations, validate_inventory
from benchmarks.historical_word_lengths import caesar_segments, latin_segments

OUT = Path('experiments/results/latin-length-failures')


def mismatch(word, paths, cipher_length, position, minimum_code=1, maximum_code=3):
    lower = (cipher_length+maximum_code-1)//maximum_code
    upper = cipher_length//minimum_code
    counts = sorted(paths)
    if any(lower <= k <= upper for k in counts):
        return None
    if max(counts) < lower:
        kind = 'too-short'
    elif min(counts) > upper:
        kind = 'too-long'
    else:
        kind = 'unattainable-count'
    gap = min(max(lower-k, k-upper, 0) for k in counts)
    return {'position': position+1, 'word': word, 'ciphertext_length': cipher_length,
            'allowed_unit_counts': [lower, upper], 'attainable_unit_counts': counts,
            'kind': kind, 'minimum_unit_gap': gap,
            'additional_contraction_cannot_fix': kind == 'too-short'}


def rank(row):
    return row['failed_positions'], row['total_unit_gap'], row['start_record']


def keep_best(rows, row, limit):
    rows.append(row)
    rows.sort(key=rank)
    del rows[limit:]


def diagnose(segments, rules, cipher_words, limit=10):
    if not cipher_words or limit < 1:
        raise ValueError('Nonempty ciphertext and positive top limit required')
    lengths = list(map(len, cipher_words))
    pairs = [(i, j) for i in range(len(lengths)) for j in range(i+1, len(lengths))
             if cipher_words[i] == cipher_words[j]]
    cache = {}
    hist = Counter()
    position_counts = [Counter() for _ in lengths]
    failing_words = Counter()
    best = []
    best_repeat = []
    best_contractible = []
    repeat_windows = contractible_windows = windows = 0
    offset = 0
    for segment in segments:
        pending = deque(maxlen=len(lengths))
        for local, word in enumerate(segment):
            if word is None:
                pending.clear()
                continue
            if word not in cache:
                paths = unitizations(word, rules)
                cache[word] = (paths, [mismatch(word, paths, c, i) for i, c in enumerate(lengths)])
            pending.append((offset+local, word))
            if len(pending) != len(lengths):
                continue
            windows += 1
            words = [w for _, w in pending]
            failures = [cache[w][1][i] for i, w in enumerate(words) if cache[w][1][i] is not None]
            hist[len(failures)] += 1
            for failure in failures:
                position_counts[failure['position']-1][failure['kind']] += 1
                failing_words[(failure['position'], failure['word'], failure['kind'])] += 1
            conflicts = [{'left_position': i+1, 'right_position': j+1,
                          'ciphertext_word': ''.join(cipher_words[i]),
                          'left_plaintext': words[i], 'right_plaintext': words[j]}
                         for i, j in pairs if words[i] != words[j]]
            too_short = sum(f['kind'] == 'too-short' for f in failures)
            row = {'start_record': pending[0][0], 'end_record_exclusive': offset+local+1,
                   'plaintext': words, 'failed_positions': len(failures),
                   'total_unit_gap': sum(f['minimum_unit_gap'] for f in failures),
                   'too_short_positions': too_short, 'failures': failures,
                   'minimum_unit_counts': [min(cache[w][0]) for w in words],
                   'equal_ciphertext_word_conflicts': conflicts}
            keep_best(best, row, limit)
            if not conflicts:
                repeat_windows += 1
                keep_best(best_repeat, row, limit)
            if not too_short:
                contractible_windows += 1
                keep_best(best_contractible, row, limit)
        offset += len(segment)
    return {'windows': windows, 'failed_position_histogram': dict(sorted(hist.items())),
            'minimum_failed_positions': min(hist) if hist else None,
            'positions': [{'position': i+1, 'ciphertext_word': ''.join(cipher_words[i]),
                           'ciphertext_length': lengths[i], 'failures': dict(counts),
                           'failure_fraction': sum(counts.values())/windows if windows else 0}
                          for i, counts in enumerate(position_counts)],
            'most_frequent_failing_words': [{'position': p, 'word': w, 'kind': k, 'windows': n}
                                          for (p, w, k), n in failing_words.most_common(30)],
            'repetition_compatible_windows': repeat_windows,
            'windows_without_too_short_failures': contractible_windows,
            'closest_windows': best, 'closest_repetition_compatible_windows': best_repeat,
            'closest_windows_without_too_short_failures': best_contractible}


def run():
    config = json.loads(CONFIG.read_text())
    validate_inventory(config)
    baseline = json.loads(Path('experiments/results/conflict-selection.json').read_text())
    request = baseline['baseline_request']
    if checksum({'request': request, 'codeword_domains': 'observed'}) != baseline['baseline_input_sha256']:
        raise ValueError('Baseline hash mismatch')
    if (len(request['ciphertext']['words']) != 22
            or sum(map(len, request['ciphertext']['words'])) != 104
            or request['bounds']['min_code_length'] != 1
            or request['bounds']['max_code_length'] != 3):
        raise ValueError('Expected the fixed 22-word L1–3 baseline')
    corpora = []
    segments, metadata = caesar_segments()
    corpora.append(('caesar', segments, [metadata]))
    for identifier, filename, incipit in [('aquinas', 'latin-aquinas-ente.html', 'Quia parvus error'),
                                         ('caroli', 'latin-caroli.html', 'Secundis sedentibus')]:
        segments, metadata = latin_segments(filename, incipit)
        corpora.append((identifier, segments, [metadata]))
    rows = []
    for profile in ('letters', 'bounded-seven'):
        ids = config['profiles'][profile]
        rules = [r for r in config['rules'] if r['id'] in ids]
        for identifier, segments, metadata in corpora:
            row = {'source_id': identifier, 'profile': profile, 'sources': metadata,
                   'records_sha256': checksum(segments), **diagnose(segments, rules, request['ciphertext']['words'])}
            rows.append(row)
            print(identifier, profile, 'minimum failures', row['minimum_failed_positions'],
                  'repetition-compatible windows', row['repetition_compatible_windows'])
    report = {'schema_version': 1, 'inventory_sha256': checksum(config),
              'baseline_sha256': checksum(baseline),
              'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'ranking': 'Failed-position count, then summed minimum unit-count distance to allowed intervals, then source record index. Other rankings separately restrict to repetition-compatible windows or windows without too-short failures.',
              'rows': rows, 'complete': True, 'solver_calls': 0,
              'scope': 'Necessary length and exact repetition diagnostics of selected attested Latin windows. Gaps and source boundaries preserved. New reversible contractions can reduce unit counts but cannot increase original letter counts or make distinct spellings decode identically. No new contraction inventory or cipher changes.'}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    with (OUT/'positions.csv').open('w', newline='') as handle:
        columns = ['source_id', 'profile', 'position', 'ciphertext_word', 'ciphertext_length',
                   'failure_fraction', 'too-long', 'too-short', 'unattainable-count']
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            for position in row['positions']:
                writer.writerow({'source_id': row['source_id'], 'profile': row['profile'],
                    **{k: position[k] for k in ('position', 'ciphertext_word', 'ciphertext_length', 'failure_fraction')},
                    **{k: position['failures'].get(k, 0) for k in ('too-long', 'too-short', 'unattainable-count')}})
    return report


if __name__ == '__main__':
    run()
