"""Fixed contiguous Latin/Swabian passages, known/hidden recovery and paired shuffles."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter

from benchmarks.predictive_calibration import german_stream
from benchmarks.small_varied_length_controls import key
from benchmarks.varied_length_vocabulary_ladder import vocabularies
from benchmarks.full_vocabulary_h1_known import solve as known_solve
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.structured_negative_controls import diagnostics
from benchmarks.varied_length_shuffle_controls import prediction as control_prediction
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/natural-passage-calibration')
LATIN=Path('data/processed/caesar-latin-v2.json')
TEMPLATES={'latin':Path('data/generated/clean-latin-voynich/inputs/words-23.json'),
           'swabian':Path('data/generated/german-regional-audit/budget-1800000ms/inputs/123-full-30.json')}
TRAIN=24
HELD=6
PROFILES=('fixed-two','mixed-one-two-three')
KEY_SEED=4501
SHUFFLE_SEED=4502


def select_passage(records,allowed):
    for start in range(len(records)//2,len(records)-TRAIN-HELD+1):
        block=records[start:start+TRAIN+HELD];words=tuple(tuple(r['tokens']) for r in block)
        if any(not w or w not in allowed or r.get('excluded_reason') is not None for w,r in zip(words,block)):continue
        train,held=words[:TRAIN],words[TRAIN:]
        if len(set(held)-set(train))<3:continue
        if {s for w in held for s in w}-{s for w in train for s in w}:continue
        return start,Text(train),Text(held),block
    raise ValueError('No eligible contiguous passage; do not project or broaden')


def load_sources():
    latin=json.loads(LATIN.read_text());german,xml_hash=german_stream()
    records={'latin':latin['records'],'swabian':german}
    records={lang:[dict(r,excluded_reason=r.get('excluded_reason')) for r in rs] for lang,rs in records.items()}
    templates={lang:json.loads(path.read_text()) for lang,path in TEMPLATES.items()}
    return records,templates,{'latin_sha256':digest(latin),'german_xml_sha256':xml_hash,
        'record_stream_sha256':{lang:digest(rs) for lang,rs in records.items()},'template_sha256':{lang:digest(t) for lang,t in templates.items()}}


def prepare():
    records,templates,sources=load_sources()
    code_paths=(Path(__file__),Path('benchmarks/predictive_calibration.py'),Path('benchmarks/german_regional_audit.py'),
        Path('benchmarks/german_selection.py'),Path('benchmarks/historical_word_lengths.py'),
        Path('benchmarks/small_varied_length_controls.py'),Path('benchmarks/varied_length_vocabulary_ladder.py'),
        Path('benchmarks/german_shuffle_controls.py'),Path('benchmarks/structured_negative_controls.py'),
        Path('benchmarks/varied_length_shuffle_controls.py'),Path('benchmarks/public_length_calibration.py'),
        Path('benchmarks/full_vocabulary_h1_known.py'),Path('benchmarks/frozen_key_holdout.py'),
        Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/observed_codes.py'),
        Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'))
    identity={'sources':sources,'code_sha256':{str(p):digest(p.read_text()) for p in code_paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources or implementation changed')
        return p
    passages={};cases=[];unavailable=[]
    for lang,stream in records.items():
        allowed=set(tuple(w) for w in templates[lang]['request']['dictionary']['words'])
        start,plain,held_plain,block=select_passage(stream,allowed)
        alphabet=Alphabet(tuple(sorted({s for w in plain.words+held_plain.words for s in w})))
        base=WordDictionary(tuple(sorted(set(plain.words+held_plain.words))))
        dictionaries,provenance=vocabularies(base,alphabet,stream,(64,));dictionary=dictionaries[64]
        passages[lang]={'record_start':start,'train_record_indices':list(range(start,start+TRAIN)),
            'held_record_indices':list(range(start+TRAIN,start+TRAIN+HELD)),'source_records':block,
            'plaintext':asdict(plain),'holdout_plaintext':asdict(held_plain),'dictionary':asdict(dictionary),
            'added_word_provenance':provenance,'alphabet':asdict(alphabet)}
        for profile in PROFILES:
            encoder=key(alphabet.symbols,tuple('uvwxyz'),profile,KEY_SEED)
            train=encoder.encode(plain,(0,)*plain.size);held=encoder.encode(held_plain,(0,)*held_plain.size)
            q=HiddenRecoveryRequest(train,alphabet,Alphabet(tuple('uvwxyz')),Bounds('verbose',1,1,3),dictionary,timeout_ms=5000)
            truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':[0]*plain.size,'nulls':[]};verify(q,truth)
            if encoder.decode(held)!=held_plain:raise RuntimeError('Generating continuation failed')
            lengths=sorted({len(encoder.codebook[s][0]) for w in plain.words for s in w})
            if lengths!=([2] if profile=='fixed-two' else [1,2,3]):raise RuntimeError('Profile not genuinely exercised')
            case_id=f'{lang}-{profile}'
            cases.append({'id':case_id,'kind':'positive','language':lang,'profile':profile,'request':asdict(q),
                'truth':truth,'holdout':asdict(held),'holdout_plaintext':asdict(held_plain),'generating_lengths':lengths})
            full=Text(train.words+held.words)
            try:shuffled,generation=typewise_shuffle(full,SHUFFLE_SEED)
            except ValueError as error:
                if str(error)!='Unable to generate a changed collision-free word-type shuffle':raise
                unavailable.append({'id':case_id+'-shuffle','status':'UNAVAILABLE_AFTER_1000_DRAWS'});continue
            audit=diagnostics(full,shuffled)
            if not all(audit[k] for k in ('word_length_sequence_preserved','glyph_counts_per_word_preserved','exact_repetition_partition_preserved')):raise RuntimeError('Control invariant failed')
            request=asdict(q);request['ciphertext']=asdict(Text(shuffled.words[:TRAIN]))
            if shuffled.words[:TRAIN]==train.words:raise RuntimeError('Training unchanged; stop rather than accept or tune')
            cases.append({'id':case_id+'-shuffle','positive_id':case_id,'kind':'shuffle','language':lang,'profile':profile,
                'request':request,'holdout':asdict(Text(shuffled.words[TRAIN:])), 'construction':generation,'invariants':audit})
    protocol={'identity':identity,'train_words':TRAIN,'heldout_words':HELD,'dictionary_size':64,'profiles':PROFILES,
        'key_seed':KEY_SEED,'shuffle_seed':SHUFFLE_SEED,'timeout_ms_per_fit':5000,'planned_fits':12,
        'selection':'First contiguous 24+6 eligible records at/after each source midpoint, all in corrected source dictionary, at least three distinct novel held types and all held letters seen in training. No skipped/projected records and no solver outcome selection. Training/held inventories union retained in oracle-assisted 64-word dictionary, filled in original corpus order under fixed passage alphabet.',
        'scope':'One real normalized passage per language, Latin Caesar and cached Swabian source 123. New keys, H1 L1-3, free selection, flat observed domains. Positive known-word and hidden-word arms plus one hidden-word shuffle arm per profile. No oracle lengths or profile passed to hidden recovery. Construction may see held plaintext for corpus selection/dictionary/alphabet; this is an assisted small-scale calibration, not blind language identification. All inputs frozen before solves; no tuning/retries/extra encodings. Exact and novel-exact positive predictions, dictionary compatibility only for randomized controls. Same-source/profile cases correlated; no p-values or manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'passages':passages,'cases':cases,'unavailable':unavailable}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def evaluate_positive(case,q,result):
    scored=evaluate(case,q,result)
    if result['status']=='SAT':
        exact=[w['fully_decoded'] and tuple(w['decoded_prefix'])==tuple(t) for w,t in zip(scored['prediction']['word_results'],case['holdout_plaintext']['words'])]
        scored['novel_exact_words']=sum(hit and not w['seen_in_training'] for hit,w in zip(exact,scored['prediction']['word_results']))
    return scored


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'arms':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        arms=('known-words','hidden-words') if case['kind']=='positive' else ('hidden-words',)
        for arm in arms:
            if any(a['case']==case['id'] and a['arm']==arm for a in r['arms']):continue
            print(case['id'],arm,'timeout=5000ms',flush=True)
            start=perf_counter()
            if arm=='known-words':
                plain=Text(tuple(tuple(w) for w in case['truth']['plaintext']['words']));recovered=known_solve(plain,q)
            else:recovered=recover_observed_codes(q)
            wall=perf_counter()-start;result=asdict(recovered);verify(q,result)
            if case['kind']=='positive' and result['status']=='UNSAT':raise RuntimeError('Known positive incorrectly UNSAT')
            row={'case':case['id'],'arm':arm,'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
            if result['status']=='SAT' and case['kind']=='positive':
                row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
                if arm=='known-words' and row['training_exact_words']!=TRAIN:raise RuntimeError('Known words changed')
            row.update(evaluate_positive(case,q,result) if case['kind']=='positive' else control_prediction(case,q,result))
            r['arms'].append(row);write_json(path,r)
            print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p)
    records,templates,_=load_sources()
    for lang,passage in p['passages'].items():
        start,plain,held,block=select_passage(records[lang],set(tuple(w) for w in templates[lang]['request']['dictionary']['words']))
        assert start==passage['record_start'] and block==passage['source_records']
        assert digest(asdict(plain))==digest(passage['plaintext']) and digest(asdict(held))==digest(passage['holdout_plaintext'])
        alphabet=Alphabet(tuple(passage['alphabet']['symbols']));base=WordDictionary(tuple(sorted(set(plain.words+held.words))))
        dictionaries,provenance=vocabularies(base,alphabet,records[lang],(64,))
        assert digest(asdict(dictionaries[64]))==digest(passage['dictionary']) and digest(provenance)==digest(passage['added_word_provenance'])
    expected=0
    for case in p['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        if case['kind']=='positive':verify(q,case['truth'])
        else:
            positive=next(c for c in p['cases'] if c['id']==case['positive_id'])
            base=HiddenRecoveryRequest.from_dict(positive['request']);full=Text(base.ciphertext.words+tuple(tuple(w) for w in positive['holdout']['words']))
            shuffled,generation=typewise_shuffle(full,SHUFFLE_SEED)
            assert digest(generation)==digest(case['construction']) and digest(diagnostics(full,shuffled))==digest(case['invariants'])
            assert shuffled.words==q.ciphertext.words+tuple(tuple(w) for w in case['holdout']['words'])
        for arm in (('known-words','hidden-words') if case['kind']=='positive' else ('hidden-words',)):
            expected+=1;row=next(a for a in r['arms'] if a['case']==case['id'] and a['arm']==arm)
            assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
            if row['result']['status']=='SAT' and case['kind']=='positive':
                assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
                if arm=='known-words':assert row['training_exact_words']==TRAIN
            evaluation=evaluate_positive(case,q,row['result']) if case['kind']=='positive' else control_prediction(case,q,row['result'])
            assert all(digest(row[k])==digest(v) for k,v in evaluation.items())
    assert len(r['arms'])==expected
    write_json(OUT/'validation.json',{'verified':True,'arms':expected,'checks':['sources/code hashes','contiguous source passages','coverage/novel selection','assisted dictionary reconstruction','shuffle regeneration','full witnesses','known identities','frozen scoring'], 'limitation':'UNSAT solver-reported; controls not assumed impossible.'})
    print('Validated natural-passage calibration')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared four natural positives and four shuffles before solving')
