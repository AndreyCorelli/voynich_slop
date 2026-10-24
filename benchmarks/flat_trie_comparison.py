"""Fixed flat/trie search comparison on the preserved 36-type controls."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks import dictionary_equality_reuse as flat
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/flat-trie-comparison')


def prepare():
    source,baseline,public=flat.prepare()
    saved=json.loads((flat.OUT/'report.json').read_text())
    if not saved['complete'] or saved['prepared_sha256']!=digest(public):raise ValueError('Unmatched flat baseline')
    identity={'source_sha256':digest(source),'flat_prepared_sha256':digest(public),'flat_report_sha256':digest(saved),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('src/voynich_smt/solver/dictionary_encoding.py'),
             Path('src/voynich_smt/language/dictionary.py'),Path('src/voynich_smt/solver/recovery.py'),
             Path('src/voynich_smt/solver/observed_codes.py'),Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return source,p
    cases=[]
    for case in public['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        if q.dictionary_encoding!='flat':raise ValueError('Expected flat source')
        previous=next(c for c in saved['cases'] if c['id']==case['id'])
        if previous['request_sha256']!=digest(asdict(q)):raise ValueError('Unmatched request')
        cases.append({'id':case['id'],'requests':{'flat':asdict(q),'trie':asdict(replace(q,dictionary_encoding='trie'))},'saved_flat':previous})
    protocol={'identity':identity,'case_ids':flat.CASE_IDS,'timeout_ms_per_arm':5000,'new_fits':2,'reused_flat_fits':2,
        'environment':public['protocol']['environment'],
        'semantics':'Only dictionary encoding changes flat to trie; equivalent membership including padding, same hidden words and lengths, full dictionary/alphabets, H1 L1-3, free selection and observed domains. Flat results reused after hash/request checks; one new trie fit each. Construction separate; measured timeout may overshoot. First verified SAT key frozen-scored; UNKNOWN unresolved. No tuning, longer timeout or new fixture selection. If both trie fits remain UNKNOWN, stop this search-encoding sweep and revisit simpler varied-length calibration controls.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return source,p


def run():
    source,p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'arms':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        for encoding in ('flat','trie'):
            if any(a['id']==case['id'] and a['encoding']==encoding for a in r['arms']):continue
            q=HiddenRecoveryRequest.from_dict(case['requests'][encoding])
            original=next(c for c in source['cases'] if c['id']==case['id'])
            if encoding=='flat':row=dict(case['saved_flat'],encoding='flat',reused=True)
            else:
                print(case['id'],'trie; solver timeout=5000ms',flush=True)
                start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start
                verify(q,result)
                if result['status']=='UNSAT':raise RuntimeError('Known positive returned UNSAT')
                row={'id':case['id'],'encoding':encoding,'reused':False,'request_sha256':digest(asdict(q)),
                    'result':result,'fit_wall_seconds':wall,'construction_seconds':result['capacity'].get('construction_seconds')}
                if result['status']=='SAT':row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],original['truth']['plaintext']['words']))
                row.update(evaluate(original,q,result))
                print(result['status'],f"solver={result['runtime_seconds']:.2f}s",f"construction={row['construction_seconds']:.2f}s",f"exact={row.get('exact_words')}",flush=True)
            r['arms'].append(row);write_json(path,r)
    r['complete']=True;write_json(path,r);return r


def validate():
    source,p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['arms'])==4
    for case in p['cases']:
        before=dict(case['requests']['flat']);after=dict(case['requests']['trie'])
        assert before.pop('dictionary_encoding')=='flat' and after.pop('dictionary_encoding')=='trie' and before==after
        for encoding in ('flat','trie'):
            row=next(a for a in r['arms'] if a['id']==case['id'] and a['encoding']==encoding)
            q=HiddenRecoveryRequest.from_dict(case['requests'][encoding]);assert row['request_sha256']==digest(asdict(q))
            original=next(c for c in source['cases'] if c['id']==case['id']);verify(q,original['truth']);verify(q,row['result'])
            assert not row['result']['capacity'].get('oracle_word_lengths',False)
            if encoding=='flat':assert digest(row)==digest(dict(case['saved_flat'],encoding='flat',reused=True))
            else:assert not row['reused']
            if row['result']['status']=='SAT':assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],original['truth']['plaintext']['words']))
            assert all(digest(row[k])==digest(v) for k,v in evaluate(original,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'arms':4,'reused':2,'checks':['code/source hashes','requests differ only in encoding','exact cached flat results','synthetic/recovered witnesses','no oracle lengths','independent frozen scoring']})
    print('Validated four matched encoding arms')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared two trie fits; flat controls reused')
