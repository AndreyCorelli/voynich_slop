"""Coverage-conditioned projected-Latin key-ranking control; fixed short budgets."""
import argparse
from collections import Counter
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import random

from benchmarks.corpus_sequence_selection import sequence_score
from benchmarks.frozen_key_holdout import score
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.l3_conflict import verify
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Bounds, Encoder, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE = Path('data/processed/caesar-latin-v2.json')
REFERENCE = Path('experiments/results/corpus-sequence-selection/prepared.json')
OUT = Path('experiments/results/coverage-sequence-selection')


def covered_block(evaluation, start, maximum=32):
    """Earliest prefix with at least two occurrences of each continuation letter."""
    for size in range(4, maximum+1):
        training=evaluation[start:start+size]; held=evaluation[start+size:start+size+4]
        if len(training)!=size or len(held)!=4: break
        counts=Counter(s for _,w in training for s in w)
        if all(counts[s]>=2 for _,w in held for s in w):
            return training, held
    raise ValueError('No coverage-eligible block within fixed 32-word ceiling')


def alternating_choices(plain):
    counts=Counter(); choices=[]
    for word in plain.words:
        for symbol in word:
            choices.append(counts[symbol] % 2); counts[symbol]+=1
    return tuple(choices)


def coverage(truth, held):
    mappings=used_mappings(truth); seen={tuple(m['code']) for m in mappings}
    # Generating codes are all length two; this audit does not infer recovered segmentation.
    return [all(tuple(w[i:i+2]) in seen for i in range(0,len(w),2)) for w in held.words]


def identity():
    paths=(Path(__file__), Path('benchmarks/corpus_sequence_selection.py'),
           Path('src/voynich_smt/solver/recovery.py'))
    return {str(p):digest(p.read_text()) for p in paths}


def prepare():
    reference=json.loads(REFERENCE.read_text()); corpus=json.loads(SOURCE.read_text())
    if reference['source_sha256']!=digest(corpus): raise ValueError('Reference source changed')
    hashes=identity(); path=OUT/'prepared.json'
    if path.exists():
        saved=json.loads(path.read_text())
        if saved['identity']!=hashes or saved['reference_sha256']!=digest(reference):
            raise ValueError('Prepared source or code changed')
        return saved
    protocol={'identity':hashes,'reference_sha256':digest(reference),
        'model':reference['model'],'vocabulary':reference['vocabulary'],
        'source_sha256':digest(corpus),'split_record':reference['split_record'],
        'evaluation_start_projected_offset':16,'minimum_train_words':4,'maximum_train_words':32,
        'holdout_words':4,'max_keys':3,'timeout_ms':5000,
        'key_seeds':[707,808],'choice_seeds':[909,1010],'shuffle_seeds':[1111,1212],
        'coverage_rule':'Earliest 4..32 word prefix with >=2 occurrences of every letter in next four projected words; training choices alternate per letter, continuation choices are free seeded draws.',
        'ranking':'Unchanged reference-only smoothed score on recovered training plaintext; first key wins ties.',
        'scope':'Coverage-conditioned synthetic projected Latin, not blind passage selection or intact prose. Training choices are engineered to guarantee coverage, not independent random draws or a modeled cycle. Hidden recovery remains free H2/L1-3.'}
    write_json(OUT/'protocol.json',protocol)
    evaluation=[(i,''.join(r['tokens'])) for i,r in enumerate(corpus['records'])
        if i>=protocol['split_record'] and ''.join(r['tokens']) in protocol['vocabulary']]
    alphabet=Alphabet(tuple(sorted({s for w in protocol['vocabulary'] for s in w})))
    ca=Alphabet(tuple('uvwxyz')); bounds=Bounds('verbose',2,1,3)
    dictionary=WordDictionary.from_strings(protocol['vocabulary']); start=16; cases=[]
    for j,(ks,cs,ss) in enumerate(zip(protocol['key_seeds'],protocol['choice_seeds'],protocol['shuffle_seeds'])):
        train_records, held_records=covered_block(evaluation,start)
        start+=len(train_records)+4
        plain=Text.from_string(' '.join(w for _,w in train_records))
        held_plain=Text.from_string(' '.join(w for _,w in held_records))
        codes=list(itertools.product(ca.symbols,repeat=2));random.Random(ks).shuffle(codes)
        encoder=Encoder({s:tuple(codes[2*i:2*i+2]) for i,s in enumerate(alphabet.symbols)})
        choices=alternating_choices(plain); train=encoder.encode(plain,choices)
        held,held_choices=generate_ciphertext(held_plain,encoder,cs)
        truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
        covered=coverage(truth,held)
        if covered!=[True]*4 or encoder.decode(held)!=held_plain:raise RuntimeError('Coverage control failed')
        full=Text(train.words+held.words); shuffled,metadata=typewise_shuffle(full,ss)
        size=len(train.words)
        for kind,text in [('synthetic',full),('shuffle',shuffled)]:
            q=HiddenRecoveryRequest(Text(text.words[:size]),alphabet,ca,bounds,dictionary,timeout_ms=5000)
            case={'id':f'block-{j+1}-{kind}','request':asdict(q),'holdout':asdict(Text(text.words[size:])),
                  'training_record_indices':[i for i,_ in train_records],
                  'holdout_record_indices':[i for i,_ in held_records]}
            if kind=='synthetic':
                verify(q,truth)
                case.update(truth=truth,holdout_plaintext=asdict(held_plain),holdout_choices=held_choices,
                    generating_training_score=sequence_score(plain.words,protocol['model']),
                    generating_covered_holdout_words=sum(covered),
                    generating_holdout_score=score(held,encoder,dictionary,train.words))
            else:case['shuffle']=metadata
            cases.append(case)
    saved=dict(protocol,cases=cases);write_json(path,saved)
    return saved


def run():
    prepared = prepare(); path = OUT/'report.json'
    report = {'prepared_sha256':digest(prepared),'cases':[],'complete':False}
    if path.exists():
        report = json.loads(path.read_text())
        if report['prepared_sha256'] != digest(prepared): raise ValueError('Checkpoint changed')
    for case in prepared['cases']:
        if any(r['id']==case['id'] for r in report['cases']): continue
        q = HiddenRecoveryRequest.from_dict(case['request']); exclusions=[]; fits=[]; attempts=[]
        print(case['id'], flush=True)
        for _ in range(prepared['max_keys']):
            result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,
                q.timeout_ms,dictionary=q.dictionary,max_word_length=3,codeword_domains='observed',key_exclusions=tuple(exclusions)))
            verify(q,result); attempts.append({'status':result['status'],'runtime_seconds':result['runtime_seconds']})
            print(result['status'],f"{result['runtime_seconds']:.2f}s",flush=True)
            if result['status']!='SAT': break
            mappings=used_mappings(result)
            if any(all(m in mappings for m in ex['segments']) for ex in exclusions): raise RuntimeError('Repeated used ownership')
            fits.append({'result':result,'training_score':sequence_score(result['plaintext']['words'],prepared['model'])})
            exclusions.append({'kind':'word','segments':mappings})
        # Freeze the training-selected index before accessing the holdout.
        selected=max(range(len(fits)),key=lambda i: fits[i]['training_score']) if fits else None
        row={'id':case['id'],'attempts':attempts,'fits':fits,'first_index':0 if fits else None,
             'selected_index':selected,'selection_scope':'Capped returned key set only',
             'evaluation_status':'NOT_EVALUATED_NO_SAT' if not fits else 'EVALUATED_FROZEN_KEYS'}
        for fit in fits:
            book=fit['result']['encoder']['codebook']
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in book.items()})
            held=Text(tuple(tuple(w) for w in case['holdout']['words']))
            prediction=score(held,encoder,q.dictionary,q.ciphertext.words)
            fit['prediction']=prediction
            if 'truth' in case:
                fit['exact_words']=sum(r['fully_decoded'] and tuple(r['decoded_prefix'])==tuple(w)
                    for r,w in zip(prediction['word_results'],case['holdout_plaintext']['words']))
        report['cases'].append(row); write_json(path,report)
    report['complete']=True;write_json(path,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if args.run:run()
    else:prepare();print('Prepared coverage-controlled cases; use --run for bounded fits.')
