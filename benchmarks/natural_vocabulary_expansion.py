"""Dictionary-only 64 to 256 expansion on frozen natural replication cases."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks import natural_passage_replication as baseline
from benchmarks.varied_length_vocabulary_ladder import vocabularies
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/natural-vocabulary-expansion')
SIZE=256


def build(source, previous, records):
    if not previous['complete'] or previous['prepared_sha256']!=digest(source):
        raise ValueError('Unmatched completed baseline')
    dictionaries={};provenance={}
    for passage_id, passage in source['passages'].items():
        base=WordDictionary(tuple(tuple(w) for w in passage['dictionary']['words']))
        alphabet=Alphabet(tuple(passage['alphabet']['symbols']))
        ds, added=vocabularies(base,alphabet,records[passage['language']],(SIZE,))
        dictionaries[passage_id]=asdict(ds[SIZE]);provenance[passage_id]=added
    cases=[]
    for original in source['cases']:
        passage_id=original['id'].split('-fixed-two')[0].split('-mixed-one-two-three')[0]
        q=HiddenRecoveryRequest.from_dict(original['request'])
        q=replace(q,dictionary=WordDictionary(tuple(tuple(w) for w in dictionaries[passage_id]['words'])))
        old=next(a for a in previous['arms'] if a['case']==original['id'] and a['arm']=='hidden-words')
        if old['request_sha256']!=digest(original['request']):raise ValueError('Unmatched baseline request')
        case=dict(original,request=asdict(q),previous_64=old,passage_id=passage_id)
        if case['kind']=='positive':verify(q,case['truth'])
        cases.append(case)
    return dictionaries,provenance,cases


def prepare():
    source=baseline.prepare();previous=json.loads((baseline.OUT/'report.json').read_text())
    records,_,sources=baseline.load_sources()
    paths=(Path(__file__),Path(baseline.__file__),Path('benchmarks/varied_length_vocabulary_ladder.py'),
           Path('benchmarks/l3_conflict.py'),Path('src/voynich_smt/solver/recovery.py'),
           Path('src/voynich_smt/solver/observed_codes.py'),Path('src/voynich_smt/solver/dictionary_encoding.py'),
           Path('src/voynich_smt/language/dictionary.py'),Path('benchmarks/frozen_key_holdout.py'),
           Path('benchmarks/public_length_calibration.py'))
    identity={'source_sha256':digest(source),'baseline_report_sha256':digest(previous),'sources':sources,
              'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or implementation changed')
        return p
    dictionaries,provenance,cases=build(source,previous,records)
    protocol={'identity':identity,'planned_fits':len(cases),'dictionary_size':SIZE,'timeout_ms_per_fit':5000,
        'selection':'Retain each frozen 64-word dictionary in order; append first distinct eligible corpus words under the same passage alphabet to 256. No new passages, seeds, shuffles, solver-based selection or retries.',
        'scope':'Eight hidden positives and eight paired hidden shuffles from the four natural replication passages. Only dictionary changes. Ciphertexts, held-out text, alphabets, bounds, free selection, flat encoding and five-second solver timeout unchanged. Reuse completed 64-word hidden rows; no new known-word fits, whose solver inputs do not depend on the dictionary. Assisted vocabulary retains true training and held-out words. First SAT key frozen-scored; positive exact/novel exact and control dictionary compatibility reported separately. UNKNOWN unscored; UNSAT solver-reported without independent proof certificates. Same-source/profile cases correlated; no language inference or population false-fit rate.'}
    p={'identity':identity,'protocol':protocol,'dictionaries':dictionaries,'added_word_provenance':provenance,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def evaluation(case,q,result):
    return baseline.evaluate_positive(case,q,result) if case['kind']=='positive' else baseline.control_prediction(case,q,result)


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(row['id']==case['id'] for row in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],'vocab=256 timeout=5000ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start;verify(q,result)
        if case['kind']=='positive' and result['status']=='UNSAT':raise RuntimeError('Verified generating positive returned UNSAT')
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        if case['kind']=='positive' and result['status']=='SAT':
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
        row.update(evaluation(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    source=baseline.prepare();previous=json.loads((baseline.OUT/'report.json').read_text());records,_,_=baseline.load_sources()
    dictionaries,provenance,cases=build(source,previous,records)
    assert digest(dictionaries)==digest(p['dictionaries']) and digest(provenance)==digest(p['added_word_provenance'])
    assert digest(cases)==digest(p['cases'])
    assert r['complete'] and r['prepared_sha256']==digest(p)
    assert len(r['cases'])==len(cases) and len({row['id'] for row in r['cases']})==len(cases)
    for case, original in zip(cases,source['cases']):
        before=dict(original['request']);after=dict(case['request']);before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after) and case['holdout']==original['holdout']
        old_words=original['request']['dictionary']['words'];new_words=case['request']['dictionary']['words']
        assert digest(new_words[:64])==digest(old_words) and len(new_words)==SIZE
        q=HiddenRecoveryRequest.from_dict(case['request']);row=next(a for a in r['cases'] if a['id']==case['id'])
        assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
        if case['kind']=='positive':
            verify(q,case['truth']);assert row['result']['status']!='UNSAT'
            if row['result']['status']=='SAT':
                assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluation(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(cases),'checks':['source/code hashes','dictionary reconstruction and nesting','dictionary-only changes','matched 64-word results','generating and recovered witnesses','frozen scores'], 'limitation':'UNKNOWN unresolved; UNSAT has no independent proof certificate.'})
    print('Validated natural dictionary expansion')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen sixteen dictionary-only expansion inputs')
