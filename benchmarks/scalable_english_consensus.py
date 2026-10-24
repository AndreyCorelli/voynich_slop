"""Public-only restart agreement and separately evaluated agreement accuracy."""
from collections import Counter
import gzip
import json
from pathlib import Path

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory


def collect(root,output):
    inference=json.loads((root/'inference.json').read_text())
    protocol=inference['protocol']
    stream=CipherStream.load(root/'public/cipher.json')
    assert stream.identity==protocol['cipher_sha256']
    keys,initial=[],[]
    for run in inference['runs']:
        keys.append(run['joint_archive'][0]['assignments'])
        with gzip.open(root/f"traces/seed-{run['seed']}.jsonl.gz",'rt') as handle:
            first=json.loads(next(handle))
        assert first['kind']=='initial'
        initial.append(first['assignments'])
    rows=[]
    for cipher in range(stream.type_count):
        votes=Counter(key[cipher] for key in keys)
        word,count=min(votes.items(),key=lambda pair:(-pair[1],pair[0]))
        supporters=[i for i,key in enumerate(keys) if key[cipher]==word]
        rows.append({'cipher':cipher,'word_id':word,'votes':count,
                     'strict_majority':count>len(keys)/2 and count>=2,
                     'changed_in_all_supporters':all(initial[i][cipher]!=word for i in supporters)})
    majority=[r['word_id'] for r in rows if r['strict_majority']]
    assert len(set(majority))==len(majority)  # Strict majority of injective keys.
    result={'scope':'public-only restart stability; no freezing or posterior claim',
            'protocol':protocol,'input_inference_sha256':digest(inference),'runs':len(keys),'rows':rows,
            'limitations':['Shared initial keys and source-model bias can create agreement.',
                           'One complete score-selected key per seed; archives are not independent votes.']}
    with output.open('x') as handle: json.dump(result,handle,indent=2); handle.write('\n')
    return result


def evaluate(resources,root,truth_path,output):
    saved=json.loads((root/'consensus-public.json').read_text())
    stream=CipherStream.load(root/'public/cipher.json')
    truth=json.loads(truth_path.read_text())
    assert stream.identity==saved['protocol']['cipher_sha256']==truth['public_sha256']
    counts=Counter(c for doc in stream.documents for c in doc)
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        assert inventory.identity==saved['protocol']['inventory_sha256']
        groups={}
        for label,predicate in (
            ('majority',lambda r:r['strict_majority']),
            ('unanimous',lambda r:saved['runs']>=2 and r['votes']==saved['runs']),
            ('unanimous_changed',lambda r:saved['runs']>=2 and r['votes']==saved['runs'] and r['changed_in_all_supporters']),
            ('unanimous_frequent',lambda r:saved['runs']>=2 and r['votes']==saved['runs'] and counts[r['cipher']]>=100),
            ('majority_changed',lambda r:r['strict_majority'] and r['changed_in_all_supporters']),
            ('majority_unchanged_prior',lambda r:r['strict_majority'] and not r['changed_in_all_supporters'])):
            rows=[r for r in saved['rows'] if predicate(r)]
            correct=[r for r in rows if inventory.word(r['word_id'])==truth['decoding'][r['cipher']]]
            tokens=sum(counts[r['cipher']] for r in rows)
            groups[label]={'types':len(rows),'tokens':tokens,'correct_types':len(correct),
                           'type_precision':len(correct)/len(rows) if rows else None,
                           'token_precision':sum(counts[r['cipher']] for r in correct)/tokens if tokens else None}
        result={'scope':'evaluation-only stability calibration','groups':groups,
                'warning':'Agreement reflects repeated heuristic searches; do not treat it as calibrated confidence.'}
        with output.open('x') as handle: json.dump(result,handle,indent=2); handle.write('\n')
        return result
    finally:
        inventory.close()
