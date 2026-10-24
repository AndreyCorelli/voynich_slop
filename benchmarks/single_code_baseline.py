"""One-code H1 versus H2, with matched own-model positives and structural controls."""
import argparse
from dataclasses import asdict,replace
import itertools
import json
from pathlib import Path
import random

from benchmarks.structured_negative_controls import generate,diagnostics
from benchmarks.guided_model_calibration import evaluate
from benchmarks.l3_conflict import verify
from benchmarks.frozen_key_holdout import score
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE=Path('experiments/results/structured-negative-controls')
OUT=Path('experiments/results/single-code-baseline')
KEY_SEED=1919
CONTROL_SEED=2020


def encoder_for(alphabet,cipher_alphabet):
    codes=list(itertools.product(cipher_alphabet.symbols,repeat=2))
    random.Random(KEY_SEED).shuffle(codes)
    if len(alphabet.symbols)>len(codes):raise ValueError('Insufficient fixed length-two capacity')
    return Encoder({s:(codes[i],) for i,s in enumerate(alphabet.symbols)})


def request_for(case,h):
    base=HiddenRecoveryRequest.from_dict(case['request'])
    return replace(base,bounds=Bounds('verbose',h,1,3),timeout_ms=5000)


def identity():
    paths=[Path(__file__),Path('src/voynich_smt/solver/recovery.py'),
           Path('benchmarks/structured_negative_controls.py'),Path('benchmarks/guided_model_calibration.py')]
    return {str(p):digest(p.read_text()) for p in paths}


def prepare():
    source=json.loads((SOURCE/'prepared.json').read_text());saved=json.loads((SOURCE/'report.json').read_text())
    if not saved['complete'] or saved['prepared_sha256']!=digest(source):raise ValueError('Mismatched source results')
    solver_path='src/voynich_smt/solver/recovery.py'
    if source['identity'][solver_path]!=digest(Path(solver_path).read_text()):raise ValueError('Cannot reuse results from changed solver')
    hashes=identity();path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=hashes or p['source_sha256']!=digest(source) or p['source_report_sha256']!=digest(saved):raise ValueError('Source/code changed')
        return p
    protocol={'identity':hashes,'source_sha256':digest(source),'source_report_sha256':digest(saved),
        'models':{'H1':'One prefix-free codeword per unit, length 1-3','H2':'One or two prefix-free codewords per unit, length 1-3'},
        'key_seed':KEY_SEED,'control_seed':CONTROL_SEED,'timeout_ms_per_fit':5000,'fits_per_arm':1,
        'scope':'Nested codebook bounds with same alphabet/dictionary/profile per ciphertext. H1 is deterministic variable-length substitution, not length-one monoalphabetic substitution. Four new H1 positives plus fixed pair-chunk controls; existing eleven H2-positive/control cases retained. No vocabulary or contraction changes; no statistical guidance. Historical H2 outcomes reused only under unchanged solver/request.'}
    write_json(OUT/'protocol.json',protocol)
    cases=[];unavailable=[]
    for old in source['cases']:
        case=dict(old,id=old['id']+'-original',generating_h=2)
        row=next(r for r in saved['cases'] if r['id']==old['id'])
        verify(request_for(case,2),row['result'])
        case['cached_h2_result']=row['result'];case['cached_h2_source_id']=old['id']
        cases.append(case)
    for old in source['cases']:
        if old['kind']!='positive':continue
        q=HiddenRecoveryRequest.from_dict(old['request'])
        plain=Text(tuple(tuple(w) for w in old['truth']['plaintext']['words']))
        held_plain=Text(tuple(tuple(w) for w in old['holdout_plaintext']['words']))
        encoder=encoder_for(q.plaintext_alphabet,q.ciphertext_alphabet)
        train=encoder.encode(plain,(0,)*plain.size);held=encoder.encode(held_plain,(0,)*held_plain.size)
        full=Text(train.words+held.words)
        truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':(0,)*plain.size,'nulls':[]}
        known={code for word in plain.words for s in word for code in encoder.codebook[s]}
        if not all(encoder.codebook[s][0] in known for word in held_plain.words for s in word):raise RuntimeError('H1 holdout coverage failure')
        for kind in ['positive','pair-chunks']:
            if kind=='positive':changed=full;metadata={'kind':'positive'}
            else:changed,metadata=generate(full,'pair-chunks',CONTROL_SEED)
            case_id=old['source_id']+'-H1-'+kind
            if changed is None:
                unavailable.append({'id':case_id,'construction':metadata});continue
            request=asdict(q);request['ciphertext']=asdict(Text(changed.words[:len(train.words)]))
            case={'id':case_id,'kind':kind,'generating_h':1,'source_id':old['source_id'],'request':request,
                  'holdout':asdict(Text(changed.words[len(train.words):])),'rules':old['rules'],'construction':metadata}
            if kind=='positive':
                case.update(truth=truth,holdout_plaintext=asdict(held_plain),generating_rules=old['rules'],generating_covered_holdout_words=4)
                verify(request_for(case,1),truth);verify(request_for(case,2),truth)
                assert encoder.decode(held)==held_plain
            cases.append(case)
    p={'protocol':protocol,'identity':hashes,'source_sha256':digest(source),'source_report_sha256':digest(saved),'cases':cases,'unavailable':unavailable}
    write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    if path.exists():
        r=json.loads(path.read_text())
        if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    else:r={'prepared_sha256':digest(p),'cases':[],'unavailable':p['unavailable'],'complete':False}
    for case in p['cases']:
        row=next((x for x in r['cases'] if x['id']==case['id']),None)
        if row is None:
            row={'id':case['id'],'kind':case['kind'],'generating_h':case['generating_h'],'arms':[]};r['cases'].append(row)
        for h in (1,2):
            if any(a['h']==h for a in row['arms']):continue
            q=request_for(case,h)
            if h==2 and 'cached_h2_result' in case:
                result=case['cached_h2_result'];provenance='REUSED_UNCHANGED_REQUEST_AND_SOLVER'
            else:
                print(case['id'],f'H{h}',flush=True)
                result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
                    dictionary=q.dictionary,max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed'))
                print(result['status'],f"{result['runtime_seconds']:.2f}s",flush=True)
                provenance='NEW_FIT'
            verify(q,result)
            arm={'h':h,'request_sha256':digest(asdict(q)),'result':result,'provenance':provenance,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
            if result['status']=='SAT':
                evcase=dict(case,kind='synthetic' if case['kind']=='positive' else 'structural-control')
                arm.update(evaluate(result,evcase,q,case['rules']),evaluation_status='EVALUATED_FROZEN_KEY')
            row['arms'].append(arm);write_json(path,r)
        h1,h2=row['arms']
        if h1['result']['status']=='SAT' and h2['result']['status']=='UNSAT':raise RuntimeError('Nested H1/H2 result contradiction')
    r['complete']=True;write_json(path,r);return r


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');a=parser.parse_args()
    if a.run:run()
    else:
        p=prepare();print(f"Prepared {len(p['cases'])} cases with H1/H2 arms; eleven historical H2 fits reused. Use --run.")
