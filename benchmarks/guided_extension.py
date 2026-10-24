"""Extend a recovered suffix key with rotatable pins and core-guided mapping release."""
import argparse
from collections import Counter
from dataclasses import asdict,replace
import json
from pathlib import Path
import platform
from time import perf_counter
import z3

from voynich_smt.cipher.base import Encoder
from voynich_smt.cipher.selection import accepts
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.guided import recover_guided,forced_cycle_conflicts


def load_input(payload):
    if set(payload)!={'request','guidance'}:
        raise ValueError('Expected a guided input wrapper')
    request=HiddenRecoveryRequest.from_dict(payload['request'])
    guide=payload['guidance']
    required={'encoder','pinned_symbols','rotate','hint_symbols','word_hints'}
    if not required<=set(guide) or set(guide)-required-{'minimize_core'}:
        raise ValueError('Invalid guidance fields')
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in guide['encoder']['codebook'].items()},
                    tuple(guide['encoder'].get('null_symbols',())))
    words={int(i):tuple(w) for i,w in guide['word_hints'].items()}
    return request,encoder,dict(pinned_symbols=guide['pinned_symbols'],rotate=guide['rotate'],
        hint_symbols=guide['hint_symbols'],word_hints=words,minimize_core=guide.get('minimize_core',False))


def run(config,output,artifacts,resume=False):
    required={'source_report','timeout_ms','dictionary_encoding'}
    if (not required<=set(config) or set(config)-required-{'minimize_core'}
        or type(config['timeout_ms']) is not int or config['timeout_ms']<=0
        or config['dictionary_encoding'] not in {'flat','trie'}
        or type(config.get('minimize_core',False)) is not bool):
        raise ValueError('Invalid guided extension configuration')
    source=json.loads(Path(config['source_report']).read_text())
    if source['conflict']['status']!='SAT' or not source['conflict']['verified']:
        raise ValueError('Verified suffix witness required')
    witness=next(row for row in source['experiments'] if row['id']==source['conflict']['experiment_id'])
    suffix_request=HiddenRecoveryRequest.from_dict(json.loads(Path(witness['public_input']).read_text()))
    row=witness['result']
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in row['encoder']['codebook'].items()})
    plain=Text(tuple(tuple(w) for w in row['plaintext']['words']))
    if (encoder.encode(plain,tuple(row['choices']))!=suffix_request.ciphertext
        or encoder.decode(suffix_request.ciphertext)!=plain
        or not suffix_request.dictionary.accepts(plain)
        or not accepts(plain,encoder,tuple(row['choices']),suffix_request.selection)):
        raise ValueError('Source witness failed independent verification')
    prefix_row=next(e for e in source['experiments'] if e['id']==source['prefix']['experiment_id'])
    request=HiddenRecoveryRequest.from_dict(json.loads(Path(prefix_row['public_input']).read_text()))
    start=source['source_conflict']['start']
    if (request.ciphertext.words[start:]!=suffix_request.ciphertext.words
        or request.bounds!=suffix_request.bounds or request.dictionary!=suffix_request.dictionary
        or request.plaintext_alphabet!=suffix_request.plaintext_alphabet
        or request.ciphertext_alphabet!=suffix_request.ciphertext_alphabet
        or request.selection!=suffix_request.selection):
        raise ValueError('Prefix must extend the exact suffix under identical scientific parameters')
    request=replace(request,timeout_ms=config['timeout_ms'],dictionary_encoding=config['dictionary_encoding'])
    usage=Counter(s for w in plain.words for s in w)
    used=sorted(usage)
    cycle_conflicts=forced_cycle_conflicts(request.ciphertext,encoder,used)
    word_hints={start+i:w for i,w in enumerate(plain.words)}
    blockers=[]
    for i,word in enumerate(request.ciphertext.words[:start]):
        try:
            decoded=encoder.decode(Text((word,))).words[0]
            reason='outside-vocabulary' if decoded not in request.dictionary.words else 'decodable'
        except ValueError:
            decoded=None;reason='undecodable'
        blockers.append({'word_index':i,'ciphertext':list(word),'decoded':list(decoded) if decoded else None,'reason':reason})
    report={'schema_version':1,'config':config,'config_sha256':digest(config),
        'source_report':config['source_report'],'source_sha256':digest(source),
        'environment':{'python':platform.python_version(),'z3':z3.get_version_string()},
        'request_sha256':digest(asdict(request)),'suffix_used_symbols':used,'fixed_key_word_checks':blockers,
        'forced_cycle_conflicts':cycle_conflicts,
        'semantics':'Every attempt checks the whole original prefix; nonempty pins define conditional submodels',
        'experiments':[],'complete':False}
    if resume and output.exists():
        previous=json.loads(output.read_text())
        if any(previous[k]!=report[k] for k in ('config_sha256','source_sha256','environment','request_sha256')):
            raise ValueError('Resume requires identical configuration, source, request and environment')
        if previous['complete']:return previous
        report=previous
    done={e['id']:e for e in report['experiments']}

    def check(name,pins,rotate):
        if name in done:return done[name]
        guide={'encoder':asdict(encoder),'pinned_symbols':sorted(pins),'rotate':rotate,
            'hint_symbols':used,'word_hints':{str(i):list(w) for i,w in word_hints.items()},
            'minimize_core':config.get('minimize_core',False)}
        path=artifacts/'inputs'/f'{name}.json'
        payload={'request':asdict(request),'guidance':guide};write_json(path,payload)
        print(f'{name}: {len(pins)} pinned letters; rotate={rotate}',flush=True)
        begin=perf_counter()
        result=recover_guided(request,encoder,pins,rotate=rotate,hint_symbols=used,word_hints=word_hints,
                              minimize_core=config.get('minimize_core',False))
        row={'id':name,'public_input':str(path),'input_sha256':digest(payload),'pinned_symbols':sorted(pins),
            'rotate':rotate,'wall_seconds':perf_counter()-begin,'result':asdict(result)}
        report['experiments'].append(row);done[name]=row;write_json(output,report)
        print(f'  {result.status} check={result.runtime_seconds:.3f}s core={result.capacity.get("pinned_unsat_core")}',flush=True)
        return row

    def finish(row):
        report.update(complete=True,outcome={'status':row['result']['status'],
            'verified':row['result']['verified'],'experiment_id':row['id'],
            'pinned_symbols':row['pinned_symbols'],
            'scope':'full model SAT' if row['result']['status']=='SAT' else
                    ('unrestricted model' if not row['pinned_symbols'] else 'conditional pinned submodel')})
        write_json(output,report);return report

    exact=check('exact-key',sorted(encoder.codebook),False)
    if exact['result']['status']=='SAT':return finish(exact)
    for conflict in cycle_conflicts:
        certificate=check(f'single-pin-{conflict["symbol"]}',[conflict['symbol']],True)
        if certificate['result']['status']=='SAT':
            raise RuntimeError('Forced cycle certificate contradicted by a verified SAT model')
    pins=used[:]
    phase=check('used-mappings-rotatable',pins,True)
    if phase['result']['status']=='SAT':return finish(phase)
    releases=[]
    while pins:
        # UNKNOWN offers no conflict proof: then release the least-used remaining
        # mapping by heuristic, and label that choice explicitly.
        core=phase['result']['capacity'].get('pinned_unsat_core',[])
        certified=[c['symbol'] for c in cycle_conflicts if c['symbol'] in pins]
        literal=[sorted(set(b['decoded'])) for b in blockers if b['reason']=='outside-vocabulary'
                 and set(b['decoded'])<=set(pins)]
        smallest=min(literal,key=lambda group:(len(group),group)) if literal else []
        choices=certified or smallest or [s for s in core if s in pins] or pins
        symbol=min(choices,key=lambda s:(usage[s],s))
        releases.append({'symbol':symbol,'basis':'forced cycle certificate' if certified else
                         ('fixed decoding outside vocabulary' if smallest else
                          ('UNSAT core' if core else 'frequency heuristic after unresolved/coreless check'))})
        pins=[s for s in pins if s!=symbol]
        phase=check(f'released-{len(releases):02d}-'+''.join(e['symbol'] for e in releases),pins,True)
        report['releases']=releases[:];write_json(output,report)
        if phase['result']['status']=='SAT':return finish(phase)
    return finish(phase)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=Path('experiments/configs/guided-extension.json'))
    p.add_argument('--output',type=Path,default=Path('experiments/results/guided-extension.json'))
    p.add_argument('--artifact-dir',type=Path,default=Path('data/generated/guided-extension'))
    p.add_argument('--resume',action='store_true')
    p.add_argument('--replay',type=Path)
    args=p.parse_args()
    if args.replay:
        request,encoder,kwargs=load_input(json.loads(args.replay.read_text()))
        result=recover_guided(request,encoder,**kwargs)
        print(json.dumps(asdict(result),indent=2))
    else:run(json.loads(args.config.read_text()),args.output,args.artifact_dir,args.resume)


if __name__=='__main__':main()
