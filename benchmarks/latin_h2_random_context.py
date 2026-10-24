"""Frozen 48/96-word context comparisons for seven natural random arms."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_natural_random as source
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-random-context')
TASKS = source.TASKS


def protocol():
    prior = source.prepare(); raw = json.loads(Path(source.context.prior.prepare()['source_path']).read_text())
    compact = source.context.prior.baseline.compact
    policies = json.loads((compact.OUT/'report.json').read_text())['modes']
    automata = {m: compact.load_automaton(row['automaton']) for m,row in policies.items()}
    jobs = []
    for old in prior['jobs']:
        if old['selection'] != 'iid-random': continue
        index = old['pair']-1; fixture = old['fixture']; start = old['record_start']
        records = raw['records'][start-48:start]
        prefix = [source.context.prior.passages.morphology.canonical(''.join(r['tokens'])) for r in records]
        invalid = [i for i,(r,w) in enumerate(zip(records,prefix)) if r.get('excluded_reason') is not None or not w or not set(w)<=set(fixture['case']['alphabet']['symbols'])]
        for length in (48,96):
            f = {**fixture, 'truth': dict(fixture['truth'])}; before = [] if length == 48 else prefix
            f['truth']['train'] = before+fixture['truth']['train']
            positive = source.random_encrypt(before,fixture['truth']['key'],11601+index)+fixture['arms']['positive'] if not invalid or length == 48 else None
            coverage = {m: {'missing_training':[w for w in f['truth']['train'] if not a.accepts(w)],'missing_held':[w for w in old['full_held'] if not a.accepts(w)]} for m,a in automata.items()}
            seen = {c for w in positive for c in w} if positive is not None else set()
            mask = [set(w)<=seen for w in old['full_held_cipher']]
            f['held_cipher'] = [w for w,covered in zip(old['full_held_cipher'],mask) if covered]
            f['truth']['held'] = [w for w,covered in zip(old['full_held'],mask) if covered]
            f['arms'] = {'positive':positive,'shuffle':pattern_preserving_shuffle(positive,f['shuffle_seed'])} if positive is not None else None
            job = {**old,'job':f"passage-{index+1}-words-{length}",'training_length':length,'record_start':start-len(before),
                   'fixture':f,'coverage':coverage,'observed_codes':sorted(seen),'covered_mask':mask,'structural_failures':[] if length == 48 else invalid,
                   'admitted':(length == 48 or not invalid) and not coverage['through-medieval-rare']['missing_training'],
                   'prefix_choice_seed':11601+index,'prefix_records':[] if length == 48 else records,'reuse':None}
            if length == 48:
                assert f == fixture
                if job['admitted']:
                    folder=source.OUT/old['job']; names=['prepared.json']+[f'{t}-{s}.json' for t in TASKS for s in ('result','phases')]
                    job['reuse']={'folder':str(folder),'files':{name:digest((folder/name).read_text()) for name in names}}
            jobs.append(job)
    paths=[Path(__file__),Path(source.__file__),Path(source.context.__file__)]
    return {'prior_sha256':digest(prior),'source_sha256':digest(raw),'jobs':jobs,'code_sha256':{str(p):digest(p.read_text()) for p in paths},
        'scope':'Seven adaptive random-arm 48/96 context pairs, all original ciphers and six holdouts fixed. Independent random prefix stream. Same dictionary and budgets, partial holdout scoring, no replacements or target additions. Exact old records reused. Overlapping contexts/repeated holdouts are not independent replication.'}


def prepare():
    p=protocol(); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def worker(job,task):
    folder=OUT/job
    if task=='ambiguity': source.context.prior.baseline.ambiguity(folder)
    else: source.context.prior.baseline.encoding.configure(folder,'dag'); source.context.prior.baseline.engine.fit(task)


def validate():
    p=prepare(); context=source.context; old=context.OUT,context.prepare
    try:
        context.OUT=OUT; context.prepare=lambda:p; context.validate()
    finally: context.OUT,context.prepare=old
    report=json.loads((OUT/'report.json').read_text()); pairs=[]
    for short,long in zip(p['jobs'][::2],p['jobs'][1::2]):
        assert short['full_held_cipher']==long['full_held_cipher'] and short['full_held']==long['full_held']
        if long['fixture']['arms']:
            assert long['fixture']['arms']['positive'][-48:]==short['fixture']['arms']['positive']
        if short['reuse']:
            for name,sha in short['reuse']['files'].items():
                original=Path(short['reuse']['folder'])/name; copied=OUT/short['job']/name
                assert digest(original.read_text())==sha and original.read_bytes()==copied.read_bytes()
        pairs.append({'pair':short['pair'],'conditions':{str(j['training_length']):next(r for r in report['conditions'] if r['job']==j['job']) for j in (short,long)}})
    write_json(OUT/'comparison.json',{'prepared_sha256':digest(p),'pairs':pairs})


def run():
    p = prepare()
    print('Frozen seven matched pairs;', sum(j['admitted'] for j in p['jobs']), 'admitted conditions', flush=True)
    for job in p['jobs']:
        if not job['admitted']: print(job['job'], 'NOT_ADMITTED', flush=True); continue
        fixture = job['fixture']; folder = OUT/job['job']
        write_json(folder/'prepared.json', fixture)
        if job['reuse']:
            source = Path(job['reuse']['folder'])
            for name, sha in job['reuse']['files'].items():
                assert digest((source/name).read_text()) == sha
                if (folder/name).exists(): assert (folder/name).read_bytes() == (source/name).read_bytes()
                else: shutil.copyfile(source/name, folder/name)
            print(job['job'], 'REUSED', flush=True); continue
        for task in TASKS:
            path = folder/f'{task}-result.json'; print(job['job'], task, flush=True)
            if not path.exists():
                start = perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'benchmarks.latin_h2_random_context', '--worker', job['job'], '--task', task], capture_output=True, text=True, timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path, {'status': 'WALL_TIMEOUT', 'verified': False, 'wall_seconds': perf_counter()-start, 'fixture_sha256': digest(fixture)})
            row = json.loads(path.read_text()); print(row['status'], row.get('training_exact'), row.get('held_exact'), flush=True)
    validate()



if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true'); parser.add_argument('--worker'); parser.add_argument('--task',choices=TASKS); args=parser.parse_args()
    if args.worker: worker(args.worker,args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
