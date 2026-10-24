"""Independent morphology model versus oracle-generated controls."""
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.word_mapping.corpora import WordStream

PARENT = Path('experiments/results/word-mapping/widening-calibration')
OUT = Path('experiments/results/word-mapping/structural-language-calibration')


def run():
    entries = json.loads((PARENT/'morphology.json').read_text())['entries']
    train = WordStream.load(PARENT/'splits/train.json')
    model = StructuralLanguageModel(entries).fit(train.segments())
    # Scorer has no dependency on any truth object. Truth is loaded below only
    # to generate evaluation controls and measure their intended errors.
    oracle_report = json.loads(Path('experiments/results/word-mapping/structural-oracle-calibration/report.json').read_text())
    rows = []
    for base in oracle_report['rows']:
        target = base['target']
        public = json.loads((PARENT/f'public/fit-{target}.json').read_text())
        truth = json.loads((PARENT/f'truth/fit-{target}.json').read_text())
        gold = truth['decoding']
        oracle = StructuralOracle(entries, gold)
        compatible = base['compatible_dictionary']
        broken = dict(gold)
        remaining = [c for c in sorted(gold) if oracle.kind(gold[c]) == 'content']
        while remaining:
            a = remaining.pop()
            b = next((b for b in remaining if not oracle.profiles[gold[a]] & oracle.profiles[gold[b]]), None)
            if b is not None:
                remaining.remove(b)
                broken[a], broken[b] = gold[b], gold[a]
        functions = [c for c in sorted(gold) if oracle.kind(gold[c]) == 'fixed']
        changed = dict(gold)
        if len(functions)>1:
            for a,b in zip(functions, functions[1:]+functions[:1]):
                changed[a] = gold[b]
        mappings = {'perfect': gold, 'compatible': compatible, 'broken_features': broken,
                    'changed_function_words': changed}
        scores = {}
        for name, mapping in mappings.items():
            decoded = tuple(tuple(mapping[c] for c in segment) for segment in public['segments'])
            scores[name] = model.score(decoded)
        if abs(scores['perfect']-scores['compatible']) > 1e-7:
            raise ValueError('Morphology-invariance failed')
        # Assess locally broken controls too, rather than only wholesale damage.
        local = []
        pairs = []
        keys = sorted(gold)
        import random
        rng = random.Random(377)
        for _ in range(2000):
            a,b = rng.sample(keys, 2)
            if oracle.kind(gold[a]) == oracle.kind(gold[b]) == 'content' and not oracle.profiles[gold[a]] & oracle.profiles[gold[b]]:
                pairs.append((a,b))
                if len(pairs) == 100:
                    break
        # Score only affected segments, preserving their original boundaries.
        segment_ids = defaultdict(set)
        for i, segment in enumerate(public['segments']):
            for c in segment:
                segment_ids[c].add(i)
        for a,b in pairs:
            indices = sorted(segment_ids[a] | segment_ids[b])
            original = tuple(tuple(gold[c] for c in public['segments'][i]) for i in indices)
            altered = tuple(tuple(gold[b] if c==a else gold[a] if c==b else gold[c]
                                  for c in public['segments'][i]) for i in indices)
            local.append({'original': [gold[a],gold[b]], 'score_delta': model.score(altered)-model.score(original)})
        rows.append({'target': target, 'scores': scores,
            'per_event_delta': {k: (v-scores['perfect'])/(sum(map(len,public['segments']))+len(public['segments'])) for k,v in scores.items()},
            'broken_local_swaps': local, 'local_prefer_original': sum(x['score_delta'] < -1e-9 for x in local),
            'local_ties': sum(abs(x['score_delta']) <= 1e-9 for x in local)})
        print(target, rows[-1]['per_event_delta'], 'local correct', rows[-1]['local_prefer_original'], '/',len(local),flush=True)
    report = {'training_sha256': train.identity, 'oracle_report_sha256': digest(oracle_report),
        'states': len(model.states), 'alpha': model.alpha, 'backoff': model.backoff,
        'scope': 'morphological sequence proxy, no dependency or semantic model; no search or final-test evaluation',
        'rows': rows, 'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path('src/voynich_smt/structural_language.py'), Path('src/voynich_smt/structural_oracle.py'))},
        'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         [PARENT/'morphology.json', PARENT/'splits/train.json',
                          *(PARENT/'public').glob('fit-*.json'), *(PARENT/'truth').glob('fit-*.json')]}}
    write_json(OUT/'report.json',report)


if __name__ == '__main__':
    run()
