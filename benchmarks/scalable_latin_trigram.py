"""Bounded Latin trigram experiment on the frozen larger corpus and inventory."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import sqlite3
import statistics
import time

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.scalable.latin_corpus import documents,sha,write
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram,BOS
from voynich_smt.word_mapping.scalable.trigram import InterpolatedTrigram,load_model
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.data import CipherStream,generate
from voynich_smt.word_mapping.scalable.search import SearchConfig,peak_rss

PARENT=Path('experiments/results/scalable-latin-corpus-morphology/v2')
SOURCE=PARENT/'models/20000000/surface'
PREVIOUS=Path('experiments/results/scalable-latin-shuffle-contrast/v1')
ROOT=Path('experiments/results/scalable-latin-trigram/v1')


def design():
    return {'version':1,'parent_resources':str(SOURCE),'corpus_sha256':sha(PARENT/'corpus/corpus.json'),
      'inventory_sha256':json.loads((PARENT/'resources/inventory-report.json').read_text())['sha256'],
      'weights':[.25,.5,.75],'trigram_discount':.5,
      'training':'Same complete admitted 5.94M-token source streams; no sentence resets; BOS/EOS at book-file boundaries only',
      'retrieval':'Unchanged existing bigram projection; full injective inventory and all-occurrence trigram acceptance score',
      'development':['apuleius-1','curtius-3','suetonius-augustus'],
      'development_gate':'On >=2/3 works, reference beats null/random and median 10/25/50% corruption, and its trigram-minus-bigram contribution exceeds that of the frequency key',
      'gate_scope':'Incremental context gate, not full likelihood-versus-frequency gate: known baseline already fails latter. Report both without hiding failures.',
      'selection':'Among passing weights, maximize pooled per-token development reference-minus-frequency score margin; ties prefer .5 then lower weight',
      'replication':'Previously inspected Gellius I; not a fresh validation work',
      'restarts':[3,5,7],'initialization':'frequency','proposals':4000,'budget_seconds_per_chain':600,
      'baseline':'Reuse completed original-surface Gellius chains if hashes and protocols/initial keys match',
      'fresh_confirmation':'Livy I only after frozen method shows clear Gellius improvement; Ammianus and Quintilian remain sealed',
      'promotion':'Mean token accuracy >= baseline + .01 and top50 correct nondecreasing, OR >=2 more correct top50 and mean nondecreasing, OR more correct primary anchors without more wrong primary anchors',
      'primary_anchor':'Unanimous over 3 restarts, public count>=100; agreement is not probability',
      'no_tuning':'No topic, target vocab, given sentence boundaries or guessed anchors; no Gellius/Livy parameter tuning',
      'limits':['Adjacent 3-word phrases only; no long-distance syntax or neural modeling.',
                'Bigram retrieval can miss trigram-specific candidates; this is the first cheap screen.',
                'Three shared-frequency-start seeds do not establish confidence or generalization.']}


def build():
    ROOT.mkdir(parents=True,exist_ok=False);write(ROOT/'design.json',design())
    resources=ROOT/'resources';resources.mkdir();os.link(SOURCE/'inventory.sqlite',resources/'inventory.sqlite')
    inventory=Inventory(resources/'inventory.sqlite');t=time.monotonic()
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        corpus=json.loads((PARENT/'corpus/corpus.json').read_text());triples=Counter();h=hashlib.sha256();tokens=0
        for i,document in enumerate(documents(PARENT/'corpus',corpus['documents'])):
            a,b=BOS,BOS;dh=hashlib.sha256();n=0
            for word in document:
                wid=inventory.id(word);triples[a,b,wid]+=1
                dh.update(wid.to_bytes(8,'little'));a,b=b,wid;n+=1
            triples[a,b,base.eos]+=1
            h.update(n.to_bytes(8,'little'));h.update(dh.digest());tokens+=n
            if (i+1)%100==0:print(json.dumps({'stage':'count','documents':i+1,'tokens':tokens,'triples':len(triples),'seconds':time.monotonic()-t}),flush=True)
        if h.hexdigest()!=base.training_sha256:raise ValueError('Training stream differs from frozen parent')
        model=InterpolatedTrigram(base,triples,weight=.5,discount=.5);del triples;gc.collect()
        model.save(resources/'model.sqlite')
        report={'training_tokens':tokens,'documents':len(corpus['documents']),'observed_trigrams':len(model.triples),
             'observed_pairs':len(base.edges),'inventory_forms':inventory.size,'inventory_sha256':inventory.identity,
             'parent_model_sha256':base.identity,'model_sha256':model.identity,'training_sha256':base.training_sha256,
             'seconds':time.monotonic()-t,'peak_rss_bytes':peak_rss(),
             'language':model.config.language,'tokenization':model.config.tokenization}
        write(resources/'report.json',report);print(json.dumps({'stage':'built',**report}),flush=True)
        return report
    finally:inventory.close()


def prepare_fixture(record,inventory,base):
    target=ROOT/'fixtures'/record['id']
    plain=(PARENT/'corpus/evaluation-only'/f"{record['id']}.txt").read_text().split()
    stream,truth=generate((plain,),seed=83,tokenization='latin-iu-continuous-v1')
    target.mkdir(parents=True,exist_ok=False);stream.save(target/'public/cipher.json');truth.save(target/'evaluation-only/truth.json')
    provenance=PARENT/'corpus/evaluation-only'/f"{record['id']}.json"
    write(target/'evaluation-only/provenance.json',{'record':record,'parent':json.loads(provenance.read_text()),'parent_sha256':sha(provenance),'cipher_sha256':stream.identity})
    words=sorted(set(plain));key={};used=set();missing=[]
    for w in words:
        try:wid=inventory.id(w);key[w]=wid;used.add(wid)
        except KeyError:missing.append(w)
    proxy=(w for w,c in enumerate(base.counts[:-1]) if not c and w not in used)
    for w in missing:key[w]=next(proxy)
    freq=DictionaryState.initialize(stream,base,method='frequency',seed=3).assignments
    nullkey=dict(zip(words,(w for w,c in enumerate(base.counts[:-1]) if not c)))
    controls={'reference':[key[w] for w in plain],'frequency':[freq[c] for c in stream.documents[0]],'null':[nullkey[w] for w in plain]}
    for level in (.1,.25,.5):
        for seed in range(3):
            rng=random.Random(1000+seed);chosen=rng.sample(words,max(2,int(level*len(words))));values=[key[w] for w in chosen];rng.shuffle(values)
            corrupt={**key,**dict(zip(chosen,values))};controls[f'corrupt-{level}-{seed}']=[corrupt[w] for w in plain]
    for seed in range(3):
        rng=random.Random(seed);randomkey=dict(zip(words,rng.sample(range(base.size),len(words))))
        controls[f'random-{seed}']=[randomkey[w] for w in plain]
        shuffled=controls['reference'].copy();rng.shuffle(shuffled);controls[f'shuffled-{seed}']=shuffled
    # Previously optimized development smoke keys are stronger wrong-key controls
    # than the initial frequency dictionary; no such key is supplied to search.
    for method in ('surface','contrast','regularized'):
        old=PREVIOUS/f'smoke-{method}'
        if record['id']=='apuleius-1' and (old/'inference.json').exists():
            inferred=json.loads((old/'inference.json').read_text())
            assert inferred['protocol']['cipher_sha256']==stream.identity
            assert inferred['protocol']['inventory_sha256']==inventory.identity
            mapping=inferred['runs'][0]['joint_archive'][0]['assignments']
            controls['optimized-'+method]=[mapping[c] for c in stream.documents[0]]
    missing_set=set(missing)
    return controls,{'tokens':len(plain),'types':len(words),'missing_types':len(missing),
                    'missing_tokens':sum(w in missing_set for w in plain)}


def score_variants(model,sequence,weights):
    # Exact per-sequence trigram aggregation, without repeated whole-stream passes
    # per weight. Use the same source counts for every interpolation setting.
    sequence=tuple(sequence)
    if not sequence:raise ValueError('Expected a nonempty control sequence')
    pairs=Counter();triples=Counter();a,b=BOS,BOS
    for c in sequence:pairs[b,c]+=1;triples[a,b,c]+=1;a,b=b,c
    pairs[b,model.eos]+=1;triples[a,b,model.eos]+=1
    base=model.bigram
    scores={'bigram':math.fsum(n*math.log(base.probability(u,v)) for (u,v),n in pairs.items())-math.log1p(-base.probability(BOS,base.eos))}
    values=[]
    for (a,b,c),n in triples.items():
        lower=base.probability(b,c);total=model.totals3.get((a,b),0)
        higher=(max(model.triples.get((a,b,c),0)-model.discount,0)/total+model.discount*model.distinct3[a,b]/total*lower) if total else lower
        values.append((n,lower,higher))
    for w in weights:
        old=model.weight;model.weight=w
        initial=model.probability3(BOS,BOS,model.eos);model.weight=old
        scores[str(w)]=math.fsum(n*math.log((1-w)*lo+w*hi) for n,lo,hi in values)-math.log1p(-initial)
    return scores


def screen():
    inventory=Inventory(ROOT/'resources/inventory.sqlite')
    try:
        model=load_model(ROOT/'resources/model.sqlite',inventory);protocol=json.loads((ROOT/'design.json').read_text())
        weights=protocol['weights'];rows=[]
        for record in json.loads((PARENT/'design.json').read_text())['heldouts']:
            if record['id'] not in protocol['development']:continue
            controls,coverage=prepare_fixture(record,inventory,model.bigram)
            scores={name:score_variants(model,sequence,weights) for name,sequence in controls.items()}
            rows.append({'id':record['id'],**coverage,'scores':scores})
            write(ROOT/'development-progress.json',{'works':rows})
            print(json.dumps({'stage':'screen','work':record['id'],'reference':scores['reference'],'frequency':scores['frequency']}),flush=True)
        variants=[]
        for w in weights:
            works=[]
            for row in rows:
                scores={name:s[str(w)] for name,s in row['scores'].items()};ref=scores['reference']
                contribution=row['scores']['reference'][str(w)]-row['scores']['reference']['bigram']
                wrong_contribution=row['scores']['frequency'][str(w)]-row['scores']['frequency']['bigram']
                checks={'null':ref>scores['null'],'random':ref>statistics.median(scores[f'random-{i}'] for i in range(3)),
                       'incremental_context':contribution>wrong_contribution}
                for level in (.1,.25,.5):checks[f'corrupt-{level}']=ref>statistics.median(scores[f'corrupt-{level}-{i}'] for i in range(3))
                works.append({'id':row['id'],'checks':checks,'pass':all(checks.values()),'full_reference_beats_frequency':ref>scores['frequency'],
                      'reference_contribution':contribution,'frequency_contribution':wrong_contribution,
                      'reference_minus_frequency':ref-scores['frequency']})
            variants.append({'weight':w,'works':works,'pass':sum(r['pass'] for r in works)>=2,
                 'reference_minus_frequency_per_token':sum(r['reference_minus_frequency'] for r in works)/sum(r['tokens']+1 for r in rows)})
        passing=[r for r in variants if r['pass']]
        winner=max(passing,key=lambda r:(r['reference_minus_frequency_per_token'],-abs(r['weight']-.5),-r['weight'])) if passing else None
        result={'works':rows,'variants':variants,'selected_weight':None if winner is None else winner['weight'],
              'gate':protocol['development_gate'],'gate_scope':protocol['gate_scope'],'sealed_recovery_evaluated':False}
        write(ROOT/'development.json',result)
        if winner:
            # Freeze the selected metadata without touching the immutable parent
            # counts. The source trigram database is a new experiment artifact.
            model.weight=winner['weight']
            with sqlite3.connect(ROOT/'resources/model.sqlite') as db:
                metadata={'format_version':1,'weight':model.weight,'discount':model.discount,'sha256':model.identity}
                db.execute('UPDATE trigram_metadata SET metadata=?',(json.dumps(metadata),))
            report=json.loads((ROOT/'resources/report.json').read_text());report.update(model_sha256=model.identity,selected_weight=model.weight)
            write(ROOT/'resources/report.json',report)
        print(json.dumps({'stage':'selection','weight':result['selected_weight']}),flush=True)
        return result
    finally:inventory.close()


def trial(resources,fixture,output):
    from benchmarks.scalable_english_run import run
    from benchmarks.scalable_latin_shuffle_contrast import measure
    isolated=ROOT/'isolated-fixtures'/output.name
    shutil.copytree(fixture/'public',isolated/'public')
    shutil.copytree(fixture/'evaluation-only',isolated/'evaluation-only')
    private=isolated/'evaluation-only';hidden=isolated/'evaluation-unavailable-during-search'
    private.rename(hidden)
    try:
        run(resources,isolated/'public/cipher.json',output,seeds=(3,5,7),
            config=SearchConfig(initialization='frequency',proposals=4000,budget_seconds=600,reserve_seconds=10),trace=True)
    finally:hidden.rename(private)
    gc.collect()
    return measure(resources,output,isolated)


def compare(baseline_path,new_path):
    results={};protocols=[];initial=[]
    for name,folder in [('bigram',baseline_path),('trigram',new_path)]:
        inferred=json.loads((folder/'inference.json').read_text());evaluation=json.loads((folder/'evaluation.json').read_text())
        anchors=json.loads((folder/'anchors-evaluation.json').read_text())
        protocol=dict(inferred['protocol']);protocol.pop('model_sha256');protocols.append(protocol)
        keys=[]
        for r in inferred['runs']:
            assert r['step']==4000 and r['stop_reason']=='proposal_limit'
            with gzip.open(folder/f"traces/seed-{r['seed']}.jsonl.gz",'rt') as f:
                first=json.loads(next(f));assert first['kind']=='initial';keys.append(first['assignments'])
        initial.append(keys)
        majority=[r for r in anchors['rows'] if r['strict_majority']]
        results[name]={'mean_token_accuracy':evaluation['mean_score_selected_token_accuracy'],
           'selected_token_accuracy':evaluation['selected_token_accuracy'],
           'per_seed':[{'seed':r['seed'],'token_accuracy':r['score_selected_best']['token_accuracy']} for r in evaluation['runs']],
           'top':anchors['top'],'primary':anchors['primary'],'primary_rows':anchors['primary_rows'],
           'majority_pool':{'types':len(majority),'correct_types':sum(r['correct'] for r in majority)},
           'search_seconds':sum(r['elapsed_seconds'] for r in inferred['runs']),
           'peak_rss_bytes':max(r['peak_rss_bytes'] for r in inferred['runs'])}
    assert protocols[0]==protocols[1],'Baseline differs beyond model identity'
    assert initial[0]==initial[1],'Initial dictionaries differ'
    a,b=results['bigram'],results['trigram']
    mean_gain=b['mean_token_accuracy']-a['mean_token_accuracy']
    top_gain=b['top']['50']['correct_types']-a['top']['50']['correct_types']
    old_wrong=a['primary']['types']-a['primary']['correct_types'];new_wrong=b['primary']['types']-b['primary']['correct_types']
    checks={'mean_gain':mean_gain>=.01 and top_gain>=0,
            'top50_gain':top_gain>=2 and mean_gain>=0,
            'anchor_gain':b['primary']['correct_types']>a['primary']['correct_types'] and new_wrong<=old_wrong}
    return {'methods':results,'promotion_checks':checks,'promote':any(checks.values()),
            'paired_protocols_verified':True,'identical_initial_keys_verified':True,
            'mean_accuracy_change':mean_gain,'top50_correct_change':top_gain,
            'note':'Agreement across shared frequency starts is not calibrated confidence.'}


def replication():
    selected=json.loads((ROOT/'development.json').read_text())['selected_weight']
    if selected is None:raise ValueError('No trigram weight passed development')
    protocol=json.loads((ROOT/'design.json').read_text())
    write(ROOT/'replication-design.json',{'parent_design_sha256':digest(protocol),'selected_weight':selected,
          'fixture':'Previously inspected Gellius I','baseline':str(PREVIOUS/'validation-surface'),
          'promotion':protocol['promotion'],'method_frozen_before_recovery':True})
    inventory=Inventory(ROOT/'resources/inventory.sqlite')
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        record=next(r for r in json.loads((PARENT/'design.json').read_text())['heldouts'] if r['id']=='gellius-1')
        controls,coverage=prepare_fixture(record,inventory,base)
        oldstream=CipherStream.load(PREVIOUS/'validation-surface/public/cipher.json')
        newstream=CipherStream.load(ROOT/'fixtures/gellius-1/public/cipher.json')
        assert oldstream.identity==newstream.identity
        write(ROOT/'replication-coverage.json',coverage);del controls,base;gc.collect()
    finally:inventory.close()
    trial(ROOT/'resources',ROOT/'fixtures/gellius-1',ROOT/'replication-trigram')
    gc.collect()
    result=compare(PREVIOUS/'validation-surface',ROOT/'replication-trigram')
    write(ROOT/'replication-comparison.json',result)
    print(json.dumps({'stage':'replication','mean_change':result['mean_accuracy_change'],'promote':result['promote']}),flush=True)
    return result


def confirm():
    if not json.loads((ROOT/'replication-comparison.json').read_text())['promote']:
        raise ValueError('No clear replication gain; leave sealed works untested')
    metadata=json.loads((ROOT/'resources/report.json').read_text())
    write(ROOT/'confirmation-design.json',{'fixture':'livy-1','model_sha256':metadata['model_sha256'],
          'selected_weight':metadata['selected_weight'],'seeds':[3,5,7],'proposals':4000,
          'selection':'Frozen before fresh recovery; no Livy retuning; original bigram control',
          'remaining_sealed':['ammianus-14','quintilian-1']})
    inventory=Inventory(ROOT/'resources/inventory.sqlite')
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        record=next(r for r in json.loads((PARENT/'design.json').read_text())['heldouts'] if r['id']=='livy-1')
        controls,coverage=prepare_fixture(record,inventory,base)
        write(ROOT/'confirmation-coverage.json',coverage);del controls,base;gc.collect()
    finally:inventory.close()
    fixture=ROOT/'fixtures/livy-1'
    trial(SOURCE,fixture,ROOT/'confirmation-bigram');gc.collect()
    trial(ROOT/'resources',fixture,ROOT/'confirmation-trigram');gc.collect()
    result=compare(ROOT/'confirmation-bigram',ROOT/'confirmation-trigram')
    write(ROOT/'confirmation-comparison.json',result)
    print(json.dumps({'stage':'confirmation','mean_change':result['mean_accuracy_change'],'promote':result['promote']}),flush=True)
    return result


def summarize():
    development=json.loads((ROOT/'development.json').read_text())
    resource=json.loads((ROOT/'resources/report.json').read_text())
    with sqlite3.connect(ROOT/'resources/model.sqlite') as db:
        metadata=json.loads(db.execute('SELECT metadata FROM trigram_metadata').fetchone()[0])
        singletons=db.execute('SELECT count(*) FROM trigrams WHERE n=1').fetchone()[0]
    if development['selected_weight'] is not None:
        assert metadata['weight']==development['selected_weight']
    assert metadata['sha256']==resource['model_sha256']
    result={'resources':resource,'selected_weight':development['selected_weight'],
        'singleton_trigrams':singletons,'singleton_fraction':singletons/resource['observed_trigrams'],
        'gate_scope':development['gate_scope'],'defaults_changed':False}
    if (ROOT/'replication-comparison.json').exists():
        replication=json.loads((ROOT/'replication-comparison.json').read_text())
        result['replication']=replication
        if replication['promote']:
            if not (ROOT/'confirmation-comparison.json').exists():
                raise ValueError('Promising replication requires frozen fresh confirmation before final summary')
            result['confirmation']=json.loads((ROOT/'confirmation-comparison.json').read_text())
            result['fresh_confirmation_evaluated']=True
            result['remaining_sealed']=['ammianus-14','quintilian-1']
            result['decision']=('Fresh confirmation passes a declared improvement criterion; retain results for broader validation without changing defaults.'
                                if result['confirmation']['promote'] else
                                'Inspected-work gain does not meet fresh confirmation criteria; retain experimental model, preserve defaults.')
        else:
            result['fresh_confirmation_evaluated']=False
            result['remaining_sealed']=['livy-1','ammianus-14','quintilian-1']
            result['decision']='No clear replication gain under declared criteria; retain experimental model, preserve defaults and sealed works.'
    else:
        if development['selected_weight'] is not None:raise ValueError('Selected model still requires replication')
        result['decision']='No weight passes development; stop inference.'
    write(ROOT/'summary.json',result)
    print(json.dumps({'stage':'summary','selected_weight':result['selected_weight'],
          'fresh_confirmation_evaluated':result.get('fresh_confirmation_evaluated',False),
          'decision':result.get('decision','Fresh confirmation results retained; no automatic default change')}),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['build','screen','replication','confirm','summarize'])
    parser.add_argument('--output',type=Path,default=ROOT)
    args=parser.parse_args();ROOT=args.output;globals()[args.stage]()
