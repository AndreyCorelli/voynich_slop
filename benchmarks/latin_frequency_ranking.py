"""Frozen external-unigram reranking of existing candidate pools; no solver calls."""
from collections import Counter
import json
import math
from pathlib import Path

from benchmarks.generating_key_ranking import evaluate
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

OUT = Path('experiments/results/latin-frequency-ranking')
SOURCES = ('corpus-sequence-selection', 'coverage-sequence-selection')


def frequency_score(words, model):
    """All tokens contribute, including unseen words; no top-word rejection."""
    forms = [''.join(w) for w in words]
    if not forms:
        raise ValueError('Empty candidate')
    denominator = model['tokens'] + model['alpha'] * (len(model['counts']) + 1)
    return sum(math.log((model['counts'].get(w, 0) + model['alpha']) / denominator)
               for w in forms) / len(forms)


def rank_training(candidates, model):
    values = [frequency_score(c['plaintext']['words'], model) for c in candidates]
    return values, sorted(range(len(values)), key=lambda i: (-values[i], i))


def run():
    if (OUT/'protocol.json').exists():
        raise ValueError('Preserve frozen output; experiment already started')
    reference = json.loads(Path('experiments/results/corpus-sequence-selection/prepared.json').read_text())
    corpus = json.loads(Path('data/processed/caesar-latin-v2.json').read_text())
    assert digest(corpus) == reference['source_sha256']
    counts = Counter(''.join(r['tokens']) for r in corpus['records'][:reference['split_record']] if r['tokens'])
    model = {'counts': dict(sorted(counts.items())), 'tokens': sum(counts.values()), 'alpha': 1}
    protocol = {'model': model, 'source_sha256': digest(corpus),
        'reference_record_range': [0, reference['split_record']],
        'ranking': 'Mean add-one external unigram log probability; stable first-candidate ties; all words counted.',
        'scope': 'Retrospective saved pools, projected twelve-word Latin; same author disjoint reference. No truth injection, new recovery, contractions, full prose or manuscript test.',
        'code_sha256': digest(Path(__file__).read_text()), 'input_sha256': {}}
    inputs = []
    for source in SOURCES:
        root = Path('experiments/results')/source
        prepared = json.loads((root/'prepared.json').read_text())
        report = json.loads((root/'report.json').read_text())
        assert report['complete'] and report['prepared_sha256'] == digest(prepared)
        protocol['input_sha256'][source] = {'prepared': digest(prepared), 'report': digest(report)}
        inputs.append((source, prepared, report))
    write_json(OUT/'protocol.json', protocol)
    rows = []
    for source, prepared, saved in inputs:
        for case in prepared['cases']:
            old = next(r for r in saved['cases'] if r['id'] == case['id'])
            candidates = [f['result'] for f in old['fits']]
            values, order = rank_training(candidates, model)
            selected = order[0] if order else None
            # Selection frozen before continuation or truth is inspected.
            q = HiddenRecoveryRequest.from_dict(case['request'])
            evaluations = []
            for candidate in candidates:
                if 'truth' in case:
                    ev = evaluate(candidate, case, q)
                else:
                    from benchmarks.frozen_key_holdout import score
                    from voynich_smt.cipher.base import Encoder
                    from voynich_smt.models.text import Text
                    book = candidate['encoder']['codebook']
                    encoder = Encoder({s: tuple(tuple(c) for c in cs) for s, cs in book.items()})
                    ev = {'prediction': score(Text(tuple(tuple(w) for w in case['holdout']['words'])), encoder, q.dictionary, q.ciphertext.words)}
                evaluations.append(ev)
            rows.append({'source': source, 'id': case['id'], 'scores': values, 'order': order,
                'selected_index': selected, 'sequence_selected_index': old['selected_index'],
                'candidate_count': len(candidates), 'evaluations': evaluations,
                'evaluation_status': 'EVALUATED' if candidates else 'NOT_EVALUATED_NO_SAT'})
    result = {'protocol_sha256': digest(protocol), 'cases': rows, 'solver_calls': 0, 'complete': True}
    write_json(OUT/'report.json', result)
    for row in rows:
        print(row['source'], row['id'], 'selected', row['selected_index'], 'sequence', row['sequence_selected_index'])
        print([(e.get('exact_words'), e['prediction'].get('dictionary_words'), e['prediction'].get('fully_decoded_words')) for e in row['evaluations']])
    return result


if __name__ == '__main__':
    run()
