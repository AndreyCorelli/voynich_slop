"""Seven paired H2 duplication-layout diagnostics, with fresh replication."""
import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_identifiability as baseline
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_automaton import WordAutomaton

OUT = Path('experiments/results/latin-h2-layout')
COPY_NAMES = ('prepared.json','positive-result.json','positive-phases.json','shuffle-result.json','shuffle-phases.json','ambiguity-result.json','ambiguity-phases.json')


def two_pass(fixture):
    types = fixture['truth']['train'][::2]
    assert fixture['truth']['train'] == [word for word in types for _ in range(2)]
    train = types * 2
    positive, held = baseline.encrypt(train, fixture['truth']['held'], fixture['truth']['key'])
    assert held == fixture['held_cipher']
    assert Counter(train) == Counter(fixture['truth']['train'])
    assert Counter(c for w in positive for c in w) == Counter(c for w in fixture['arms']['positive'] for c in w)
    return {**fixture, 'truth': {**fixture['truth'], 'train': train},
            'arms': {'positive': positive, 'shuffle': pattern_preserving_shuffle(positive, fixture['shuffle_seed'])}}


def fresh_fixture(source):
    full = baseline.compact.prepare()['inventories']['upstream-default']['inventory']
    eligible = [w for w in baseline.compact.inventory_lines(full['path']) if 3 <= len(w) <= 6]
    pool = sorted(random.Random(8101).sample(eligible,512))
    types, held = baseline.select_family(pool,8401,8501)
    words = baseline.nested_words(pool,eligible,(32768,))[0]
    folder = OUT / 'inventories' / '8101'; folder.mkdir(parents=True,exist_ok=True)
    metadata = []
    for name,raw in [('words.txt.gz',gzip.compress(('\n'.join(words)+'\n').encode(),mtime=0)),
                     ('automaton.json.gz',gzip.compress(json.dumps(asdict(WordAutomaton.from_sorted(words)),separators=(',',':')).encode(),mtime=0))]:
        path = folder / name
        if path.exists(): assert path.read_bytes() == raw
        else: path.write_bytes(raw)
        metadata.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
    inventory,automaton=metadata; inventory['word_count']=32768
    alphabet=source['rungs'][0]['fixtures'][0]['case']['alphabet']
    codes=[''.join(pair) for pair in product('qrstuvwx',repeat=2)]; random.Random(8201).shuffle(codes)
    key={letter:codes[2*i:2*i+2] for i,letter in enumerate(alphabet['symbols'])}
    train=[word for word in types for _ in range(2)]; positive,held_cipher=baseline.encrypt(train,held,key)
    return {'id':'seed-8101','case':{'mode':'upstream-default','kind':'synthetic-h2','alphabet':alphabet,'automaton':automaton},
            'inventory':inventory,'solver_ms':30000,'worker_wall_seconds':60,'max_homophones':2,
            'arms':{'positive':positive,'shuffle':pattern_preserving_shuffle(positive,8301)},'held_cipher':held_cipher,
            'truth':{'train':train,'held':held,'key':key},'selection_seed':8101,'held_seed':8401,'extra_seed':8501,'key_seed':8201,'shuffle_seed':8301}


def prepare():
    source=baseline.prepare()
    assert json.loads((baseline.OUT/'validation.json').read_text())['verified']
    pairs=[]; rungs=[]
    for old in source['rungs']:
        if old['seed'] not in (7101,7102): continue
        pairs.append((old['job'],old['fixtures'][0],baseline.OUT/old['job']/old['fixtures'][0]['id']))
    pairs.append(('seed-8101-types-24',fresh_fixture(source),None))
    for pair,adjacent,origin in pairs:
        for layout,fixture in (('adjacent',adjacent),('two-pass',two_pass(adjacent))):
            rung={'job':f'{pair}-{layout}','pair':pair,'layout':layout,'fixtures':[fixture]}
            if layout=='adjacent' and origin is not None:
                assert json.loads((origin/'prepared.json').read_text())==fixture
                rung['reuse']={'directory':str(origin),'files':{name:hashlib.sha256((origin/name).read_bytes()).hexdigest() for name in COPY_NAMES}}
            rungs.append(rung)
    paths=[Path(__file__),Path(baseline.__file__),Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    p={'baseline_sha256':digest(source),'code_sha256':{str(path):digest(path.read_text()) for path in paths},'rungs':rungs,
       'scope':'Seven paired layouts: six adaptive diagnostics reuse validated adjacent seed7101/7102 cases at12/18/24 types; seventh is fresh seed8101 at24 types, both layouts frozen before fits. Words, keys, inventories, held plaintext/cipher and global code counts match within pair. Only duplicate ordering and resulting training cipher co-occurrence change. Same DAG/pruning/free-H2/budgets and first-key/exclusion policy. No fixture replacement or score rescue.'}
    path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def worker(job,task):
    p=json.loads((OUT/'prepared.json').read_text()); rung=next(r for r in p['rungs'] if r['job']==job)
    folder=OUT/job/rung['fixtures'][0]['id']
    if task=='ambiguity': baseline.ambiguity(folder)
    else: baseline.encoding.configure(folder,'dag'); baseline.engine.fit(task)


def run():
    p=prepare()
    for rung in p['rungs']:
        fixture=rung['fixtures'][0]; root=OUT/rung['job']; folder=root/fixture['id']; write_json(folder/'prepared.json',fixture)
        if 'reuse' in rung:
            for name,checksum in rung['reuse']['files'].items():
                raw=(Path(rung['reuse']['directory'])/name).read_bytes(); assert hashlib.sha256(raw).hexdigest()==checksum
                path=folder/name
                if path.exists(): assert path.read_bytes()==raw
                else: path.write_bytes(raw)
        rows={}
        for task in ('positive','shuffle','ambiguity'):
            path=folder/f'{task}-result.json'; print(rung['job'],task,'reused' if 'reuse' in rung else 'new',flush=True)
            if not path.exists():
                start=perf_counter()
                try:
                    result=subprocess.run([sys.executable,'-m','benchmarks.latin_h2_layout','--worker',rung['job'],'--task',task],capture_output=True,text=True,timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path,{'status':'WALL_TIMEOUT','verified':False,'wall_seconds':perf_counter()-start})
            row=json.loads(path.read_text()); print(row['status'],row.get('timings'),'exact=',row.get('training_exact'),row.get('held_exact'),flush=True); rows[task]=row
        write_json(root/'report.json',{'prepared_sha256':digest(rung),'complete':True,'fixtures':{fixture['id']:{arm:rows[arm] for arm in fixture['arms']}}})
    validate()


def validate():
    p=prepare(); old=baseline.OUT,baseline.prepare
    try:
        baseline.OUT=OUT; baseline.prepare=lambda:p; baseline.validate()
    finally: baseline.OUT,baseline.prepare=old
    comparisons=[]
    for adjacent,two in zip(p['rungs'][::2],p['rungs'][1::2]):
        assert adjacent['pair']==two['pair'] and adjacent['layout']=='adjacent' and two['layout']=='two-pass'
        a,b=adjacent['fixtures'][0],two['fixtures'][0]; assert two_pass(a)==b
        assert a['case']==b['case'] and a['inventory']==b['inventory'] and a['truth']['key']==b['truth']['key']
        record={'pair':adjacent['pair'],'fresh':adjacent['pair'].startswith('seed-8101'),'layouts':{}}
        for rung in (adjacent,two):
            folder=OUT/rung['job']/rung['fixtures'][0]['id']
            if 'reuse' in rung:
                for name,checksum in rung['reuse']['files'].items(): assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==checksum
            first=json.loads((folder/'positive-result.json').read_text()); exclusion=json.loads((folder/'ambiguity-result.json').read_text())
            record['layouts'][rung['layout']]={'fixture_sha256':digest(rung['fixtures'][0]),'first_result_sha256':digest(first),'exclusion_sha256':digest(exclusion),
                'status':first['status'],'training_exact':first.get('training_exact'),'held_exact':first.get('held_exact'),'observed_codes':len(first.get('recovered_key',{})) if first['status']=='SAT' else len({c for w in rung['fixtures'][0]['arms']['positive'] for c in w}),
                'alternative_status':exclusion['status'],'alternative_method':exclusion.get('method'),'timings':first.get('timings'),
                'candidate_rows':sum(first['pruned_candidate_counts']) if 'pruned_candidate_counts' in first else None}
        comparisons.append(record)
    write_json(OUT/'comparison.json',{'prepared_sha256':digest(p),'pairs':comparisons})
    write_json(OUT/'validation.json',{'verified':True,'iterations':7,'layout_cases':14,'fit_arms':28,'ambiguity_records':14,'reused_cases':6,'new_cases':8})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true')
    parser.add_argument('--worker'); parser.add_argument('--task',choices=['positive','shuffle','ambiguity']); args=parser.parse_args()
    if args.worker: worker(args.worker,args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
