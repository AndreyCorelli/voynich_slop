"""Explain saved first strict improvements from perfect Latin dictionaries."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from voynich_smt.data.corpus import write_json
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.ngram import BOS, EOS, NgramModel
from voynich_smt.word_mapping.objective import objective_score

PARENT = Path('experiments/results/word-mapping/widening-calibration')
ORACLE = Path('experiments/results/word-mapping/zero-corruption-calibration')
OUT = Path('experiments/results/word-mapping/first-corruption-audit')


def explain(model, context):
    """Expose probabilities and exactly additive probability-mass paths, not log shares."""
    a, b, c = context
    cfg = model.config
    den1 = model.total + cfg.alpha * (len(model.vocabulary) + 2)
    den2 = model.bigram_totals[b] + cfg.backoff_strength
    den3 = model.trigram_totals[a, b] + cfg.backoff_strength
    p1 = (model.unigram[c] + cfg.alpha) / den1
    p2 = (model.bigram[b, c] + cfg.backoff_strength * p1) / den2
    p3 = (model.trigram[a, b, c] + cfg.backoff_strength * p2) / den3
    # Expand recursive interpolation into three sources of predictive mass.
    unigram_factor = (cfg.unigram_weight + cfg.bigram_weight * cfg.backoff_strength / den2
        + cfg.trigram_weight * cfg.backoff_strength**2 / (den3 * den2))
    masses = {
        'unigram_observed': unigram_factor * model.unigram[c] / den1,
        'unigram_pseudocount': unigram_factor * cfg.alpha / den1,
        'bigram_observed': (cfg.bigram_weight + cfg.trigram_weight * cfg.backoff_strength / den3)
                           * model.bigram[b, c] / den2,
        'trigram_observed': cfg.trigram_weight * model.trigram[a, b, c] / den3,
    }
    probability = math.fsum(masses.values())
    assert math.isclose(probability, model.probability(a, b, c), rel_tol=1e-12)
    names = {BOS: '<BOS>', EOS: '<EOS>', 2: '<OOV>'}
    return {'context': [names[i] if i < 3 else model.vocabulary[i-3] for i in context],
        'unigram_count': model.unigram[c], 'bigram_count': model.bigram[b, c],
        'trigram_count': model.trigram[a, b, c], 'bigram_context_count': model.bigram_totals[b],
        'trigram_context_count': model.trigram_totals[a, b],
        'p1': p1, 'p2': p2, 'p3': p3, 'probability_mass': masses,
        'probability': probability, 'log_score': math.log(probability)}


def events(model, segment):
    ids = [BOS, BOS] + [model.form_ids[w] for w in segment] + [EOS]
    return list(zip(ids, ids[1:], ids[2:]))


def run():
    model = NgramModel.load(PARENT / 'model.json')
    forms = tuple(json.loads((PARENT / 'candidates-oracle.json').read_text())['forms'])
    form_ids = {w: i for i, w in enumerate(forms)}
    rows, inputs = [], [PARENT / 'model.json', PARENT / 'candidates-oracle.json']
    for path in sorted((ORACLE / 'runs').glob('*/greedy/seed-*/report.json')):
        saved = json.loads(path.read_text())
        target = saved['target']
        public_path = PARENT / f'public/fit-{target}.json'
        truth_path = PARENT / f'truth/fit-{target}.json'
        inputs.extend([path, public_path, truth_path])
        public, truth = [json.loads(p.read_text()) for p in (public_path, truth_path)]
        witness = saved['first_departure']
        assert witness == {k: v for k, v in saved['perfect_score_witness'].items() if k != 'accepted'}
        assert witness['score_delta'] > 1e-9
        gold = {w: form_ids[f] for w, f in truth['decoding'].items()}
        before = WordMapping(forms, gold)
        after = WordMapping(forms, {**gold, **witness['changes']})
        assert before.collapse_penalty == after.collapse_penalty == 0
        plain_before, plain_after = [m.render(public['segments']) for m in (before, after)]
        assert plain_before == tuple(map(tuple, truth['plaintext']))
        counts = Counter(w for s in public['segments'] for w in s)
        changed = [{'cipher': w, 'before': forms[gold[w]], 'after': forms[f], 'occurrences': counts[w]}
                   for w, f in witness['changes'].items() if f != gold[w]]
        lost = sum(r['occurrences'] for r in changed)
        assert -lost == witness['token_delta']
        affected = []
        for si, (left, right) in enumerate(zip(plain_before, plain_after)):
            for pos, (old, new) in enumerate(zip(events(model, left), events(model, right))):
                if old == new:
                    continue
                old_info, new_info = explain(model, old), explain(model, new)
                affected.append({'segment': si, 'prediction_position': pos,
                    'before': old_info, 'after': new_info,
                    'log_score_delta': new_info['log_score']-old_info['log_score']})
        delta = math.fsum(e['log_score_delta'] for e in affected)
        initial_score = objective_score(model, public['segments'], before, injective=True)
        assert math.isclose(initial_score, saved['initial_score'], abs_tol=1e-7)
        full_delta = objective_score(model, public['segments'], after, injective=True) - initial_score
        assert math.isclose(delta, full_delta, abs_tol=1e-7)
        assert math.isclose(delta, witness['score_delta'], abs_tol=1e-7)
        rows.append({'target': target, 'seed': saved['seed'], 'proposal': witness['evaluation'],
            'tokens': sum(counts.values()), 'changes': changed, 'lost_tokens': lost,
            'accuracy_loss_percentage_points': 100*lost/sum(counts.values()),
            'score_delta': delta, 'full_score_delta': full_delta,
            'objective_delta': {'language_log_likelihood': delta, 'collapse_penalty': 0,
                                'frequency_penalty': 0, 'morphology': 0},
            'events': affected})
    assert len(rows) == 10
    report = {'scope': 'Earlier Latin optimizer; saved first accepted strict improvement from truth; no new blind recovery.',
        'model_config': model.artifact()['config'], 'model_sha256': model.identity,
        'attribution': 'Probability masses add exactly; their logarithms do not. Penalties have zero weight in this protocol.',
        'inputs_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(inputs))},
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'validated': True, 'runs': rows}
    write_json(OUT / 'report.json', report)
    for r in rows:
        print(r['target'], r['seed'], r['proposal'], r['changes'], 'gain', round(r['score_delta'], 6))
    return report


if __name__ == '__main__':
    run()
