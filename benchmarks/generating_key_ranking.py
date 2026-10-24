"""Truth-assisted ranking capacity check on fixed coverage-control candidates."""
from pathlib import Path
import json

from benchmarks.corpus_sequence_selection import sequence_score
from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text

SOURCE = Path('experiments/results/coverage-sequence-selection')
OUT = Path('experiments/results/generating-key-ranking')


def rank_training(candidates, model):
    """No continuation, truth labels or cipher keys enter this rule."""
    scores = [sequence_score(c['plaintext']['words'], model) for c in candidates]
    order = sorted(range(len(candidates)), key=lambda i: (-scores[i], i))
    return scores, order


def evaluate(result, case, q):
    encoder = Encoder({s: tuple(tuple(c) for c in cs)
                       for s, cs in result['encoder']['codebook'].items()})
    held = Text(tuple(tuple(w) for w in case['holdout']['words']))
    prediction = score(held, encoder, q.dictionary, q.ciphertext.words)
    exact = sum(r['fully_decoded'] and tuple(r['decoded_prefix']) == tuple(w)
                for r, w in zip(prediction['word_results'], case['holdout_plaintext']['words']))
    return {'prediction': prediction, 'exact_words': exact}


def run():
    if (OUT/'report.json').exists() or (OUT/'protocol.json').exists():
        raise ValueError('Fixed diagnostic already started; preserve output')
    prepared = json.loads((SOURCE/'prepared.json').read_text())
    saved = json.loads((SOURCE/'report.json').read_text())
    if not saved['complete'] or saved['prepared_sha256'] != digest(prepared):
        raise ValueError('Incomplete or mismatched saved experiment')
    protocol = {'prepared_sha256': digest(prepared), 'saved_report_sha256': digest(saved),
        'model_sha256': digest(prepared['model']),
        'candidate_rule': 'All saved SAT fits for each positive, then append generating truth; no additional recovery.',
        'ranking': 'Unchanged training-only sequence score; ties favor original candidate order.',
        'scope': 'Retrospective truth-assisted capacity diagnostic, not hidden-key recovery or blind validation. Only two saved positive blocks; no score tuning.',
        'code_sha256': {str(p): digest(p.read_text()) for p in
            (Path(__file__), Path('benchmarks/corpus_sequence_selection.py'),
             Path('benchmarks/frozen_key_holdout.py'))}}
    write_json(OUT/'protocol.json', protocol)
    rows = []
    for case in prepared['cases']:
        if 'truth' not in case: continue
        previous = next(r for r in saved['cases'] if r['id'] == case['id'])
        q = HiddenRecoveryRequest.from_dict(case['request'])
        candidates = [fit['result'] for fit in previous['fits']] + [case['truth']]
        for candidate in candidates: verify(q, candidate)
        scores, order = rank_training(candidates, prepared['model'])
        selected = order[0]; generating = len(candidates)-1
        # Freeze ranking before any continuation evaluation.
        evaluation = [evaluate(candidate, case, q) for candidate in candidates]
        truth_used = digest(used_mappings(case['truth']))
        rows.append({'id': case['id'], 'training_words':len(q.ciphertext.words),
            'candidates': [{'index':i, 'origin':'injected_generating' if i == generating else 'saved_recovery',
                'result':candidate, 'training_score':scores[i],
                'used_ownership_matches_generating':digest(used_mappings(candidate))==truth_used,
                **evaluation[i]} for i,candidate in enumerate(candidates)],
            'training_rank_order':order,'generating_rank':order.index(generating)+1,
            'generating_index':generating,'selected_index':selected,
            'generating_selected':selected==generating,
            'generating_minus_best_recovered_score':scores[generating]-max(scores[:generating]),
            'baseline_selected_index':previous['selected_index'],
            'baseline_exact_words':evaluation[previous['selected_index']]['exact_words'],
            'augmented_exact_words':evaluation[selected]['exact_words']})
    report={'protocol':protocol,'cases':rows,'complete':True,'solver_calls':0}
    write_json(OUT/'report.json',report)
    for row in rows:
        print(f"{row['id']}: generating rank={row['generating_rank']}/{len(row['candidates'])}; "
              f"exact {row['baseline_exact_words']}/4 -> {row['augmented_exact_words']}/4; "
              f"score margin={row['generating_minus_best_recovered_score']:+.6f}")
    return report


if __name__ == '__main__': run()
