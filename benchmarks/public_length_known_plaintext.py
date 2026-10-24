"""Training-plaintext oracle diagnostic on four preserved midpoint SAT cases."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks import public_length_calibration as calibration
from benchmarks.full_vocabulary_h1_known import solve
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text

SOURCE=calibration.OUT
OUT=Path('experiments/results/public-length-known-plaintext')
CASE_IDS=('fixed-two-seed-3101','fixed-two-seed-3102',
          'mixed-one-two-three-seed-3101','mixed-one-two-three-seed-3102')


def prepare():
    p=json.loads((SOURCE/'prepared.json').read_text())
    hidden=json.loads((SOURCE/'report.json').read_text())
    if not hidden['complete'] or hidden['prepared_sha256']!=digest(p):raise ValueError('Unmatched hidden results')
    identity={'source_sha256':digest(p),'hidden_report_sha256':digest(hidden),
        'code_sha256':{str(path):digest(path.read_text()) for path in
            (Path(__file__),Path('benchmarks/full_vocabulary_h1_known.py'),
             Path('benchmarks/public_length_calibration.py'),Path('src/voynich_smt/solver/recovery.py'),
             Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'protocol.json'
    if path.exists():
        protocol=json.loads(path.read_text())
        if protocol['identity']!=identity:raise ValueError('Frozen inputs or implementation changed')
        return p,hidden,protocol
    selected=[a['case'] for a in hidden['arms'] if a['arm']=='public-midpoint' and a['result']['status']=='SAT']
    if tuple(selected)!=CASE_IDS:raise ValueError('Expected four preserved successful cases')
    protocol={'identity':identity,'case_ids':CASE_IDS,'timeout_ms_per_fit':5000,'fits_per_case':1,
        'revealed_plaintexts':{c['id']:c['truth']['plaintext'] for c in p['cases'] if c['id'] in CASE_IDS},
        'semantics':'Only training plaintext identities and their inherent token counts revealed. Same ciphertext, alphabets, H1 L1-3, free selection, observed domains and five-second budget. No key, code lengths, segmentation or continuation supplied. Dictionary search removed; original full dictionary retained for verification and frozen scoring. Outcome-selected four cases: diagnostic, not blind hidden recovery or suite-wide estimate.'}
    write_json(path,protocol);return p,hidden,protocol


def run():
    p,hidden,protocol=prepare();path=OUT/'report.json'
    report=json.loads(path.read_text()) if path.exists() else {'protocol_sha256':digest(protocol),'cases':[],'complete':False}
    if report['protocol_sha256']!=digest(protocol):raise ValueError('Checkpoint changed')
    for case_id in CASE_IDS:
        if any(row['id']==case_id for row in report['cases']):continue
        case=next(c for c in p['cases'] if c['id']==case_id)
        q=HiddenRecoveryRequest.from_dict(case['request'])
        plain=Text(tuple(tuple(w) for w in protocol['revealed_plaintexts'][case_id]['words']))
        verify(q,case['truth'])
        print(case_id,'known plaintext; budget=5000ms',flush=True)
        result=asdict(solve(plain,q));verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Verified positive returned UNSAT')
        if result['status']=='SAT' and tuple(tuple(w) for w in result['plaintext']['words'])!=plain.words:raise RuntimeError('Revealed plaintext changed')
        previous=next(a for a in hidden['arms'] if a['case']==case_id and a['arm']=='public-midpoint')
        row={'id':case_id,'request_sha256':digest(asdict(q)),'result':result,
            'hidden_exact_words':previous['exact_words'],'hidden_solver_seconds':previous['solver_seconds']}
        row.update(calibration.evaluate(case,q,result));report['cases'].append(row);write_json(path,report)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"exact={row.get('exact_words')}",flush=True)
    report['complete']=True;write_json(path,report);return report


def validate():
    p,hidden,protocol=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['protocol_sha256']==digest(protocol)
    assert tuple(row['id'] for row in r['cases'])==CASE_IDS
    for row in r['cases']:
        case=next(c for c in p['cases'] if c['id']==row['id'])
        q=HiddenRecoveryRequest.from_dict(case['request'])
        assert row['request_sha256']==digest(asdict(q))
        verify(q,case['truth']);verify(q,row['result'])
        assert protocol['revealed_plaintexts'][row['id']]==case['truth']['plaintext']
        if row['result']['status']=='SAT':assert row['result']['plaintext']['words']==case['truth']['plaintext']['words']
        evaluation=calibration.evaluate(case,q,row['result'])
        assert all(digest(row[k])==digest(value) for k,value in evaluation.items())
        previous=next(a for a in hidden['arms'] if a['case']==row['id'] and a['arm']=='public-midpoint')
        assert row['hidden_exact_words']==previous['exact_words']
        assert row['hidden_solver_seconds']==previous['solver_seconds']
    write_json(OUT/'validation.json',{'verified':True,'cases':4,'checks':['source and code hashes','matched requests','revealed training plaintext','full witnesses','independent frozen predictions','hidden comparisons']})
    print('Validated four matched plaintext-revealed diagnostics')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    if args.validate:validate()
    else:run()
