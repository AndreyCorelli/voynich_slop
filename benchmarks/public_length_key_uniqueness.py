"""Truth-assisted held-out mapping uniqueness under known training plaintext."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks import public_length_known_plaintext as known
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

OUT=Path('experiments/results/public-length-key-uniqueness')


def exclusion(case):
    symbols=sorted({s for w in case['holdout_plaintext']['words'] for s in w})
    book=case['truth']['encoder']['codebook']
    if any(len(book[s])!=1 for s in symbols):raise ValueError('H1 mapping diagnostic only')
    return {'kind':'word','segments':[{'symbol':s,'code':book[s][0]} for s in symbols]}


def solve(plain,q,rule):
    if q.bounds.max_homophones!=1:raise ValueError('H1 mapping diagnostic only')
    return _recover(plain,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,
        q.bounds,q.timeout_ms,representation=q.representation,selection=q.selection,
        codeword_domains='observed',key_exclusions=(rule,))


def changed_mappings(result,rule):
    return [s['symbol'] for s in rule['segments']
            if tuple(s['code']) not in [tuple(c) for c in result['encoder']['codebook'][s['symbol']]]]


def prepare():
    p,hidden,oracle_protocol=known.prepare()
    oracle=json.loads((known.OUT/'report.json').read_text())
    if not oracle['complete'] or oracle['protocol_sha256']!=digest(oracle_protocol):raise ValueError('Unmatched oracle baseline')
    identity={'prepared_sha256':digest(p),'hidden_sha256':digest(hidden),'oracle_sha256':digest(oracle),
        'code_sha256':{str(path):digest(path.read_text()) for path in
            (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'protocol.json'
    if path.exists():
        protocol=json.loads(path.read_text())
        if protocol['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return p,oracle,protocol
    for row in oracle['cases']:
        if row['result']['status']!='SAT' or row['exact_words']!=3:raise ValueError('Expected predictive baseline')
    rules={c['id']:exclusion(c) for c in p['cases'] if c['id'] in known.CASE_IDS}
    protocol={'identity':identity,'case_ids':known.CASE_IDS,'timeout_ms_per_fit':5000,'fits_per_case':1,
        'excluded_conjunctions':rules,
        'semantics':'Known training plaintext, unchanged H1 L1-3 model and observed domains. One negated conjunction of all generating symbol/code ownership facts for held-out letters. At least one must differ. No held-out ciphertext or word constraints. Truth-assisted, outcome-selected uniqueness diagnostic. UNSAT certifies these mappings only under the known-word bounded model; SAT is independently checked and frozen-scored; UNKNOWN unresolved.'}
    write_json(path,protocol);return p,oracle,protocol


def run():
    p,oracle,protocol=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'protocol_sha256':digest(protocol),'cases':[],'complete':False}
    if r['protocol_sha256']!=digest(protocol):raise ValueError('Checkpoint changed')
    for case_id in known.CASE_IDS:
        if any(row['id']==case_id for row in r['cases']):continue
        case=next(c for c in p['cases'] if c['id']==case_id)
        q=HiddenRecoveryRequest.from_dict(case['request'])
        plain=Text(tuple(tuple(w) for w in case['truth']['plaintext']['words']))
        rule=protocol['excluded_conjunctions'][case_id]
        verify(q,case['truth'])
        print(case_id,'require changed held-out mapping; budget=5000ms',flush=True)
        result=asdict(solve(plain,q,rule));verify(q,result)
        conclusion={'UNSAT':'HELD_OUT_MAPPINGS_FORCED','SAT':'ALTERNATIVE_HELD_OUT_MAPPING','UNKNOWN':'UNRESOLVED'}[result['status']]
        row={'id':case_id,'request_sha256':digest(asdict(q)),'result':result,'conclusion':conclusion}
        if result['status']=='SAT':
            if tuple(tuple(w) for w in result['plaintext']['words'])!=plain.words:raise RuntimeError('Training words changed')
            changes=changed_mappings(result,rule)
            if not changes:raise RuntimeError('Exclusion violated')
            row['changed_symbols']=changes
        row.update(evaluate(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p,oracle,protocol=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['protocol_sha256']==digest(protocol)
    assert tuple(row['id'] for row in r['cases'])==known.CASE_IDS
    for row in r['cases']:
        case=next(c for c in p['cases'] if c['id']==row['id'])
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth']);verify(q,row['result'])
        assert row['request_sha256']==digest(asdict(q))
        assert protocol['excluded_conjunctions'][row['id']]==exclusion(case)
        assert row['conclusion']=={'UNSAT':'HELD_OUT_MAPPINGS_FORCED','SAT':'ALTERNATIVE_HELD_OUT_MAPPING','UNKNOWN':'UNRESOLVED'}[row['result']['status']]
        if row['result']['status']=='SAT':
            assert row['result']['plaintext']['words']==case['truth']['plaintext']['words']
            assert row['changed_symbols']==changed_mappings(row['result'],exclusion(case)) and row['changed_symbols']
        assert all(digest(row[k])==digest(v) for k,v in evaluate(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'checks':['source and code hashes','baseline SAT witnesses','exclusion scope','alternative SAT witnesses if present','frozen scoring','status interpretation'],
        'limitation':'UNSAT recorded from solver checks; no independently replayed proof certificate.'})
    print('Validated four diagnostic records; UNSAT is solver-reported, not proof-certificate checked')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    if args.validate:validate()
    else:run()
