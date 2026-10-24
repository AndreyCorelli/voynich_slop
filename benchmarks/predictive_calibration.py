"""Frozen six-case predictive calibration; prepare by default, solve by explicit case."""
import argparse
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

from benchmarks.frozen_key_holdout import score
from benchmarks.german_regional_audit import normalized_v2
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.historical_word_lengths import source
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import generate_encoder,generate_ciphertext,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

ROOT=Path('data/generated/predictive-calibration')
OUT=Path('experiments/results/predictive-calibration')
PROTOCOL=Path('experiments/configs/predictive-calibration.json')


def first_run(records,size=52,dictionary=None,same_folio=False):
    run=[]
    for i,r in enumerate(records):
        word=tuple(r['tokens'])
        if not word or (dictionary is not None and word not in dictionary):run=[];continue
        if same_folio and run and r['folio']!=records[run[-1]]['folio']:run=[]
        run.append(i)
        if len(run)==size:return Text(tuple(tuple(records[k]['tokens']) for k in run)),run
    raise ValueError('No eligible fixed-size passage')


def german_stream():
    source('german-corpus.tar.xz')
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        raw=archive.extractfile('XML/123.xml').read()
    root=ET.fromstring(raw);records=[]
    def walk(node):
        if node.tag in {'bibliographie','annotation'}:return
        if node.tag in {'eingriff','ueberschrift'}:records.append({'tokens':[]});return
        if node.tag=='wortform':
            for mi,m in enumerate(node.findall('morph')):
                raw_form=''.join(m.itertext());words,_=normalized_v2(raw_form)
                if not words:records.append({'tokens':[]});continue
                for word in words:records.append({'tokens':list(word),'word_number':node.get('nr'),
                    'morph_index':mi,'raw_form':raw_form})
            return
        for child in node:walk(child)
    walk(root)
    return records,hashlib.sha256(raw).hexdigest()


def prepare():
    protocol=json.loads(PROTOCOL.read_text())
    if protocol['train_words']!=30 or protocol['holdout_words']!=22:raise ValueError('Fixed 30+22 protocol required')
    latin_path=Path('data/generated/clean-latin-voynich/inputs/words-23.json')
    german_path=Path('data/generated/german-regional-audit/budget-1800000ms/inputs/123-full-30.json')
    templates={name:HiddenRecoveryRequest.from_dict(json.loads(p.read_text())['request'])
               for name,p in [('latin',latin_path),('swabian',german_path)]}
    if templates['latin'].ciphertext_alphabet!=templates['swabian'].ciphertext_alphabet:
        raise ValueError('Same cipher alphabet required')
    voynich=json.loads(Path('data/processed/zl-eva.json').read_text())
    text,indices=first_run(voynich['records'],same_folio=True)
    shuffled,metadata=typewise_shuffle(text,protocol['shuffle_seed'])
    caesar=json.loads(Path('data/processed/caesar-latin-v2.json').read_text())
    german,xml_hash=german_stream()
    sources={'latin':caesar['records'],'swabian':german}
    manifest={'protocol':protocol,'protocol_sha256':digest(protocol),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'voynich_corpus_sha256':digest(voynich),'caesar_corpus_sha256':digest(caesar),
        'german_xml_sha256':xml_hash,'voynich_record_indices':indices,
        'voynich_records':[voynich['records'][i] for i in indices],
        'shuffle_generator':metadata,'cases':[]}
    for language,base in templates.items():
        if base.bounds.max_homophones!=2 or (base.bounds.min_code_length,base.bounds.max_code_length)!=(1,3):
            raise ValueError('Fixed H2/L1–3 model required')
        plain,pi=first_run(sources[language],dictionary=set(base.dictionary.words))
        encoder=generate_encoder(base.plaintext_alphabet,base.ciphertext_alphabet,base.bounds,protocol['key_seed'])
        synthetic,choices=generate_ciphertext(plain,encoder,protocol['choice_seed'])
        for kind,cipher in [('synthetic',synthetic),('voynich',text),('shuffle',shuffled)]:
            name=f'{language}-{kind}';train=Text(cipher.words[:30]);held=Text(cipher.words[30:])
            q=replace(base,ciphertext=train,selection=HomophoneSelection('free'),timeout_ms=protocol['fit_budget_ms'],max_word_length=None)
            public={'request':asdict(q),'codeword_domains':'observed'}
            inp=ROOT/'inputs'/f'{name}.json';hp=ROOT/'holdouts'/f'{name}.json'
            holdout={'ciphertext':asdict(held)};write_json(inp,public);write_json(hp,holdout)
            entry={'id':name,'language':language,'kind':kind,'public_input':str(inp),'input_sha256':digest(public),
                'holdout':str(hp),'holdout_sha256':digest(holdout),'train_glyphs':train.size,'holdout_glyphs':held.size,
                'dictionary_sha256':digest(asdict(q.dictionary))}
            if kind=='synthetic':
                truth={'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,
                    'source_record_indices':pi,'source_records':[sources[language][i] for i in pi]}
                verify(q,{'status':'SAT','verified':True,'encoder':truth['encoder'],
                    'plaintext':asdict(Text(plain.words[:30])),'choices':choices[:sum(map(len,plain.words[:30]))],'nulls':[]})
                if encoder.decode(held)!=Text(plain.words[30:]):raise RuntimeError('Generating holdout decode failed')
                generating_score=score(held,encoder,q.dictionary,train.words)
                if generating_score['dictionary_words']!=22:raise RuntimeError('Generating holdout dictionary check failed')
                tp=ROOT/'truth'/f'{name}.json';write_json(tp,truth)
                entry.update(truth_path=str(tp),truth_sha256=digest(truth),generating_holdout_score=generating_score)
            manifest['cases'].append(entry)
    write_json(OUT/'prepared.json',manifest)
    print('Prepared six cases; generating synthetic keys decode all 22 held-out words.',flush=True)
    return manifest


def run_case(name,budget_ms=None):
    manifest=prepare();entry=next((e for e in manifest['cases'] if e['id']==name),None)
    if entry is None:raise ValueError('Unknown fixed case')
    budget=budget_ms or manifest['protocol']['fit_budget_ms']
    output=OUT/f'{name}-{budget}ms.json'
    if output.exists():raise ValueError('Result already exists; preserve it rather than silently rerun')
    payload=json.loads(Path(entry['public_input']).read_text())
    if digest(payload)!=entry['input_sha256']:raise ValueError('Training input changed')
    q=replace(HiddenRecoveryRequest.from_dict(payload['request']),timeout_ms=budget)
    print(f'{name}: fitting budget={budget}ms',flush=True)
    result=asdict(recover_observed_codes(q));verify(q,result)
    report={'case':entry,'protocol_sha256':manifest['protocol_sha256'],'effective_request_sha256':digest(asdict(q)),
        'fit_budget_ms':budget,'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT',
        'semantics':'UNKNOWN is unresolved, not failed prediction. Frozen recovered encoder evaluated only after independently verified SAT; no use of generating truth during recovery.'}
    if result['status']=='SAT':
        encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
        hold=json.loads(Path(entry['holdout']).read_text())
        if digest(hold)!=entry['holdout_sha256']:raise ValueError('Holdout changed')
        report['holdout_score']=score(Text(tuple(map(tuple,hold['ciphertext']['words']))),encoder,q.dictionary,q.ciphertext.words)
        report['frozen_encoder_sha256']=digest(asdict(encoder));report['evaluation_status']='EVALUATED_FROZEN_KEY'
        if entry['kind']=='synthetic':
            report['predictive_gate_passed']=(report['holdout_score']['fully_decoded_words']>=manifest['protocol']['gate_fully_decoded_words']
                and report['holdout_score']['dictionary_words']>=manifest['protocol']['gate_dictionary_words'])
    write_json(output,report)
    print(result['status'],f"solver={result['runtime_seconds']:.2f}s",report['evaluation_status'],flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=[f'{l}-{k}' for l in ('latin','swabian') for k in ('synthetic','voynich','shuffle')])
    parser.add_argument('--timeout-ms',type=int)
    args=parser.parse_args()
    if args.timeout_ms is not None and (args.timeout_ms<=0 or not args.case):parser.error('Positive timeout requires --case')
    if args.case:run_case(args.case,args.timeout_ms)
    else:prepare()
