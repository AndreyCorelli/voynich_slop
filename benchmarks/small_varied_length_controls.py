"""Frozen reduced-vocabulary controls with genuinely varied generating code lengths."""
import argparse
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import platform
import random
from time import perf_counter

import z3
from benchmarks.full_vocabulary_h1_known import solve as known_solve
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/small-varied-length-controls')
SOURCE=Path('experiments/results/novel-word-holdout/prepared.json')
SEEDS=(4301,4302)
PROFILES=('fixed-two','mixed-one-two','mixed-one-two-three')


def key(symbols,glyphs,profile,seed):
    rng=random.Random(seed)
    if profile=='fixed-two':
        pool=list(product(glyphs,repeat=2));rng.shuffle(pool);codes=pool[:len(symbols)]
    else:
        roots=list(glyphs);rng.shuffle(roots)
        short=[(g,) for g in roots[:2]]
        pairs=list(product(roots[2:],glyphs));rng.shuffle(pairs)
        if profile=='mixed-one-two':codes=short+pairs[:len(symbols)-2]
        elif profile=='mixed-one-two-three':
            medium=pairs[:6];long=[p+(g,) for p in pairs[6:] for g in glyphs];rng.shuffle(long)
            codes=short+medium+long[:len(symbols)-8]
        else:raise ValueError('Unknown frozen profile')
    rng.shuffle(codes)
    return Encoder({s:(c,) for s,c in zip(symbols,codes,strict=True)})


def prepare():
    original=json.loads(SOURCE.read_text())
    identity={'source_sha256':digest(original),'code_sha256':{str(p):digest(p.read_text()) for p in
        (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/observed_codes.py'),
         Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'),
         Path('benchmarks/full_vocabulary_h1_known.py'),Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen source or code changed')
        return p
    fixture=next(c for c in original['cases'] if c['id']=='latin-letters-H1')
    dictionary=WordDictionary(tuple(tuple(w) for w in fixture['request']['dictionary']['words']))
    alphabet=Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
    glyphs=Alphabet(tuple('uvwxyz'))
    plain=Text(tuple(tuple(w) for w in fixture['truth']['plaintext']['words']))
    held_plain=Text(tuple(tuple(w) for w in fixture['holdout_plaintext']['words']))
    if {s for w in held_plain.words for s in w}-{s for w in plain.words for s in w}:raise ValueError('Uncovered held-out units')
    cases=[]
    for profile in PROFILES:
        for seed in SEEDS:
            encoder=key(alphabet.symbols,glyphs.symbols,profile,seed)
            train=encoder.encode(plain,(0,)*plain.size);held=encoder.encode(held_plain,(0,)*held_plain.size)
            request=HiddenRecoveryRequest(train,alphabet,glyphs,Bounds('verbose',1,1,3),dictionary,timeout_ms=5000)
            truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':[0]*plain.size,'nulls':[]}
            verify(request,truth)
            if set(held_plain.words)&set(plain.words) or set(held.words)&set(train.words):raise ValueError('Holdout not novel')
            if encoder.decode(held)!=held_plain:raise ValueError('Generating holdout failed')
            used_lengths=sorted({len(encoder.codebook[s][0]) for w in plain.words for s in w})
            expected={'fixed-two':[2],'mixed-one-two':[1,2],'mixed-one-two-three':[1,2,3]}[profile]
            if used_lengths!=expected:raise ValueError('Generating lengths not actually varied in training; do not resample')
            cases.append({'id':f'{profile}-seed-{seed}','profile':profile,'seed':seed,'request':asdict(request),
                'truth':truth,'holdout':asdict(held),'holdout_plaintext':asdict(held_plain),
                'generating_training_code_lengths':used_lengths,'all_heldout_codes_seen_in_training':True})
    protocol={'identity':identity,'profiles':PROFILES,'seeds':SEEDS,'arms':['known-words','hidden-words'],
        'timeout_ms_per_arm':5000,'fits_per_arm':1,'total_fits':12,'dictionary_size':len(dictionary.words),
        'alphabet_size':len(alphabet.symbols),'training_types':len(set(plain.words)),'training_words':len(plain.words),'heldout_types':len(set(held_plain.words)),
        'environment':{'python':platform.python_version(),'platform':platform.platform(),'z3':z3.get_version_string()},
        'scope':'Fixed existing twelve-word letter-only Latin inventory, new keys, genuinely varied code lengths with prefix-free tree construction. Prior reduced novel-word controls generated length-two codes only; prior varied-length controls used full vocabulary. All inputs frozen before fits. No words/key/lengths/segmentation/continuation in hidden arm; known arm receives training plaintext only and removes dictionary search. Generating profile hidden in both arms. Same H1 L1-3 and observed domains, equal solver timeout. Engineered toy vocabulary, not natural prose or manuscript calibration. No retries/tuning/extra encodings; first verified key frozen-scored.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'arms':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        plain=Text(tuple(tuple(w) for w in case['truth']['plaintext']['words']))
        for arm in p['protocol']['arms']:
            if any(a['case']==case['id'] and a['arm']==arm for a in r['arms']):continue
            print(case['id'],arm,'timeout=5000ms',flush=True)
            start=perf_counter();result=asdict(known_solve(plain,q) if arm=='known-words' else recover_observed_codes(q));wall=perf_counter()-start
            verify(q,result)
            if result['status']=='UNSAT':raise RuntimeError('Verified synthetic positive returned UNSAT')
            row={'case':case['id'],'arm':arm,'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
            if result['status']=='SAT':
                row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],plain.words))
                if arm=='known-words' and row['training_exact_words']!=len(plain.words):raise RuntimeError('Known words changed')
            row.update(evaluate(case,q,result));r['arms'].append(row);write_json(path,r)
            print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['arms'])==12
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth'])
        held=Text(tuple(tuple(w) for w in case['holdout_plaintext']['words']))
        train=Text(tuple(tuple(w) for w in case['truth']['plaintext']['words']))
        encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in case['truth']['encoder']['codebook'].items()})
        assert encoder.encode(held,(0,)*held.size).words==tuple(tuple(w) for w in case['holdout']['words'])
        assert not set(train.words)&set(held.words)
        assert {s for w in held.words for s in w}<={s for w in train.words for s in w}
        assert case['generating_training_code_lengths']==sorted({len(encoder.codebook[s][0]) for w in train.words for s in w})
        for arm in p['protocol']['arms']:
            row=next(a for a in r['arms'] if a['case']==case['id'] and a['arm']==arm)
            assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
            if row['result']['status']=='SAT':
                assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],train.words))
                if arm=='known-words':assert row['training_exact_words']==len(train.words)
            assert all(digest(row[k])==digest(v) for k,v in evaluate(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'arms':12,'checks':['hashes','synthetic/recovered witnesses','varied generating lengths','novel code-covered holdout','matched requests','known training identities','independent frozen scores']})
    print('Validated twelve small-vocabulary varied-length arms')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared six positives and twelve fixed-budget arms')
