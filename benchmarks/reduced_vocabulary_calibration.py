"""Fixed nested truth-assisted vocabulary diagnostic; no Voynich solves."""
import argparse
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import random

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

ROOT=Path('experiments/results/predictive-calibration')
CONFIG=Path('experiments/configs/reduced-vocabulary-calibration.json')


def nested_vocabularies(full_words,required_words,sizes,seed):
    full=set(full_words);required=set(required_words)
    if not required<=full:raise ValueError('Required words outside full vocabulary')
    if sizes!=sorted(set(sizes)) or any(type(n)is not int or not len(required)<=n<=len(full) for n in sizes):
        raise ValueError('Invalid vocabulary ladder sizes')
    distractors=sorted(full-required);random.Random(seed).shuffle(distractors)
    return {n:WordDictionary(tuple(sorted(required|set(distractors[:n-len(required)])))) for n in sizes}


def codeword_coverage(truth,training_size):
    choices=iter(truth['choices']);book=truth['encoder']['codebook']
    codes=[[tuple(book[s][next(choices)]) for s in word] for word in truth['plaintext']['words']]
    seen={c for word in codes[:training_size] for c in word}
    return [all(c in seen for c in word) for word in codes[30:]]


def run(resume=False):
    config=json.loads(CONFIG.read_text());manifest=json.loads((ROOT/'prepared.json').read_text())
    entry=next(e for e in manifest['cases'] if e['id']=='latin-synthetic')
    payload=json.loads(Path(entry['public_input']).read_text());truth=json.loads(Path(entry['truth_path']).read_text())
    hold=json.loads(Path(entry['holdout']).read_text())
    for value,key in ((payload,'input_sha256'),(truth,'truth_sha256'),(hold,'holdout_sha256')):
        if digest(value)!=entry[key]:raise ValueError('Saved source changed')
    base=HiddenRecoveryRequest.from_dict(payload['request']);required=tuple(map(tuple,truth['plaintext']['words']))
    vocabularies=nested_vocabularies(base.dictionary.words,required,config['vocabulary_sizes'],config['distractor_seed'])
    continuation=Text(tuple(map(tuple,hold['ciphertext']['words'])))
    identity={'config_sha256':digest(config),'manifest_sha256':digest(manifest),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report={'identity':identity,'config':config,'required_distinct_words':len(set(required)),
        'vocabularies':{str(n):{'words':d.words,'sha256':digest(asdict(d))} for n,d in vocabularies.items()},
        'experiments':[],'complete':False}
    output=ROOT/'reduced-vocabulary-10000ms.json'
    if output.exists():
        if not resume:raise ValueError('Existing checkpoint: use --resume')
        cached=json.loads(output.read_text())
        if cached['identity']!=identity:raise ValueError('Resume source/config/code changed')
        report['experiments']=cached['experiments']
    for size in config['training_sizes']:
        covered=codeword_coverage(truth,size)
        for n,dictionary in vocabularies.items():
            name=f'words-{size}-vocabulary-{n}'
            q=replace(base,ciphertext=Text(base.ciphertext.words[:size]),dictionary=dictionary,timeout_ms=config['timeout_ms'])
            known=Text(tuple(map(tuple,truth['plaintext']['words'][:size])))
            verify(q,{'status':'SAT','verified':True,'encoder':truth['encoder'],'plaintext':asdict(known),
                      'choices':truth['choices'][:known.size],'nulls':[]})
            cached=[e for e in report['experiments'] if e['id']==name]
            if cached:
                if len(cached)!=1 or cached[0]['request_sha256']!=digest(asdict(q)):raise ValueError('Cached request mismatch')
                verify(q,cached[0]['result']);continue
            print(f'{name}: budget={q.timeout_ms}ms',flush=True)
            result=asdict(recover_observed_codes(q));verify(q,result)
            row={'id':name,'training_words':size,'vocabulary_size':n,'request_sha256':digest(asdict(q)),
                'result':result,'generating_codeword_covered_holdout_words':sum(covered),
                'evaluation_status':'NOT_EVALUATED_NO_SAT'}
            if result['status']=='SAT':
                encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
                prediction=score(continuation,encoder,base.dictionary,q.ciphertext.words)
                exact=[w['fully_decoded'] and tuple(w['decoded_prefix'])==expected for w,expected in zip(prediction['word_results'],required[30:])]
                row.update(holdout_score_full_dictionary=prediction,
                    holdout_score_reduced_dictionary=score(continuation,encoder,dictionary,q.ciphertext.words),
                    exact_generating_words=sum(exact),exact_words_with_seen_generating_codewords=sum(x and c for x,c in zip(exact,covered)),
                    evaluation_status='EVALUATED_FROZEN_KEY')
            report['experiments'].append(row);write_json(output,report)
            print(result['status'],f"solver={result['runtime_seconds']:.2f}s",flush=True)
            if result['status']=='UNSAT':raise RuntimeError('Known-solvable reduced case incorrectly UNSAT')
    report['complete']=True;write_json(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--resume',action='store_true')
    run(parser.parse_args().resume)
