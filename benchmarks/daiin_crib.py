"""Conditional finite crib attack; word-family presence, not full-text decoding."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
from time import perf_counter

import z3

TARGETS = ('von', 'vor', 'vil', 'vns', 'nach', 'nicht', 'nun', 'noch',
           'der', 'die', 'das', 'dem', 'den', 'des')


def compatible(key):
    codes = list(key.values())
    return all(not a.startswith(b) and not b.startswith(a)
               for a, b in combinations(codes, 2))


def alignments(plain, cipher, pinned=None, maximum=3):
    """Exhaust every bounded segmentation, checking repeated letters and prefix freedom."""
    def walk(i, j, key):
        if i == len(plain):
            if j == len(cipher):
                yield dict(key)
            return
        letter = plain[i]
        if letter in key:
            code = key[letter]
            if cipher.startswith(code, j):
                yield from walk(i + 1, j + len(code), key)
            return
        remaining = len(plain) - i - 1
        for size in range(1, min(maximum, len(cipher) - j - remaining) + 1):
            code = cipher[j:j + size]
            extended = dict(key, **{letter: code})
            if compatible(extended):
                yield from walk(i + 1, j + size, extended)
    yield from walk(0, 0, dict(pinned or {}))


def final_letter_obstruction(counts, cipher='daiin', plain_length=3):
    """Necessary condition without prefix freedom or a maximum code length.

    With nonempty codes, the final plaintext letter owns a suffix of at most
    len(cipher) - (plain_length - 1) characters. Longer plaintext words starting
    with that letter require proper extensions of one of these suffixes.
    """
    return {cipher[-size:]: sorted(w for w in counts
                                  if w.startswith(cipher[-size:]) and len(w) > size)
            for size in range(1, len(cipher) - plain_length + 2)}


def solve_family(counts, crib, targets, timeout_ms):
    start = perf_counter()
    letters = sorted(set(crib + ''.join(targets)))
    codes = sorted({''} | {w[i:i+n] for w in counts for i in range(len(w))
                           for n in range(1, min(3, len(w)-i)+1)})
    ids = {c: i for i, c in enumerate(codes)}
    keys = {p: z3.Int('key_' + p) for p in letters}
    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=0)
    pins = list(alignments(crib, 'daiin'))
    solver.add(z3.Or(*[z3.And(*[keys[p] == ids[c] for p, c in pin.items()]) for pin in pins]))
    rows, presence, summaries = {}, {}, {}
    for target in targets:
        found = {}
        for pin in pins:
            for cipher in counts:
                if not len(target) <= len(cipher) <= 3 * len(target):
                    continue
                for key in alignments(target, cipher, pin):
                    signature = tuple(sorted(key.items()))
                    found[signature] = cipher
        rows[target] = found
        presence[target] = z3.Bool('present_' + target)
        solver.add(presence[target] == z3.Or(*[
            z3.And(*[keys[p] == ids[code] for p, code in signature]) for signature in found]))
        candidates = sorted(set(found.values()), key=lambda w: (-counts[w], w))
        summaries[target] = {'candidate_types': len(candidates), 'candidate_key_rows': len(found),
                             'top_candidates': [[w, counts[w]] for w in candidates[:12]]}
    domains = {p: {''} for p in letters}
    for pin in pins:
        for p, code in pin.items():
            domains[p].add(code)
    for found in rows.values():
        for signature in found:
            for p, code in signature:
                domains[p].add(code)
    for p in letters:
        solver.add(z3.Or(*[keys[p] == ids[code] for code in sorted(domains[p])]))
    for a, b in combinations(letters, 2):
        for ca in sorted(domains[a] - {''}):
            bad = [ids[cb] for cb in sorted(domains[b] - {''})
                   if ca.startswith(cb) or cb.startswith(ca)]
            if bad:
                solver.add(z3.Implies(keys[a] == ids[ca],
                                     z3.And(*[keys[b] != v for v in bad])))
    branch_results = []
    for pin in pins:
        possible = {target: ('sat' if any(all(dict(sig).get(p) == code
                    for p, code in pin.items()) for sig in rows[target]) else 'unsat')
                    for target in targets}
        branch_results.append({'crib_key': pin, 'individual_presence': possible,
                               'method': 'exhaustive bounded alignment enumeration'})
    # Exact cardinality search; UNKNOWN never counts as an impossibility proof.
    checks, witness, maximum = [], None, None
    for count in range(len(targets), -1, -1):
        solver.push()
        solver.add(z3.PbGe([(b, 1) for b in presence.values()], count))
        status = solver.check()
        checks.append({'at_least': count, 'status': str(status),
                       'reason_unknown': solver.reason_unknown() if status == z3.unknown else None})
        if status == z3.sat:
            model = solver.model()
            key = {p: codes[model.eval(keys[p]).as_long()] for p in letters}
            decoded = {w: ''.join(key[p] for p in w) for w in targets
                       if z3.is_true(model.eval(presence[w]))}
            used = set(crib + ''.join(decoded))
            used_key = {p: key[p] for p in sorted(used)}
            assert compatible(used_key)
            assert ''.join(key[p] for p in crib) == 'daiin'
            assert all(c in counts for c in decoded.values())
            witness = {'key': used_key, 'targets': decoded, 'independently_verified': True}
            if all(c['status'] == 'unsat' for c in checks[:-1]):
                maximum = len(decoded)
            solver.pop()
            break
        solver.pop()
    return {'crib': crib, 'legal_crib_segmentations': pins, 'targets': summaries,
            'branches': branch_results, 'cardinality_checks': checks,
            'proved_maximum_simultaneous_targets': maximum, 'witness': witness,
            'runtime_seconds': perf_counter() - start}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout-ms', type=int, default=5000)
    parser.add_argument('--cribs', nargs='+', default=['vnd'])
    parser.add_argument('--min-count', type=int, default=1)
    parser.add_argument('--output', type=Path, default=Path('experiments/results/daiin-crib/report.json'))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    eva_path = Path('data/processed/zl-eva.json')
    vocab_path = Path('data/generated/german-selection/vocabulary.json')
    eva = json.loads(eva_path.read_text())
    vocab = json.loads(vocab_path.read_text())
    counts = Counter(''.join(r['tokens']) for r in eva['records']
                     if not r['excluded_reason'] and all(len(t) == 1 and t.isascii() and t.isalpha()
                                                       for t in r['tokens']))
    counts = Counter({w: n for w, n in counts.items() if n >= args.min_count})
    attested = [w for w in TARGETS if vocab['frequencies'].get(w, 0)]
    report = {'model': 'Partial key with one nonempty 1–3 EVA-character code per represented plaintext letter; global prefix freedom; preserved word boundaries; no nulls. Targets may occur anywhere among clean manuscript word types. Remaining text is unconstrained.',
              'scope': 'Conditional family-presence test, not full-vocabulary coverage or language identification. Candidate counts are marginal over crib segmentations, not simultaneous assignments.',
              'z3_version': z3.get_version_string(),
              'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [eva_path, vocab_path]},
              'german_source': vocab['source'], 'eva_tokens': sum(counts.values()),
              'eva_types': len(counts), 'minimum_type_frequency': args.min_count, 'daiin_count': counts['daiin'],
              'crib_corpus_counts': {w: vocab['frequencies'].get(w, 0) for w in args.cribs},
              'target_corpus_counts': {w: vocab['frequencies'].get(w, 0) for w in TARGETS},
              'attested_targets': attested,
              'vnd_final_d_proper_extensions': final_letter_obstruction(counts),
              'runs': []}
    for crib in args.cribs:
        result = solve_family(counts, crib, attested, args.timeout_ms)
        report['runs'].append(result)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(crib, result['proved_maximum_simultaneous_targets'],
              result['witness'], round(result['runtime_seconds'], 2), flush=True)


if __name__ == '__main__':
    main()
