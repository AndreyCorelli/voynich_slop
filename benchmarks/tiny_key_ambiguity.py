"""Six-solution cap on a tiny hidden-word synthetic ambiguity experiment."""
from dataclasses import asdict
import hashlib
from pathlib import Path

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

OUT=Path('experiments/results/tiny-key-ambiguity')


def used_mappings(result):
    choices=iter(result['choices']);codebook=result['encoder']['codebook']
    used=set()
    for word in result['plaintext']['words']:
        for symbol in word:used.add((symbol,tuple(codebook[symbol][next(choices)])))
    return [{'symbol':s,'code':c} for s,c in sorted(used)]


def run():
    output=OUT/'report.json'
    if output.exists():raise ValueError('Fixed experiment already recorded; do not overwrite')
    plain=Text.from_string('ab ac ba ca')
    encoder=Encoder({'a':(('x','x'),('x','y')),'b':(('y','x'),('y','y')),'c':(('z','x'),('z','y'))})
    choices=(0,0,1,0,1,0,1,1)
    cipher=encoder.encode(plain,choices)
    continuation_plain=Text.from_string('abc cab bca aab')
    continuation_choices=(1,1,1,0,0,0,1,0,1,0,1,1)
    continuation=encoder.encode(continuation_plain,continuation_choices)
    dictionary=WordDictionary.from_strings(('ab','ac','ba','ca','abc','cab','bca','aab'))
    q=HiddenRecoveryRequest(cipher,Alphabet(tuple('abc')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,3),dictionary,timeout_ms=5000)
    truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
    verify(q,truth)
    generating_score=score(continuation,encoder,dictionary,cipher.words)
    generating_used={(s,tuple(encoder.codebook[s][k])) for word,offset in [] for s,k in []}
    generating_used={(x['symbol'],tuple(x['code'])) for x in used_mappings(truth)}
    if len(generating_used)!=6:raise RuntimeError('All generating homophones must appear in training')
    report={'request':asdict(q),'request_sha256':digest(asdict(q)),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'continuation':asdict(continuation),'generating_truth':truth,
        'generating_continuation_plaintext':asdict(continuation_plain),'generating_continuation_choices':continuation_choices,
        'generating_score':generating_score,'all_six_generating_homophones_seen_in_training':True,
        'max_solutions':6,'timeout_ms_per_attempt':5000,'solutions':[],'attempts':[],
        'semantics':'Tiny artificial vocabulary; not Latin/German or full benchmark calibration. Recover at most six distinct used-ownership explanations. Blocking all previously used symbol/code facts excludes supersets and code-slot permutations; unused-code variants alone do not count. This is not exhaustive uniform key sampling. All true homophones covered in training; predictions frozen, holdout/truth not passed to solver.'}
    exclusions=[];seen=set()
    for attempt in range(6):
        result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,
            q.bounds,q.timeout_ms,dictionary=q.dictionary,min_word_length=1,
            max_word_length=max(map(len,dictionary.words)),selection=q.selection,
            key_exclusions=tuple(exclusions),codeword_domains='observed'))
        verify(q,result);report['attempts'].append({'status':result['status'],'runtime_seconds':result['runtime_seconds']})
        if result['status']!='SAT':
            report['stop_reason']=result['status'];write_json(output,report);break
        mappings=used_mappings(result);signature=digest(mappings)
        if signature in seen:raise RuntimeError('Repeated used mapping explanation')
        seen.add(signature)
        recovered=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
        prediction=score(continuation,recovered,dictionary,cipher.words)
        exact=[r['fully_decoded'] and tuple(r['decoded_prefix'])==w for r,w in zip(prediction['word_results'],continuation_plain.words)]
        row={'number':attempt+1,'result':result,'used_mappings':mappings,'used_mappings_sha256':signature,
             'prediction':prediction,'exact_generating_words':sum(exact)}
        report['solutions'].append(row);exclusions.append({'kind':'word','segments':mappings})
        write_json(output,report)
        print(f"Solution {attempt+1}: SAT {result['runtime_seconds']:.2f}s; decoded={prediction['fully_decoded_words']}/4, dictionary={prediction['dictionary_words']}/4, exact={sum(exact)}/4",flush=True)
    else:report['stop_reason']='SIX_SOLUTION_CAP'
    report['complete']=True;write_json(output,report)
    return report


if __name__=='__main__':run()
