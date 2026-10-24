"""Posthoc frequency-initialization baseline for the completed widening study."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from benchmarks.word_mapping_recovery import public_input
from benchmarks.word_mapping_widening import OUT, accuracy_subset, load_candidates, load_truth
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.ngram import NgramModel


def run(out=OUT, *, validate=False):
    out = Path(out)
    report = json.loads((out / 'report.json').read_text())
    validated = json.loads((out / 'validation.json').read_text())
    if not validated['validated'] or validated['report_sha256'] != digest(report):
        raise ValueError('Validated widening report required')
    model = NgramModel.load(out / 'model.json')
    candidate = load_candidates(out / 'candidates-oracle.json')
    held = public_input(out / 'public/holdout.json')
    held_truth = load_truth(out / 'truth/holdout.json')
    rows = []
    targets = sorted({row['job']['target'] for row in report['rows']})
    for target in targets:
        public = public_input(out / f'public/fit-{target}.json')
        truth = load_truth(out / f'truth/fit-{target}.json')
        # Frequency initialization has unique forms and ignores its random seed.
        initial = candidate.initialize(public.segments, active_types=len(truth.decoding), seed=0, mode='frequency')
        if initial.collapse_penalty:
            raise ValueError('Frequency baseline unexpectedly requires injective repair')
        initial_score = model.score(initial.render(public.segments)).log_likelihood
        details = []
        for row in report['rows']:
            if row['job']['target'] != target or row['job']['coverage'] != 'oracle' or 'scaled' not in row['job']['budget_modes']:
                continue
            directory = out / 'runs' / row['job']['label']
            checkpoint = json.loads((directory / 'checkpoint.json').read_text())
            if not math.isclose(initial_score, checkpoint['initial_objective'], abs_tol=1e-7, rel_tol=1e-12):
                raise ValueError('Frequency baseline differs from actual search start')
            archive = json.loads((directory / 'archive.json').read_text())
            if digest(archive) != row['archive_sha256']:
                raise ValueError('Archive changed')
            mapping = WordMapping(candidate.forms, archive['rows'][0]['assignments'])
            counts = Counter(w for s in public.segments for w in s)
            correct = [{'surface': truth.decoding[w], 'occurrences': n} for w, n in counts.items()
                       if mapping.forms[mapping.assignments[w]] == truth.decoding[w]]
            details.append({'seed': row['job']['seed'],
                'correct_forms': sorted(correct, key=lambda x: (-x['occurrences'], x['surface']))})
        rows.append({'target': target, 'initial_frequency_recovery': recovery(public, truth, initial),
            'initial_holdout_recurring': accuracy_subset(held, held_truth, initial, lambda w, f: w in initial.assignments),
            'final_scaled_correct_forms': details})
    result = {'source_report_sha256': digest(report),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'policy': 'posthoc oracle-pool frequency initializer; no collisions; checked against actual initial objectives',
        'rows': rows}
    path = out / 'frequency-initialization-diagnostic.json'
    if validate:
        if json.loads(path.read_text()) != result:
            raise ValueError('Frequency diagnostic differs')
    else:
        write_json(path, result)
    print(json.dumps([{'target': r['target'],
                      'initial_token_accuracy': r['initial_frequency_recovery']['exact_token_accuracy'],
                      'initial_holdout_recurring_accuracy': r['initial_holdout_recurring']['accuracy']} for r in rows], indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()
    run(args.out, validate=args.validate)
