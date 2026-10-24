"""Compare the free-choice witness with uninterrupted Caesar passages of equal size."""
from collections import Counter, deque
from dataclasses import asdict
import json
from math import ceil
from pathlib import Path
from statistics import median

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import Corpus, digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def quantile(values,fraction):
    ordered=sorted(values)
    position=(len(ordered)-1)*fraction
    lower=int(position);upper=ceil(position)
    return ordered[lower]+(ordered[upper]-ordered[lower])*(position-lower)


def windows(records,size,cipher_lengths,min_code_length,max_code_length):
    """Excluded records interrupt passages; they must never be silently bridged."""
    if size<=0 or len(cipher_lengths)!=size or not 1<=min_code_length<=max_code_length:
        raise ValueError('Invalid passage size or code-length bounds')
    pending=deque(maxlen=size)
    for index,record in enumerate(records):
        if not record['tokens']:
            pending.clear();continue
        pending.append((index,len(record['tokens'])))
        if len(pending)!=size:continue
        indices,lengths=zip(*pending)
        total=sum(lengths)
        yield {'start_record':indices[0],'end_record_exclusive':indices[-1]+1,
               'mean':total/size,'median':median(lengths),'total_letters':total,
               'short_words_le_2':sum(n<=2 for n in lengths),
               'lengths':list(lengths),
               'positionwise_length_compatible':all(
                   p*min_code_length<=c<=p*max_code_length
                   for p,c in zip(lengths,cipher_lengths))}


def main():
    corpus_path=Path('data/processed/caesar-latin-v2.json');corpus=Corpus.load(corpus_path)
    if corpus.normalization['parser_version']!=2:raise ValueError('Footer-free corpus required')
    witness_path=Path('experiments/results/conflict-selection-free-30min.json')
    saved=json.loads(witness_path.read_text());request=HiddenRecoveryRequest.from_dict(saved['request'])
    if digest({'request':asdict(request),'codeword_domains':saved['codeword_domains']})!=saved['input_sha256']:
        raise ValueError('Saved witness request checksum mismatch')
    verify(request,saved['result'])
    if request.nulls.enabled or request.bounds.min_code_length<1:
        raise ValueError('Noncompressive, null-free model required')
    cipher_lengths=list(map(len,request.ciphertext.words))
    plain_lengths=list(map(len,saved['result']['plaintext']['words']))
    size=len(cipher_lengths)
    rows=list(windows(corpus.records,size,cipher_lengths,
                      request.bounds.min_code_length,request.bounds.max_code_length))
    if not rows:raise ValueError('No uninterrupted equal-size corpus passages')
    plain_total=sum(plain_lengths);cipher_total=sum(cipher_lengths)
    lower_total=sum(ceil(c/request.bounds.max_code_length) for c in cipher_lengths)
    upper_total=sum(c//request.bounds.min_code_length for c in cipher_lengths)
    short=sum(n<=2 for n in plain_lengths)
    all_lengths=[len(r['tokens']) for r in corpus.records if r['tokens']]
    metrics={}
    for metric in ('mean','median','short_words_le_2'):
        values=[r[metric] for r in rows]
        metrics[metric]={'minimum':min(values),'p05':quantile(values,.05),
                         'median':median(values),'p95':quantile(values,.95),'maximum':max(values)}
    report={'schema_version':1,'corpus':str(corpus_path),'corpus_sha256':corpus.identity,
        'witness_report':str(witness_path),'witness_sha256':digest(saved),
        'request_sha256':digest(asdict(request)),'word_count':size,
        'ciphertext':{'lengths':cipher_lengths,'total_characters':cipher_total,
                      'mean':cipher_total/size,'median':median(cipher_lengths)},
        'witness':{'plaintext':[''.join(w) for w in saved['result']['plaintext']['words']],
                   'lengths':plain_lengths,'total_letters':plain_total,'mean':plain_total/size,
                   'median':median(plain_lengths),'short_words_le_2':short,
                   'character_expansion':cipher_total/plain_total},
        'all_caesar_tokens':{'count':len(all_lengths),'mean':sum(all_lengths)/len(all_lengths),
                             'median':median(all_lengths)},
        'equal_size_passages':{'count':len(rows),'metrics':metrics,
            'mean_le_witness':sum(r['total_letters']<=plain_total for r in rows),
            'median_le_witness':sum(r['median']<=median(plain_lengths) for r in rows),
            'short_word_count_ge_witness':sum(r['short_words_le_2']>=short for r in rows),
            'total_length_compatible':sum(lower_total<=r['total_letters']<=upper_total for r in rows),
            'positionwise_length_compatible':sum(r['positionwise_length_compatible'] for r in rows)},
        'model_necessary_bounds':{'minimum_plaintext_letters':lower_total,
            'maximum_plaintext_letters':upper_total,'maximum_mean':upper_total/size,
            'maximum_median':median([c//request.bounds.min_code_length for c in cipher_lengths]),
            'reason':'Each plaintext letter emits at least min_code_length ciphertext characters, without compression or word merging.'},
        'shortest_mean_passage':min(rows,key=lambda r:(r['total_letters'],r['start_record'])),
        'most_short_words_passage':max(rows,key=lambda r:r['short_words_le_2']),
        'scope':'Descriptive comparison with this one Caesar corpus; overlapping passages are not independent samples. Length compatibility is necessary, not sufficient, for a key or plaintext fit. This is not a probability that the manuscript encodes Latin and adds no solver constraint.',
        'complete':True}
    write_json('experiments/results/word-length-plausibility.json',report)
    print(json.dumps({k:report[k] for k in ('ciphertext','witness','equal_size_passages','model_necessary_bounds')},indent=2))
    return report


if __name__=='__main__':main()
