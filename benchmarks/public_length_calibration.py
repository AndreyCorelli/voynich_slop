"""Prospective fixed-seed comparison of frozen midpoint search and ordinary recovery."""
import argparse
from dataclasses import asdict,replace
from itertools import islice,product
import json
from pathlib import Path
import random
from time import perf_counter

from benchmarks import full_vocabulary_h1_public_lengths as public
from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/public-length-calibration')
SEEDS=(3101,3102)
PROFILES=('fixed-two','fixed-three','mixed-one-two-three')


def codebook(symbols,glyphs,profile,seed):
    rng=random.Random(seed)
    if profile in ('fixed-two','fixed-three'):
        pool=list(product(glyphs,repeat=2 if profile=='fixed-two' else 3))
        rng.shuffle(pool);codes=pool[:len(symbols)]
    elif profile=='mixed-one-two-three':
        roots=list(glyphs);rng.shuffle(roots)
        short=(roots.pop(),)
        pairs=list(product(roots,glyphs));rng.shuffle(pairs)
        medium=pairs[:10]
        long=[p+(g,) for p in pairs[10:] for g in glyphs];rng.shuffle(long)
        codes=[short]+medium+long[:len(symbols)-11]
        rng.shuffle(codes)
    else:raise ValueError('Unknown frozen profile')
    return Encoder({s:(tuple(c),) for s,c in zip(symbols,codes,strict=True)})


def hashes():
    return {str(p):digest(p.read_text()) for p in (Path(__file__),Path(public.__file__),
        Path('src/voynich_smt/solver/length_search.py'),Path('src/voynich_smt/solver/recovery.py'),
        Path('src/voynich_smt/solver/observed_codes.py'),Path('benchmarks/full_vocabulary_h1_lengths.py'),
        Path('benchmarks/frozen_key_holdout.py'))}


def prepare():
    source=json.loads((public.SOURCE/'prepared.json').read_text())
    identity={'source_sha256':digest(source),'code_sha256':hashes()}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return p
    q=HiddenRecoveryRequest.from_dict(source['requests']['full'])
    plain=Text(tuple(tuple(w) for w in source['truth']['plaintext']['words']))
    held_plain=Text(tuple(tuple(w) for w in source['holdout_plaintext']['words']))
    cases=[]
    for profile in PROFILES:
        for seed in SEEDS:
            enc=codebook(q.plaintext_alphabet.symbols,q.ciphertext_alphabet.symbols,profile,seed)
            train=enc.encode(plain,(0,)*plain.size)
            held=enc.encode(held_plain,(0,)*held_plain.size)
            request=replace(q,ciphertext=train)
            truth={'status':'SAT','verified':True,'encoder':asdict(enc),'plaintext':asdict(plain),'choices':[0]*plain.size,'nulls':[]}
            verify(request,truth)
            if enc.decode(held)!=held_plain:raise RuntimeError('Generating continuation failed')
            if set(held.words)&set(train.words) or set(held_plain.words)&set(plain.words):raise RuntimeError('Holdout not novel')
            assert {s for w in held_plain.words for s in w}<={s for w in plain.words for s in w}
            start=perf_counter();vectors=tuple(islice(public.proposals(request),3))
            cases.append({'id':f'{profile}-seed-{seed}','profile':profile,'seed':seed,
                'request':asdict(request),'truth':truth,'holdout':asdict(held),
                'holdout_plaintext':asdict(held_plain),'scheduled_vectors':vectors,
                'schedule_seconds':perf_counter()-start})
    protocol={'identity':identity,'profiles':PROFILES,'seeds':SEEDS,'timeout_ms_per_arm':5000,
        'arms':['ordinary','public-midpoint'],'max_public_branches':3,
        'scope':'New keys, preserved engineered Latin words and full dictionary. Rules/seeds fixed before solves; no retries or outcome-based selection. Both arms use observed domains and H1 L1-3. Public schedules use only requests. Generating truth used only to validate positives and evaluate frozen predictions. Solver budget excludes construction and scheduling. This is prospective key variation, not independent text or manuscript calibration.'}
    p={'identity':identity,'protocol':protocol,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,p)
    return p


def evaluate(case,q,result):
    if result['status']!='SAT':return {'evaluation_status':'NOT_EVALUATED_NO_SAT'}
    enc=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
    held=Text(tuple(tuple(w) for w in case['holdout']['words']))
    prediction=score(held,enc,q.dictionary,q.ciphertext.words)
    exact=sum(w['fully_decoded'] and tuple(w['decoded_prefix'])==tuple(t)
        for w,t in zip(prediction['word_results'],case['holdout_plaintext']['words']))
    return {'evaluation_status':'EVALUATED_FROZEN_KEY','prediction':prediction,'exact_words':exact}


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'arms':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        for arm in p['protocol']['arms']:
            if any(a['case']==case['id'] and a['arm']==arm for a in r['arms']):continue
            print(case['id'],arm,flush=True)
            start=perf_counter()
            if arm=='ordinary':
                result=asdict(recover_observed_codes(q));verify(q,result)
                search=None
                if result['status']=='UNSAT':raise RuntimeError('Known positive returned global UNSAT')
            else:
                search=public.search(q,case['scheduled_vectors'])
                result=search['attempts'][-1]['result'] if search['status']=='SAT' else {'status':'UNKNOWN'}
            row={'case':case['id'],'arm':arm,'request_sha256':digest(asdict(q)),
                'result':result,'search':search,'wall_seconds':perf_counter()-start,
                'solver_seconds':search['solver_seconds'] if search else result['runtime_seconds']}
            row.update(evaluate(case,q,result));r['arms'].append(row);write_json(path,r)
            print(result['status'],f"solver={row['solver_seconds']:.2f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['arms'])==12
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth'])
        assert case['scheduled_vectors']==[list(v) for v in islice(public.proposals(q),3)]
        for row in (a for a in r['arms'] if a['case']==case['id']):
            assert row['request_sha256']==digest(asdict(q))
            if row['search']:
                remaining=5000
                for attempt in row['search']['attempts']:
                    from math import ceil
                    assert attempt['budget_ms']==remaining
                    remaining-=ceil(attempt['result']['runtime_seconds']*1000)
                    verify(q,attempt['result'])
                    if attempt['result']['status']=='SAT':assert list(map(len,attempt['result']['plaintext']['words']))==attempt['word_lengths']
            verify(q,row['result'])
            evaluation=evaluate(case,q,row['result'])
            assert all(digest(row[k])==digest(v) for k,v in evaluation.items())
    write_json(OUT/'validation.json',{'verified':True,'arms':12,'checks':['hashes','public schedules','synthetic witnesses','shared budgets','recovered witnesses','frozen predictions']})
    print('Validated 12 arms')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    if args.validate:validate()
    elif args.run:run()
    else:prepare();print('Prepared six positives and twelve five-second arms')
