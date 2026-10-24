"""Fixed corpus-order training diversity test with known lengths, hidden identities."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path

from benchmarks import public_length_known_lengths as lengths
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text

OUT=Path('experiments/results/training-diversity')
CORPUS=Path('data/processed/caesar-latin-v2.json')
CASE_IDS=('fixed-two-seed-3101','mixed-one-two-three-seed-3101')
SIZES=(18,36)


def select_types(original,held,dictionary,records,count=36):
    selected=list(dict.fromkeys(tuple(w) for w in original))
    excluded=set(map(tuple,held));allowed=set(dictionary.words)
    if set(selected)&excluded:raise ValueError('Training overlaps holdout')
    provenance=[]
    for index,record in enumerate(records):
        if len(selected)>=count:break
        if record['excluded_reason'] is not None:continue
        word=tuple(record['tokens'])
        if word not in allowed or word in excluded or word in selected:continue
        selected.append(word);provenance.append({'record_index':index,'word':word})
    if len(selected)!=count:raise ValueError('Insufficient eligible types; do not broaden')
    return selected,provenance


def prepare():
    source=json.loads((lengths.SOURCE/'prepared.json').read_text())
    baseline=json.loads((lengths.OUT/'report.json').read_text())
    corpus=json.loads(CORPUS.read_text())
    if not baseline['complete']:raise ValueError('Length-only baseline incomplete')
    identity={'source_sha256':digest(source),'baseline_sha256':digest(baseline),'corpus_sha256':digest(corpus),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('benchmarks/full_vocabulary_h1_lengths.py'),Path('benchmarks/public_length_calibration.py'),
             Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return p
    cases=[];reused=[]
    for case_id in CASE_IDS:
        original=next(c for c in source['cases'] if c['id']==case_id)
        q=HiddenRecoveryRequest.from_dict(original['request'])
        types,provenance=select_types(original['truth']['plaintext']['words'],original['holdout_plaintext']['words'],q.dictionary,corpus['records'])
        if len(set(map(tuple,original['truth']['plaintext']['words'])))!=9:raise ValueError('Expected nine-type baseline')
        base=next(c for c in baseline['cases'] if c['id']==case_id)
        if base['request_sha256']!=digest(asdict(q)):raise ValueError('Unmatched baseline')
        reused.append({'case':case_id,'distinct_training_types':9,'result':base})
        enc=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in original['truth']['encoder']['codebook'].items()})
        for n in SIZES:
            plain=Text(tuple(w for w in types[:n] for _ in range(2)))
            train=enc.encode(plain,(0,)*plain.size);request=replace(q,ciphertext=train)
            truth={'status':'SAT','verified':True,'encoder':asdict(enc),'plaintext':asdict(plain),'choices':[0]*plain.size,'nulls':[]}
            verify(request,truth)
            if set(train.words)&set(map(tuple,original['holdout']['words'])):raise ValueError('Ciphertext holdout overlap')
            cases.append({'id':f'{case_id}-types-{n}','source_case':case_id,'distinct_training_types':n,
                'request':asdict(request),'truth':truth,'revealed_lengths':list(map(len,plain.words)),
                'selected_types':types[:n],'added_type_provenance':provenance[:n-9],
                'holdout':original['holdout'],'holdout_plaintext':original['holdout_plaintext']})
    protocol={'identity':identity,'case_ids':CASE_IDS,'sizes':[9,18,36],'new_fits':4,'timeout_ms_per_fit':5000,
        'selection':'Keep original nine types/order, then first new eligible distinct normalized Caesar words in corpus record order; require full-dictionary membership, exclude three held-out types. Repeat each training type twice. No outcome, length or frequency filtering.',
        'scope':'Two existing keys, same full dictionary/heldout/model. Only exact training word lengths revealed, identities hidden. Nested engineered type lists, not intact corpus passages. Nine-type saved fits reused; four new fits, no retries. Solver budget excludes construction. More types also increase total training words and glyphs; cannot isolate diversity from total evidence.'}
    p={'identity':identity,'protocol':protocol,'reused_baselines':reused,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(row['id']==case['id'] for row in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],f"words={len(q.ciphertext.words)}; budget=5000ms",flush=True)
        result=asdict(lengths.solve(tuple(case['revealed_lengths']),q));verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Known positive returned UNSAT')
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result}
        if result['status']=='SAT':
            if list(map(len,result['plaintext']['words']))!=case['revealed_lengths']:raise RuntimeError('Fixed lengths changed')
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
        row.update(evaluate(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.2f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==4
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth'])
        assert len(set(map(tuple,case['truth']['plaintext']['words'])))==case['distinct_training_types']
        assert case['revealed_lengths']==list(map(len,case['truth']['plaintext']['words']))
        assert not set(map(tuple,case['truth']['plaintext']['words']))&set(map(tuple,case['holdout_plaintext']['words']))
        row=next(c for c in r['cases'] if c['id']==case['id']);verify(q,row['result'])
        assert row['request_sha256']==digest(asdict(q))
        if row['result']['status']=='SAT':
            assert list(map(len,row['result']['plaintext']['words']))==case['revealed_lengths']
            assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluate(case,q,row['result']).items())
    corpus=json.loads(CORPUS.read_text());source=json.loads((lengths.SOURCE/'prepared.json').read_text())
    for case_id in CASE_IDS:
        original=next(c for c in source['cases'] if c['id']==case_id);q=HiddenRecoveryRequest.from_dict(original['request'])
        types,provenance=select_types(original['truth']['plaintext']['words'],original['holdout_plaintext']['words'],q.dictionary,corpus['records'])
        for case in (c for c in p['cases'] if c['source_case']==case_id):
            assert digest(case['selected_types'])==digest(types[:case['distinct_training_types']])
            assert digest(case['added_type_provenance'])==digest(provenance[:case['distinct_training_types']-9])
    write_json(OUT/'validation.json',{'verified':True,'new_fits':4,'reused_baselines':2,'checks':['hashes','corpus selection and nesting','synthetic witnesses','holdout disjointness','matched requests','length-constrained witnesses','frozen scoring']})
    print('Validated four new fits and preserved baseline provenance')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared four new fits; two nine-type results reused')
