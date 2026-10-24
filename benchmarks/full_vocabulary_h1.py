"""Matched reduced/full Latin dictionary H1 control with novel, code-covered words."""
import argparse
from dataclasses import asdict,replace
import itertools
import json
from pathlib import Path

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

FIXTURE=Path('experiments/results/novel-word-holdout/prepared.json')
FULL=Path('data/generated/clean-latin-voynich/inputs/words-23.json')
OUT=Path('experiments/results/full-vocabulary-h1')


def identity():
    return {str(p):digest(p.read_text()) for p in
        (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/frozen_key_holdout.py'))}


def prepare():
    fixture=json.loads(FIXTURE.read_text());full=json.loads(FULL.read_text());hashes=identity()
    ids={'fixture':digest(fixture),'full_template':digest(full),'code':hashes};path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=ids:raise ValueError('Prepared source/code changed')
        return p
    source=next(c for c in fixture['cases'] if c['id']=='latin-letters-H1')
    small=HiddenRecoveryRequest.from_dict(source['request'])
    template=HiddenRecoveryRequest.from_dict(full['request'])
    base=replace(small,plaintext_alphabet=template.plaintext_alphabet,bounds=Bounds('verbose',1,1,3),timeout_ms=5000)
    fullq=replace(base,dictionary=template.dictionary)
    # Keep every observed generating assignment unchanged; complete only unused Latin letters.
    codebook={s:tuple(tuple(c) for c in cs) for s,cs in source['truth']['encoder']['codebook'].items()}
    occupied={c for cs in codebook.values() for c in cs}
    available=iter(c for c in itertools.product(base.ciphertext_alphabet.symbols,repeat=2) if c not in occupied)
    for symbol in base.plaintext_alphabet.symbols:
        if symbol not in codebook:
            try:codebook[symbol]=(next(available),)
            except StopIteration:raise ValueError('Cannot complete alphabet in fixed length-two capacity')
    encoder=Encoder(codebook)
    truth=dict(source['truth'],encoder=asdict(encoder));verify(base,truth);verify(fullq,truth)
    held=Text(tuple(tuple(w) for w in source['holdout']['words']))
    held_plain=Text(tuple(tuple(w) for w in source['holdout_plaintext']['words']))
    seen={tuple(m['code']) for m in used_mappings(truth)}
    if not all(tuple(w[i:i+2]) in seen for w in held.words for i in range(0,len(w),2)):raise RuntimeError('Generating code coverage failed')
    train_plain=Text(tuple(tuple(w) for w in truth['plaintext']['words']))
    if set(train_plain.words)&set(held_plain.words) or set(base.ciphertext.words)&set(held.words):raise RuntimeError('Holdout is not novel')
    if encoder.encode(held_plain,tuple(source['holdout_choices']))!=held or encoder.decode(held)!=held_plain:raise RuntimeError('Generating continuation verification failed')
    protocol={'identity':ids,'source_case':'latin-letters-H1','models':['reduced','full'],
        'dictionary_sizes':{'reduced':len(base.dictionary.words),'full':len(fullq.dictionary.words)},
        'alphabet':asdict(base.plaintext_alphabet),'timeout_ms_per_fit':5000,'fits_per_arm':1,
        'training_words':len(base.ciphertext.words),'holdout_words':len(held.words),
        'semantics':'Matched H1/L1-3 letter-only recovery: identical alphabets, observations, code domains and budgets; only dictionary differs. Existing engineered short-word fixture, full corrected Latin vocabulary. Held types remain in dictionary but absent from training; all held generating codes observed. No contraction, language guidance, key enumeration or budget increase. Unused alphabet labels completed without changing observed generating mappings.'}
    write_json(OUT/'protocol.json',protocol)
    p={'identity':ids,'protocol':protocol,'requests':{'reduced':asdict(base),'full':asdict(fullq)},
       'truth':truth,'holdout':asdict(held),'holdout_plaintext':asdict(held_plain),'holdout_choices':source['holdout_choices'],
       'generating_score_full_dictionary':score(held,encoder,fullq.dictionary,base.ciphertext.words),
       'all_generating_holdout_codewords_seen':True,'all_holdout_words_novel':True}
    write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    if path.exists():
        r=json.loads(path.read_text())
        if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    else:r={'prepared_sha256':digest(p),'arms':[],'complete':False}
    for name in ('reduced','full'):
        if any(a['id']==name for a in r['arms']):continue
        q=HiddenRecoveryRequest.from_dict(p['requests'][name])
        print(f"{name}: vocabulary={len(q.dictionary.words)}; alphabet={len(q.plaintext_alphabet.symbols)}; budget=5000ms",flush=True)
        result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
            dictionary=q.dictionary,max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed'))
        verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Independently verified synthetic positive incorrectly UNSAT')
        arm={'id':name,'request_sha256':digest(asdict(q)),'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
        if result['status']=='SAT':
            book=result['encoder']['codebook'];encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in book.items()})
            held=Text(tuple(tuple(w) for w in p['holdout']['words']))
            prediction=score(held,encoder,q.dictionary,q.ciphertext.words)
            exact=[w['fully_decoded'] and tuple(w['decoded_prefix'])==tuple(t)
                for w,t in zip(prediction['word_results'],p['holdout_plaintext']['words'])]
            if prediction['seen_ciphertext_words']!=0:raise RuntimeError('Prediction contains training repeats')
            arm.update(prediction=prediction,exact_words=sum(exact),novel_exact_words=sum(exact),
                evaluation_status='EVALUATED_FROZEN_KEY')
        r['arms'].append(arm);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.2f}s",'exact='+str(arm.get('exact_words')),flush=True)
    r['complete']=True;write_json(path,r);return r


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');a=parser.parse_args()
    if a.run:run()
    else:
        prepare();print('Prepared matched reduced/full H1 positive. Use --run for two five-second fits.')
