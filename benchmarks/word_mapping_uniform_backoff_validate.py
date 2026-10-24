"""Independently rescore persisted uniform-backoff perfect-start outputs."""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from benchmarks.word_mapping_first_corruption import PARENT, ORACLE
from benchmarks.word_mapping_uniform_backoff import OUT
from benchmarks.word_mapping_recovery import public_input
from benchmarks.word_mapping_widening import load_truth
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.evaluation import recovery
from voynich_smt.word_mapping.ngram import NgramModel
from voynich_smt.word_mapping.objective import objective_score
from voynich_smt.word_mapping.uniform_backoff import UniformBackoffModel


def validate():
    manifest = json.loads((OUT/'manifest.json').read_text())
    for p, expected in {**manifest['inputs_sha256'], **manifest['code_sha256']}.items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == expected
    model = UniformBackoffModel.from_model(NgramModel.load(PARENT/'model.json'))
    assert model.identity == manifest['experimental_model_sha256']
    forms = tuple(json.loads((PARENT/'candidates-oracle.json').read_text())['forms'])
    ids = {w:i for i,w in enumerate(forms)}
    report = json.loads((OUT/'report.json').read_text())
    assert report['manifest_sha256'] == digest(manifest)
    hashes, baseline_hashes = [], {}
    for target in [500,2000,8000,16000,32000]:
        public, truth = public_input(PARENT/f'public/fit-{target}.json'), load_truth(PARENT/f'truth/fit-{target}.json')
        gold = WordMapping(forms,{w:ids[f] for w,f in truth.decoding.items()})
        initial = objective_score(model,public.segments,gold,injective=True)
        for test in [t for t in report['original_moves'] if t['target']==target]:
            changed = WordMapping(forms,{**gold.assignments,**test['changes']})
            delta = objective_score(model,public.segments,changed,injective=True)-initial
            assert delta < 0 and math.isclose(delta,test['new_delta'],abs_tol=1e-7)
        for policy in ['greedy','annealing']:
            accuracies = []
            for seed in [101,202]:
                row = json.loads((OUT/f'runs/{target}/{policy}/seed-{seed}.json').read_text())
                hashes.append(digest(row))
                assert math.isclose(initial,row['initial_score'],abs_tol=1e-7)
                for which in ['current','best']:
                    mapping = WordMapping(forms,row[f'{which}_assignments'])
                    score = objective_score(model,public.segments,mapping,injective=True)
                    assert math.isclose(score,row['trace'][-1][f'{which}_score'],abs_tol=1e-7)
                    assert recovery(public,truth,mapping) == row['trace'][-1][f'{which}_recovery']
                accuracies.append(row['trace'][-1]['best_recovery']['exact_token_accuracy'])
                assert sum(v['proposed'] for v in row['quality'].values()) == 20000
                witness = row['perfect_score_witness']
                if witness:
                    mapping = WordMapping(forms,{**gold.assignments,**witness['changes']})
                    delta = objective_score(model,public.segments,mapping,injective=True)-initial
                    assert math.isclose(delta,witness['score_delta'],abs_tol=1e-7)
                baseline_path = ORACLE/f'runs/{target}/{policy}/seed-{seed}/report.json'
                baseline = json.loads(baseline_path.read_text())
                baseline_hashes[str(baseline_path)] = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
                assert row['baseline_best_accuracy'] == baseline['trace'][-1]['best_recovery']['exact_token_accuracy']
            summary = next(s for s in report['summary'] if s['target']==target and s['policy']==policy)
            assert summary['new_mean_accuracy'] == mean(accuracies)
    assert hashes == report['run_sha256']
    assert report['proposals'] == 20*20000
    write_json(OUT/'validation.json',{'validated':True,'report_sha256':digest(report),
        'runs':20,'proposals':400000,'baseline_inputs_sha256':baseline_hashes,
        'checks':['input and model hashes','all final current/best full scores and recovery',
                  'strict-improvement witnesses','proposal counts','paired baseline accuracies','run and summary identities'],
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('Validated all 20 runs, 400,000 proposals, final scores, accuracies and strict-improvement witnesses.')


if __name__=='__main__':
    validate()
