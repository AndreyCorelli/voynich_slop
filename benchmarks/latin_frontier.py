"""One-dimension Latin vocabulary/cipher relaxations with paired selection rules."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import random

import z3

from voynich_smt.cipher.base import Bounds, Encoder, generate_encoder
from voynich_smt.cipher.selection import accepts, choose
from voynich_smt.data.controls import control
from voynich_smt.data.corpus import Corpus, digest, statistics, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text


def validate(config):
    keys = {'voynich','latin','sample','synthetic_seeds','control_seed','controls','timeout_ms','selection_policies','stages'}
    if not isinstance(config,dict) or not keys <= config.keys() or config.keys() - keys - {'single_letter_words'}:
        raise ValueError('Invalid frontier configuration fields')
    if 'single_letter_words' in config and (
        not isinstance(config['single_letter_words'],list)
        or any(not isinstance(w,str) or len(w)!=1 for w in config['single_letter_words'])
        or len(set(config['single_letter_words'])) != len(config['single_letter_words'])
    ):
        raise ValueError('Single-letter whitelist must contain unique character strings')
    if type(config['timeout_ms']) is not int or config['timeout_ms'] <= 0:
        raise ValueError('Timeout must be positive')
    if type(config['control_seed']) is not int:
        raise ValueError('Control seed must be an integer')
    if (not isinstance(config['sample'],dict) or 'words' not in config['sample']
            or config['sample'].keys() - {'words','offset','seed','folio','section','line','max_tokens'}
            or type(config['sample']['words']) is not int or config['sample']['words']<=0):
        raise ValueError('Invalid sample selection')
    kinds={'word-shuffle','within-word-shuffle','frequency-shuffle','uniform','prefix-stem-suffix'}
    if (not isinstance(config['controls'],list) or any(not isinstance(k,str) or k not in kinds for k in config['controls'])
            or len(set(config['controls'])) != len(config['controls'])):
        raise ValueError('Controls must be supported unique names')
    if not config['synthetic_seeds'] or any(type(s) is not int for s in config['synthetic_seeds']):
        raise ValueError('Synthetic seeds must be nonempty integers')
    if len(set(config['synthetic_seeds'])) != len(config['synthetic_seeds']):
        raise ValueError('Synthetic seeds must be unique')
    if not config['selection_policies'] or len({digest(p) for p in config['selection_policies']}) != len(config['selection_policies']):
        raise ValueError('Selection policies must be nonempty and unique')
    for policy in config['selection_policies']:
        HomophoneSelection(**policy)
    if not config['stages'] or len({s['name'] for s in config['stages']}) != len(config['stages']):
        raise ValueError('Stages must be nonempty and uniquely named')
    previous = None
    for stage in config['stages']:
        if set(stage) != {'name','vocabulary_size','max_homophones','max_code_length'}:
            raise ValueError('Invalid stage fields')
        size = stage['vocabulary_size']
        if size != 'all' and (type(size) is not int or size <= 0):
            raise ValueError('Vocabulary size must be positive or all')
        if any(type(stage[k]) is not int or stage[k] < 1 for k in ('max_homophones','max_code_length')):
            raise ValueError('Cipher bounds must be positive integers')
        if previous:
            changed = [k for k in ('vocabulary_size','max_homophones','max_code_length') if stage[k] != previous[k]]
            if len(changed) != 1:
                raise ValueError('Consecutive stages must change exactly one dimension')
            key = changed[0]
            old, new = previous[key], stage[key]
            if old == 'all' or (new != 'all' and new <= old):
                raise ValueError('Stages must monotonically relax one dimension')
        previous = stage


def certify_existing_witnesses(report):
    """A timeout in a broader model does not erase a verified narrower witness."""
    witnesses = {}
    for stage in report['stages']:
        for policy in stage['policies']:
            for experiment in policy['experiments']:
                key = (digest(policy['selection']), experiment['dataset'], experiment['ciphertext_sha256'])
                result = experiment['result']
                if result['status']=='SAT' and result['verified']:
                    witnesses[key] = (stage['name'], experiment)
                    continue
                if key not in witnesses:
                    continue
                name, previous = witnesses[key]
                request = HiddenRecoveryRequest.from_dict(json.loads(Path(experiment['public_input']).read_text()))
                old = previous['result']
                encoder = Encoder({s:tuple(tuple(c) for c in codes) for s,codes in old['encoder']['codebook'].items()},
                                  tuple(old['encoder'].get('null_symbols',())))
                plaintext = Text(tuple(tuple(w) for w in old['plaintext']['words']))
                choices = tuple(old['choices'])
                valid = (not encoder.null_symbols and not old.get('nulls')
                         and set(encoder.codebook)==set(request.plaintext_alphabet.symbols)
                         and request.dictionary.accepts(plaintext)
                         and all(request.min_word_length<=len(w)<=
                                 (request.max_word_length or max(map(len,request.dictionary.words)))
                                 for w in plaintext.words)
                         and all(1<=len(codes)<=request.bounds.max_homophones and all(
                             request.bounds.min_code_length<=len(code)<=request.bounds.max_code_length
                             and all(g in request.ciphertext_alphabet.symbols for g in code) for code in codes)
                             for codes in encoder.codebook.values())
                         and encoder.encode(plaintext,choices)==request.ciphertext
                         and encoder.decode(request.ciphertext)==plaintext
                         and accepts(plaintext,encoder,choices,request.selection))
                if valid:
                    if result['status']=='UNSAT':
                        raise RuntimeError('UNSAT conflicts with an independently verified prior witness')
                    experiment['inherited_feasibility'] = {
                        'status':'SAT','verified':True,'source_stage':name,
                        'source_public_input':previous['public_input'],
                        'method':'prior explanation independently checked against this request',
                        'solver_status_unchanged':result['status']}


def run(config, output, artifacts, stage_names=None, resume=False):
    validate(config)
    latin, voynich = Corpus.load(config['latin']), Corpus.load(config['voynich'])
    observed, selection = voynich.sample(**config['sample'])
    if (any(p.get('mode')=='cycle' and p.get('reset','text')=='text' for p in config['selection_policies'])
            and any(b!=a+1 for a,b in zip(selection['record_indices'],selection['record_indices'][1:]))):
        raise ValueError('Text-wide cycles require uninterrupted source words; skipped words would change counter phases')
    vocabulary, seen = [], set()
    for record in latin.records:
        word = tuple(record['tokens'])
        if len(word)==1 and 'single_letter_words' in config and word[0] not in config['single_letter_words']:
            continue
        if word and word not in seen:
            vocabulary.append(word); seen.add(word)
    plain = Alphabet(tuple(latin.normalization['alphabet']))
    cipher = Alphabet(tuple(sorted({g for r in voynich.records for g in r['tokens']})))
    report = {'schema_version':1, 'config':config, 'config_sha256':digest(config),
              'environment':{'python':platform.python_version(),'z3':z3.get_version_string(),'platform':platform.platform()},
              'latin_corpus_sha256':latin.identity, 'latin_source':latin.source, 'voynich_selection':selection,
              'complete':False, 'stages':[],
              'assumptions':{'language':'finite corpus vocabulary, independent word membership',
                             'single_letter_words':config.get('single_letter_words','all corpus tokens'),
                             'prefix_free':True,'preserve_spaces':True,'tokenization':'eva-characters',
                             'nulls':False,'contextual_codes':False,'objective':'feasibility',
                             'synthetic_matching':'same bounds, alphabets, dictionary, word count; token lengths differ',
                             'cycle':'per-letter ordered codes, phase zero, counters continue across spaces'},
              'negative_interpretation':'A stage must pass every synthetic gate; even then UNSAT excludes only the specified model.'}
    if stage_names and not set(stage_names) <= {s['name'] for s in config['stages']}:
        raise ValueError('Unknown requested stages')
    if resume and output.exists():
        previous = json.loads(output.read_text())
        if any(digest(previous.get(k)) != digest(report[k]) for k in
               ('config_sha256','latin_corpus_sha256','voynich_selection','environment')):
            raise ValueError('Resume requires identical configuration, corpora, sample and environment')
        report['stages'] = [s for s in previous['stages'] if s.get('complete')]
    report['selected_stage_names'] = stage_names or [s['name'] for s in config['stages']]
    write_json(output,report)
    for stage in config['stages']:
        if stage_names and stage['name'] not in stage_names:
            continue
        if any(s['name'] == stage['name'] for s in report['stages']):
            continue
        size = len(vocabulary) if stage['vocabulary_size'] == 'all' else stage['vocabulary_size']
        if size > len(vocabulary):
            raise ValueError('Requested vocabulary exceeds acquired corpus')
        dictionary = WordDictionary(tuple(vocabulary[:size]))
        accepted = set(dictionary.words)
        # Choose corpus windows after an explicit vocabulary/length filter; never supply truth to recovery.
        eligible = [(i, tuple(r['tokens'])) for i,r in enumerate(latin.records)
                    if tuple(r['tokens']) in accepted and len(r['tokens']) <= 6]
        if len(eligible) < len(observed.words):
            raise ValueError('Insufficient eligible synthetic words')
        bounds = Bounds('verbose', stage['max_homophones'], 1, stage['max_code_length'])
        inputs = []
        for seed in config['synthetic_seeds']:
            offset = random.Random(seed).randrange(len(eligible) - len(observed.words) + 1)
            chosen = eligible[offset:offset + len(observed.words)]
            plaintext = Text(tuple(w for _,w in chosen))
            key = generate_encoder(plain,cipher,bounds,seed)
            choices = choose(plaintext,key,HomophoneSelection('cycle'))
            ciphertext = key.encode(plaintext,choices)
            assert key.decode(ciphertext) == plaintext
            identity = f'synthetic-seed{seed}'
            truth_path = artifacts/'ground_truth'/stage['name']/f'{identity}.json'
            metadata = {'seed':seed,'latin_record_indices':[i for i,_ in chosen],
                        'plaintext_selection':'seeded window after public vocabulary and length<=6 filter',
                        'generator_policy':{'mode':'cycle','reset':'text'}}
            write_json(truth_path, {'plaintext':asdict(plaintext),'encoder':asdict(key),'choices':choices,
                                   'metadata':metadata,'latin_corpus_sha256':latin.identity})
            inputs.append((identity,ciphertext,metadata))
        inputs.append(('voynich',observed,selection))
        for kind in config['controls']:
            text, metadata = control(observed,kind,config['control_seed'])
            inputs.append((kind,text,metadata))
        stage_report = {**stage, 'actual_vocabulary_size':size, 'dictionary_sha256':digest(dictionary.words),
                        'policies':[]}
        report['stages'].append(stage_report)
        order = {s['name']:i for i,s in enumerate(config['stages'])}
        report['stages'].sort(key=lambda s:order[s['name']])
        for raw_policy in config['selection_policies']:
            policy = HomophoneSelection(**raw_policy)
            policy_report = {'selection':asdict(policy),'experiments':[], 'synthetic_gate_passed':False}
            stage_report['policies'].append(policy_report)
            for identity,ciphertext,metadata in inputs:
                request = HiddenRecoveryRequest(ciphertext,plain,cipher,bounds,dictionary,
                          timeout_ms=config['timeout_ms'],selection=policy)
                path = artifacts/'inputs'/stage['name']/f'{policy.mode}-{policy.reset}-{identity}.json'
                write_json(path,asdict(request))
                request = HiddenRecoveryRequest.from_dict(json.loads(path.read_text()))
                print(f'{stage["name"]} {policy.mode} {identity}: constructing/checking', flush=True)
                result = request.solve()
                policy_report['experiments'].append({'dataset':identity,'ciphertext_sha256':digest(asdict(ciphertext)),
                       'public_input':str(path),'sample_metadata':metadata,'statistics':statistics(ciphertext),
                       'result':asdict(result)})
                gates = [e['result'] for e in policy_report['experiments'] if e['dataset'].startswith('synthetic-')]
                policy_report['synthetic_gate_passed'] = (len(gates)==len(config['synthetic_seeds']) and
                                                           all(r['status']=='SAT' and r['verified'] for r in gates))
                write_json(output,report)
                print(f'  {result.status} {result.runtime_seconds:.3f}s; construction={result.capacity["construction_seconds"]:.3f}s',flush=True)
        stage_report['complete'] = True
    report['complete'] = True
    certify_existing_witnesses(report)
    write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path('experiments/configs/latin-frontier.json'))
    parser.add_argument('--output',type=Path,default=Path('experiments/results/latin-frontier.json'))
    parser.add_argument('--artifact-dir',type=Path,default=Path('data/generated/latin-frontier'))
    parser.add_argument('--stages',nargs='+')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    try:
        run(json.loads(args.config.read_text()),args.output,args.artifact_dir,args.stages,args.resume)
    except (ValueError,TypeError,KeyError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
