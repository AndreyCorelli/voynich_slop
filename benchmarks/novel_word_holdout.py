"""Fixed word-type-disjoint, fully covered H1/H2 prediction calibration."""
import argparse
from collections import Counter
from dataclasses import asdict,replace
import itertools
import json
from pathlib import Path
import random

from benchmarks.coverage_sequence_selection import alternating_choices
from benchmarks.guided_model_calibration import shortest,expanded,evaluate
from benchmarks.l3_conflict import verify
from benchmarks.frozen_key_holdout import score
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Bounds,Encoder,generate_ciphertext
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import tokenize_dictionary
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

REFERENCE=Path('experiments/results/guided-model-calibration/reference.json')
INVENTORY=Path('experiments/configs/guided-model-calibration.json')
OUT=Path('experiments/results/novel-word-holdout')
KEY_SEED=2121
CHOICE_SEED=2222


def select_types(vocabulary,rules):
    """First lexicographic three-type subset covered by remaining types in both profiles."""
    for held in itertools.combinations(sorted(vocabulary),3):
        training=sorted(set(vocabulary)-set(held))
        if all({s for w in held for s in shortest(w,active)} <=
               {s for w in training for s in shortest(w,active)} for active in ([],rules)):
            return training,list(held)
    raise ValueError('No covered three-type holdout in fixed vocabulary; do not broaden')


def identity():
    paths=[Path(__file__),Path('src/voynich_smt/solver/recovery.py'),
           Path('src/voynich_smt/language/contractions.py'),Path('benchmarks/guided_model_calibration.py')]
    return {str(p):digest(p.read_text()) for p in paths}


def prepare():
    reference=json.loads(REFERENCE.read_text());inventory=json.loads(INVENTORY.read_text());hashes=identity()
    path=OUT/'prepared.json'
    ids={'reference':digest(reference),'inventory':digest(inventory),'code':hashes}
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=ids:raise ValueError('Prepared code/reference/inventory changed')
        return p
    protocol={'identity':ids,'key_seed':KEY_SEED,'choice_seed':CHOICE_SEED,'timeout_ms':5000,'fits_per_arm':1,
        'holdout_type_count':3,'training_repetitions_per_type':2,
        'selection':'First lexicographic three-type subset whose units occur in remaining types under both letter/mixed shortest tokenizations. No solver or prediction criterion.',
        'ordering':'Reference unigram frequency descending, lexical tie break; two copies of each training type, one of each held type.',
        'scope':'Engineered type-disjoint vocabulary fixtures, not corpus passages. Fixed twelve-spelling inventories and contraction rules; held words remain in solver dictionary. H1/H2 generation and recovery cross-test. No statistical guidance or tuning.'}
    write_json(OUT/'protocol.json',protocol)
    cases=[];selections={}
    for language in ('latin','swabian'):
        vocabulary=reference['vocabularies'][language];rules=inventory['rules'][language]
        training,held=select_types(vocabulary,rules)
        counts=reference['models'][language]['unigrams']
        order=lambda w:(-counts.get(w,0),w)
        training=sorted(training,key=order);held=sorted(held,key=order)
        selections[language]={'training_types':training,'heldout_types':held}
        for profile in ('letters','mixed'):
            active=rules if profile=='mixed' else []
            dictionary=WordDictionary(tokenize_dictionary(vocabulary,active))
            alphabet=Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
            ca=Alphabet(tuple('uvwxyz'))
            plain=Text(tuple(shortest(w,active) for w in training for _ in range(2)))
            held_plain=Text(tuple(shortest(w,active) for w in held))
            for h in (1,2):
                codes=list(itertools.product(ca.symbols,repeat=2));random.Random(KEY_SEED).shuffle(codes)
                if h*len(alphabet.symbols)>len(codes):raise ValueError('Fixed code capacity insufficient')
                encoder=Encoder({s:tuple(codes[h*i:h*i+h]) for i,s in enumerate(alphabet.symbols)})
                choices=(0,)*plain.size if h==1 else alternating_choices(plain)
                train=encoder.encode(plain,choices)
                continuation,held_choices=generate_ciphertext(held_plain,encoder,CHOICE_SEED)
                q=HiddenRecoveryRequest(train,alphabet,ca,Bounds('verbose',h,1,3),dictionary,timeout_ms=5000)
                truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
                verify(q,truth)
                seen={tuple(m['code']) for m in used_mappings(truth)}
                if not all(tuple(w[i:i+2]) in seen for w in continuation.words for i in range(0,len(w),2)):raise RuntimeError('Generating-code coverage failure')
                if set(expanded(plain.words,active))&set(expanded(held_plain.words,active)):raise RuntimeError('Word-type overlap')
                if set(train.words)&set(continuation.words):raise RuntimeError('Ciphertext overlap')
                if encoder.decode(continuation)!=held_plain:raise RuntimeError('Generating-key decode failure')
                cases.append({'id':f'{language}-{profile}-H{h}','language':language,'profile':profile,'generating_h':h,
                    'request':asdict(q),'truth':truth,'holdout':asdict(continuation),'holdout_plaintext':asdict(held_plain),
                    'holdout_choices':held_choices,'rules':active,'generating_rules':active,
                    'generating_score':score(continuation,encoder,dictionary,train.words),
                    'heldout_contraction_units':sum(len(s)>1 for w in held_plain.words for s in w)})
    p={'identity':ids,'protocol':protocol,'selections':selections,'cases':cases}
    write_json(path,p);return p


def request_for(case,h):
    base=HiddenRecoveryRequest.from_dict(case['request'])
    return replace(base,bounds=Bounds('verbose',h,1,3))


def run():
    p=prepare();path=OUT/'report.json'
    if path.exists():
        r=json.loads(path.read_text())
        if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    else:r={'prepared_sha256':digest(p),'cases':[],'complete':False}
    for case in p['cases']:
        row=next((x for x in r['cases'] if x['id']==case['id']),None)
        if row is None:
            row={'id':case['id'],'arms':[]};r['cases'].append(row)
        for h in (1,2):
            if any(a['h']==h for a in row['arms']):continue
            q=request_for(case,h);print(case['id'],f'recover H{h}',flush=True)
            result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
                dictionary=q.dictionary,max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed'))
            verify(q,result)
            arm={'h':h,'request_sha256':digest(asdict(q)),'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
            if result['status']=='SAT':
                arm.update(evaluate(result,dict(case,kind='synthetic'),q,case['rules']),evaluation_status='EVALUATED_FROZEN_KEY')
                if arm['prediction']['seen_ciphertext_words']!=0:raise RuntimeError('Prediction is not novel')
            row['arms'].append(arm);write_json(path,r)
            print(result['status'],f"{result['runtime_seconds']:.2f}s",'exact='+str(arm.get('exact_words')),flush=True)
        if row['arms'][0]['result']['status']=='SAT' and row['arms'][1]['result']['status']=='UNSAT':raise RuntimeError('Nested-model contradiction')
    r['complete']=True;write_json(path,r);return r


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');a=parser.parse_args()
    if a.run:run()
    else:
        p=prepare();print('Prepared eight positives with H1/H2 recovery; all held-out types novel and code-covered. Use --run.')
