"""Single covered-positive test of training score inside shared-key search."""
from dataclasses import asdict, replace
import json
import math
from pathlib import Path

from benchmarks.corpus_sequence_selection import sequence_score
from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE=Path('experiments/results/coverage-sequence-selection/prepared.json')
OUT=Path('experiments/results/feasible-sequence-search')


def weights(dictionary, model):
    """Frozen add-one log probabilities, rounded to integer thousandths."""
    v=len(model['vocabulary']);alpha=model['alpha']
    pairs={(a,b):n for a,b,n in model['pairs']}
    initial={w:round(1000*math.log((model['unigrams'].get(''.join(w),0)+alpha)/(model['tokens']+alpha*v)))
             for w in dictionary.words}
    transitions={(a,b):round(1000*math.log((pairs.get((''.join(a),''.join(b)),0)+alpha)/
                 (model['outgoing'].get(''.join(a),0)+alpha*v))) for a in dictionary.words for b in dictionary.words}
    return {'initial':initial,'transitions':transitions,'max_checks':3}


def integer_score(words,spec):
    words=tuple(tuple(w) for w in words)
    return spec['initial'][words[0]]+sum(spec['transitions'][a,b] for a,b in zip(words,words[1:]))


def run():
    if (OUT/'protocol.json').exists():raise ValueError('Fixed test already started; preserve output')
    saved=json.loads(SOURCE.read_text());case=next(c for c in saved['cases'] if c['id']=='block-2-synthetic')
    q=replace(HiddenRecoveryRequest.from_dict(case['request']),timeout_ms=5000)
    spec=weights(q.dictionary,saved['model'])
    protocol={'source_sha256':digest(saved),'case_id':case['id'],'request_sha256':digest(asdict(q)),
        'timeout_ms_per_arm':5000,'maximum_checks_per_arm':3,'weight_scale':1000,
        'model_sha256':digest(saved['model']),
        'initial_weights':[[w,s] for w,s in spec['initial'].items()],
        'transition_weights':[[a,b,s] for (a,b),s in spec['transitions'].items()],
        'semantics':'Saved covered positive, retrospective development diagnostic. Shared-key feasible score improvements versus ordinary ownership enumeration. Same five-second solver ceilings; construction separately recorded. No continuation-based tuning, seed changes or larger budgets. Integer objective versus original score has rounding differences.',
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/language_objective.py'))}}
    write_json(OUT/'protocol.json',protocol)
    verify(q,case['truth'])
    report={'protocol':protocol,'arms':[],'complete':False}
    # Freeze both arms' candidates and selections before continuation evaluation.
    exclusions=[];baseline=[];attempts=[];remaining=5000
    for _ in range(3):
        if remaining<=0:break
        result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,
            remaining,dictionary=q.dictionary,max_word_length=3,codeword_domains='observed',key_exclusions=tuple(exclusions)))
        verify(q,result);attempts.append(result)
        remaining-=max(1,int(result['runtime_seconds']*1000+0.999))
        if result['status']!='SAT':break
        baseline.append({'result':result,'training_score':sequence_score(result['plaintext']['words'],saved['model']),
                         'integer_score':integer_score(result['plaintext']['words'],spec)})
        exclusions.append({'kind':'word','segments':used_mappings(result)})
    index=max(range(len(baseline)),key=lambda i:baseline[i]['training_score']) if baseline else None
    report['arms'].append({'id':'ordinary','attempts':attempts,'fits':baseline,'selected_index':index})
    write_json(OUT/'report.json',report)
    result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
        dictionary=q.dictionary,max_word_length=3,codeword_domains='observed',language_objective=spec))
    verify(q,result)
    feasible=[]
    if result['status']=='SAT':
        value=integer_score(result['plaintext']['words'],spec)
        if value!=result['capacity']['language_objective']['score']:raise RuntimeError('Objective verification failed')
        feasible.append({'result':result,'training_score':sequence_score(result['plaintext']['words'],saved['model']),
                         'integer_score':value})
    report['arms'].append({'id':'feasible-guided','attempts':[result],'fits':feasible,
                          'selected_index':0 if feasible else None})
    held=Text(tuple(tuple(w) for w in case['holdout']['words']))
    for arm in report['arms']:
        for fit in arm['fits']:
            book=fit['result']['encoder']['codebook']
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in book.items()})
            prediction=score(held,encoder,q.dictionary,q.ciphertext.words)
            exact=[r['fully_decoded'] and tuple(r['decoded_prefix'])==tuple(w)
                for r,w in zip(prediction['word_results'],case['holdout_plaintext']['words'])]
            fit.update(prediction=prediction,exact_words=sum(exact),
                       novel_exact_words=sum(ok and not r['seen_in_training'] for ok,r in zip(exact,prediction['word_results'])))
        chosen=arm['fits'][arm['selected_index']] if arm['selected_index'] is not None else None
        print(arm['id'], 'exact='+str(chosen['exact_words'])+'/4' if chosen else 'NO SAT',flush=True)
    report['complete']=True;write_json(OUT/'report.json',report);return report


if __name__=='__main__':run()
