"""Separate footer-vocabulary effects with explicit, reproducible add-back requests."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.observed_codes import recover_observed_codes

VARIANTS = {
    'restore-i': ('i',),
    'restore-iv': ('iv',),
    'restore-i-iv': ('i', 'iv'),
    'restore-i-iv-iulius': ('i', 'iv', 'iulius'),
    'restore-by-of': ('by', 'of'),
    'restore-old-witness-words': ('by', 'iv', 'of'),
}
ENGLISH_VARIANTS = {
    'restore-i-iv-iulius-by': ('i', 'iv', 'iulius', 'by'),
    'restore-i-iv-iulius-of': ('i', 'iv', 'iulius', 'of'),
    'restore-i-iv-iulius-by-of': ('i', 'iv', 'iulius', 'by', 'of'),
}


def variant_request(base, original, additions, timeout_ms):
    clean=set(base.dictionary.words)
    extra={tuple(w) for w in additions}
    old=set(original.dictionary.words)
    if not extra or extra & clean or not clean | extra <= old:
        raise ValueError('Additions must be removed entries of the original vocabulary')
    # Retain original source order so additions do not arbitrarily reorder entries.
    words=tuple(w for w in original.dictionary.words if w in clean | extra)
    return replace(base,dictionary=WordDictionary(words),timeout_ms=timeout_ms)


def run(timeout_ms=30000, prepare_only=False, resume=False, group='original'):
    if type(timeout_ms) is not int or timeout_ms<=0:
        raise ValueError('Timeout must be positive')
    if group not in {'original', 'english'}:
        raise ValueError('Unknown variant group')
    variants = VARIANTS if group == 'original' else ENGLISH_VARIANTS
    artifact_name = 'vocabulary-restoration' if group == 'original' else 'english-word-restoration'
    clean_path=Path('data/generated/clean-latin-voynich/inputs/words-23.json')
    original_path=Path('data/generated/observed-codes-voynich/inputs/words-23.json')
    clean=json.loads(clean_path.read_text());original=json.loads(original_path.read_text())
    if clean['codeword_domains']!='observed' or original['codeword_domains']!='observed':
        raise ValueError('Observed domains required')
    base=HiddenRecoveryRequest.from_dict(clean['request'])
    old=HiddenRecoveryRequest.from_dict(original['request'])
    if replace(base,dictionary=old.dictionary,timeout_ms=old.timeout_ms)!=old:
        raise ValueError('Inputs differ beyond vocabulary and timeout')
    witness_path=Path('experiments/results/voynich-observed-codes-23-30min.json')
    saved=json.loads(witness_path.read_text())
    witness_request=HiddenRecoveryRequest.from_dict(saved['request'])
    if replace(witness_request,timeout_ms=old.timeout_ms)!=old:
        raise ValueError('Witness does not match original request')
    verify(witness_request,saved['result'])
    config={'timeout_ms':timeout_ms,'variants':{k:list(v) for k,v in variants.items()},
            'clean_input_sha256':digest(clean),'original_input_sha256':digest(original),
            'witness_sha256':digest(saved)}
    output=Path('experiments/results')/(artifact_name+'.json')
    report={'schema_version':1,'config':config,'config_sha256':digest(config),
            'scope':'Only explicit vocabulary additions; fixed 23-word ciphertext and H2/L3 model. UNKNOWN is inconclusive. Existing SAT witnesses rechecked without solver hints.',
            'experiments':[],'complete':False}
    if resume and output.exists():
        report=json.loads(output.read_text())
        if report['config_sha256']!=digest(config):
            raise ValueError('Resume requires identical requests, variants, witness and timeout')
    done={r['id']:r for r in report['experiments']}
    prepared=[]
    for name, additions in variants.items():
        request=variant_request(base,old,additions,timeout_ms)
        payload={'request':asdict(request),'codeword_domains':'observed'}
        path=Path('data/generated')/artifact_name/'inputs'/(name+'.json')
        write_json(path,payload)
        prepared.append({'id':name,'public_input':str(path),'input_sha256':digest(payload),
                         'additions':list(additions),'vocabulary_size':len(request.dictionary.words)})
    report['prepared_inputs']=prepared
    write_json(output,report)
    if prepare_only:return report
    for entry in prepared:
        name=entry['id']
        if name in done:continue
        request=HiddenRecoveryRequest.from_dict(json.loads(Path(entry['public_input']).read_text())['request'])
        # A legal known witness proves SAT even if fresh search might time out.
        reused=None
        try:
            verify(request,saved['result'])
            reused=saved['result']
        except RuntimeError:
            pass
        print(f"{name}: +{','.join(entry['additions'])}; vocabulary={entry['vocabulary_size']}",flush=True)
        start=perf_counter()
        if reused is not None:
            result=reused
            method='existing witness independently checked against this vocabulary; no new solve'
        else:
            result=asdict(recover_observed_codes(request))
            verify(request,result)
            method='fresh fully hidden solve; no key, segmentation or length hints'
        row={**entry,'method':method,'result':result,'wall_seconds':perf_counter()-start}
        if reused is not None:row['witness_source']=str(witness_path)
        report['experiments'].append(row)
        write_json(output,report)
        print(f"  {result['status']}; {row['method']}",flush=True)
    report['complete']=True
    write_json(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--group',choices=('original','english'),default='original')
    args=parser.parse_args()
    run(args.timeout_ms,args.prepare_only,args.resume,args.group)
