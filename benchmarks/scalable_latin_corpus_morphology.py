"""Versioned larger-corpus and ambiguity-preserving morphology experiment."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import time
import os

from voynich_smt.word_mapping.scalable.latin_corpus import census, documents, sha, write

ROOT = Path('experiments/results/scalable-latin-corpus-morphology/v2')
SOURCE = Path('data/raw/latin-corpus-library')


def design():
    return {'version': 1, 'source': {'url': 'https://github.com/cltk/lat_text_latin_library',
         'commit': subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'], text=True).strip(),
         'license': 'Upstream Public Domain Mark 1.0 declaration; retained with raw collection',
         'license_sha256': sha(SOURCE/'LICENSE.md'), 'readme_sha256': sha(SOURCE/'README.md')},
      'heldouts': [
        {'id':'apuleius-1','author':'Apuleius','split':'development','path':'apuleius/apuleius1.txt'},
        {'id':'curtius-3','author':'Curtius','split':'development','path':'curtius/curtius3.txt'},
        {'id':'suetonius-augustus','author':'Suetonius','split':'development','path':'suetonius/suet.aug.txt'},
        {'id':'gellius-1','author':'Gellius','split':'validation','path':'gellius/gellius1.txt'},
        {'id':'livy-1','author':'Livy','split':'sealed-test','path':'livy/liv.1.txt'},
        {'id':'ammianus-14','author':'Ammianus','split':'sealed-test','path':'ammianus/14.txt'},
        {'id':'quintilian-1','author':'Quintilian','split':'sealed-test','path':'quintilian/quintilian.institutio1.txt'}],
      'excluded_authors':['Caesar','Apuleius','Curtius','Suetonius','Gellius','Livy','Ammianus','Quintilian'],
      'training_directories': {'cicero':'Cicero','augustine':'Augustine','bible':'Jerome',
        'tertullian':'Tertullian','lactantius':'Lactantius','jerome':'Jerome',
        'columella':'Columella','cato':'Cato','tacitus':'Tacitus','nepos':'Nepos',
        'justin':'Justin','orosius':'Orosius','isidore':'Isidore','erasmus':'Erasmus',
        'bede':'Bede','aquinas':'Aquinas','ambrose':'Ambrose','arnobius':'Arnobius',
        'cassiodorus':'Cassiodorus','gregorytours':'GregoryTours','pauldeacon':'PaulDeacon',
        'frontinus':'Frontinus','fronto':'Fronto','capellanus':'Capellanus',
        'albertanus':'Albertanus','abelard':'Abelard','fulgentius':'Fulgentius',
        'leothegreat':'Leo','justinian':'Justinian','theodosius':'Theodosius',
        'malaterra':'Malaterra','kempis':'Kempis','williamtyre':'WilliamTyre',
        'ottofreising':'OttoFreising'},
      'excluded_filename_fragments':['capitula','fragment','frag.', 'index', 'praefatio'],
      'minimum_document_tokens':500,'maximum_target_tokens':35000,
      'training_sizes':[100000,1000000,5000000,20000000],
      'channel_weights':[[1,0,0],[.75,.25,0],[.75,0,.25],[.5,.25,.25],[.25,.375,.375]],
      'analysis_iterations':3,'analysis_prior':1.,'state_alpha':1.,'emission_beta':1.,'channel_reserve':.01,
      'search':{'seeds':[3,5,7],'proposals':4000,'initializations':['random','frequency']},
      'gate':'Reference beats frequency, null and median corruption at each level on >=2/3 development works',
      'selection':'Development only; validation before opening sealed test; no Caesar fitting',
      'normalization':'latin-iu-continuous-v1',
      'note':'Whole source book files, one continuous stream each; line-format filtering favors prose.'}


def prepare():
    ROOT.mkdir(parents=True,exist_ok=False)
    protocol=design(); write(ROOT/'design.json',protocol)
    t=time.monotonic(); report=census(SOURCE,ROOT/'corpus',protocol)
    write(ROOT/'corpus-build.json',{'seconds':time.monotonic()-t,'training_tokens':report['training_tokens'],
          'documents':len(report['documents']),'source':protocol['source']})
    print(json.dumps({'stage':'corpus','tokens':report['training_tokens'],'documents':len(report['documents'])}),flush=True)


def selected(size):
    corpus=json.loads((ROOT/'corpus/corpus.json').read_text())
    ids=set(corpus['subsets'][str(size)]['documents'])
    return [r for r in corpus['documents'] if r['id'] in ids]


def pilot():
    from voynich_smt.word_mapping.morphology import WhitakerAnnotator
    from voynich_smt.word_mapping.scalable.search import peak_rss
    t=time.monotonic(); counts=Counter(); edges=Counter(); tokens=0
    for doc in documents(ROOT/'corpus',selected(100000)):
        counts.update(doc); edges.update(zip(('<BOS>',)+doc,doc+('<EOS>',))); tokens+=len(doc)
    count_seconds=time.monotonic()-t
    annotator=WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    forms=sorted(counts); t=time.monotonic(); known=0; analyses=0
    for form in forms:
        result=annotator.annotate(form); known+=bool(result); analyses+=len(result)
    morph_seconds=time.monotonic()-t
    report={'tokens':tokens,'types':len(counts),'edges':len(edges),'count_seconds':count_seconds,
        'morphology_seconds':morph_seconds,'analyzed_types':known,'analyses':analyses,
        'types_per_second':len(forms)/morph_seconds,'peak_rss_bytes':peak_rss(),
        'rough_2_6m_analysis_seconds':2600000*morph_seconds/len(forms),
        'caveat':'Dictionary-only forms can have different throughput/ambiguity; no build-time guarantee.'}
    write(ROOT/'pilot.json',report); print(json.dumps(report),flush=True)


def resources():
    from itertools import chain
    from benchmarks.scalable_latin_caesar import lexicon_words, LEXICON
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.morphology_index import MorphologyIndex
    base=ROOT/'resources'; base.mkdir(exist_ok=True)
    records=selected(20000000)
    path=base/'inventory.sqlite'
    inventory=(Inventory(path) if path.exists() else Inventory.build(path,
       chain(lexicon_words(LEXICON),(w for doc in documents(ROOT/'corpus',records) for w in doc))))
    try:
        write(base/'inventory-report.json',{'size':inventory.size,'sha256':inventory.identity,
              'policy':'Entire generated default lexicon union all admitted training forms; no heldout access',
              'lexicon_sha256':sha(LEXICON)})
        MorphologyIndex.build(base/'morphology',inventory,Path('data/vendor/whitakers-words'))
    finally: inventory.close()


def train(size):
    import numpy as np
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.morphology_index import MorphologyIndex
    from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
    from voynich_smt.word_mapping.scalable.config import ModelConfig
    from voynich_smt.word_mapping.scalable.factored_lm import FactoredLatinModel,analysis_weights
    from voynich_smt.word_mapping.scalable.latin_annotations import source_evidence
    from voynich_smt.word_mapping.scalable.search import peak_rss
    base=ROOT/'resources'; out=ROOT/f'models/{size}';out.mkdir(parents=True,exist_ok=True)
    protocol={'corpus_sha256':sha(ROOT/'corpus/corpus.json'),
              'design_sha256':sha(ROOT/'design.json'),'size':size,
              'method':'normalized-local-factors-v1','analysis_estimator':'bounded-unigram-soft-allocation-v1',
              'state_alpha':1.,'emission_beta':1.,'channel_reserve':.01}
    protocol_path=out/'training-protocol.json'
    if protocol_path.exists() and json.loads(protocol_path.read_text())!=protocol:
        raise ValueError('Training resume inputs changed')
    write(protocol_path,protocol)
    inventory=Inventory(base/'inventory.sqlite')
    try:
        surface=out/'surface';surface.mkdir(exist_ok=True)
        if not (surface/'inventory.sqlite').exists():os.link(base/'inventory.sqlite',surface/'inventory.sqlite')
        t=time.monotonic()
        if (surface/'model.sqlite').exists():model=SparseBigram.load(surface/'model.sqlite',inventory)
        else:
            docs=((inventory.id(w) for w in doc) for doc in documents(ROOT/'corpus',selected(size)))
            model=SparseBigram.train(inventory,docs,config=ModelConfig(language='la',tokenization='latin-iu-continuous-v1'))
            model.save(surface/'model.sqlite')
        surface_seconds=time.monotonic()-t
        print(json.dumps({'stage':'surface','size':size,'seconds':surface_seconds,'edges':len(model.edges)}),flush=True)
        index=MorphologyIndex(base/'morphology',inventory)
        paths=[(c,Path(f'data/latin-grammar-benchmark/{c}-r2.17/la_{c}-ud-train.conllu')) for c in ('proiel','perseus')]
        evidence,annotation_report=source_evidence(index,inventory,paths,set(design()['excluded_authors']))
        write(out/'annotation-report.json',annotation_report)
        t=time.monotonic(); weights,trace=analysis_weights(index,model.counts,supervised=evidence,iterations=3)
        np.save(out/'analysis-weights.npy',weights)
        write(out/'analysis-fit.json',{'trace':trace,'method':'fixed-three-step source-unigram soft allocation; not likelihood EM',
                                     'supervised':annotation_report,'weights_sha256':sha(out/'analysis-weights.npy')})
        training={'fit':json.loads((out/'analysis-fit.json').read_text()),'corpus_tokens':sum(r['tokens'] for r in selected(size))}
        factor=FactoredLatinModel(model,index,weights,training=training)
        factored_seconds=time.monotonic()-t
        controls=gates(inventory,model,factor,out)
        write(out/'gates.json',controls)
        # Save only variants passing predeclared gates, not all copies of large
        # count tables. The full fitted analysis and gate outcomes are retained.
        passing=[r for r in controls['variants'] if r['pass']]
        factor_passing=[r for r in passing if r['mixture']!=[1,0,0]]
        if factor_passing:
            chosen=max(factor_passing,key=lambda r:r['reference_mean_log_probability'])
            factor.mixture=tuple(chosen['mixture']);factor._probability.cache_clear()
            dest=out/'factored';dest.mkdir(exist_ok=True)
            if not (dest/'inventory.sqlite').exists():os.link(base/'inventory.sqlite',dest/'inventory.sqlite')
            factor.save(dest/'model.sqlite')
            write(out/'selection.json',{'selected':chosen,'criterion':'Highest development reference per-token score among passing morphology variants',
                  'note':'Development likelihood selection; sealed test unopened.'})
        write(out/'training-report.json',{'requested_size':size,'tokens':training['corpus_tokens'],
          'inventory_forms':inventory.size,'observed_forms':sum(bool(c) for c in model.counts[:-1]),
          'edges':len(model.edges),'surface_seconds':surface_seconds,'factored_seconds':factored_seconds,
          'peak_rss_bytes':peak_rss(),'passing_variants':len(passing),'factor_passing_variants':len(factor_passing)})
        print(json.dumps({'stage':'gates','size':size,'pass':[r['mixture'] for r in passing]}),flush=True)
    finally:inventory.close()


def summarize():
    corpus=json.loads((ROOT/'corpus/corpus.json').read_text())
    records=[]
    for size in (1000000,5000000,20000000):
        base=ROOT/f'models/{size}'
        report=json.loads((base/'training-report.json').read_text())
        gates_report=json.loads((base/'gates.json').read_text())
        for v in gates_report['variants']:
            total=sum(w['tokens']+1 for w in v['works'])
            records.append({'requested_size':size,'training_tokens':report['tokens'],
                'mixture':v['mixture'],'passing_works':sum(w['pass'] for w in v['works']),
                'reference_mean_log_probability':v['reference_mean_log_probability'],
                'reference_minus_frequency_per_token':sum(w['scores']['reference']-w['scores']['frequency'] for w in v['works'])/total,
                'pass':v['pass']})
    any_pass=any(r['pass'] for r in records)
    decision={'stage':'development objective screening','results':records,
      'any_pass':any_pass,'training_tokens_available':corpus['training_tokens'],
      'sealed_test_recovery_evaluated':False,'default_changed':False,
      'decision':('Surviving variants require validation before sealed-test decoding.' if any_pass else
                  'Stop full decoding for rejected variants. Preserve resources and implementations.'),
      'scope':'Objective screening only; no recovery improvement is measured.',
      'implementation_departures':[
          'Available corpus is 5.94M clean tokens, not 20M; whole book files remain separate.',
          'Analysis estimator uses three fixed source-unigram soft-allocation steps, not validated likelihood EM.',
          'Source annotation crosswalk constrains compatible POS/features; it does not force lemma-string identities.',
          'Current memory fits measured runs; existing sparse in-memory counts retained, compact disk storage deferred.',
          'No survivor means retrieval recall, full searches, validation selection and sealed-test decoding are not run.']}
    write(ROOT/'summary.json',decision)
    print(json.dumps({'stage':'summary','any_pass':decision['any_pass'],'training_tokens':corpus['training_tokens']}))


def gates(inventory,surface,factor,out):
    """Evaluation-side controls only. No keys are supplied to actual inference."""
    import math
    import random
    import statistics
    from voynich_smt.word_mapping.scalable.data import generate
    from voynich_smt.word_mapping.scalable.state import DictionaryState
    variants=[{'mixture':w,'works':[]} for w in design()['channel_weights']]
    for record in design()['heldouts']:
        if record['split']!='development':continue
        plain=(ROOT/'corpus/evaluation-only'/f"{record['id']}.txt").read_text().split()
        types=sorted(set(plain)); mapping={}; used=set();missing=[]
        for word in types:
            try:wid=inventory.id(word);mapping[word]=wid;used.add(wid)
            except KeyError:missing.append(word)
        proxies=(i for i,c in enumerate(surface.counts[:-1]) if not c and i not in used)
        for word in missing:mapping[word]=next(proxies)
        reference=[mapping[w] for w in plain]
        stream,_=generate((plain,),seed=83,tokenization='latin-iu-continuous-v1')
        frequency=DictionaryState.initialize(stream,surface,method='frequency',seed=3).assignments
        freqwords=[frequency[c] for c in stream.documents[0]]
        nulltypes={w:i for w,i in zip(types,(i for i,c in enumerate(surface.counts[:-1]) if not c))}
        null=[nulltypes[w] for w in plain]
        controls={'frequency':freqwords,'null':null}
        for level in (.1,.25,.5):
            for seed in range(3):
                rng=random.Random(1000+seed);selectedtypes=rng.sample(types,max(2,int(len(types)*level)))
                values=[mapping[w] for w in selectedtypes];rng.shuffle(values)
                corrupt={**mapping,**dict(zip(selectedtypes,values))}
                controls[f'corrupt-{level}-{seed}']=[corrupt[w] for w in plain]
        for seed in range(3):
            rng=random.Random(seed);key=rng.sample(range(surface.size),len(types))
            rand=dict(zip(types,key));controls[f'random-{seed}']=[rand[w] for w in plain]
            shuffled=list(reference);rng.shuffle(shuffled);controls[f'shuffle-{seed}']=shuffled
        # Cache the three component log probabilities on each reference/control
        # edge. Repeated mixture evaluation never refits counts or analyses.
        allstreams={'reference':reference,**controls}; scores={}
        for name,sequence in allstreams.items():
            edges=Counter(zip((-1,)+tuple(sequence),tuple(sequence)+(surface.eos,)))
            components=[(n,(surface.probability(a,b),*(c.probability(a,b) for c in factor.channels)))
                        for (a,b),n in edges.items()]
            for variant in variants:
                mix=variant['mixture']
                score=math.fsum(n*math.log(sum(w*p for w,p in zip(mix,probs))) for n,probs in components)
                start=sum(w*p for w,p in zip(mix,(surface.probability(-1,surface.eos),
                          *(c.probability(-1,surface.eos) for c in factor.channels))))
                scores.setdefault(tuple(mix),{})[name]=score-math.log1p(-start)
        for variant in variants:
            s=scores[tuple(variant['mixture'])];ref=s['reference']
            checks={'beats_frequency':ref>s['frequency'],'beats_null':ref>s['null']}
            for level in (.1,.25,.5):
                checks[f'beats_corrupt_{level}']=ref>statistics.median(s[f'corrupt-{level}-{seed}'] for seed in range(3))
            missing_set=set(missing)
            variant['works'].append({'id':record['id'],'tokens':len(plain),'types':len(types),'missing_types':len(missing),
                'missing_tokens':sum(w in missing_set for w in plain),
                'scores':s,'checks':checks,'pass':all(checks.values())})
    for variant in variants:
        variant['pass']=sum(r['pass'] for r in variant['works'])>=2
        variant['reference_mean_log_probability']=sum(r['scores']['reference'] for r in variant['works'])/sum(r['tokens']+1 for r in variant['works'])
    return {'rule':design()['gate'],'variants':variants,'truth_role':'Evaluation controls only; no inference initialization',
            'sealed_test_opened':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','pilot','resources','train','summarize'])
    parser.add_argument('--size',type=int,default=1000000)
    parser.add_argument('--output',type=Path,default=ROOT,
                        help='Versioned experiment root; prepare requires a new directory')
    args=parser.parse_args()
    ROOT=args.output
    if args.stage=='train':train(args.size)
    else:globals()[args.stage]()
