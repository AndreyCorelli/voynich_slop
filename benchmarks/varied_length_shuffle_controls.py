"""Paired typewise glyph shuffles for the six tractable 64-word positives."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks import varied_length_vocabulary_ladder as ladder
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.structured_negative_controls import diagnostics
from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/varied-length-shuffle-controls')
SEEDS=(4401,4402)
REQUIRED=('word_length_sequence_preserved','glyph_counts_per_word_preserved','exact_repetition_partition_preserved')


def prepare():
    original,source=ladder.prepare();baseline=json.loads((ladder.OUT/'report.json').read_text())
    if not baseline['complete'] or baseline['prepared_sha256']!=digest(source):raise ValueError('Unmatched positive baseline')
    identity={'source_sha256':digest(source),'baseline_sha256':digest(baseline),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('benchmarks/german_shuffle_controls.py'),Path('benchmarks/structured_negative_controls.py'),
             Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/observed_codes.py'),
             Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return p
    positives=[];controls=[];unavailable=[]
    for case in (c for c in source['cases'] if c['vocabulary_size']==64):
        q=HiddenRecoveryRequest.from_dict(case['request'])
        positive=next(c for c in baseline['cases'] if c['id']==case['id'])
        if positive['request_sha256']!=digest(asdict(q)) or positive['result']['status']!='SAT':raise ValueError('Expected matched verified SAT')
        verify(q,positive['result'])
        fixture=next(c for c in original['cases'] if c['id']==case['source_case'])
        held=Text(tuple(tuple(w) for w in fixture['holdout']['words']))
        full=Text(q.ciphertext.words+held.words)
        positives.append({'id':case['id'],'request':asdict(q),'saved_result':positive,'holdout':asdict(held)})
        for seed in SEEDS:
            case_id=f"{case['id']}-shuffle-{seed}"
            try:changed,generation=typewise_shuffle(full,seed)
            except ValueError as error:
                if str(error)!='Unable to generate a changed collision-free word-type shuffle':raise
                unavailable.append({'id':case_id,'seed':seed,'status':'UNAVAILABLE_AFTER_1000_DRAWS'});continue
            audit=diagnostics(full,changed)
            if not all(audit[k] for k in REQUIRED) or not audit['changed_word_occurrences']:raise RuntimeError('Control invariants failed')
            train=Text(changed.words[:len(q.ciphertext.words)]);continuation=Text(changed.words[len(q.ciphertext.words):])
            if set(train.words)&set(continuation.words):raise RuntimeError('Control holdout no longer novel')
            if train==q.ciphertext:raise RuntimeError('Only held-out words changed; do not silently accept unchanged training')
            controls.append({'id':case_id,'positive_id':case['id'],'seed':seed,'request':asdict(replace(q,ciphertext=train)),
                'holdout':asdict(continuation),'construction':generation,'invariants':audit})
    protocol={'identity':identity,'control_seeds':SEEDS,'max_draws':1000,'timeout_ms_per_fit':5000,
        'reused_positives':6,'planned_controls':12,'selection':'Existing typewise within-word glyph shuffle on concatenated train/holdout. Same shuffled spelling for each repeated type; reject collisions and fully unchanged draws only. No solver, generating-key or holdout score used in selection. Training must change; failure stops rather than selecting by solve.',
        'scope':'Six fixed 64-word positives, same alphabets/H1 L1-3/budgets/model. Controls preserve per-word lengths/glyph counts and full repetition partition. Construction sees held-out ciphertext solely to preserve novelty; solver receives training request only. No known plaintext/code lengths. Controls not guaranteed model-impossible: SAT means dictionary compatibility. Score control continuation with frozen SAT key but no generating-plaintext accuracy claim. No language/manuscript inference, p-values, independence claim or extra seed tuning.'}
    p={'identity':identity,'protocol':protocol,'positives':positives,'controls':controls,'unavailable':unavailable}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def prediction(case,q,result):
    if result['status']!='SAT':return {'evaluation_status':'NOT_EVALUATED_NO_SAT'}
    enc=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
    held=Text(tuple(tuple(w) for w in case['holdout']['words']))
    result_score=score(held,enc,q.dictionary,q.ciphertext.words)
    if result_score['seen_ciphertext_words']!=0:raise RuntimeError('Control continuation repeats training')
    return {'evaluation_status':'EVALUATED_FROZEN_KEY','prediction':result_score}


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'controls':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['controls']:
        if any(c['id']==case['id'] for c in r['controls']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],'timeout=5000ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start;verify(q,result)
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        row.update(prediction(case,q,result));r['controls'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"holdout_dictionary={row.get('prediction',{}).get('dictionary_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['controls'])==len(p['controls'])
    for case in p['controls']:
        positive=next(c for c in p['positives'] if c['id']==case['positive_id'])
        q=HiddenRecoveryRequest.from_dict(case['request']);base=HiddenRecoveryRequest.from_dict(positive['request'])
        before=dict(positive['request']);after=dict(case['request']);before.pop('ciphertext');after.pop('ciphertext');assert before==after
        full=Text(base.ciphertext.words+tuple(tuple(w) for w in positive['holdout']['words']))
        changed,generation=typewise_shuffle(full,case['seed'])
        assert digest(generation)==digest(case['construction']) and digest(diagnostics(full,changed))==digest(case['invariants'])
        assert all(case['invariants'][k] for k in REQUIRED)
        assert changed.words==q.ciphertext.words+tuple(tuple(w) for w in case['holdout']['words'])
        row=next(c for c in r['controls'] if c['id']==case['id']);assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
        assert all(digest(row[k])==digest(v) for k,v in prediction(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'controls':len(r['controls']),'reused_positives':6,'checks':['code/source hashes','ciphertext-only request changes','seeded regeneration','structural invariants','recovered witnesses','novel frozen holdout scoring'], 'limitation':'UNSAT is solver-reported, without independent proof certificates; randomized controls are not guaranteed impossible.'})
    print('Validated paired randomized controls')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared paired shuffles; use --run')
