"""Seven frozen fresh-fixture H2 diversity and observed-key uniqueness cases."""
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
import z3
from benchmarks import latin_compact_membership as compact
from benchmarks import latin_h2_compressed as encoding
from benchmarks import latin_h2_pool as engine
from benchmarks.latin_h2_ladder import nested_words
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.homophone_patterns import homophone_subsets
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.language.word_patterns import equality_pattern
from voynich_smt.solver.candidate_semijoin import propagate_candidates
from voynich_smt.solver.compressed_candidates import compressed_membership

OUT = Path('experiments/results/latin-h2-identifiability')
PROTOCOL = ((7101,12),(7101,18),(7101,24),(7102,12),(7102,18),(7102,24),(7103,24))


def select_family(pool, held_seed, extra_seed):
    remaining = sorted(pool); base = []; covered = set()
    for _ in range(12):
        word = min(remaining, key=lambda w: (-len(set(w)-covered), w))
        base.append(word); covered.update(word); remaining.remove(word)
    held = random.Random(held_seed).sample([w for w in remaining if set(w) <= covered], 6)
    extras = sorted(set(remaining)-set(held)); random.Random(extra_seed).shuffle(extras)
    return base + extras[:12], held


def encrypt(train, held, key):
    counters = Counter()
    def word(value):
        result = []
        for letter in value:
            result.append(key[letter][counters[letter] % 2]); counters[letter] += 1
        return result
    return [word(w) for w in train], [word(w) for w in held]


def prepare():
    source = compact.prepare(); full = source['inventories']['upstream-default']['inventory']
    eligible = [w for w in compact.inventory_lines(full['path']) if 3 <= len(w) <= 6]
    alphabet = sorted(set(''.join(eligible))); families = {}; rungs = []
    for seed in sorted({s for s,_ in PROTOCOL}):
        index = seed-7100; pool = sorted(random.Random(seed).sample(eligible,512))
        types, held = select_family(pool,7400+index,7500+index)
        words = nested_words(pool,eligible,(32768,))[0]
        folder = OUT / 'inventories' / str(seed); folder.mkdir(parents=True,exist_ok=True)
        metadata = []
        for name,raw in [('words.txt.gz',gzip.compress(('\n'.join(words)+'\n').encode(),mtime=0)),
                         ('automaton.json.gz',gzip.compress(json.dumps(asdict(WordAutomaton.from_sorted(words)),separators=(',',':')).encode(),mtime=0))]:
            path=folder/name
            if path.exists(): assert path.read_bytes()==raw
            else: path.write_bytes(raw)
            metadata.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()})
        inventory,automaton=metadata; inventory['word_count']=32768
        codes=[''.join(pair) for pair in product('qrstuvwx',repeat=2)]; random.Random(7200+index).shuffle(codes)
        key={letter:codes[2*i:2*i+2] for i,letter in enumerate(alphabet)}
        families[seed]={'types':types,'held':held,'key':key,'inventory':inventory,'automaton':automaton}
    for seed,count in PROTOCOL:
        family=families[seed]; index=seed-7100
        train=[word for word in family['types'][:count] for _ in range(2)]
        positive,held_cipher=encrypt(train,family['held'],family['key'])
        observed={code for word in positive for code in word}
        assert all(code in observed for word in held_cipher for code in word)
        assert all(set(family['key'][c])<=observed for c in set(''.join(train)))
        shuffle=pattern_preserving_shuffle(positive,7300+index); assert shuffle!=positive
        fixture={'id':f'seed-{seed}','case':{'mode':'upstream-default','kind':'synthetic-h2','alphabet':{'symbols':alphabet},'automaton':family['automaton']},
                 'inventory':family['inventory'],'solver_ms':30000,'worker_wall_seconds':60,'max_homophones':2,
                 'arms':{'positive':positive,'shuffle':shuffle},'held_cipher':held_cipher,
                 'truth':{'train':train,'held':family['held'],'key':family['key']},
                 'selection_seed':seed,'held_seed':7400+index,'extra_seed':7500+index,'key_seed':7200+index,'shuffle_seed':7300+index}
        rungs.append({'job':f'seed-{seed}-types-{count}','types':count,'seed':seed,'fixtures':[fixture]})
    for seed in families:
        related=[r['fixtures'][0] for r in rungs if r['seed']==seed]
        for left,right in zip(related,related[1:]):
            assert left['arms']['positive']==right['arms']['positive'][:len(left['arms']['positive'])]
            assert left['held_cipher']==right['held_cipher'] and left['inventory']==right['inventory']
    paths=[Path(__file__),Path(engine.__file__),Path(encoding.__file__),Path('src/voynich_smt/solver/compressed_candidates.py'),
           Path('src/voynich_smt/solver/candidate_semijoin.py'),Path('src/voynich_smt/solver/capacity_matching.py'),Path('src/voynich_smt/solver/homophone_propagation.py'),
           Path('src/voynich_smt/language/homophone_patterns.py'),Path('benchmarks/latin_h2_ladder.py')]
    p={'source_sha256':digest(source),'eligible_count':len(eligible),'rungs':rungs,'code_sha256':{str(path):digest(path.read_text()) for path in paths},
       'scope':'Seven fresh synthetic H2 cases, whole original 512 sampling pools retained in 32768 dictionaries. Nested 12/18/24 distinct types on seeds 7101/7102, independent 24-type seed7103; six fresh novel holdouts/family, frozen before fits. Adjacent duplicated words give nested cipher prefixes and fixed held ciphertext. Free choice H<=2, Boolean DAG plus unchanged matching/semijoin. First-key scores only; separate 30s alternative-key checks, each worker capped at60s. No fixture replacement.'}
    path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def mapping_solver(cipher,candidates,domains,alphabet,capacity,budget,excluded):
    observed=sorted(domains); eq={(code,letter):z3.Bool(f'map_{i}_{j}') for i,code in enumerate(observed) for j,letter in enumerate(alphabet)}
    solver=z3.Solver(); solver.set(timeout=budget)
    solver.add([z3.PbEq([(eq[code,l],1) for l in alphabet],1) for code in observed])
    solver.add([z3.PbLe([(eq[code,l],1) for code in observed],capacity) for l in alphabet])
    solver.add([z3.Not(eq[code,l]) for code in observed for l in alphabet if l not in domains[code]])
    for i,(word,pool) in enumerate(zip(cipher,candidates)):
        solver.add(compressed_membership(word,pool,eq,f'word_{i}','dag'))
    solver.add(z3.Or([z3.Not(eq[code,letter]) for code,letter in excluded.items()]))
    return solver,eq


def ambiguity(folder):
    fixture=json.loads((folder/'prepared.json').read_text()); first=json.loads((folder/'positive-result.json').read_text())
    row={'fixture_sha256':digest(fixture),'first_result_sha256':digest(first),'verified':False}
    if first['status']!='SAT':
        write_json(folder/'ambiguity-result.json',{**row,'status':'NOT_EVALUATED_NO_SAT'}); return
    total=perf_counter(); timings={}
    def checkpoint(phase):
        write_json(folder/'ambiguity-phases.json',{'fixture_sha256':digest(fixture),'phase':phase,'timings':timings,'worker_elapsed_seconds':perf_counter()-total})
    def verify(key):
        a=compact.load_automaton(fixture['case']['automaton']); observed={c for w in fixture['arms']['positive'] for c in w}
        assert set(key)==observed and max(Counter(key.values()).values())<=fixture['max_homophones']
        words=[''.join(key[c] for c in w) for w in fixture['arms']['positive']]
        assert all(a.accepts(w) for w in words) and key!=first['recovered_key']
        return words
    checkpoint('checking-generating-witness')
    truth={code:l for l,codes in fixture['truth']['key'].items() for code in codes if code in first['recovered_key']}
    if truth!=first['recovered_key']:
        words=verify(truth)
        row.update(status='SAT',verified=True,method='generating-key-witness',alternative_key=truth,training_words=words)
    else:
        checkpoint('filtering'); start=perf_counter()
        metadata=fixture['inventory']; assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest()==metadata['sha256']
        cipher=fixture['arms']['positive']
        subsets=homophone_subsets(compact.inventory_lines(metadata['path']),[equality_pattern(w) for w in cipher])
        timings['filter_seconds']=perf_counter()-start
        checkpoint('propagating'); start=perf_counter()
        candidates,domains,rounds,contradiction=propagate_candidates(cipher,[subsets[equality_pattern(w)] for w in cipher],fixture['case']['alphabet']['symbols'],2)
        assert not contradiction
        timings['propagation_seconds']=perf_counter()-start
        checkpoint('constructing'); start=perf_counter()
        solver,eq=mapping_solver(cipher,candidates,domains,fixture['case']['alphabet']['symbols'],2,fixture['solver_ms'],first['recovered_key'])
        timings['construction_seconds']=perf_counter()-start
        checkpoint('solving'); start=perf_counter(); status=solver.check(); timings['solver_seconds']=perf_counter()-start
        row.update(status=str(status).upper(),method='exclude-first-observed-key',pruned_candidate_counts=list(map(len,candidates)))
        if status==z3.sat:
            model=solver.model(); key={code:next(l for l in fixture['case']['alphabet']['symbols'] if z3.is_true(model.eval(eq[code,l],model_completion=True))) for code in domains}
            row.update(verified=True,alternative_key=key,training_words=verify(key))
        elif status==z3.unknown: row['reason']=solver.reason_unknown()
    row.update(timings=timings,worker_elapsed_seconds=perf_counter()-total)
    write_json(folder/'ambiguity-result.json',row); checkpoint('complete')


def worker(job,task):
    p=json.loads((OUT/'prepared.json').read_text()); rung=next(r for r in p['rungs'] if r['job']==job)
    folder=OUT/job/rung['fixtures'][0]['id']
    if task=='ambiguity': ambiguity(folder)
    else: encoding.configure(folder,'dag'); engine.fit(task)


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
                    result=subprocess.run([sys.executable,'-m','benchmarks.latin_h2_identifiability','--worker',rung['job'],'--task',task],capture_output=True,text=True,timeout=fixture['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path,{'status':'WALL_TIMEOUT','verified':False,'wall_seconds':perf_counter()-start})
            row=json.loads(path.read_text()); print(row['status'],row.get('timings'),'exact=',row.get('training_exact'),row.get('held_exact'),flush=True)
            rows[task]=row
        write_json(root/'report.json',{'prepared_sha256':digest(rung),'complete':True,'fixtures':{fixture['id']:{arm:rows[arm] for arm in fixture['arms']}}})
    validate()


def validate():
    p=prepare(); old=engine.OUT,engine.prepare,engine.propagate_candidates,engine.candidate_membership
    try:
        for rung in p['rungs']:
            fixture=rung['fixtures'][0]; root=OUT/rung['job']; folder=root/fixture['id']
            encoding.configure(root,'dag'); engine.prepare=lambda rung=rung:rung; engine.validate()
            first=json.loads((folder/'positive-result.json').read_text()); row=json.loads((folder/'ambiguity-result.json').read_text())
            if row['status']=='WALL_TIMEOUT': continue
            assert row['fixture_sha256']==digest(fixture) and row['first_result_sha256']==digest(first)
            if first['status']!='SAT': assert row['status']=='NOT_EVALUATED_NO_SAT'; continue
            phase=json.loads((folder/'ambiguity-phases.json').read_text()); assert phase['phase']=='complete' and phase['timings']==row['timings'] and phase['fixture_sha256']==digest(fixture)
            assert row['status'] in ('SAT','UNSAT','UNKNOWN')
            if row['status']=='SAT':
                key=row['alternative_key']; assert key!=first['recovered_key'] and set(key)==set(first['recovered_key'])
                assert max(Counter(key.values()).values())<=2
                words=[''.join(key[c] for c in w) for w in fixture['arms']['positive']]
                assert words==row['training_words'] and row['verified']
                a=compact.load_automaton(fixture['case']['automaton']); assert all(a.accepts(w) for w in words)
            if row['method']=='generating-key-witness':
                truth={code:l for l,codes in fixture['truth']['key'].items() for code in codes if code in first['recovered_key']}
                assert row['alternative_key']==truth
            else:
                assert row['method']=='exclude-first-observed-key'
                assert row['pruned_candidate_counts']==first['pruned_candidate_counts']
                assert row['status']!='SAT' or row['alternative_key']!=first['recovered_key']
                if row['status']=='UNSAT': assert first['training_exact']==len(fixture['truth']['train']) and first['held_exact']==len(fixture['truth']['held'])
    finally: engine.OUT,engine.prepare,engine.propagate_candidates,engine.candidate_membership=old
    write_json(OUT/'validation.json',{'verified':True,'iterations':len(p['rungs']),'fit_arms':2*len(p['rungs']),'ambiguity_records':len(p['rungs'])})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true')
    parser.add_argument('--worker'); parser.add_argument('--task',choices=['positive','shuffle','ambiguity']); args=parser.parse_args()
    if args.worker: worker(args.worker,args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
