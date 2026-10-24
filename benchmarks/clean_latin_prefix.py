"""Find a certified SAT/UNSAT boundary for the fixed i/iv/iulius vocabulary."""
import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes


def truncate_witness(result, count):
    truncated=deepcopy(result)
    words=result['plaintext']['words'][:count]
    truncated['plaintext']['words']=words
    truncated['choices']=result['choices'][:sum(map(len,words))]
    truncated['segmentation']=result['segmentation'][:count]
    return truncated


def boundary(experiments):
    sat=[r['word_count'] for r in experiments if r['result']['status']=='SAT']
    unsat=[r['word_count'] for r in experiments if r['result']['status']=='UNSAT']
    lo=max(sat,default=0);hi=min(unsat)
    if lo>=hi:raise RuntimeError('Conflicting prefix certificates')
    return {'largest_verified_sat':lo,'smallest_proved_unsat':hi,
            'minimality_proven':hi==lo+1,
            'unresolved_sizes':list(range(lo+1,hi))}


def run(timeout_ms=30000,resume=False):
    if type(timeout_ms) is not int or timeout_ms<=0:raise ValueError('Positive timeout required')
    source_path=Path('experiments/results/restore-i-iv-iulius-30min.json')
    source=json.loads(source_path.read_text())
    base=HiddenRecoveryRequest.from_dict(source['request'])
    prepared=json.loads(Path(source['source_input']).read_text())
    original=HiddenRecoveryRequest.from_dict(prepared['request'])
    if (not source['complete'] or source['result']['status']!='UNSAT'
        or source['codeword_domains']!='observed'
        or base!=replace(original,timeout_ms=base.timeout_ms)
        or digest({'request':asdict(base),'codeword_domains':'observed'})!=source['input_sha256']):
        raise ValueError('Invalid source UNSAT report or request hash')
    if len(base.ciphertext.words)!=23:raise ValueError('Expected the complete 23-word baseline')
    witness_path=Path('experiments/results/voynich-observed-codes-23-30min.json')
    saved=json.loads(witness_path.read_text())
    witness_request=HiddenRecoveryRequest.from_dict(saved['request'])
    if replace(witness_request,dictionary=base.dictionary,timeout_ms=base.timeout_ms)!=base:
        raise ValueError('Original witness has different scientific parameters')
    verify(witness_request,saved['result'])
    artifacts=Path('data/generated/clean-latin-prefix/inputs')
    inputs={}
    for count in range(1,24):
        request=replace(base,ciphertext=Text(base.ciphertext.words[:count]),timeout_ms=timeout_ms)
        payload={'request':asdict(request),'codeword_domains':'observed'}
        path=artifacts/f'words-{count:02d}.json'
        write_json(path,payload)
        inputs[count]=(request,path,digest(payload))
    output=Path('experiments/results/clean-latin-prefix.json')
    report={'schema_version':1,'source_report':str(source_path),'source_sha256':digest(source),
            'witness_source':str(witness_path),'witness_sha256':digest(saved),
            'semantics':'Only contiguous prefixes from word zero; fixed vocabulary and phase-zero text-wide cycles. UNKNOWN does not move either bound. UNSAT certificates are solver reports, not independently checked proof objects.',
            'experiments':[],'complete':False}
    if resume and output.exists():
        previous=json.loads(output.read_text())
        if any(previous[k]!=report[k] for k in ('source_sha256','witness_sha256')):
            raise ValueError('Resume requires identical source reports')
        report=previous
        for row in report['experiments']:
            request=HiddenRecoveryRequest.from_dict(row['request'])
            if replace(request,ciphertext=base.ciphertext,timeout_ms=base.timeout_ms)!=base:
                raise ValueError('Cached request has different scientific parameters')
            if request.ciphertext.words!=base.ciphertext.words[:row['word_count']]:
                raise ValueError('Cached request is not a contiguous prefix')
            if digest({'request':asdict(request),'codeword_domains':'observed'})!=row['input_sha256']:
                raise ValueError('Cached input checksum mismatch')
            verify(request,row['result'])
    else:
        report['experiments'].append({'word_count':23,'request':asdict(base),
            'input_sha256':source['input_sha256'],'result':source['result'],
            'method':'imported full-prefix UNSAT report','source_report':str(source_path)})
        # The original key may certify an initial block despite failing later words.
        for count in range(1,24):
            request,path,checksum=inputs[count]
            result=truncate_witness(saved['result'],count)
            try:verify(request,result)
            except RuntimeError:break
            report['experiments'].append({'word_count':count,'request':asdict(request),
                'input_sha256':checksum,'public_input':str(path),'result':result,
                'method':'truncated existing witness independently checked; no new solve'})
    report['boundary']=boundary(report['experiments'])
    while not report['boundary']['minimality_proven']:
        lo=report['boundary']['largest_verified_sat'];hi=report['boundary']['smallest_proved_unsat']
        attempted={r['word_count'] for r in report['experiments']
                   if r['result']['status']=='UNKNOWN' and r['request']['timeout_ms']>=timeout_ms}
        choices=[n for n in range(lo+1,hi) if n not in attempted]
        if not choices:break
        count=min(choices,key=lambda n:(abs(n-(lo+hi)/2),n))
        request,path,checksum=inputs[count]
        report['next_input']=str(path)
        write_json(output,report)
        print(f'Prefix {count}: SAT >= {lo}, UNSAT <= {hi}; budget={timeout_ms}ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(request));verify(request,result)
        report['experiments'].append({'word_count':count,'request':asdict(request),
            'input_sha256':checksum,'public_input':str(path),'result':result,
            'wall_seconds':perf_counter()-start,'method':'fresh fully hidden prefix solve'})
        report['boundary']=boundary(report['experiments'])
        print(f"  {result['status']}; solver={result['runtime_seconds']:.2f}s",flush=True)
        write_json(output,report)
        if result['status']=='UNKNOWN':
            # Leave the exact unresolved request available for a larger user-run budget.
            break
    report['complete']=report['boundary']['minimality_proven']
    if report['complete']:report.pop('next_input',None)
    write_json(output,report)
    print(json.dumps(report['boundary'],indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    run(args.timeout_ms,args.resume)
