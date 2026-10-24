"""Matched occurrence/type allowances on repeated unknown synthetic words."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter
from benchmarks import small_varied_length_controls as small
from benchmarks import varied_length_vocabulary_ladder as ladder
from benchmarks import varied_length_shuffle_controls as shuffles
from benchmarks.l3_conflict import verify
from benchmarks.public_length_calibration import evaluate
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.oov_recovery import recover_oov
from voynich_smt.solver.oov_type_recovery import recover_oov_types

OUT=Path('experiments/results/oov-type-calibration')


def verify_budget(q,result,arm):
    if result['status']!='SAT':return
    missing=[tuple(w) for w in result['plaintext']['words'] if tuple(w) not in q.dictionary.words]
    if (len(set(missing)) if arm=='type' else len(missing))>1:raise RuntimeError('OOV budget exceeded')
    maximum=q.max_word_length or max(map(len,q.dictionary.words))
    verify(replace(q,dictionary=WordDictionary(q.dictionary.words+tuple(dict.fromkeys(missing))),max_word_length=maximum),result)


def build(fixtures,vocabulary,controls):
    cases=[]
    for original in (c for c in vocabulary['cases'] if c['vocabulary_size']==64):
        fixture=next(c for c in fixtures['cases'] if c['id']==original['source_case'])
        deleted=tuple(fixture['truth']['plaintext']['words'][0])
        occurrences=sum(tuple(w)==deleted for w in fixture['truth']['plaintext']['words'])
        if occurrences!=2:raise ValueError('Expected predetermined missing type repeated twice')
        control=next(c for c in controls['controls'] if c['positive_id']==original['id'] and c['seed']==4401)
        for kind,source in [('positive',dict(original,truth=fixture['truth'],holdout=fixture['holdout'],holdout_plaintext=fixture['holdout_plaintext'])),('shuffle',control)]:
            q=HiddenRecoveryRequest.from_dict(source['request'])
            q=replace(q,dictionary=WordDictionary(tuple(w for w in q.dictionary.words if w!=deleted)))
            if len(q.dictionary.words)!=63:raise ValueError('Deletion failed')
            case=dict(source,id=original['id']+'-'+kind,kind=kind,request=asdict(q),removed_word=deleted,removed_occurrences=occurrences)
            if kind=='positive':verify_budget(q,case['truth'],'type')
            cases.append(case)
    return cases


def prepare():
    fixtures=small.prepare();_,vocabulary=ladder.prepare();controls=shuffles.prepare()
    paths=(Path(__file__),Path('src/voynich_smt/solver/oov_type_recovery.py'),Path('src/voynich_smt/solver/oov_recovery.py'),
           Path('benchmarks/l3_conflict.py'),Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))
    identity={'fixtures_sha256':digest(fixtures),'vocabulary_sha256':digest(vocabulary),'controls_sha256':digest(controls),
              'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources/code changed')
        return p
    cases=build(fixtures,vocabulary,controls)
    protocol={'identity':identity,'planned_fits':24,'arms':['occurrence','type'],'budget':1,'timeout_ms':5000,
        'selection':'Six existing 64-word synthetic positives: three profiles times seeds 4301/4302; existing paired shuffle seed 4401 only, chosen before solving. Delete first training type, et, occurring twice. No replacement: 63 words. Same ciphertext/holdout and five-second budgets. Freeze all cases before solving, no retries.',
        'scope':'Compare one unknown occurrence with one unknown type on identical requests. Type budget supported only for free deterministic H1: prefix-free injective encoding means distinct ciphertext words correspond to distinct plaintext words. Count one membership violation per ciphertext type; check actual plaintext types independently. Occurrence arm excludes original truth by construction but may admit alternative SAT fits; type arm has verified generating witness. First SAT keys frozen-scored. Engineered repeated-word controls, not natural prose. Same profile/text correlations and vocabulary assistance remain; UNKNOWN unresolved, UNSAT solver-reported without proof certificates; no manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def scoring(case,q,result):
    return evaluate(case,q,result) if case['kind']=='positive' else shuffles.prediction(case,q,result)


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'arms':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        for arm in ('occurrence','type'):
            if any(a['case']==case['id'] and a['arm']==arm for a in r['arms']):continue
            print(case['id'],arm,'timeout=5000ms',flush=True)
            start=perf_counter();result=asdict((recover_oov_types if arm=='type' else recover_oov)(q,1));wall=perf_counter()-start
            verify_budget(q,result,arm)
            if arm=='type' and case['kind']=='positive' and result['status']=='UNSAT':raise RuntimeError('Known type-positive UNSAT')
            row={'case':case['id'],'arm':arm,'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
            if result['status']=='SAT':
                missing=[tuple(w) for w in result['plaintext']['words'] if tuple(w) not in q.dictionary.words]
                row.update(oov_occurrences=len(missing),oov_types=len(set(missing)))
                if case['kind']=='positive':row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
            row.update(scoring(case,q,result));r['arms'].append(row);write_json(path,r)
            print(result['status'],f"solver={result['runtime_seconds']:.3f}s exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    fixtures=small.prepare();_,vocabulary=ladder.prepare();controls=shuffles.prepare()
    assert digest(build(fixtures,vocabulary,controls))==digest(p['cases'])
    expected={(c['id'],a) for c in p['cases'] for a in ('occurrence','type')}
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['arms'])==len(expected)
    assert {(a['case'],a['arm']) for a in r['arms']}==expected
    for row in r['arms']:
        case=next(c for c in p['cases'] if c['id']==row['case']);q=HiddenRecoveryRequest.from_dict(case['request'])
        assert row['request_sha256']==digest(asdict(q));verify_budget(q,row['result'],row['arm'])
        if case['kind']=='positive' and row['arm']=='type':assert row['result']['status']!='UNSAT'
        if row['result']['status']=='SAT':
            missing=[tuple(w) for w in row['result']['plaintext']['words'] if tuple(w) not in q.dictionary.words]
            assert row['oov_occurrences']==len(missing) and row['oov_types']==len(set(missing))
            if case['kind']=='positive':assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in scoring(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'arms':len(expected),'checks':['source/code hashes','matched requests/shuffles','predetermined repeated deletion','actual type/occurrence budgets','SAT witnesses','frozen scores'],'limitation':'UNSAT solver-reported; UNKNOWN unresolved.'})
    print('Validated repeated unknown type calibration')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen twelve cases and 24 fits')
