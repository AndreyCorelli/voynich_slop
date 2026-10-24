"""One additional training-used key, frozen holdout agreement, no truth selection."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
from benchmarks import oov_type_calibration as source
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.oov_type_recovery import _recover

OUT=Path('experiments/results/second-key-agreement')


def exclusion(result):
    used=sorted({s for w in result['plaintext']['words'] for s in w})
    return {'kind':'pin_core','mappings':{s:result['encoder']['codebook'][s] for s in used}}


def solve(q,rule):
    return _recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,q.timeout_ms,
        dictionary=q.dictionary,min_word_length=q.min_word_length,
        max_word_length=q.max_word_length or max(map(len,q.dictionary.words)),
        selection=q.selection,dictionary_encoding=q.dictionary_encoding,codeword_domains='observed',
        key_exclusions=(rule,),max_oov_words=1)


def prepare():
    p=source.prepare();r=json.loads((source.OUT/'report.json').read_text())
    if not r['complete'] or r['prepared_sha256']!=digest(p):raise ValueError('Unmatched source results')
    paths=(Path(__file__),Path(source.__file__),Path('src/voynich_smt/solver/oov_type_recovery.py'),
           Path('benchmarks/l3_conflict.py'),Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))
    identity={'source_sha256':digest(p),'report_sha256':digest(r),'code_sha256':{str(f):digest(f.read_text()) for f in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        frozen=json.loads(path.read_text())
        if frozen['identity']!=identity:raise ValueError('Frozen code/results changed')
        return frozen
    cases=[]
    for case in p['cases']:
        first=next(a for a in r['arms'] if a['case']==case['id'] and a['arm']=='type')
        q=HiddenRecoveryRequest.from_dict(case['request']);source.verify_budget(q,first['result'],'type')
        cases.append(dict(case,first=first,exclusion=exclusion(first['result']) if first['result']['status']=='SAT' else None))
    protocol={'identity':identity,'timeout_ms':5000,'planned_additional_fits':sum(c['exclusion'] is not None for c in cases),
        'selection':'Reuse first type-arm keys from all six positives and six paired shuffles. For each SAT fit, exclude conjunction of its mappings for plaintext symbols used in training; allow unused mappings to vary without counting as distinct. One additional solve per eligible case, no retries. No true plaintext or holdout score enters exclusion or key selection.',
        'scope':'Same one-OOV-type model, dictionary, ciphertext and budget. Second keys independently verified then frozen-scored. Agreement requires both keys fully decode a heldout word identically; truth used afterward to audit correctness. No additional fit when first is non-SAT; preserve UNSAT/UNKNOWN as ineligible. Two-key agreement is not an exhaustive uniqueness proof or statistically calibrated confidence. Correlated engineered examples, not manuscript evidence.'}
    frozen={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,frozen);return frozen


def agreement(case,second_scored):
    first=case['first']['prediction']['word_results'];second=second_scored['prediction']['word_results']
    words=[]
    for i,(a,b) in enumerate(zip(first,second)):
        same=a['fully_decoded'] and b['fully_decoded'] and a['decoded_prefix']==b['decoded_prefix']
        row={'index':i,'both_fully_decoded':a['fully_decoded'] and b['fully_decoded'],'agree':same}
        if case['kind']=='positive':
            truth=tuple(case['holdout_plaintext']['words'][i])
            row.update(first_correct=a['fully_decoded'] and tuple(a['decoded_prefix'])==truth,
                       second_correct=b['fully_decoded'] and tuple(b['decoded_prefix'])==truth,
                       agreement_correct=same and tuple(a['decoded_prefix'])==truth)
        words.append(row)
    return {'word_results':words,'agree_words':sum(w['agree'] for w in words),
            'agree_correct_words':sum(w.get('agreement_correct',False) for w in words) if case['kind']=='positive' else None}


def verify_second(case,q,result):
    source.verify_budget(q,result,'type')
    if result['status']=='SAT':
        assert any(digest(result['encoder']['codebook'][s])!=digest(codes) for s,codes in case['exclusion']['mappings'].items())


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(a['id']==case['id'] for a in r['cases']):continue
        row={'id':case['id'],'first_status':case['first']['result']['status']}
        if case['exclusion'] is None:row['evaluation_status']='NO_FIRST_SAT_KEY'
        else:
            q=HiddenRecoveryRequest.from_dict(case['request']);print(case['id'],'second key timeout=5000ms',flush=True)
            start=perf_counter();result=asdict(solve(q,case['exclusion']));wall=perf_counter()-start;verify_second(case,q,result)
            row.update(result=result,fit_wall_seconds=wall,request_sha256=digest(asdict(q)))
            row.update(source.scoring(case,q,result))
            if result['status']=='SAT':row['agreement']=agreement(case,row)
            print(result['status'],f"solver={result['runtime_seconds']:.3f}s agreement={row.get('agreement',{}).get('agree_words')}",flush=True)
        r['cases'].append(row);write_json(path,r)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==len(p['cases'])
    assert len({a['id'] for a in r['cases']})==len(p['cases'])
    for case in p['cases']:
        row=next(a for a in r['cases'] if a['id']==case['id'])
        assert row['first_status']==case['first']['result']['status']
        if case['exclusion'] is None:assert row['evaluation_status']=='NO_FIRST_SAT_KEY' and 'result' not in row;continue
        assert digest(case['exclusion'])==digest(exclusion(case['first']['result']))
        q=HiddenRecoveryRequest.from_dict(case['request']);assert row['request_sha256']==digest(asdict(q));verify_second(case,q,row['result'])
        scored=source.scoring(case,q,row['result']);assert all(digest(row[k])==digest(v) for k,v in scored.items())
        if row['result']['status']=='SAT':assert digest(row['agreement'])==digest(agreement(case,scored))
        else:assert 'agreement' not in row
    write_json(OUT/'validation.json',{'verified':True,'cases':len(p['cases']),'checks':['source/code identity','training-used exclusion only','distinct verified witnesses','frozen scoring/agreement','non-SAT handling'],'limitation':'Two keys do not exhaust compatible keys; UNSAT solver-reported.'})
    print('Validated second-key agreement')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen second-key exclusions')
