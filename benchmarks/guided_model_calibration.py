"""Fixed cross-profile, guided versus ordinary synthetic calibration matrix."""
import argparse
from collections import Counter
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import random
import time

from benchmarks.corpus_sequence_selection import train_model, sequence_score
from benchmarks.coverage_sequence_selection import alternating_choices
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.l3_conflict import verify
from benchmarks.predictive_calibration import german_stream
from benchmarks.tiny_key_ambiguity import used_mappings
from benchmarks.frozen_key_holdout import score
from voynich_smt.cipher.base import Bounds, Encoder, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import tokenizations, tokenize_dictionary, expand_units
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

CONFIG=Path('experiments/configs/guided-model-calibration.json')
OUT=Path('experiments/results/guided-model-calibration')


def shortest(word,rules):
    return min(tokenizations(word,rules),key=lambda p:(len(p),p))


def expanded(words,rules):
    return [expand_units(w,rules) for w in words]


def training_score(words,model,rules):
    return sequence_score(expanded(words,rules),model)


def covered_records(evaluation,start,rules,config):
    for n in range(config['minimum_train_words'],config['maximum_train_words']+1):
        train=evaluation[start:start+n];held=evaluation[start+n:start+n+config['holdout_words']]
        if len(held)!=config['holdout_words']:break
        # Same source block for both generation profiles; both must cover true held units.
        valid=True
        for active in ([],rules):
            counts=Counter(s for _,w in train for s in shortest(w,active))
            if any(counts[s]<2 for _,w in held for s in shortest(w,active)):valid=False
        # Require contraction use in training; continuation activity is reported separately.
        if not any(any(len(s)>1 for s in shortest(w,rules)) for _,w in train):valid=False
        if valid:return train,held
    raise ValueError('No fixed coverage/contraction-eligible block; do not broaden automatically')


def code_identity():
    paths=[Path(__file__),Path('src/voynich_smt/solver/recovery.py'),
           Path('src/voynich_smt/language/contractions.py'),
           Path('benchmarks/corpus_sequence_selection.py'),Path('benchmarks/predictive_calibration.py')]
    return {str(p):digest(p.read_text()) for p in paths}


def prepare():
    config=json.loads(CONFIG.read_text());latin=json.loads(Path('data/processed/caesar-latin-v2.json').read_text())
    german,xml_hash=german_stream()
    sources={'latin':latin['records'],'swabian':german}
    identity={'config':digest(config),'code':code_identity(),'latin':digest(latin),'swabian_xml':xml_hash}
    output=OUT/'prepared.json'
    if output.exists():
        saved=json.loads(output.read_text())
        if saved['identity']!=identity:raise ValueError('Prepared source/config/code changed')
        return saved
    protocol={'config':config,'identity':identity,'scope':config['limitations']}
    write_json(OUT/'protocol.json',protocol)
    models={};vocabularies={};splits={}
    # Freeze both language scores before generating evaluation cases.
    for language,records in sources.items():
        split=len(records)//2;splits[language]=split
        words=[''.join(r['tokens']) for r in records[:split] if r['tokens']]
        counts=Counter(w for w in words if len(w)<=config['max_word_spelling_length'])
        vocabulary=sorted(sorted(counts,key=lambda w:(-counts[w],w))[:config['vocabulary_size']])
        vocabularies[language]=vocabulary
        models[language]=train_model([w for w in words if w in vocabulary],vocabulary)
    write_json(OUT/'reference.json',{'models':models,'vocabularies':vocabularies,'splits':splits,'identity':identity})
    cases=[]
    for language,records in sources.items():
        rules=config['rules'][language];vocabulary=vocabularies[language]
        evaluation=[(i,''.join(r['tokens'])) for i,r in enumerate(records)
            if i>=splits[language] and ''.join(r['tokens']) in vocabulary]
        train_records,held_records=covered_records(evaluation,config[language+'_start_projected_offset'],rules,config)
        for profile in config['profiles']:
            active=rules if profile=='mixed' else []
            dictionary=WordDictionary(tokenize_dictionary(vocabulary,active))
            alphabet=Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
            ca=Alphabet(tuple('uvwxyz'));bounds=Bounds('verbose',2,1,3)
            codes=list(itertools.product(ca.symbols,repeat=2));random.Random(config['key_seed']).shuffle(codes)
            if 2*len(alphabet.symbols)>len(codes):raise ValueError('Fixed alphabet capacity insufficient')
            encoder=Encoder({s:tuple(codes[2*i:2*i+2]) for i,s in enumerate(alphabet.symbols)})
            plain=Text(tuple(shortest(w,active) for _,w in train_records))
            held_plain=Text(tuple(shortest(w,active) for _,w in held_records))
            choices=alternating_choices(plain);train=encoder.encode(plain,choices)
            held,held_choices=generate_ciphertext(held_plain,encoder,config['holdout_choice_seed'])
            truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':choices,'nulls':[]}
            seen={tuple(m['code']) for m in used_mappings(truth)}
            if not all(tuple(w[i:i+2]) in seen for w in held.words for i in range(0,len(w),2)):raise RuntimeError('Coverage failure')
            if encoder.decode(held)!=held_plain:raise RuntimeError('Generating decode failure')
            full=Text(train.words+held.words);shuffled,metadata=typewise_shuffle(full,config['shuffle_seed'])
            for kind,text in [('synthetic',full),('shuffle',shuffled)]:
                q=HiddenRecoveryRequest(Text(text.words[:len(train.words)]),alphabet,ca,bounds,dictionary,timeout_ms=5000)
                if kind=='synthetic':verify(q,truth)
                case={'id':f'{language}-{profile}-{kind}','language':language,'generation_profile':profile,
                    'kind':kind,'ciphertext':asdict(q.ciphertext),'holdout':asdict(Text(text.words[len(train.words):])),
                    'ciphertext_alphabet':asdict(ca),'bounds':asdict(bounds),
                    'training_record_indices':[i for i,_ in train_records],'holdout_record_indices':[i for i,_ in held_records]}
                if kind=='synthetic':case.update(truth=truth,holdout_plaintext=asdict(held_plain),holdout_choices=held_choices,
                    generating_rules=active,generating_covered_holdout_words=4)
                else:case['shuffle']=metadata
                cases.append(case)
    prepared={'identity':identity,'config':config,'models':models,'vocabularies':vocabularies,'splits':splits,'cases':cases}
    write_json(output,prepared);return prepared


def request_for(case,profile,prepared):
    rules=prepared['config']['rules'][case['language']] if profile=='mixed' else []
    dictionary=WordDictionary(tokenize_dictionary(prepared['vocabularies'][case['language']],rules))
    alphabet=Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
    q=HiddenRecoveryRequest(Text(tuple(tuple(w) for w in case['ciphertext']['words'])),alphabet,
        Alphabet(tuple(case['ciphertext_alphabet']['symbols'])),Bounds(**case['bounds']),dictionary,timeout_ms=5000)
    return q,rules


def proposals(q,model,rules,width,limit):
    """Training-only beam over publicly feasible dictionary words and prefix relations."""
    graph=q.dictionary.candidate_graph(q.ciphertext,q.bounds,1,max(map(len,q.dictionary.words)))
    beam=[()]
    for wi,words in enumerate(graph.candidates):
        options=[]
        for prefix in beam:
            for word in words:
                if all(rel.accepts(prefix[rel.left],word) for rel in graph.relations if rel.right==wi):
                    path=prefix+(word,);options.append(path)
        beam=sorted(options,key=lambda p:(-training_score(p,model,rules),p))[:width]
        if not beam:break
    return [Text(p) for p in beam[:limit]]


def evaluate(result,case,q,rules):
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
    held=Text(tuple(tuple(w) for w in case['holdout']['words']))
    prediction=score(held,encoder,q.dictionary,q.ciphertext.words)
    spellings=expanded(result['plaintext']['words'],rules)
    for row in prediction['word_results']:
        row['expanded_word']=expand_units(row['decoded_prefix'],rules) if row['fully_decoded'] else None
    expanded_vocab={expand_units(w,rules) for w in q.dictionary.words}
    dictionary_hits=sum(row['fully_decoded'] and row['expanded_word'] in expanded_vocab for row in prediction['word_results'])
    novel_hits=sum(row['fully_decoded'] and not row['seen_in_training'] and row['expanded_word'] in expanded_vocab for row in prediction['word_results'])
    evaluation={'prediction':prediction,'expanded_training_words':spellings,
        'expanded_dictionary_words':dictionary_hits,'novel_expanded_dictionary_words':novel_hits}
    if case['kind']=='synthetic':
        truth=expanded(case['holdout_plaintext']['words'],case['generating_rules'])
        exact=[row['fully_decoded'] and row['expanded_word']==w for row,w in zip(prediction['word_results'],truth)]
        evaluation.update(exact_words=sum(exact),novel_exact_words=sum(ok and not row['seen_in_training'] for ok,row in zip(exact,prediction['word_results'])))
    return evaluation


def run_case(name):
    prepared=prepare();config=prepared['config'];case=next(c for c in prepared['cases'] if c['id']==name)
    output=OUT/(name+'.json')
    if output.exists():
        report=json.loads(output.read_text())
        if report['prepared_sha256']!=digest(prepared):raise ValueError('Saved report changed')
    else:report={'case_id':name,'prepared_sha256':digest(prepared),'arms':[],'complete':False}
    for profile in config['profiles']:
        q,rules=request_for(case,profile,prepared);model=prepared['models'][case['language']]
        for method in config['methods']:
            arm_id=profile+'-'+method
            if any(a['id']==arm_id for a in report['arms']):continue
            print(name,arm_id,flush=True)
            started=time.perf_counter()
            proposed=proposals(q,model,rules,config['beam_width'],config['max_attempts']) if method=='guided' else []
            proposal_seconds=time.perf_counter()-started
            attempts=[];fits=[];exclusions=[];remaining=config['total_solver_budget_ms_per_arm'];stop='ATTEMPT_CAP'
            for index in range(config['max_attempts']):
                if remaining<=0:stop='BUDGET_EXHAUSTED';break
                if method=='guided' and index>=len(proposed):stop='PROPOSAL_EXHAUSTED';break
                result=asdict(_recover(proposed[index] if method=='guided' else None,q.ciphertext,q.plaintext_alphabet,
                    q.ciphertext_alphabet,q.bounds,remaining,dictionary=q.dictionary if method=='ordinary' else None,
                    max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed',key_exclusions=tuple(exclusions)))
                remaining-=max(1,int(result['runtime_seconds']*1000+0.999))
                verify(q,result);attempts.append({'result':result,'timeout_ms':max(1,remaining+max(1,int(result['runtime_seconds']*1000+0.999)))})
                print(result['status'],f"{result['runtime_seconds']:.2f}s",flush=True)
                if result['status']=='SAT':
                    fits.append({'result':result,'training_score':training_score(result['plaintext']['words'],model,rules)})
                    if method=='ordinary':exclusions.append({'kind':'word','segments':used_mappings(result)})
                elif result['status']=='UNKNOWN':stop='UNKNOWN';break
                elif method=='ordinary':stop='UNSAT';break
            # Guided UNSAT rejects proposals only, never the whole dictionary hypothesis.
            selected=max(range(len(fits)),key=lambda i:fits[i]['training_score']) if fits else None
            arm={'id':arm_id,'method':method,'recovery_profile':profile,'request':asdict(q),
                 'proposals':[asdict(p) for p in proposed],'proposal_seconds':proposal_seconds,
                 'attempts':attempts,'fits':fits,'selected_index':selected,'stop_reason':stop,
                 'total_solver_seconds':sum(a['result']['runtime_seconds'] for a in attempts),
                 'overall_unsat_proven':method=='ordinary' and bool(attempts) and attempts[0]['result']['status']=='UNSAT',
                 'evaluation_status':'EVALUATED_FROZEN_KEYS' if fits else 'NOT_EVALUATED_NO_SAT'}
            for fit in fits:fit.update(evaluate(fit['result'],case,q,rules))
            report['arms'].append(arm);write_json(output,report)
    report['complete']=True;write_json(output,report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case');parser.add_argument('--run-all',action='store_true')
    args=parser.parse_args()
    if args.case and args.run_all:parser.error('Choose one case or --run-all')
    if args.case:run_case(args.case)
    elif args.run_all:
        for case in prepare()['cases']:run_case(case['id'])
    else:
        p=prepare();print('Prepared eight cases, four arms each; use --case ID or --run-all. Five-second total solver budget per arm.')
