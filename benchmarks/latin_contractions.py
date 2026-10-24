"""Offline contraction-capacity pilot; no SMT imports, calls or cipher changes."""
from collections import Counter, deque
import csv
import hashlib
import json
from pathlib import Path

from benchmarks.historical_word_lengths import caesar_segments, latin_segments

CONFIG = Path('experiments/configs/latin-contractions.json')
OUT = Path('experiments/results/latin-contractions')


def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_inventory(config):
    rules = config['rules']
    if not rules or len({r['id'] for r in rules}) != len(rules):
        raise ValueError('Rules must have unique IDs')
    for r in rules:
        if (not r['expansion'].isalpha() or len(r['expansion']) < 2
                or r['position'] not in {'any', 'initial', 'final', 'whole'}
                or not r['id'].isascii() or not r['id'].replace('-', '').isalnum()):
            raise ValueError('Invalid contraction rule')
    for ids in config['profiles'].values():
        if len(set(ids)) != len(ids) or not set(ids) <= {r['id'] for r in rules}:
            raise ValueError('Invalid profile rule IDs')


def applies(word, index, rule):
    expansion = rule['expansion']
    end = index+len(expansion)
    return (word.startswith(expansion, index)
            and (rule['position'] not in {'initial', 'whole'} or index == 0)
            and (rule['position'] not in {'final', 'whole'} or end == len(word)))


def unitizations(word, rules):
    """One reversible witness per attainable length, including uncontracted letters."""
    if not word or not word.isalpha():
        raise ValueError('Expected a normalized nonempty alphabetic word')
    paths = [{} for _ in range(len(word)+1)]
    paths[0][0] = ()
    for index in range(len(word)):
        edges = [(index+1, word[index])]
        edges.extend((index+len(r['expansion']), '<'+r['id']+'>')
                     for r in rules if applies(word, index, r))
        for count, path in paths[index].items():
            for end, unit in edges:
                paths[end].setdefault(count+1, path+(unit,))
    return paths[-1]


def expand(units, rules):
    table = {'<'+r['id']+'>': r['expansion'] for r in rules}
    if any(u not in table and (len(u) != 1 or not u.isalpha()) for u in units):
        raise ValueError('Unknown unit')
    return ''.join(table.get(u, u) for u in units)


def summarize(histogram, size, ceiling):
    count = sum(histogram.values())
    if not count:
        return {'windows': 0}
    def rank(index):
        seen = 0
        for total in sorted(histogram):
            seen += histogram[total]
            if index < seen:
                return total/size
    def quantile(p):
        index = (count-1)*p
        lower = int(index)
        upper = lower if lower == index else lower+1
        return rank(lower)+(rank(upper)-rank(lower))*(index-lower)
    below = sum(n for total, n in histogram.items() if total <= ceiling)
    return {'windows': count, 'minimum': min(histogram)/size,
            'p05': quantile(.05), 'median': quantile(.5), 'p95': quantile(.95),
            'at_or_below_ceiling': below, 'fraction_at_or_below_ceiling': below/count,
            'histogram_minimum_unit_totals': dict(sorted(histogram.items()))}


def scan(segments, rules, cipher_words, minimum_code=1, maximum_code=3):
    size = len(cipher_words)
    if not size or not 1 <= minimum_code <= maximum_code:
        raise ValueError('Invalid ciphertext or code-length bounds')
    cipher_lengths = list(map(len, cipher_words))
    pairs = [(i, j) for i in range(size) for j in range(i+1, size) if cipher_words[i] == cipher_words[j]]
    cache = {}
    hits = Counter()
    tokens = original = compressed = barriers = 0
    histogram = Counter()
    candidates = []
    positions = repeat_compatible = 0
    offset = 0
    for segment in segments:
        pending = deque(maxlen=size)
        for local_index, word in enumerate(segment):
            if word is None:
                barriers += 1
                pending.clear()
                continue
            if word not in cache:
                paths = unitizations(word, rules)
                for path in paths.values():
                    if expand(path, rules) != word:
                        raise ValueError('Contraction round trip failed')
                cache[word] = paths
            paths = cache[word]
            smallest = min(paths)
            for unit in paths[smallest]:
                if unit.startswith('<'):
                    hits[unit[1:-1]] += 1
            tokens += 1
            original += len(word)
            compressed += smallest
            pending.append((offset+local_index, word, paths))
            if len(pending) != size:
                continue
            histogram[sum(min(p) for _, _, p in pending)] += 1
            eligible = []
            for (_, _, p), c in zip(pending, cipher_lengths):
                choices = [k for k in p if k*minimum_code <= c <= k*maximum_code]
                if not choices:
                    break
                eligible.append(choices)
            if len(eligible) != size:
                continue
            positions += 1
            words = [w for _, w, _ in pending]
            conflicts = [{'left_word': i, 'right_word': j, 'ciphertext_word': ''.join(cipher_words[i]),
                          'left_plaintext': words[i], 'right_plaintext': words[j]}
                         for i, j in pairs if words[i] != words[j]]
            repeat_compatible += not conflicts
            candidates.append({'start_record': pending[0][0], 'end_record_exclusive': offset+local_index+1,
                'plaintext': words, 'attainable_unit_counts_by_position': [sorted(p) for _, _, p in pending],
                'compatible_unit_counts_by_position': [sorted(c) for c in eligible],
                'one_length_compatible_unitization': [list(p[min(c)]) for (_, _, p), c in zip(pending, eligible)],
                'equal_ciphertext_word_conflicts': conflicts})
        offset += len(segment)
    return {'tokens': tokens, 'barriers': barriers, 'original_letters': original,
            'minimum_units': compressed, 'letters_saved': original-compressed,
            'fraction_letters_saved': (original-compressed)/original if original else 0,
            'maximally_contracted_rule_occurrences': dict(hits),
            **summarize(histogram, size, sum(cipher_lengths)//minimum_code),
            'positionwise_optional_length_compatible': positions,
            'positionwise_and_repetition_compatible': repeat_compatible}, candidates


def run():
    config = json.loads(CONFIG.read_text())
    validate_inventory(config)
    baseline = json.loads(Path('experiments/results/conflict-selection.json').read_text())
    request = baseline['baseline_request']
    if checksum({'request': request, 'codeword_domains': 'observed'}) != baseline['baseline_input_sha256']:
        raise ValueError('Baseline request hash mismatch')
    cipher_words = request['ciphertext']['words']
    bounds = request['bounds']
    if (len(cipher_words) != 22 or sum(map(len, cipher_words)) != 104
            or bounds['min_code_length'] != 1 or bounds['max_code_length'] != 3):
        raise ValueError('Expected fixed 22-word H2/L3 block')
    corpora = []
    segments, metadata = caesar_segments()
    corpora.append(('caesar', segments, [metadata]))
    medieval = []
    medieval_metadata = []
    for identifier, filename, incipit in [('aquinas', 'latin-aquinas-ente.html', 'Quia parvus error'),
                                         ('caroli', 'latin-caroli.html', 'Secundis sedentibus')]:
        segments, metadata = latin_segments(filename, incipit)
        corpora.append((identifier, segments, [metadata]))
        medieval.extend(segments)
        medieval_metadata.append(metadata)
    corpora.append(('medieval-latin', medieval, medieval_metadata))
    rows = []
    OUT.mkdir(parents=True, exist_ok=True)
    for profile, ids in config['profiles'].items():
        rules = [r for r in config['rules'] if r['id'] in ids]
        for identifier, segments, metadata in corpora:
            metrics, candidates = scan(segments, rules, cipher_words)
            candidate_path = OUT/f'{identifier}-{profile}-candidates.json'
            candidate_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2)+'\n')
            rows.append({'source_id': identifier, 'profile': profile, 'sources': metadata,
                'records_sha256': checksum(segments), 'candidates_path': str(candidate_path),
                'candidates_sha256': checksum(candidates), **metrics})
            print(f"{identifier}/{profile}: saved={metrics['fraction_letters_saved']:.2%}; ceiling={metrics['fraction_at_or_below_ceiling']:.2%}; positions={metrics['positionwise_optional_length_compatible']}; repetition={metrics['positionwise_and_repetition_compatible']}")
    report = {'schema_version': 1, 'inventory': config, 'inventory_sha256': checksum(config),
        'baseline_sha256': checksum(baseline), 'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'window_words': 22, 'ceiling_total_units': 104, 'rows': rows, 'complete': True,
        'solver_calls': 0, 'semantics': 'Minimum-unit distributions are maximum-compression envelopes for optional, distinct reversible contractions. Positionwise checks use every attainable count, not only minima. Same word boundaries, spelling and non-overlapping optional rules. Repetition checks are necessary and apply to original spellings because units expand uniquely. No language likelihood, observed scribal frequency or SAT conclusion is computed.'}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    columns = ['source_id', 'profile', 'windows', 'fraction_letters_saved', 'p05', 'median', 'p95',
               'fraction_at_or_below_ceiling', 'positionwise_optional_length_compatible',
               'positionwise_and_repetition_compatible']
    with (OUT/'summary.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in columns})
    return report


if __name__ == '__main__':
    run()
