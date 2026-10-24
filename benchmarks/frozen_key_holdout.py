"""Next-block prediction with saved frozen keys; no solver or key repairs."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random

from benchmarks.l3_conflict import verify
from benchmarks.german_shuffle_controls import typewise_shuffle
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.controls import control
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text

OUT=Path('experiments/results/frozen-key-holdout')
SEEDS=tuple(range(20))


def next_block(records,training,size=22):
    words=[tuple(r['tokens']) for r in records]
    starts=[i for i in range(len(words)-len(training.words)+1)
            if tuple(words[i:i+len(training.words)])==training.words]
    if len(starts)!=1:raise ValueError('Training block must have one exact contiguous match')
    start=starts[0];end=start+len(training.words);chosen=records[end:end+size]
    if len(chosen)!=size or any(not r['tokens'] for r in chosen):
        raise ValueError('Immediate holdout has excluded or missing words; do not skip or relocate')
    if any(r['folio']!=records[start]['folio'] for r in chosen):
        raise ValueError('Immediate holdout crosses folio boundary')
    return Text(tuple(words[end:end+size])),{'train_start_record':start,'train_end_record_exclusive':end,
        'holdout_record_indices':list(range(end,end+size)),
        'holdout_records':chosen,'folio':records[start]['folio']}


def decode_word(word,encoder):
    lookup={c:(s,k) for s,codes in encoder.codebook.items() for k,c in enumerate(codes)}
    prefixes={c[:n] for c in lookup for n in range(1,len(c)+1)}
    plain=[];choices=[];pending=();consumed=0
    for i,g in enumerate(word):
        pending+=(g,)
        if pending in lookup:
            s,k=lookup[pending];plain.append(s);choices.append(k);consumed=i+1;pending=()
        elif pending not in prefixes:
            return {'fully_decoded':False,'decoded_prefix':plain,'choices':choices,
                    'complete_code_glyphs':consumed,'failure_index':i,'failure':'no matching code prefix'}
    if pending:
        return {'fully_decoded':False,'decoded_prefix':plain,'choices':choices,
                'complete_code_glyphs':consumed,'failure_index':len(word),'failure':'incomplete final code'}
    assert encoder.encode(Text((tuple(plain),)),tuple(choices)).words[0]==word
    return {'fully_decoded':True,'decoded_prefix':plain,'choices':choices,'complete_code_glyphs':len(word)}


def score(text,encoder,dictionary,training_words=()):
    vocab=set(dictionary.words);seen=set(training_words);rows=[]
    for word in text.words:
        decoded=decode_word(word,encoder)
        decoded['dictionary_member']=decoded['fully_decoded'] and tuple(decoded['decoded_prefix']) in vocab
        rows.append({'ciphertext':word,'seen_in_training':word in seen,**decoded})
    complete=sum(r['fully_decoded'] for r in rows);members=sum(r['dictionary_member'] for r in rows)
    consumed=sum(r['complete_code_glyphs'] for r in rows)
    novel=[r for r in rows if not r['seen_in_training']]
    return {'word_count':len(rows),'fully_decoded_words':complete,'dictionary_words':members,
        'seen_ciphertext_words':len(rows)-len(novel),'novel_ciphertext_words':len(novel),
        'novel_fully_decoded_words':sum(r['fully_decoded'] for r in novel),
        'novel_dictionary_words':sum(r['dictionary_member'] for r in novel),
        'fully_decoded_fraction':complete/len(rows),'dictionary_fraction':members/len(rows),
        'dictionary_fraction_among_decoded':members/complete if complete else None,
        'glyph_count':text.size,'complete_code_glyphs':consumed,'glyph_prefix_coverage':consumed/text.size,
        'word_results':rows}


def baselines():
    p=Path('experiments/results/latin-mixed-comparison/letters-voynich-30min.json');r=json.loads(p.read_text())
    public={k:r[k] for k in ('request','codeword_domains')}
    if digest(public)!=r['input_sha256']:raise ValueError('Latin input hash mismatch')
    yield 'latin-letters',HiddenRecoveryRequest.from_dict(r['request']),r['result'],{'report':str(p),'report_sha256':digest(r)}
    p=Path('experiments/results/german-regional-audit/budget-1800000ms.json');r=json.loads(p.read_text())
    for n in (123,233):
        row=next(e for e in r['rows'] if e['source_id']==n);result=next(e['result'] for e in r['experiments'] if e['source_id']==n)
        public=json.loads(Path(row['public_input']).read_text())
        if digest(public)!=row['input_sha256']:raise ValueError('German input hash mismatch')
        yield f'german-{n}',HiddenRecoveryRequest.from_dict(public['request']),result,{'report':str(p),'report_sha256':digest(r),'input_sha256':digest(public)}


def run():
    corpus=json.loads(Path('data/processed/zl-eva.json').read_text())
    report={'corpus_sha256':digest(corpus),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'seeds':list(SEEDS),'experiments':[],'solver_calls':0,
        'semantics':'Freeze one saved key per model. Exact immediate next 22 eligible contiguous words, same folio, no skipped records or repairs. Each key has its own training endpoint; Latin holdout partly overlaps German training, so cross-model results are not independent or identical-window comparisons. Existing manuscript data are retrospective, not prospectively blind. Shuffles match lengths/global glyph counts; typewise also preserves per-word multisets and exact equality. No p-values or cipher-family exclusion.'}
    for name,q,result,provenance in baselines():
        if result['status']!='SAT':raise ValueError('Verified SAT baseline required')
        verify(q,result)
        encoder=Encoder({s:tuple(tuple(c) for c in codes) for s,codes in result['encoder']['codebook'].items()})
        holdout,selection=next_block(corpus['records'],q.ciphertext)
        real=score(holdout,encoder,q.dictionary,q.ciphertext.words);controls=[]
        for family in ('typewise','frequency'):
            for seed in SEEDS:
                shuffled,_=(typewise_shuffle(holdout,seed) if family=='typewise' else control(holdout,'frequency-shuffle',seed))
                assert tuple(map(len,shuffled.words))==tuple(map(len,holdout.words))
                assert Counter(g for w in shuffled.words for g in w)==Counter(g for w in holdout.words for g in w)
                controls.append({'family':family,'seed':seed,'ciphertext_sha256':digest(asdict(shuffled)),
                                 'ciphertext':asdict(shuffled),'score':score(shuffled,encoder,q.dictionary,q.ciphertext.words)})
        plain=Text(tuple(tuple(w) for w in result['plaintext']['words'][:22]))
        rng=random.Random(7);choices=tuple(rng.randrange(len(encoder.codebook[s])) for w in plain.words for s in w)
        positive=encoder.encode(plain,choices);calibration=score(positive,encoder,q.dictionary,q.ciphertext.words)
        if calibration['dictionary_words']!=22:raise RuntimeError('Frozen decoder calibration failed')
        summary=[]
        for family in ('typewise','frequency'):
            cs=[c['score'] for c in controls if c['family']==family]
            summary.append({'family':family,'controls':len(cs),
                **{k:{'minimum':min(c[k] for c in cs),'mean':sum(c[k] for c in cs)/len(cs),
                      'maximum':max(c[k] for c in cs),'at_least_real':sum(c[k]>=real[k] for c in cs)}
                   for k in ('fully_decoded_words','dictionary_words','novel_dictionary_words','glyph_prefix_coverage')}})
        entry={'id':name,'baseline':provenance,'encoder_sha256':digest(asdict(encoder)),
            'frozen_encoder':asdict(encoder),'selection':selection,'real':real,'controls':controls,
            'summary':summary,'calibration':{'kind':'Re-encode fitted plaintext with new free choices; decoder sanity check, not independent language data.',
                'ciphertext':asdict(positive),'score':calibration}}
        report['experiments'].append(entry);write_json(OUT/'report.json',report)
        print(name,'decoded',real['fully_decoded_words'],'dictionary',real['dictionary_words'],'of 22',flush=True)
        for s in summary:print(s['family'],'dictionary min/mean/max',s['dictionary_words'],flush=True)
    report['complete']=True;write_json(OUT/'report.json',report)
    return report


if __name__=='__main__':run()
