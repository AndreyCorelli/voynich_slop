"""Fixed local-structure controls against ordinary recovery; no score guidance."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import json
from pathlib import Path
import random

from benchmarks.frozen_key_holdout import score
from benchmarks.german_shuffle_controls import repetition_partition
from benchmarks.guided_model_calibration import request_for, evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE=Path('experiments/results/guided-model-calibration/prepared.json')
OUT=Path('experiments/results/structured-negative-controls')
SEED=1818
MAX_DRAWS=128


def euler_word(word,rng):
    edges=defaultdict(list)
    for a,b in zip(word,word[1:]):edges[a].append(b)
    for targets in edges.values():rng.shuffle(targets)
    stack=[word[0]];reverse=[]
    while stack:
        if edges[stack[-1]]:stack.append(edges[stack[-1]].pop())
        else:reverse.append(stack.pop())
    return tuple(reversed(reverse))


def chunk_word(word,rng):
    if len(word)%2:raise ValueError('Pair-chunk controls require even word lengths')
    chunks=[word[i:i+2] for i in range(0,len(word),2)];rng.shuffle(chunks)
    return tuple(s for chunk in chunks for s in chunk)


def diagnostics(original,changed):
    return {'word_length_sequence_preserved':tuple(map(len,original.words))==tuple(map(len,changed.words)),
        'glyph_counts_per_word_preserved':all(Counter(a)==Counter(b) for a,b in zip(original.words,changed.words)),
        'exact_repetition_partition_preserved':repetition_partition(original)==repetition_partition(changed),
        'overlapping_bigram_counts_per_word_preserved':all(Counter(zip(a,a[1:]))==Counter(zip(b,b[1:])) for a,b in zip(original.words,changed.words)),
        'endpoints_per_word_preserved':all((a[0],a[-1])==(b[0],b[-1]) for a,b in zip(original.words,changed.words)),
        'aligned_pair_counts_per_word_preserved':all(Counter(a[i:i+2] for i in range(0,len(a),2))==Counter(b[i:i+2] for i in range(0,len(b),2)) for a,b in zip(original.words,changed.words)),
        'changed_word_occurrences':sum(a!=b for a,b in zip(original.words,changed.words)),
        'changed_distinct_types':len({a for a,b in zip(original.words,changed.words) if a!=b}),
        'total_distinct_types':len(set(original.words))}


def generate(text,kind,seed=SEED):
    if kind not in {'pair-chunks','bigrams'}:raise ValueError('Unknown structural control')
    rng=random.Random(seed);types=list(dict.fromkeys(text.words))
    for draw in range(MAX_DRAWS):
        transform=chunk_word if kind=='pair-chunks' else euler_word
        mapping={w:transform(w,rng) for w in types}
        if len(set(mapping.values()))!=len(types):continue
        changed=Text(tuple(mapping[w] for w in text.words))
        if changed==text:continue
        audit=diagnostics(text,changed)
        required=['word_length_sequence_preserved','glyph_counts_per_word_preserved','exact_repetition_partition_preserved']
        required+=['aligned_pair_counts_per_word_preserved'] if kind=='pair-chunks' else ['overlapping_bigram_counts_per_word_preserved','endpoints_per_word_preserved']
        if not all(audit[k] for k in required):raise RuntimeError('Structural invariant failed')
        return changed,{'kind':kind,'seed':seed,'accepted_draw':draw,'max_draws':MAX_DRAWS,**audit}
    return None,{'kind':kind,'seed':seed,'max_draws':MAX_DRAWS,
        'status':'UNAVAILABLE_NO_CHANGED_COLLISION_FREE_DRAW','scope':'Bounded construction failure, not proof no alternative exists.'}


def identity():
    paths=[Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/guided_model_calibration.py'),
           Path('benchmarks/frozen_key_holdout.py')]
    return {str(p):digest(p.read_text()) for p in paths}


def prepare():
    source=json.loads(SOURCE.read_text());hashes=identity();path=OUT/'prepared.json'
    if path.exists():
        saved=json.loads(path.read_text())
        if saved['source_sha256']!=digest(source) or saved['identity']!=hashes:raise ValueError('Prepared code/source changed')
        return saved
    protocol={'source_sha256':digest(source),'identity':hashes,'seed':SEED,'max_draws':MAX_DRAWS,
        'control_kinds':['pair-chunks','bigrams'],'timeout_ms':5000,'fits_per_case':1,
        'recovery':'Ordinary observed-domain finite dictionary recovery under generation profile; no key enumeration or language objective.',
        'scope':'Local structural corruptions of saved synthetic fixtures, not guaranteed model-impossible negatives. No selection by generating-key compatibility, solver result or continuation score. Paired positive replay with same budget; unavailable controls preserved.'}
    write_json(OUT/'protocol.json',protocol)
    cases=[];unavailable=[]
    for source_case in source['cases']:
        if source_case['kind']!='synthetic':continue
        q,rules=request_for(source_case,source_case['generation_profile'],source)
        verify(q,source_case['truth'])
        full=Text(q.ciphertext.words+tuple(tuple(w) for w in source_case['holdout']['words']))
        for kind in ['positive','pair-chunks','bigrams']:
            if kind=='positive':changed=full;metadata={'kind':'positive'}
            else:changed,metadata=generate(full,kind)
            case_id=source_case['id']+'-'+kind
            if changed is None:
                unavailable.append({'id':case_id,'construction':metadata});continue
            train=Text(changed.words[:len(q.ciphertext.words)]);held=Text(changed.words[len(q.ciphertext.words):])
            request=asdict(q);request['ciphertext']=asdict(train)
            case={'id':case_id,'source_id':source_case['id'],'kind':kind,'request':request,
                  'holdout':asdict(held),'rules':rules,'construction':metadata}
            # Truth is diagnostic only; controls are not selected/rejected by this evaluation.
            book=source_case['truth']['encoder']['codebook']
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in book.items()})
            known=score(changed,encoder,q.dictionary)
            case['generating_key_audit']={'fully_decoded_words':known['fully_decoded_words'],
                'dictionary_words':known['dictionary_words'],'word_count':len(changed.words),
                'dictionary_compatible_under_generating_key':known['dictionary_words']==len(changed.words)}
            if kind=='positive':case.update(truth=source_case['truth'],holdout_plaintext=source_case['holdout_plaintext'],generating_rules=rules)
            cases.append(case)
    prepared={'protocol':protocol,'identity':hashes,'source_sha256':digest(source),'cases':cases,'unavailable':unavailable}
    write_json(path,prepared);return prepared


def run():
    prepared=prepare();path=OUT/'report.json'
    if path.exists():
        report=json.loads(path.read_text())
        if report['prepared_sha256']!=digest(prepared):raise ValueError('Checkpoint changed')
    else:report={'prepared_sha256':digest(prepared),'cases':[],'unavailable':prepared['unavailable'],'complete':False}
    from voynich_smt.experiments.hidden import HiddenRecoveryRequest
    for case in prepared['cases']:
        if any(r['id']==case['id'] for r in report['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],flush=True)
        result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
            dictionary=q.dictionary,max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed'))
        verify(q,result)
        row={'id':case['id'],'kind':case['kind'],'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
        if result['status']=='SAT':
            evaluation_case=dict(case,kind='synthetic' if case['kind']=='positive' else 'structural-control')
            row.update(evaluate(result,evaluation_case,q,case['rules']),evaluation_status='EVALUATED_FROZEN_KEY')
        report['cases'].append(row);write_json(path,report)
        print(result['status'],f"{result['runtime_seconds']:.2f}s",flush=True)
    report['complete']=True;write_json(path,report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if args.run:run()
    else:
        p=prepare();print(f"Prepared {len(p['cases'])} cases; {len(p['unavailable'])} controls unavailable. Use --run.")
