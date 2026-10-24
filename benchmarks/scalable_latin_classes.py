"""Learned-class gates and independent Latin fixtures; no target hints in fitting."""
from collections import Counter
from itertools import islice
import json
import random
import shutil
from statistics import median
from pathlib import Path
import time

from benchmarks.scalable_latin_caesar import ROOT as ORIGINAL, write, sha, frozen_documents, sentences, TOKENIZATION
from voynich_smt.word_mapping.scalable.classes import ClassWordModel
from voynich_smt.word_mapping.scalable.class_decode import ClassDecoder
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.data import generate,CipherStream
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.incremental import full_score

ROOT=ORIGINAL.parent/'classes-confidence-v1'
RESOURCES=ORIGINAL/'resources'
TEST=Path('data/latin-grammar-benchmark/perseus-r2.17/la_perseus-ud-test.conllu')
HOLDOUTS={'calibration':'phi0972.phi001','confirmation':'phi0959.phi006'}


def build():
    ROOT.mkdir(parents=True,exist_ok=False)
    write(ROOT/'design.json',{'class_parameters':{'k':32,'contexts':512,'dimensions':32,'iterations':25,'seed':23},
         'source':'Original non-Caesar train corpus only; unchanged full inventory',
         'holdouts':HOLDOUTS,'holdout_raw_sha256':sha(TEST),
         'class_gate':'Calibration reference beats median 10 corrupted, median 10 feasible random, median 10 shuffled, and every feasible collapsed key',
         'word_gate':'Nearly correct feasible reference beats all-untrained and frequency-only keys on calibration work',
         'conditional_inference':'Class stages only if class gate passes; word refinement only if word gate also passes',
         'calibration':'Fixed baseline frequency decoder, 3 seeds, 4000 proposals; fit only calibration work, evaluate once on confirmation, then frozen application to Caesar',
         'confidence_thresholds':[.5,.8,.95],'high_trust_rule':'.8 score threshold AND confirmation >=20 accepted types AND Wilson 95% precision lower bound >=.8',
         'no_target_hints':'No word identities, spelling, topic, boundaries, POS or lemmas are features of confidence model; no Caesar labels used in fitting'})
    output=ROOT/'resources';output.mkdir()
    for name in ('inventory.sqlite','protocol.json','training-pos.json'):shutil.copyfile(RESOURCES/name,output/name)
    inventory=Inventory(output/'inventory.sqlite')
    try:
        base=load_model(RESOURCES/'model.sqlite',inventory)
        docs=[tuple(inventory.id(w) for w in d) for d in frozen_documents(RESOURCES)]
        started=time.monotonic();model=ClassWordModel.train(base,docs,k=32,contexts=512,dimensions=32,iterations=25,seed=23)
        model.save(output/'model.sqlite')
        report=json.loads((RESOURCES/'report.json').read_text())
        report.update(model_sha256=model.identity,parent_model_sha256=base.identity,classes=model.training,
                      class_type_sizes=dict(model.capacities),class_token_sizes=list(model.class_lm.counts),build_seconds=time.monotonic()-started)
        write(output/'report.json',report)
    finally:inventory.close()
    # Prepare source-work-disjoint tests after resources have been frozen.
    audit=json.loads((RESOURCES/'source-audit.json').read_text())
    registry={**{key.split(':',1)[1]:'shared-work' for key in audit if key.startswith('perseus:')},
              **{value:'reserved-work' for value in HOLDOUTS.values()}}
    selected={value:[] for value in HOLDOUTS.values()}
    for source,author,tokens in sentences(TEST,'perseus',registry=registry):
        if source in selected:selected[source].extend(w for w,_ in tokens)
    train=frozen_documents(RESOURCES)
    windows=lambda d:(tuple(d[i:i+12]) for i in range(max(0,len(d)-11)))
    for role,source in HOLDOUTS.items():
        assert f'perseus:{source}' not in audit
        words=tuple(selected[source]);assert words
        target=set(windows(words));matches=set()
        for doc in train:matches.update(w for w in windows(doc) if w in target)
        if matches:raise ValueError('Held-out work has exact 12-token training overlap')
        stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION)
        fixture=ROOT/role
        stream.save(fixture/'public/cipher.json');truth.save(fixture/'evaluation-only/truth.json')
        write(fixture/'evaluation-only/provenance.json',{'work_id':source,'path':str(TEST),'sha256':sha(TEST),'tokens':len(words),
              'types':stream.type_count,'overlap_12_words':len(matches),'selection':'Entire predeclared work; no vocabulary filtering or repetition'})
    return report


def gates():
    resources=ROOT/'resources';fixture=ROOT/'calibration'
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory);stream=CipherStream.load(fixture/'public/cipher.json')
        truth=json.loads((fixture/'evaluation-only/truth.json').read_text());assert truth['public_sha256']==stream.identity
        classes=[];word_ids=[];missing=[];used=set()
        for c,w in enumerate(truth['decoding']):
            try:wid=inventory.id(w)
            except KeyError:wid=None;missing.append(c)
            word_ids.append(wid);classes.append(model.unknown if wid is None else model.labels[wid])
            if wid is not None:used.add(wid)
        reference=ClassDecoder(model,stream,classes).full_score()
        rng=random.Random(1103);corrupt=[];random_scores=[];shuffled=[]
        for _ in range(10):
            key=list(classes);subset=rng.sample(range(stream.type_count),max(2,stream.type_count//5));targets=[key[c] for c in subset];rng.shuffle(targets)
            for c,k in zip(subset,targets):key[c]=k
            corrupt.append(ClassDecoder(model,stream,key).full_score())
            remaining=dict(model.capacities);key=[]
            for c in range(stream.type_count):
                choices=[k for k,n in remaining.items() if n>0];k=rng.choice(choices);remaining[k]-=1;key.append(k)
            random_scores.append(ClassDecoder(model,stream,key).full_score())
            document=list(stream.documents[0]);rng.shuffle(document)
            shuffled_stream=CipherStream((tuple(document),),stream.type_count,tokenization=TOKENIZATION)
            shuffled.append(ClassDecoder(model,shuffled_stream,classes).full_score())
        collapsed={str(k):ClassDecoder(model,stream,[k]*stream.type_count).full_score()
                   for k,capacity in model.capacities.items() if capacity>=stream.type_count}
        checks={'corruption':reference>median(corrupt),'random':reference>median(random_scores),
                'shuffle':reference>median(shuffled),'collapse':all(reference>s for s in collapsed.values())}
        proxies=iter(w for w,n in enumerate(model.counts[:-1]) if not n and w not in used)
        for c in missing:word_ids[c]=next(proxies)
        ref_word=full_score(model,stream,DictionaryState.create(stream,model,word_ids))
        freq=full_score(model,stream,DictionaryState.frequency(stream,model))
        unused=list(islice((w for w,n in enumerate(model.counts[:-1]) if not n),stream.type_count))
        null=full_score(model,stream,DictionaryState.create(stream,model,unused))
        result={'scope':'Development gates only; truth never supplied to inference',
                'class_reference':reference,'corrupted':corrupt,'random':random_scores,'shuffled':shuffled,
                'feasible_collapsed':collapsed,'class_checks':checks,'class_pass':all(checks.values()),
                'word_reference':ref_word,'word_frequency_key':freq,'word_null':null,
                'word_pass':ref_word>freq and ref_word>null,'missing_types':len(missing),
                'limitations':'Class labels are unsupervised source categories, not gold grammar. One development work; no generalization claim.'}
        write(ROOT/'gates.json',result);return result
    finally:inventory.close()


if __name__=='__main__':
    print(json.dumps(build(),indent=2),flush=True)
    print('GATES',json.dumps(gates()),flush=True)
