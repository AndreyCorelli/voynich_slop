"""Nested contiguous Voynich prefixes under one fixed vocabulary and cipher model."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
from time import perf_counter

import z3

from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import Corpus, digest, statistics, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


def clean_run(corpus, length, exclude_uncertain_spaces=True):
    """Find the earliest uninterrupted paragraph run within one folio."""
    start, folio = None, None
    for i, record in enumerate(corpus.records):
        locator = record.get('locus','').partition(',')[2]
        good = (bool(record['tokens']) and locator[1:].startswith('P')
                and all(len(g)==1 and g.isascii() and g.islower() for g in record['tokens'])
                and (not exclude_uncertain_spaces or not record.get('uncertain_space_in_locus',False)))
        if not good or record.get('folio') != folio:
            start = None
        if good:
            if start is None:
                start = i
            folio = record.get('folio')
            if i-start+1 == length:
                return start
    raise ValueError('No sufficiently long uninterrupted clean paragraph run on a single folio')


def sample_at(corpus, start, size):
    records = corpus.records[start:start+size]
    if len(records)!=size or any(not r['tokens'] for r in records):
        raise ValueError('Sample contains missing or excluded words')
    text=Text(tuple(tuple(r['tokens']) for r in records))
    metadata={'corpus_sha256':corpus.identity,'source':corpus.source,'normalization':corpus.normalization,
              'record_indices':list(range(start,start+size)),
              'locations':[{k:r.get(k) for k in ('folio','locus','physical_line','word_in_locus','section')} for r in records],
              'selection':{'strategy':'prefix of one uninterrupted clean paragraph run','start_record':start,'words':size},
              'text':asdict(text)}
    metadata['sample_sha256']=digest(metadata)
    return text,metadata


def validate(config):
    fields={'voynich','latin','sizes','sample','single_letter_words','bounds','selection','timeout_ms'}
    if not isinstance(config,dict) or set(config)!=fields:
        raise ValueError('Invalid scaling configuration fields')
    sizes=config['sizes']
    if (not isinstance(sizes,list) or not sizes or any(type(n) is not int or n<1 for n in sizes)
            or sizes!=sorted(set(sizes))):
        raise ValueError('Sample sizes must be unique positive integers in increasing order')
    if type(config['timeout_ms']) is not int or config['timeout_ms']<=0:
        raise ValueError('Timeout must be a positive integer')
    if (not isinstance(config['sample'],dict)
            or config['sample'].get('strategy')!='first-clean-paragraph-run'
            or set(config['sample'])!={'strategy','exclude_uncertain_spaces'}
            or type(config['sample']['exclude_uncertain_spaces']) is not bool):
        raise ValueError('Invalid contiguous sample selection')
    whitelist=config['single_letter_words']
    if (not isinstance(whitelist,list) or any(not isinstance(s,str) or len(s)!=1 for s in whitelist)
            or len(set(whitelist))!=len(whitelist)):
        raise ValueError('Invalid single-letter whitelist')
    if (not isinstance(config['bounds'],dict) or set(config['bounds'])!=set(Bounds.__dataclass_fields__)
            or any(type(config['bounds'][k]) is not int for k in
                   ('max_homophones','min_code_length','max_code_length'))):
        raise ValueError('Invalid cipher bounds')
    if (not isinstance(config['selection'],dict)
            or config['selection'].keys()-HomophoneSelection.__dataclass_fields__.keys()):
        raise ValueError('Invalid homophone selection')
    Bounds(**config['bounds']);HomophoneSelection(**config['selection'])


def run(config, output, artifacts, resume=False):
    validate(config)
    latin,voynich=Corpus.load(config['latin']),Corpus.load(config['voynich'])
    vocabulary=[];seen=set()
    for record in latin.records:
        word=tuple(record['tokens'])
        if not word or (len(word)==1 and word[0] not in config['single_letter_words']):
            continue
        if word not in seen:
            vocabulary.append(word);seen.add(word)
    dictionary=WordDictionary(tuple(vocabulary))
    plain=Alphabet(tuple(latin.normalization['alphabet']))
    cipher=Alphabet(tuple(sorted({g for r in voynich.records for g in r['tokens']})))
    bounds,selection=Bounds(**config['bounds']),HomophoneSelection(**config['selection'])
    start=clean_run(voynich,max(config['sizes']),config['sample']['exclude_uncertain_spaces'])
    maximum,maximum_metadata=sample_at(voynich,start,max(config['sizes']))
    fixed={'plaintext_alphabet':asdict(plain),'ciphertext_alphabet':asdict(cipher),'bounds':asdict(bounds),
           'selection':asdict(selection),'dictionary_sha256':digest(dictionary.words),
           'dictionary_entries':len(dictionary.words),'timeout_ms':config['timeout_ms'],
           'nulls':False,'contextual_codes':False,'objective':'feasibility'}
    report={'schema_version':1,'config':config,'config_sha256':digest(config),
            'environment':{'python':platform.python_version(),'z3':z3.get_version_string(),'platform':platform.platform()},
            'fixed_model':fixed,'fixed_model_sha256':digest(fixed),'latin_corpus_sha256':latin.identity,
            'maximum_sample':maximum_metadata,'experiments':[],'complete':False,
            'interpretation':'Word count alone varies. Dictionary membership is not Latin grammar; UNKNOWN is inconclusive.'}
    if resume and output.exists():
        prior=json.loads(output.read_text())
        for field in ('config_sha256','fixed_model_sha256','latin_corpus_sha256','maximum_sample','environment'):
            if digest(prior.get(field))!=digest(report[field]):
                raise ValueError('Resume requires the same configuration, model, corpora, span and environment')
        report['experiments']=prior['experiments']
    write_json(artifacts/'samples'/'maximum.json',maximum_metadata)
    write_json(output,report)
    for size in config['sizes']:
        if any(e['word_count']==size for e in report['experiments']):
            continue
        ciphertext,metadata=sample_at(voynich,start,size)
        assert ciphertext.words==maximum.words[:size]
        request=HiddenRecoveryRequest(ciphertext,plain,cipher,bounds,dictionary,
                                      timeout_ms=config['timeout_ms'],selection=selection)
        path=artifacts/'inputs'/f'words{size}.json'
        write_json(path,asdict(request))
        write_json(artifacts/'samples'/f'words{size}.json',metadata)
        request=HiddenRecoveryRequest.from_dict(json.loads(path.read_text()))
        print(f'words={size} tokens={ciphertext.size} folio={metadata["locations"][0]["folio"]}: constructing/checking',flush=True)
        started=perf_counter();result=request.solve();wall=perf_counter()-started
        report['experiments'].append({'dataset':f'voynich-words{size}','word_count':size,
              'ciphertext_sha256':digest(asdict(ciphertext)),'sample_metadata':metadata,'public_input':str(path),
              'request_sha256':digest(asdict(request)),'fixed_model_sha256':report['fixed_model_sha256'],
              'statistics':statistics(ciphertext),'wall_seconds':wall,'result':asdict(result)})
        write_json(output,report)
        print(f'  {result.status} check={result.runtime_seconds:.3f}s construction={result.capacity["construction_seconds"]:.3f}s wall={wall:.3f}s',flush=True)
    report['complete']=True
    write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path('experiments/configs/sample-scaling.json'))
    parser.add_argument('--output',type=Path,default=Path('experiments/results/sample-scaling.json'))
    parser.add_argument('--artifact-dir',type=Path,default=Path('data/generated/sample-scaling'))
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    try:
        run(json.loads(args.config.read_text()),args.output,args.artifact_dir,args.resume)
    except (ValueError,TypeError,KeyError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
