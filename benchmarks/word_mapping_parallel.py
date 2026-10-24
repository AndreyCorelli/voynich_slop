"""Independent process workers receive public inputs; oracle evaluation stays in parent."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import json
import multiprocessing
from pathlib import Path

from benchmarks.word_mapping_ablation import (
    evaluate, job_directory, job_public, prepare, search_config, summarize)
from benchmarks.word_mapping_recovery import optimize
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.word_mapping.annealing import Annealer
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.ngram import NgramModel

_MODELS = None
_CANDIDATES = None


def _initialize_worker(out):
    global _MODELS, _CANDIDATES
    out = Path(out)
    _MODELS = {path.stem: NgramModel.load(path) for path in (out / 'models').glob('*.json')}
    value = json.loads((out / 'candidates.json').read_text())
    value['forms'] = tuple(value['forms'])
    value['lemma_forms'] = {lemma: tuple(forms) for lemma, forms in value['lemma_forms'].items()}
    _CANDIDATES = CandidateCatalog(**value)


def _search_worker(model_name, public, config, directory, resume, checkpoint_every):
    # Neither truth paths nor truth-bearing objects are arguments to this worker.
    _, timing = optimize(_MODELS[model_name], _CANDIDATES, public, config, directory,
                         resume=resume, checkpoint_every=checkpoint_every)
    return timing


def run(foundation, out, plan, *, workers=4, resume=False, checkpoint_every=10000):
    if type(workers) is not int or workers < 1:
        raise ValueError('Worker count must be positive')
    out = Path(out)
    manifest, models, candidates, fixtures, catalog = prepare(foundation, out, plan, resume=resume)
    jobs = plan.jobs()
    rows = {}
    pending = []
    for index, job in enumerate(jobs):
        public = job_public(fixtures, plan, job)
        directory = job_directory(out, job)
        path = directory / 'result.json'
        if resume and path.exists():
            saved = json.loads(path.read_text())
            row = saved['row']
            if saved['sha256'] != digest(row) or row['job'] != job:
                raise ValueError('Completed parallel result changed')
            search = Annealer(models[job['arm']['model']], candidates, public.segments,
                search_config(plan, job, public), input_sha256=public.identity).resume(directory / 'checkpoint.json')
            if not search.complete or row['search_sha256'] != search.identity:
                raise ValueError('Completed result does not match checkpoint')
            rows[index] = row
        else:
            pending.append((index, job, public, directory))
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context('spawn'),
            initializer=_initialize_worker, initargs=(out,)) as pool:
        futures = {pool.submit(_search_worker, job['arm']['model'], public,
            search_config(plan, job, public), directory, resume, checkpoint_every): (index, job, public, directory)
            for index, job, public, directory in pending}
        for future in as_completed(futures):
            index, job, public, directory = futures[future]
            timing = future.result()
            model = models[job['arm']['model']]
            search = Annealer(model, candidates, public.segments, search_config(plan, job, public),
                input_sha256=public.identity).resume(directory / 'checkpoint.json')
            row = evaluate(out, model, candidates, public, search, catalog, job)
            row['elapsed_seconds_this_invocation'] = timing['elapsed_seconds_this_invocation']
            row['evaluations_per_second'] = timing['evaluations_per_second']
            write_json(directory / 'result.json', {'row': row, 'sha256': digest(row)})
            rows[index] = row
            ordered = [rows[i] for i in sorted(rows)]
            write_json(out / 'progress.json', {'complete': False, 'completed_runs': len(rows),
                'planned_runs': len(jobs), 'completed_evaluations': sum(r['evaluations'] for r in ordered),
                'summaries': summarize(ordered)})
            print(f'Completed {len(rows)}/{len(jobs)}: {job["arm"]["name"]}, '
                  f'{job["fixture"]}, seed {job["seed"]}, budget {job["budget"]}', flush=True)
    report = {'manifest_sha256': manifest['sha256'], **summarize([rows[i] for i in range(len(jobs))])}
    write_json(out / 'report.json', report)
    write_json(out / 'progress.json', {'complete': True, 'completed_runs': len(rows),
        'planned_runs': len(jobs), 'completed_evaluations': report['total_evaluations']})
    return report
