"""Controlled morphology-preserving swaps and retrospective search evaluation."""
import json
import hashlib
from collections import defaultdict
from pathlib import Path
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.structural_oracle import StructuralOracle

PARENT = Path('experiments/results/word-mapping/widening-calibration')
OUT = Path('experiments/results/word-mapping/structural-oracle-calibration')


def run():
    morphology = json.loads((PARENT/'morphology.json').read_text())
    entries = morphology['entries']
    rows = []
    for target in (500, 2000, 8000, 16000, 32000):
        public = json.loads((PARENT/f'public/fit-{target}.json').read_text())
        truth = json.loads((PARENT/f'truth/fit-{target}.json').read_text())
        oracle = StructuralOracle(entries, truth['decoding'])
        gold = truth['decoding']
        groups = defaultdict(list)
        for cipher, word in sorted(gold.items()):
            if oracle.kind(word) == 'content':
                groups[oracle.profiles[word]].append(cipher)
        compatible = dict(gold)
        for group in groups.values():
            if len(group) > 1:
                for a, b in zip(group, group[1:]+group[:1]):
                    compatible[a] = gold[b]
        # Same global injective word dictionary, now cross grammatical profiles.
        broken = dict(gold)
        remaining = [c for c in sorted(gold) if oracle.kind(gold[c]) == 'content']
        pairs = []
        while remaining:
            a = remaining.pop()
            b = next((b for b in remaining if not oracle.profiles[gold[a]] & oracle.profiles[gold[b]]), None)
            if b is not None:
                remaining.remove(b)
                broken[a], broken[b] = gold[b], gold[a]
                pairs.append((a, b))
        changed_functions = dict(gold)
        functions = [c for c in sorted(gold) if oracle.kind(gold[c]) == 'fixed']
        if len(functions) > 1:
            for a, b in zip(functions, functions[1:]+functions[:1]):
                changed_functions[a] = gold[b]
        scenarios = {}
        for name, mapping in [('perfect', gold), ('compatible', compatible),
                              ('broken_features', broken), ('changed_function_words', changed_functions)]:
            assert len(set(mapping.values())) == len(mapping)
            scenarios[name] = oracle.evaluate(public['segments'], mapping)
        assert scenarios['compatible']['error'] == scenarios['compatible']['unknown'] == 0
        assert scenarios['perfect']['exact_accuracy'] == 1
        old = []
        forms = json.loads((PARENT/'candidates-oracle.json').read_text())['forms']
        for path in sorted(Path('experiments/results/word-mapping/zero-corruption-calibration/runs').rglob('report.json')):
            report = json.loads(path.read_text())
            if report['target'] != target:
                continue
            mapping = {c: forms[i] for c, i in report['best_assignments'].items()}
            old.append({'policy': report['policy'], 'seed': report['seed'],
                        'strict': oracle.evaluate(public['segments'], mapping),
                        'permissive': oracle.evaluate(public['segments'], mapping, permissive=True)})
        rows.append({'target': target, 'scenarios': scenarios, 'previous_runs': old,
                     'swappable_content_types': sum(len(g) for g in groups.values() if len(g)>1),
                     'disjoint_profile_pairs': len(pairs),
                     'compatible_dictionary': compatible,
                     'examples': [{'original': gold[c], 'replacement': compatible[c]}
                                  for c in sorted(gold) if gold[c] != compatible[c]][:12]})
    report = {'scope': 'plaintext-derived morphology oracle; no syntactic parsing or blind search',
              'morphology_sha256': digest(morphology), 'rows': rows,
              'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__), Path('src/voynich_smt/structural_oracle.py'))},
              'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted([* (PARENT/'public').glob('fit-*.json'),
                                               * (PARENT/'truth').glob('fit-*.json'),
                                               PARENT/'candidates-oracle.json', PARENT/'morphology.json',
                                               *Path('experiments/results/word-mapping/zero-corruption-calibration/runs').rglob('report.json')])}}
    write_json(OUT/'report.json', report)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    run()
