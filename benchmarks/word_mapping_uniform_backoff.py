"""Paired perfect-start Latin diagnostic with uniform n-gram fallback."""
import json
import math
from dataclasses import asdict
from pathlib import Path
from statistics import mean
import hashlib

from benchmarks.word_mapping_first_corruption import PARENT, ORACLE
from benchmarks.word_mapping_widening import load_truth
from benchmarks.word_mapping_recovery import public_input
from benchmarks.word_mapping_zero_corruption import snapshot, verify_witness
from voynich_smt.data.corpus import write_json, digest
from voynich_smt.oracle_mapping import OracleStartSearch
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.mapping import WordMapping
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramModel
from voynich_smt.word_mapping.objective import objective_score
from voynich_smt.word_mapping.uniform_backoff import UniformBackoffModel

OUT = Path('experiments/results/word-mapping/uniform-backoff-perfect-start-v1')


def run():
    if OUT.exists():
        raise ValueError('Output exists; preserve prior experiment')
    original = NgramModel.load(PARENT/'model.json')
    model = UniformBackoffModel.from_model(original)
    raw = json.loads((PARENT/'candidates-oracle.json').read_text())
    raw['forms'] = tuple(raw['forms'])
    candidates = CandidateCatalog(**raw)
    morphology = MorphologyCatalog.load(PARENT/'morphology.json')
    forms = candidates.forms
    ids = {w:i for i,w in enumerate(forms)}
    manifest = {'scope': 'Experimental uniform unigram fallback; unchanged observed n-grams, proposals and search; perfect-start diagnosis only',
        'original_model_sha256': original.identity, 'experimental_model_sha256': model.identity,
        'steps': 20000, 'seeds': [101,202], 'policies': ['greedy','annealing'],
        'normalization': 'Uniform base over all surface forms plus EOS and OOV; observed conditional counts unchanged',
        'code_sha256': {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/word_mapping/uniform_backoff.py')]}}
    inputs = [PARENT/'model.json', PARENT/'candidates-oracle.json', PARENT/'morphology.json']
    tests, rows = [], []
    for target in [500,2000,8000,16000,32000]:
        public_path, truth_path = PARENT/f'public/fit-{target}.json', PARENT/f'truth/fit-{target}.json'
        inputs.extend([public_path, truth_path])
        public, truth = public_input(public_path), load_truth(truth_path)
        gold = WordMapping(forms,{w:ids[f] for w,f in truth.decoding.items()})
        for seed in [101,202]:
            saved_path = ORACLE/f'runs/{target}/greedy/seed-{seed}/report.json'
            inputs.append(saved_path)
            old = json.loads(saved_path.read_text())
            witness = old['first_departure']
            changed = WordMapping(forms,{**gold.assignments, **witness['changes']})
            delta = objective_score(model,public.segments,changed,injective=True)-objective_score(model,public.segments,gold,injective=True)
            assert delta < 0
            tests.append({'target':target,'seed':seed,'old_delta':witness['score_delta'],'new_delta':delta,
                          'changes':witness['changes'],'lost_tokens':-witness['token_delta']})
    manifest['inputs_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(inputs))}
    write_json(OUT/'manifest.json',manifest)
    write_json(OUT/'original-first-move-checks.json',tests)
    print('All ten original corruptions now reduce score.',flush=True)
    for target in [500,2000,8000,16000,32000]:
        public, truth = public_input(PARENT/f'public/fit-{target}.json'), load_truth(PARENT/f'truth/fit-{target}.json')
        for policy in ['greedy','annealing']:
            for seed in [101,202]:
                config = SearchConfig(seed=seed,restarts=1,steps_per_restart=20000,
                    active_types=len(truth.decoding),initialization='frequency',injective=True,archive_size=1)
                search = OracleStartSearch(model,candidates,morphology,public,truth,config,policy=policy)
                trace = [snapshot(search,public,truth)]
                # Reproduce the original diagnostic's snapshot schedule.
                for stop in [1,10,100,1000,5000,20000]:
                    search.advance(stop-search.evaluations)
                    trace.append(snapshot(search,public,truth))
                verify_witness(search,search.first_departure)
                verify_witness(search,search.perfect_score_witness)
                old = json.loads((ORACLE/f'runs/{target}/{policy}/seed-{seed}/report.json').read_text())
                row = {'target':target,'policy':policy,'seed':seed,'config':asdict(config),
                    'initial_score':search.initial_objective,'score_gain':search.archive[0]['score']-search.initial_objective,
                    'first_departure':search.first_departure,'perfect_score_witness':search.perfect_score_witness,
                    'trace':trace,'quality':search.quality,'statistics':search.statistics,
                    'baseline_best_accuracy':old['trace'][-1]['best_recovery']['exact_token_accuracy'],
                    'best_assignments':dict(search.best_mapping.assignments),
                    'current_assignments':dict(search.scorer.assignments),'search_sha256':search.identity}
                rows.append(row)
                write_json(OUT/f'runs/{target}/{policy}/seed-{seed}.json',row)
                print(target,policy,seed,'best',round(100*trace[-1]['best_recovery']['exact_token_accuracy'],3),flush=True)
    summary=[]
    for target in [500,2000,8000,16000,32000]:
        for policy in ['greedy','annealing']:
            group=[r for r in rows if r['target']==target and r['policy']==policy]
            summary.append({'target':target,'policy':policy,
                'baseline_mean_accuracy':mean(r['baseline_best_accuracy'] for r in group),
                'new_mean_accuracy':mean(r['trace'][-1]['best_recovery']['exact_token_accuracy'] for r in group),
                'new_mean_type_accuracy':mean(r['trace'][-1]['best_recovery']['exact_type_accuracy'] for r in group),
                'mean_score_gain':mean(r['score_gain'] for r in group),
                'first_departures':[r['first_departure'] for r in group]})
    write_json(OUT/'report.json',{'manifest_sha256':digest(manifest),'validated':True,
        'runs':20,'proposals':400000,'original_moves':tests,'summary':summary,
        'run_sha256':[digest(r) for r in rows]})
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    run()
