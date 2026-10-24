"""Find the shortest UNSAT contiguous suffix ending at word 23."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks.clean_latin_prefix import boundary
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes


def suffix_witness(result, start):
    """Rotate each code list to preserve its first phase after dropping a prefix."""
    copied=deepcopy(result)
    words=result['plaintext']['words']
    removed=Counter(s for word in words[:start] for s in word)
    skipped=sum(map(len,words[:start]))
    key=copied['encoder']['codebook']
    phases={s:removed[s]%len(codes) for s,codes in key.items()}
    for s,codes in key.items():
        phase=phases[s]
        key[s]=codes[phase:]+codes[:phase]
    copied['plaintext']['words']=deepcopy(words[start:])
    copied['choices']=[(choice-phases[s])%len(key[s]) for s,choice in zip(
        (s for word in words[start:] for s in word),result['choices'][skipped:])]
    copied['segmentation']=deepcopy(result['segmentation'][start:])
    return copied


def validate_row(row,base):
    request=HiddenRecoveryRequest.from_dict(row['request'])
    count=row['word_count']
    if type(count) is not int or not 1<=count<=len(base.ciphertext.words):
        raise ValueError('Invalid suffix length')
    if (request.ciphertext.words!=base.ciphertext.words[-count:]
        or replace(request,ciphertext=base.ciphertext,timeout_ms=base.timeout_ms)!=base
        or digest({'request':asdict(request),'codeword_domains':'observed'})!=row['input_sha256']):
        raise ValueError('Cached request is not the same-model contiguous suffix')
    verify(request,row['result'])
    return request


def run(timeout_ms=30000,resume=False):
    if type(timeout_ms) is not int or timeout_ms<=0:raise ValueError('Positive timeout required')
    source_path=Path('experiments/results/restore-i-iv-iulius-30min.json')
    source=json.loads(source_path.read_text());base=HiddenRecoveryRequest.from_dict(source['request'])
    prepared=json.loads(Path(source['source_input']).read_text())
    original=HiddenRecoveryRequest.from_dict(prepared['request'])
    if (not source['complete'] or source['result']['status']!='UNSAT'
        or source['codeword_domains']!='observed'
        or base!=replace(original,timeout_ms=base.timeout_ms)
        or digest({'request':asdict(base),'codeword_domains':'observed'})!=source['input_sha256']):
        raise ValueError('Invalid source UNSAT report')
    if len(base.ciphertext.words)!=23:raise ValueError('Expected full 23-word block')
    witness_path=Path('experiments/results/voynich-observed-codes-23-30min.json')
    saved=json.loads(witness_path.read_text());old=HiddenRecoveryRequest.from_dict(saved['request'])
    if replace(old,dictionary=base.dictionary,timeout_ms=base.timeout_ms)!=base:
        raise ValueError('Witness has different scientific parameters')
    verify(old,saved['result'])
    output=Path('experiments/results/clean-latin-suffix.json')
    report={'schema_version':1,'source_report':str(source_path),'source_sha256':digest(source),
        'witness_source':str(witness_path),'witness_sha256':digest(saved),
        'semantics':'Contiguous suffixes ending at word 23; same vocabulary and H2/L3 model. Cyclic code lists are freely inferred and may rotate to absorb removed initial history. No key or phase hints in public solves. Shortest suffix only, not smallest arbitrary deletion core.',
        'experiments':[],'complete':False}
    if resume and output.exists():
        previous=json.loads(output.read_text())
        if any(previous[k]!=report[k] for k in ('source_sha256','witness_sha256')):
            raise ValueError('Resume requires identical source reports')
        report=previous
        for row in report['experiments']:validate_row(row,base)
    inputs={}
    for count in range(1,24):
        request=replace(base,ciphertext=Text(base.ciphertext.words[-count:]),timeout_ms=timeout_ms)
        payload={'request':asdict(request),'codeword_domains':'observed'}
        path=Path('data/generated/clean-latin-suffix/inputs')/f'words-{count:02d}.json'
        write_json(path,payload);inputs[count]=(request,path,digest(payload))
    if not report['experiments']:
        report['experiments'].append({'word_count':23,'start':0,'end':23,'request':asdict(base),
            'input_sha256':source['input_sha256'],'result':source['result'],
            'method':'imported full-block UNSAT report','source_report':str(source_path)})
        for count in range(1,24):
            request,path,checksum=inputs[count];result=suffix_witness(saved['result'],23-count)
            try:verify(request,result)
            except RuntimeError:break
            report['experiments'].append({'word_count':count,'start':23-count,'end':23,
                'request':asdict(request),'public_input':str(path),'input_sha256':checksum,
                'result':result,'method':'existing witness restricted and cyclic code lists rotated; independently checked, no new solve'})
    report['boundary']=boundary(report['experiments'])
    write_json(output,report)
    while not report['boundary']['minimality_proven']:
        lo=report['boundary']['largest_verified_sat'];hi=report['boundary']['smallest_proved_unsat']
        attempted={r['word_count'] for r in report['experiments']
            if r['result']['status']=='UNKNOWN' and r['request']['timeout_ms']>=timeout_ms}
        choices=[n for n in range(lo+1,hi) if n not in attempted]
        if not choices:break
        count=min(choices,key=lambda n:(abs(n-(lo+hi)/2),n))
        request,path,checksum=inputs[count];report['next_input']=str(path);write_json(output,report)
        print(f'Suffix {count} words[{23-count}:23]: SAT >= {lo}, UNSAT <= {hi}; budget={timeout_ms}ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(request));verify(request,result)
        report['experiments'].append({'word_count':count,'start':23-count,'end':23,
            'request':asdict(request),'public_input':str(path),'input_sha256':checksum,
            'result':result,'wall_seconds':perf_counter()-start,'method':'fresh fully hidden suffix solve'})
        report['boundary']=boundary(report['experiments']);write_json(output,report)
        print(f"  {result['status']}; solver={result['runtime_seconds']:.2f}s",flush=True)
        if result['status']=='UNKNOWN':break
    report['complete']=report['boundary']['minimality_proven']
    if report['complete']:
        report.pop('next_input',None)
        count=report['boundary']['smallest_proved_unsat']
        report['conflict']={'start':23-count,'end':23,'word_count':count,
            'ciphertext_words':[''.join(w) for w in base.ciphertext.words[-count:]]}
    write_json(output,report);print(json.dumps(report['boundary'],indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();run(args.timeout_ms,args.resume)
