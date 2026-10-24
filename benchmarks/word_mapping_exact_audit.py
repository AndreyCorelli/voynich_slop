"""Oracle-restricted exact optimization versus annealing on development windows."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_ablation import load_truth
from benchmarks.word_mapping_neural_probe import PARENT
from benchmarks.word_mapping_recovery import public_input, resources
from voynich_smt.bootstrap_mapping import BootstrapOptions, BootstrapSearch
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.phrase_mapping import exact_mapping_audit
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.objective import objective_score

OUT = Path('experiments/results/word-mapping/exact-mapping-audit')


def run(parent=PARENT, out=OUT, *, validate=False):
    parent, out = Path(parent), Path(out)
    manifest = json.loads((parent / 'manifest.json').read_text())
    validation = json.loads((parent / 'validation.json').read_text())
    if digest(manifest['protocol']) != manifest['sha256'] or not validation['validated'] or validation['manifest_sha256'] != manifest['sha256']:
        raise ValueError('Validated parent required')
    model, morphology, candidates = resources(parent / 'bundle-1/foundation')
    if model.identity != manifest['protocol']['model_sha256'] or digest(asdict(candidates)) != manifest['protocol']['candidate_sha256']:
        raise ValueError('Changed training resources')
    rows = []
    for bundle in ('bundle-1', 'bundle-2', 'bundle-3'):
        study = parent / bundle / 'study'
        public = public_input(study / 'fixtures/one-to-one.json')
        if public.identity != json.loads((study / 'manifest.json').read_text())['protocol']['fixture_sha256']['one-to-one']:
            raise ValueError('Changed public fixture')
        truth = load_truth(study, 'one-to-one')
        windows = [(i, start, tuple(segment[start:start+5]))
                   for i, segment in enumerate(public.segments) for start in range(0, len(segment)-4, 5)]
        selected = sorted(windows, key=lambda w: digest({'bundle': bundle, 'segment': w[0], 'start': w[1]}))[:6]
        for segment, start, window in selected:
            gold_forms = {truth.decoding[w] for w in window}
            # Explicit oracle restriction: gold forms plus training-frequency distractors.
            forms = list(sorted(gold_forms))
            for form in candidates.forms:
                if form not in forms:
                    forms.append(form)
                if len(forms) == 8:
                    break
            forms = tuple(forms)
            subset = replace(candidates, forms=forms,
                form_counts={w: candidates.form_counts[w] for w in forms},
                lemma_forms={k: tuple(w for w in values if w in forms)
                             for k, values in candidates.lemma_forms.items() if any(w in forms for w in values)},
                lemma_counts={k: n for k, n in candidates.lemma_counts.items()
                              if any(w in forms for w in candidates.lemma_forms[k])})
            segments = (window,)
            exact = exact_mapping_audit(model, segments, forms)
            gold = WordMapping(forms, {w: forms.index(truth.decoding[w]) for w in set(window)})
            gold_score = objective_score(model, segments, gold, injective=True)
            scores = exact.pop('scores')
            best = WordMapping(forms, exact['best_assignments'])
            def accuracy(mapping):
                return mean(mapping.forms[mapping.assignments[w]] == truth.decoding[w] for w in window)
            searches = []
            for seed in (101, 202):
                config = SearchConfig(seed=seed, restarts=3, steps_per_restart=2000,
                                      active_types=len(set(window)), injective=True, archive_size=10)
                search = BootstrapSearch(model, subset, morphology, segments, config, BootstrapOptions())
                search.advance()
                searches.append({'seed': seed, 'evaluations': search.evaluations,
                    'best_score': search.archive[0]['score'], 'score_gap': exact['best_score']-search.archive[0]['score'],
                    'found_optimum': math.isclose(exact['best_score'], search.archive[0]['score'], abs_tol=1e-8, rel_tol=0),
                    'token_accuracy': accuracy(search.best_mapping)})
            rows.append({'bundle': bundle, 'segment': segment, 'start': start, 'window': window,
                'public_sha256': public.identity, 'truth_sha256': digest(asdict(truth)), 'forms': forms,
                **exact, 'truth_score': gold_score,
                'mappings_better_than_truth': sum(s > gold_score+1e-9 for s in scores),
                'truth_is_optimal': math.isclose(gold_score, exact['best_score'], abs_tol=1e-9, rel_tol=0),
                'selected_optimum_token_accuracy': accuracy(best), 'searches': searches})
            print(f'Audited {bundle}/{segment}/{start}: {exact["states"]} states', flush=True)
    paths = [Path(__file__), Path('src/voynich_smt/phrase_mapping.py'), Path('src/voynich_smt/bootstrap_mapping.py'),
             *sorted(Path('src/voynich_smt/word_mapping').glob('*.py'))]
    protocol = {'parent_sha256': manifest['sha256'], 'model_sha256': model.identity,
        'candidate_policy': 'oracle gold forms plus top training frequency distractors to eight forms',
        'selection': 'six deterministic SHA-selected five-token windows per development bundle',
        'code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    summary = {'cases': len(rows), 'exhaustive_states': sum(r['states'] for r in rows),
        'truth_optimal_cases': sum(r['truth_is_optimal'] for r in rows),
        'mean_selected_optimum_token_accuracy': mean(r['selected_optimum_token_accuracy'] for r in rows),
        'annealing_runs': sum(len(r['searches']) for r in rows),
        'annealing_optimum_hits': sum(s['found_optimum'] for r in rows for s in r['searches']),
        'annealing_evaluations': sum(s['evaluations'] for r in rows for s in r['searches'])}
    report = json.loads(json.dumps({'protocol': protocol, 'protocol_sha256': digest(protocol), 'rows': rows, 'summary': summary}))
    if validate:
        if json.loads((out / 'report.json').read_text()) != report:
            raise ValueError('Exact audit differs on recomputation')
        write_json(out / 'validation.json', {'validated': True, 'report_sha256': digest(report)})
    else:
        if (out / 'report.json').exists():
            raise ValueError('Output already exists')
        write_json(out / 'report.json', report)
    print(json.dumps(summary, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.parent, args.out, validate=args.validate)
