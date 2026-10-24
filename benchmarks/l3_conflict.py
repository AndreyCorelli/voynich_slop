"""Validate length-three coding, then test the saved conflict and its original prefix."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3

from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import accepts
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover


def validate(config):
    if set(config)!={'boundary_report','synthetic_seeds','gate_timeout_ms','attempts'}:
        raise ValueError('Invalid L3 experiment configuration')
    seeds=config['synthetic_seeds']
    if not seeds or any(type(s) is not int for s in seeds) or len(set(seeds))!=len(seeds):
        raise ValueError('Seeds must be nonempty unique integers')
    if type(config['gate_timeout_ms']) is not int or config['gate_timeout_ms']<=0:
        raise ValueError('Gate timeout must be positive')
    if not config['attempts']:
        raise ValueError('At least one solver attempt is required')
    for attempt in config['attempts']:
        if set(attempt)!={'dictionary_encoding','timeout_ms'} or attempt['dictionary_encoding'] not in {'flat','trie'}:
            raise ValueError('Invalid solver attempt')
        if type(attempt['timeout_ms']) is not int or attempt['timeout_ms']<=0:
            raise ValueError('Attempt timeout must be positive')


def verify(request, result):
    """Check cached SAT witnesses too; a status flag alone is not a certificate."""
    if result['status']!='SAT':return
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()},
                    tuple(result['encoder'].get('null_symbols',())))
    plain=Text(tuple(tuple(w) for w in result['plaintext']['words']))
    choices=tuple(result['choices'])
    maximum=request.max_word_length or max(map(len,request.dictionary.words))
    valid=(result['verified'] and not encoder.null_symbols and not result.get('nulls')
        and set(encoder.codebook)==set(request.plaintext_alphabet.symbols)
        and request.dictionary.accepts(plain)
        and all(request.min_word_length<=len(w)<=maximum for w in plain.words)
        and all(1<=len(cs)<=request.bounds.max_homophones and all(
            request.bounds.min_code_length<=len(c)<=request.bounds.max_code_length
            and all(g in request.ciphertext_alphabet.symbols for g in c) for c in cs)
            for cs in encoder.codebook.values())
        and encoder.encode(plain,choices)==request.ciphertext
        and encoder.decode(request.ciphertext)==plain
        and accepts(plain,encoder,choices,request.selection))
    if not valid:raise RuntimeError('Cached SAT witness failed verification')


def load_probes():
    """Import local exploratory checks only by their complete normalized request hash."""
    cache={}
    paths=['l3-conflict-probe.json','l3-gates-probe.json','l3-prefix-probe.json','l3-trie-probe.json']
    for name in paths:
        path=Path('experiments/results')/name
        if not path.exists():continue
        report=json.loads(path.read_text())
        for row in report.get('experiments',[report]):
            request=HiddenRecoveryRequest.from_dict(json.loads(Path(row['public_input']).read_text()))
            verify(request,row['result'])
            cache[('hidden',digest(asdict(request)))]=(row['result'],str(path))
    return cache


def run(config,output,artifacts,resume=False,import_probes=False):
    validate(config)
    boundary=json.loads(Path(config['boundary_report']).read_text())
    scaling=json.loads(Path(boundary['source_report']).read_text())
    base=HiddenRecoveryRequest.from_dict(json.loads(Path(scaling['experiments'][-1]['public_input']).read_text()))
    if (base.bounds.max_code_length!=2 or base.bounds.max_homophones!=2
        or base.selection!=HomophoneSelection('cycle','text') or base.nulls.enabled or base.optimization.enabled):
        raise ValueError('Expected the null-free cyclic H2/L2 baseline')
    start,end=boundary['conflict']['start'],boundary['conflict']['end']
    if not boundary['conflict']['shortest_unsat_suffix_proven'] or not 0<=start<end<=len(base.ciphertext.words):
        raise ValueError('A proved contiguous conflict is required')
    model=replace(base,bounds=replace(base.bounds,max_code_length=3))
    report={'schema_version':1,'config':config,'config_sha256':digest(config),
        'source_sha256':digest(boundary),'source_report':config['boundary_report'],
        'baseline_bounds':asdict(base.bounds),'tested_bounds':asdict(model.bounds),
        'source_conflict':boundary['conflict'],'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'experiments':[],'synthetic_gate':{},'complete':False}
    if resume and output.exists():
        previous=json.loads(output.read_text())
        if any(previous[k]!=report[k] for k in ('config_sha256','source_sha256','environment')):
            raise ValueError('Resume requires identical configuration, source and environment')
        if previous['complete']:return previous
        report=previous
    cache=load_probes() if import_probes else {}
    done={row['id']:row for row in report['experiments']}

    def check(name,request,mode='hidden',truth=None,phase='observed'):
        if name in done:return done[name]
        public=asdict(request)
        path=artifacts/'inputs'/f'{name}.json'
        if mode=='known':public={'mode':'known','request':public,'plaintext':truth['plaintext']}
        write_json(path,public)
        truth_path=None
        if truth is not None:
            truth_path=artifacts/'truth'/f'{name}.json';write_json(truth_path,truth)
        key=(mode,digest(asdict(request)))
        print(f'{name}: constructing/checking',flush=True)
        began=perf_counter();reused=None
        if key in cache:
            result,reused=cache[key];verify(request,result)
        elif mode=='known':
            plain=Text(tuple(tuple(w) for w in truth['plaintext']['words']))
            result=asdict(recover(plain,request.ciphertext,request.plaintext_alphabet,
                request.ciphertext_alphabet,request.bounds,request.timeout_ms,
                representation=request.representation,selection=request.selection))
            verify(request,result)
        else:
            result=asdict(request.solve());verify(request,result)
        row={'id':name,'phase':phase,'mode':mode,'public_input':str(path),
            'request_sha256':digest(public),'dictionary_encoding':request.dictionary_encoding,
            'timeout_ms':request.timeout_ms,'wall_seconds':perf_counter()-began,'result':result}
        if truth is not None:
            flat=[s for w in truth['plaintext']['words'] for s in w]
            used=sorted({len(truth['encoder']['codebook'][s][k]) for s,k in zip(flat,truth['choices'])})
            if 3 not in used:raise RuntimeError('Synthetic gate did not exercise a length-three code')
            row.update(truth=str(truth_path),used_code_lengths=used)
            if result['status']=='UNSAT':raise RuntimeError('Synthetic positive control incorrectly UNSAT')
        if reused:row['reused_from']=reused
        report['experiments'].append(row);done[name]=row;write_json(output,report)
        print(f'  {result["status"]} check={result["runtime_seconds"]:.3f}s',flush=True)
        return row

    small=HiddenRecoveryRequest(Text.from_string('x'),Alphabet(tuple('abcd')),Alphabet(tuple('xyz')),
        Bounds('verbose',2,1,3),WordDictionary.from_strings(('ab','ba','aca','dad','bcd','abcd','cab','bb','dd','adc')),
        selection=model.selection,timeout_ms=config['gate_timeout_ms'])
    required=[]
    for seed in config['synthetic_seeds']:
        for profile,template in [('small',small),('full',replace(model,timeout_ms=config['gate_timeout_ms']))]:
            public,truth=generate(template,end-start,seed)
            if profile=='full':
                known=check(f'full-known-{seed}',public,'known',truth,'synthetic')
                required.append(known)
            hidden=check(f'{profile}-hidden-{seed}',public,truth=truth,phase='synthetic')
            if profile=='small':required.append(hidden)
    report['synthetic_gate']={'required_profiles':['small-hidden','full-known'],
        'passed':all(row['result']['status']=='SAT' and row['result']['verified'] for row in required),
        'full_hidden_passed':all(row['result']['status']=='SAT' and row['result']['verified']
            for row in report['experiments'] if row['id'].startswith('full-hidden-'))}
    write_json(output,report)
    if not report['synthetic_gate']['passed']:
        report['stopped_reason']='Required synthetic recovery gate remains unresolved'
        report['complete']=True;write_json(output,report);return report

    def observed(label,a,b):
        last=None
        for attempt in config['attempts']:
            request=replace(model,ciphertext=Text(base.ciphertext.words[a:b]),**attempt)
            row=check(f'{label}-{request.dictionary_encoding}-ms{request.timeout_ms}',request)
            row['source_record_indices']=scaling['maximum_sample']['record_indices'][a:b]
            last=row
            if row['result']['status']!='UNKNOWN':break
        report[label]={'status':last['result']['status'],'verified':last['result']['verified'],
            'experiment_id':last['id'],'word_count':b-a,'source_record_indices':scaling['maximum_sample']['record_indices'][a:b]}
        write_json(output,report)
        return last
    conflict=observed('conflict',start,end)
    if conflict['result']['status']=='SAT':observed('prefix',0,end)
    report['complete']=True;write_json(output,report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=Path('experiments/configs/l3-conflict.json'))
    p.add_argument('--output',type=Path,default=Path('experiments/results/l3-conflict.json'))
    p.add_argument('--artifact-dir',type=Path,default=Path('data/generated/l3-conflict'))
    p.add_argument('--resume',action='store_true')
    p.add_argument('--import-probes',action='store_true')
    args=p.parse_args()
    run(json.loads(args.config.read_text()),args.output,args.artifact_dir,args.resume,args.import_probes)


if __name__=='__main__':main()
