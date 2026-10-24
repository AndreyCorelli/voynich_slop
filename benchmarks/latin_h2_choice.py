"""Seven paired H2 cyclic versus balanced-random choice experiments."""
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
from benchmarks import latin_h2_layout as layout_source
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_automaton import WordAutomaton

OUT = Path('experiments/results/latin-h2-choice')


def balanced_random(train, key, seed):
    counts=Counter(''.join(train)); rng=random.Random(seed); bags={}
    for letter,count in sorted(counts.items()):
        if count % 2: raise ValueError('Balanced training requires even letter totals')
        bag=[key[letter][0]]*(count//2)+[key[letter][1]]*(count//2)
        rng.shuffle(bag); bags[letter]=bag
    positions=Counter(); result=[]
    for word in train:
        encrypted=[]
        for letter in word:
            encrypted.append(bags[letter][positions[letter]]); positions[letter]+=1
        result.append(encrypted)
    return result


def random_choice(fixture, seed):
    positive=balanced_random(fixture['truth']['train'],fixture['truth']['key'],seed)
    assert Counter(c for w in positive for c in w)==Counter(c for w in fixture['arms']['positive'] for c in w)
    assert positive!=fixture['arms']['positive']
    return {**fixture,'arms':{'positive':positive,'shuffle':pattern_preserving_shuffle(positive,fixture['shuffle_seed'])}}


def fresh_fixture(inventory,automaton,alphabet,eligible):
    pool=sorted(random.Random(9101).sample(eligible,512))
    types,held=baseline.select_family(pool,9401,9501)
    codes=[''.join(pair) for pair in product('qrstuvwx',repeat=2)]; random.Random(9201).shuffle(codes)
    key={letter:codes[2*i:2*i+2] for i,letter in enumerate(alphabet['symbols'])}
    train=types*2; positive,held_cipher=baseline.encrypt(train,held,key)
    return {'id':'seed-9101','case':{'mode':'upstream-default','kind':'synthetic-h2','alphabet':alphabet,'automaton':automaton},
            'inventory':inventory,'solver_ms':30000,'worker_wall_seconds':60,'max_homophones':2,
            'arms':{'positive':positive,'shuffle':pattern_preserving_shuffle(positive,9301)},'held_cipher':held_cipher,
            'truth':{'train':train,'held':held,'key':key},'selection_seed':9101,'held_seed':9401,'extra_seed':9501,'key_seed':9201,'shuffle_seed':9301}


def prepare():
    source=layout_source.prepare()
    full=baseline.compact.prepare()['inventories']['upstream-default']['inventory']
    eligible=[w for w in baseline.compact.inventory_lines(full['path']) if 3<=len(w)<=6]
    folder=OUT/'inventory'; folder.mkdir(parents=True,exist_ok=True); metadata=[]
    for name,raw in [('words.txt.gz',gzip.compress(('\n'.join(eligible)+'\n').encode(),mtime=0)),
                     ('automaton.json.gz',gzip.compress(json.dumps(asdict(WordAutomaton.from_sorted(eligible)),separators=(',',':')).encode(),mtime=0))]:
        path=folder/name
        if path.exists(): assert path.read_bytes()==raw
        else: path.write_bytes(raw)
        metadata.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
    inventory,automaton=metadata; inventory['word_count']=len(eligible)
    alphabet={'symbols':sorted(set(''.join(eligible)))}
    pairs=[]; rungs=[]
    for old in source['rungs']:
        if old['layout']!='two-pass' or old['fixtures'][0]['selection_seed'] not in (7101,7102): continue
        fixture=old['fixtures'][0]
        changed={**fixture,'inventory':inventory,'case':{**fixture['case'],'automaton':automaton}}
        pairs.append((old['pair'],changed,int(fixture['selection_seed'])+10000))
    pairs.append(('seed-9101-types-24',fresh_fixture(inventory,automaton,alphabet,eligible),19101))
    assert len(pairs)==7
    for pair,cyclic,choice_seed in pairs:
        for selection,fixture in (('cyclic',cyclic),('balanced-random',random_choice(cyclic,choice_seed))):
            rungs.append({'job':f'{pair}-{selection}','pair':pair,'selection':selection,'choice_seed':choice_seed,'fixtures':[fixture]})
    paths=[Path(__file__),Path(baseline.__file__),Path(layout_source.__file__),Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    p={'baseline_sha256':digest(source),'complete_source_inventory':full,'eligible_count':len(eligible),'code_sha256':{str(path):digest(path.read_text()) for path in paths},'rungs':rungs,
       'scope':'Seven matched cyclic versus balanced-random training-choice pairs on complete default length3..6 inventory. Six adaptive seed7101/7102 cases at12/18/24 types, fresh seed9101 at24 types. All cyclic baselines refitted with complete inventory; no old subset score reused. Same words, order, key, dictionary, held cipher and global code counts within pair; only training code choices vary. Holdout choices remain frozen cyclic. Same free-H2/DAG/pruning/budgets and first-key/exclusion policy; all inputs frozen before fits.'}
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
        rows={}
        for task in ('positive','shuffle','ambiguity'):
            path=folder/f'{task}-result.json'; print(rung['job'],task,flush=True)
            if not path.exists():
                start=perf_counter()
                try:
                    result=subprocess.run([sys.executable,'-m','benchmarks.latin_h2_choice','--worker',rung['job'],'--task',task],capture_output=True,text=True,timeout=fixture['worker_wall_seconds'])
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
        assert adjacent['pair']==two['pair'] and adjacent['selection']=='cyclic' and two['selection']=='balanced-random'
        a,b=adjacent['fixtures'][0],two['fixtures'][0]; assert random_choice(a,two['choice_seed'])==b
        assert a['truth']==b['truth'] and a['held_cipher']==b['held_cipher']
        assert a['case']==b['case'] and a['inventory']==b['inventory'] and a['truth']['key']==b['truth']['key']
        record={'pair':adjacent['pair'],'fresh':adjacent['pair'].startswith('seed-9101'),'choices':{}}
        for rung in (adjacent,two):
            folder=OUT/rung['job']/rung['fixtures'][0]['id']
            first=json.loads((folder/'positive-result.json').read_text()); exclusion=json.loads((folder/'ambiguity-result.json').read_text())
            record['choices'][rung['selection']]={'fixture_sha256':digest(rung['fixtures'][0]),'first_result_sha256':digest(first),'exclusion_sha256':digest(exclusion),
                'status':first['status'],'training_exact':first.get('training_exact'),'held_exact':first.get('held_exact'),'observed_codes':len(first.get('recovered_key',{})) if first['status']=='SAT' else len({c for w in rung['fixtures'][0]['arms']['positive'] for c in w}),
                'alternative_status':exclusion['status'],'alternative_method':exclusion.get('method'),'timings':first.get('timings'),
                'candidate_rows':sum(first['pruned_candidate_counts']) if 'pruned_candidate_counts' in first else None}
        comparisons.append(record)
    write_json(OUT/'comparison.json',{'prepared_sha256':digest(p),'pairs':comparisons})
    write_json(OUT/'validation.json',{'verified':True,'iterations':7,'choice_cases':14,'fit_arms':28,'ambiguity_records':14,'reused_cases':0,'new_cases':14,'complete_inventory_forms':p['eligible_count']})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true')
    parser.add_argument('--worker'); parser.add_argument('--task',choices=['positive','shuffle','ambiguity']); args=parser.parse_args()
    if args.worker: worker(args.worker,args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
