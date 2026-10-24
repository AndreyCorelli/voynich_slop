"""Necessary length-capacity comparison; no solver or key-fit claim."""
import hashlib
import json
from pathlib import Path

from benchmarks.latin_contractions import checksum, expand, unitizations, validate_inventory

INPUT = Path('data/generated/clean-latin-voynich/inputs/words-23.json')
INVENTORY = Path('experiments/configs/latin-contractions.json')
OUTPUT = Path('experiments/results/latin-dictionary-contractions.json')


def candidates(words, cipher_length, rules):
    out = []
    for word in words:
        paths = unitizations(word, rules)
        eligible = sorted(k for k in paths if k <= cipher_length <= 3*k)
        if eligible:
            units = paths[eligible[0]]
            if expand(units, rules) != word:
                raise ValueError('Expansion round trip failed')
            out.append({'word': word, 'compatible_counts': eligible,
                        'witness_units': list(units)})
    return out


def run():
    payload = json.loads(INPUT.read_text())
    config = json.loads(INVENTORY.read_text()); validate_inventory(config)
    request = payload['request']
    if (request['bounds']['min_code_length'], request['bounds']['max_code_length']) != (1, 3):
        raise ValueError('Expected L1–3 baseline')
    words = sorted({''.join(w) for w in request['dictionary']['words']})
    lengths = sorted({len(w) for w in request['ciphertext']['words']})
    rows = []
    for profile, ids in config['profiles'].items():
        rules = [r for r in config['rules'] if r['id'] in ids]
        by_length = {}
        for length in lengths:
            eligible = candidates(words, length, rules)
            new = [e for e in eligible if not len(e['word']) <= length <= 3*len(e['word'])]
            by_length[str(length)] = {'candidate_words': len(eligible),
                                     'newly_length_feasible_words': len(new), 'new_candidates': new}
        rows.append({'profile': profile, 'by_cipher_length': by_length})
        print(profile, {k:(v['candidate_words'],v['newly_length_feasible_words']) for k,v in by_length.items()})
    report = {'input': str(INPUT), 'input_sha256': checksum(payload),
              'inventory_sha256': checksum(config),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'dictionary_size': len(words), 'ciphertext_word_lengths': list(map(len,request['ciphertext']['words'])),
              'rows': rows, 'solver_calls': 0,
              'semantics': 'Optional reversible units plus L1–3 expansion. Independent word-length capacity only; no shared key, homophone bound, selection pattern, grammar or SAT conclusion. One verified unitization per attainable count suffices only for this screen, not a complete solver dictionary.'}
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    run()
