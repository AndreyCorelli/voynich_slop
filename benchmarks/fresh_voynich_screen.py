"""Frozen two-block Voynich screen with full dictionaries and local controls."""
import argparse
from collections import deque
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks.structured_negative_controls import generate
from benchmarks.guided_model_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds,Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import tokenize_dictionary
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

CORPUS=Path('data/processed/zl-eva.json')
OUT=Path('experiments/results/fresh-voynich-screen')
SOURCES={
 'latin':Path('data/generated/clean-latin-voynich/inputs/words-23.json'),
 'swabian':Path('data/generated/german-regional-audit/budget-1800000ms/inputs/123-full-30.json')}
SELECTION=Path('experiments/results/cross-window-passages/selection.json')
INVENTORY=Path('experiments/configs/guided-model-calibration.json')


def select_blocks(records,alphabet,excluded,size=44):
    pending=deque(maxlen=size);previous=None;chosen=[];folios=set()
    for i,r in enumerate(records):
        folio=r['folio']
        if folio!=previous:pending.clear()
        previous=folio
        if folio in excluded or folio in folios or not r['tokens'] or not set(r['tokens'])<=set(alphabet):
            pending.clear();continue
        pending.append(i)
        if len(pending)==size:
            chosen.append(list(pending));folios.add(folio);pending.clear()
            if len(chosen)==2:return chosen
    raise ValueError('No two fixed eligible fresh-folio blocks')


def novelty(train,held):
    seen=set(train.words);new=[w not in seen for w in held.words]
    return {'holdout_words':len(held.words),'seen_ciphertext_words':sum(not x for x in new),
            'novel_ciphertext_words':sum(new),'distinct_novel_ciphertext_types':len({w for w,n in zip(held.words,new) if n}),
            'novel_fraction':sum(new)/len(new)}


def identity():
    return {str(p):digest(p.read_text()) for p in
        (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/structured_negative_controls.py'),
         Path('src/voynich_smt/language/contractions.py'),Path('benchmarks/guided_model_calibration.py'))}


def prepare():
    corpus=json.loads(CORPUS.read_text());selection=json.loads(SELECTION.read_text());inventory=json.loads(INVENTORY.read_text())
    templates={language:HiddenRecoveryRequest.from_dict(json.loads(path.read_text())['request']) for language,path in SOURCES.items()}
    if templates['latin'].ciphertext_alphabet!=templates['swabian'].ciphertext_alphabet:raise ValueError('Cipher alphabets differ')
    ids={'code':identity(),'corpus':digest(corpus),'prior_selection':digest(selection),'inventory':digest(inventory),
         'templates':{k:digest(asdict(q)) for k,q in templates.items()}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=ids:raise ValueError('Prepared source/code changed')
        return p
    excluded=sorted({'f1r','f3r'}|{w['folio'] for w in selection['windows']})
    protocol={'identity':ids,'training_words':22,'holdout_words':22,'block_count':2,
        'excluded_folios':excluded,'selection':'First contiguous 44 eligible records on each of first two distinct nonexcluded folios; excluded/unsupported tokens break runs. No length, repetition or language-score selection.',
        'freshness_scope':'Excludes known f1r/f3r recovery pages and all ten cross-section target folios, conservatively at whole-folio level. Not a claim manuscript statistics were unseen in all earlier analyses.',
        'novelty_gate_minimum_words':11,'novelty_gate_action':'Measure after selection, before fitting. If either block fails, stop rather than replace or tune it.',
        'languages':['latin','swabian'],'profiles':['letters','mixed'],'h_order':[1,2],
        'timeout_ms':5000,'fits_per_arm':1,'control':'One per-block bigram/endpoints/repetition preserving draw, seed 2323, bounded 128 construction draws; must change training; unavailable recorded.',
        'scope':'Full corrected dictionaries, atomic EVA transcription tokens, free H1/H2 L1-3, no nulls. Fixed et/in contraction rules. Retrospective bounded screen, not language likelihood; UNKNOWN has no prediction score. Tiny synthetic calibration does not establish performance at full vocabulary.'}
    write_json(OUT/'protocol.json',protocol)
    indices=select_blocks(corpus['records'],templates['latin'].ciphertext_alphabet.symbols,set(excluded))
    blocks=[]
    for i,records in enumerate(indices,1):
        full=Text(tuple(tuple(corpus['records'][k]['tokens']) for k in records))
        train=Text(full.words[:22]);held=Text(full.words[22:])
        control,metadata=generate(full,'bigrams',2323)
        if control is not None and control.words[:22]==train.words:
            control=None;metadata=dict(metadata,status='UNAVAILABLE_TRAINING_UNCHANGED')
        block={'id':f'block-{i}','record_indices':records,'folio':corpus['records'][records[0]]['folio'],
            'start_locus':corpus['records'][records[0]]['locus'],'end_locus':corpus['records'][records[-1]]['locus'],
            'training':asdict(train),'holdout':asdict(held),'novelty':novelty(train,held),
            'control':asdict(control) if control is not None else None,'control_construction':metadata}
        blocks.append(block)
    dictionaries={}
    for language,template in templates.items():
        vocabulary=[''.join(w) for w in template.dictionary.words]
        for profile in ('letters','mixed'):
            rules=inventory['rules'][language] if profile=='mixed' else []
            d=WordDictionary(tokenize_dictionary(vocabulary,rules))
            alphabet=Alphabet(tuple(sorted(set(template.plaintext_alphabet.symbols)|{s for w in d.words for s in w})))
            dictionaries[language+'-'+profile]={'dictionary':asdict(d),'plaintext_alphabet':asdict(alphabet),'rules':rules,
                'expanded_spelling_count':len(vocabulary),'tokenization_count':len(d.words)}
    p={'identity':ids,'protocol':protocol,'blocks':blocks,'dictionaries':dictionaries,
       'ciphertext_alphabet':asdict(templates['latin'].ciphertext_alphabet),
       'novelty_gate_passed':all(b['novelty']['novel_ciphertext_words']>=11 for b in blocks)}
    write_json(path,p)
    for b in blocks:print(b['id'],b['folio'],b['record_indices'][0],f"novel={b['novelty']['novel_ciphertext_words']}/22",flush=True)
    return p


def request_for(p,block,language,profile,h,kind):
    spec=p['dictionaries'][language+'-'+profile]
    words=block['training']['words'] if kind=='real' else block['control']['words'][:22]
    q=HiddenRecoveryRequest(Text(tuple(tuple(w) for w in words)),Alphabet(tuple(spec['plaintext_alphabet']['symbols'])),
        Alphabet(tuple(p['ciphertext_alphabet']['symbols'])),Bounds('verbose',h,1,3),
        WordDictionary(tuple(tuple(w) for w in spec['dictionary']['words'])),timeout_ms=5000)
    return q,spec['rules']


def run():
    p=prepare()
    if not p['novelty_gate_passed']:raise ValueError('Fixed blocks fail novelty gate; preserve selection and stop')
    path=OUT/'report.json'
    if path.exists():
        r=json.loads(path.read_text())
        if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    else:r={'prepared_sha256':digest(p),'arms':[],'complete':False}
    # Fit all H1 arms before H2; no outcome-dependent changes or promotions.
    for h in (1,2):
      for block in p['blocks']:
       for language in ('latin','swabian'):
        for profile in ('letters','mixed'):
         for kind in ('real','control'):
            if kind=='control' and block['control'] is None:continue
            name=f"{block['id']}-{language}-{profile}-H{h}-{kind}"
            if any(a['id']==name for a in r['arms']):continue
            q,rules=request_for(p,block,language,profile,h,kind)
            print(name,flush=True)
            result=asdict(_recover(None,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,q.bounds,5000,
                dictionary=q.dictionary,max_word_length=max(map(len,q.dictionary.words)),codeword_domains='observed'))
            verify(q,result)
            arm={'id':name,'block_id':block['id'],'language':language,'profile':profile,'h':h,'kind':kind,
                 'request_sha256':digest(asdict(q)),'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
            if result['status']=='SAT':
                held=block['holdout']['words'] if kind=='real' else block['control']['words'][22:]
                case={'kind':'voynich','holdout':{'words':held}}
                arm.update(evaluate(result,case,q,rules),evaluation_status='EVALUATED_FROZEN_KEY')
                if kind=='real' and block['control'] is not None:
                    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
                    from benchmarks.frozen_key_holdout import score
                    arm['same_key_control_prediction']=score(Text(tuple(tuple(w) for w in block['control']['words'][22:])),encoder,q.dictionary,q.ciphertext.words)
            r['arms'].append(arm);write_json(path,r)
            print(result['status'],f"{result['runtime_seconds']:.2f}s",flush=True)
    r['complete']=True;write_json(path,r);return r


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');a=parser.parse_args()
    if a.run:run()
    else:
        p=prepare();print('Prepared fixed screen; novelty gate='+str(p['novelty_gate_passed'])+'. Use --run for five-second fits.')
