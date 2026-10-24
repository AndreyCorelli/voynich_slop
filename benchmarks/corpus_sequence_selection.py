"""Disjoint-text, capped training-only reranking pilot on projected Latin."""
import argparse
from collections import Counter
from dataclasses import asdict
import itertools
import json
import math
from pathlib import Path
import random

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
OUT = Path('experiments/results/corpus-sequence-selection')


def train_model(words, vocabulary):
    words = tuple(words)
    pairs = Counter(zip(words, words[1:]))
    outgoing = Counter(a for a, _ in zip(words, words[1:]))
    initial = Counter(words)
    return {'vocabulary': list(vocabulary), 'unigrams': dict(initial),
            'outgoing': dict(outgoing),
            'pairs': [[a, b, n] for (a, b), n in sorted(pairs.items())],
            'alpha': 1, 'tokens': len(words)}


def sequence_score(words, model):
    words = tuple(''.join(w) for w in words)
    if not words or any(w not in model['vocabulary'] for w in words):
        raise ValueError('Sequence outside scoring vocabulary')
    v = len(model['vocabulary']); alpha = model['alpha']
    pairs = {(a, b): n for a, b, n in model['pairs']}
    value = math.log((model['unigrams'].get(words[0], 0) + alpha) / (model['tokens'] + alpha*v))
    for a, b in zip(words, words[1:]):
        value += math.log((pairs.get((a, b), 0) + alpha) / (model['outgoing'].get(a, 0) + alpha*v))
    return value / len(words)


def prepare():
    path = OUT / 'prepared.json'
    if path.exists():
        saved = json.loads(path.read_text())
        if saved['code_sha256'] != digest(Path(__file__).read_text()) or saved['source_sha256'] != digest(json.loads(SOURCE.read_text())):
            raise ValueError('Prepared code/source changed')
        return saved
    corpus = json.loads(SOURCE.read_text()); records = corpus['records']; split = len(records)//2
    reference = [''.join(r['tokens']) for r in records[:split] if r['tokens']]
    counts = Counter(w for w in reference if len(w) <= 3)
    vocabulary = sorted(sorted(counts, key=lambda w: (-counts[w], w))[:12])
    projected_reference = [w for w in reference if w in vocabulary]
    model = train_model(projected_reference, vocabulary)
    # Freeze reference model before reading evaluation sequences or generating keys.
    protocol = {'source_sha256': digest(corpus), 'split_record': split,
        'reference_record_range': [0, split], 'vocabulary': vocabulary, 'model': model,
        'normalization': corpus['normalization'], 'max_keys': 3, 'timeout_ms': 5000,
        'key_seeds': [101, 202], 'choice_seeds': [303, 404], 'shuffle_seeds': [505, 606],
        'train_words': 4, 'holdout_words': 4,
        'ranking': 'Mean add-one log probability of training plaintext; ties favor first recovered key.',
        'scope': 'Disjoint halves of same author; projected short-word sequence with intervening words removed. Not intact prose, independent author, full-vocabulary or Voynich calibration.',
        'code_sha256': digest(Path(__file__).read_text()),
        'solver_sha256': digest(Path('src/voynich_smt/solver/recovery.py').read_text())}
    write_json(OUT / 'protocol.json', protocol)
    evaluation = [(i, ''.join(r['tokens'])) for i, r in enumerate(records[split:], split)
                  if ''.join(r['tokens']) in vocabulary]
    dictionary = WordDictionary.from_strings(vocabulary)
    alphabet = Alphabet(tuple(sorted({s for w in vocabulary for s in w})))
    cipher_alphabet = Alphabet(tuple('uvwxyz')); bounds = Bounds('verbose', 2, 1, 3)
    cases = []
    for j, (key_seed, choice_seed, shuffle_seed) in enumerate(zip(protocol['key_seeds'],protocol['choice_seeds'],protocol['shuffle_seeds'])):
        selected = evaluation[j*8:(j+1)*8]
        plain = Text.from_string(' '.join(w for _, w in selected))
        codes = list(itertools.product(cipher_alphabet.symbols, repeat=2))
        random.Random(key_seed).shuffle(codes)
        encoder = Encoder({s: tuple(codes[2*i:2*i+2]) for i,s in enumerate(alphabet.symbols)})
        ciphertext, choices = generate_ciphertext(plain, encoder, choice_seed)
        shuffled, metadata = typewise_shuffle(ciphertext, shuffle_seed)
        for kind, text in [('synthetic',ciphertext),('shuffle',shuffled)]:
            q = HiddenRecoveryRequest(Text(text.words[:4]),alphabet,cipher_alphabet,bounds,dictionary,timeout_ms=5000)
            case = {'id': f'block-{j+1}-{kind}', 'request': asdict(q),
                'holdout': asdict(Text(text.words[4:])), 'evaluation_record_indices': [i for i,_ in selected]}
            if kind == 'synthetic':
                truth = {'status':'SAT','verified':True,'encoder':asdict(encoder),
                         'plaintext':asdict(Text(plain.words[:4])),'choices':choices[:sum(map(len,plain.words[:4]))],'nulls':[]}
                verify(q, truth)
                assert encoder.decode(Text(text.words[4:])) == Text(plain.words[4:])
                case.update(truth=truth, holdout_plaintext=asdict(Text(plain.words[4:])),
                    generating_training_score=sequence_score(plain.words[:4],model))
            else:
                case['shuffle'] = metadata
            cases.append(case)
    saved = dict(protocol, cases=cases, reference_projected_tokens=len(projected_reference))
    write_json(path,saved)
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
    else:prepare();print('Prepared four fixed cases; use --run for the bounded pilot.')
