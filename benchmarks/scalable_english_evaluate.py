"""Evaluation-only literal metrics and full-score validation of saved joint keys."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.incremental import full_score
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.search import DictionarySearch
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.state import DictionaryState


def evaluate(resources, root, truth_path):
    inference = json.loads((root / 'inference.json').read_text())
    stream = CipherStream.load(root / 'public/cipher.json')
    truth = json.loads(truth_path.read_text())
    if truth['public_sha256'] != stream.identity:
        raise ValueError('Truth belongs to a different cipher')
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = load_model(resources / 'model.sqlite', inventory)
        protocol = inference['protocol']
        if protocol['model_sha256'] != model.identity or protocol['cipher_sha256'] != stream.identity:
            raise ValueError('Inference resource mismatch')
        counts = Counter(c for d in stream.documents for c in d)
        total = sum(counts.values())
        def metrics(assignments):
            state = DictionaryState.create(stream, model, assignments)
            correct = {c for c,w in enumerate(state.assignments) if inventory.word(w) == truth['decoding'][c]}
            return {'token_accuracy': sum(counts[c] for c in correct)/total,
                    'type_accuracy': len(correct)/stream.type_count,
                    'score': full_score(model, stream, state)}
        runs = []
        for result in inference['runs']:
            seed = result['seed']
            search = DictionarySearch.load(root / f'seed-{seed}/checkpoint.json', model, stream)
            assert search.step == result['step']
            assert abs(search.scorer.score - result['current_score']) < 1e-7
            initial = metrics(DictionaryState.initialize(stream, model,
                method=protocol['search'].get('initialization', 'random'), seed=seed).assignments)
            assert abs(initial['score'] - result['initial_score']) < 1e-7
            archived = [metrics(entry['assignments']) for entry in result['joint_archive']]
            for entry, measured in zip(result['joint_archive'], archived):
                assert abs(entry['score'] - measured['score']) < 1e-7
            current = metrics(search.scorer.state.assignments)
            runs.append({'seed': seed, 'steps': result['step'], 'stop_reason': result['stop_reason'],
                         'initial': initial, 'score_selected_best': archived[0], 'current': current,
                         'archived_hypotheses': archived})
        key = DictionaryState.frequency(stream, model).assignments
        covered, attested = set(), set()
        for c, word in enumerate(truth['decoding']):
            try:
                word_id = inventory.id(word)
            except KeyError:
                continue
            covered.add(c)
            if model.counts[word_id]:
                attested.add(c)
        resources_report = json.loads((resources / 'report.json').read_text()) if (resources / 'report.json').exists() else {}
        independent = resources_report.get('benchmark_role') == 'independent-source-resources'
        limitations = (['Work-disjoint literary holdout; exact overlap audit is recorded separately.',
                         'Older literary English is not a contemporary broad-domain benchmark.',
                         'Source model remains small and dictionary-only forms have no observed contexts.']
                        if independent else ['EWT fixture also occurs in LM training.',
                                              '35k tokens span 24 original documents, not one long work.'])
        if model.config.language == 'la':
            limitations = resources_report.get('limitations', []) + [
                'Latin surface spelling canonicalized to i/u; synthetic whole-word substitution.',
                'Independent Latin source/overlap audit is stored with the fixture.']
        if model.config.language == 'de':
            limitations = resources_report.get('limitations', []) + [
                'Historical German synthetic whole-word benchmark; exact surface recovery only.',
                'Author/work exclusions and exact overlap screen are recorded separately.']
        selected = next(r for r in runs if r['seed']==inference['selected_seed'])
        report = {'scope': 'literal evaluation; corpus provenance and overlap require the preparation audit',
                  'cipher_sha256': stream.identity, 'tokens': total, 'cipher_types': stream.type_count,
                  'runs': runs, 'frequency_baseline': metrics(key),
                  'inventory_coverage': {'covered_types': len(covered), 'total_types': stream.type_count,
                                         'token_ceiling': sum(counts[c] for c in covered)/total,
                                         'type_ceiling': len(covered)/stream.type_count,
                                         'missing_types': stream.type_count-len(covered),
                                         'missing_tokens': sum(counts[c] for c in counts if c not in covered),
                                         'lm_attested_types': len(attested),
                                         'lm_attested_token_fraction': sum(counts[c] for c in attested)/total},
                  'mean_score_selected_token_accuracy': mean(r['score_selected_best']['token_accuracy'] for r in runs),
                  'selected_seed': inference['selected_seed'], 'selected_token_accuracy': selected['score_selected_best']['token_accuracy'],
                  'grammar': 'not_evaluated', 'semantics': 'not_evaluated',
                  'limitations': limitations + ['Search objective selects keys; it is not a calibrated recovery selector.',
                                                ('Full Latin inventory remains eligible; correct-candidate coverage is not guaranteed.'
                                                 if model.config.language == 'la' else
                                                 'Full frozen historical German inventory remains eligible; candidate support is not guaranteed.'
                                                 if model.config.language == 'de' else 'Million-form feasibility remains untested.')]}
        (root / 'evaluation.json').write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--truth', type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.resources, args.run, args.truth)
    print(json.dumps(report, indent=2))
