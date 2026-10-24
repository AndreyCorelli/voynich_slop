"""Ordering-versus-frequency diagnosis with fixed public permutation controls."""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import random
import statistics
import time
import gc
import shutil

from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.shuffle_contrast import ShuffleContrast
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.latin_corpus import write,sha
from voynich_smt.data.corpus import digest

PARENT=Path('experiments/results/scalable-latin-corpus-morphology/v2')
SOURCE=PARENT/'models/20000000/surface'
ROOT=Path('experiments/results/scalable-latin-shuffle-contrast/v1')


def design():
    return {'version':1,'parent_resources':str(SOURCE),'corpus_sha256':sha(PARENT/'corpus/corpus.json'),
      'objective':'LL(decoded) - mean LL(endpoint-preserving permutations of the same decoded sequence)',
      'null_shuffles':8,'primary_seed':2701,'confirmation_seed':9901,
      'score_units':'Unnormalized ordering contrast, not a language likelihood or calibrated probability',
      'development':['apuleius-1','curtius-3','suetonius-augustus'],
      'validation':'gellius-1; only after development passes; no sealed-test recovery',
      'gate':'On >=2/3 development works, positive reference beats frequency, null, median random, and median 10/25/50% corruptions; both fixed banks must pass',
      'inference':'If promoted: smoke development then matched three-seed validation comparisons; 4000 proposals per chain, record time and full-score checks',
      'evaluation':'Literal token recovery, agreement-first top10/20/50, unanimous count>=100; no known anchors supplied',
      'selection':'No parameter sweep; banks/settings fixed before outcomes; Caesar not used for selection',
      'limits':['Bigram order only; shuffle baseline may still be exploited by overfit keys.',
                'Frequency cancellation removes evidence as well as bias; decoding must be checked.',
                'Oracle controls are evaluation only, never search initial keys.']}


def fixture(record,inventory,base):
    plain=(PARENT/'corpus/evaluation-only'/f"{record['id']}.txt").read_text().split()
    stream,truth=generate((plain,),seed=83,tokenization='latin-iu-continuous-v1')
    root=ROOT/'fixtures'/record['id'];root.mkdir(parents=True,exist_ok=False)
    stream.save(root/'public/cipher.json');truth.save(root/'evaluation-only/truth.json')
    provenance=PARENT/'corpus/evaluation-only'/f"{record['id']}.json"
    write(root/'evaluation-only/source.json',{'record':record,'parent_provenance':json.loads(provenance.read_text()),
          'parent_provenance_sha256':sha(provenance),'cipher_sha256':stream.identity})
    types=sorted(set(plain));mapping={};used=set();missing=[]
    for w in types:
        try:wid=inventory.id(w);mapping[w]=wid;used.add(wid)
        except KeyError:missing.append(w)
    proxies=(i for i,c in enumerate(base.counts[:-1]) if not c and i not in used)
    for w in missing:mapping[w]=next(proxies)
    reference=[mapping[w] for w in plain]
    freq=DictionaryState.initialize(stream,base,method='frequency',seed=3).assignments
    nulltypes=dict(zip(types,(i for i,c in enumerate(base.counts[:-1]) if not c)))
    controls={'reference':reference,'frequency':[freq[c] for c in stream.documents[0]],
              'null':[nulltypes[w] for w in plain]}
    for level in (.1,.25,.5):
        for seed in range(3):
            rng=random.Random(1000+seed);chosen=rng.sample(types,max(2,int(len(types)*level)))
            values=[mapping[w] for w in chosen];rng.shuffle(values)
            key={**mapping,**dict(zip(chosen,values))}
            controls[f'corrupt-{level}-{seed}']=[key[w] for w in plain]
    for seed in range(3):
        rng=random.Random(seed);key=dict(zip(types,rng.sample(range(base.size),len(types))))
        controls[f'random-{seed}']=[key[w] for w in plain]
        shuffled=list(reference);rng.shuffle(shuffled);controls[f'shuffled-{seed}']=shuffled
    return controls,{'tokens':len(plain),'types':len(types),'missing_types':len(missing),
                     'missing_tokens':sum(w in set(missing) for w in plain)}


def evaluate_controls(base,contrasts,controls):
    results={}
    for name,words in controls.items():
        unigram=math.fsum(math.log(base.base_probability(w)) for w in words)
        ll=base.score(words)
        contrast={str(model.seed):model.score(words) for model in contrasts}
        results[name]={'lm':ll,'unigram':unigram,'residual':ll-unigram,'contrast':contrast}
    return results


def screen():
    ROOT.mkdir(parents=True,exist_ok=False);protocol=design();write(ROOT/'design.json',protocol)
    t=time.monotonic();inventory=Inventory(SOURCE/'inventory.sqlite')
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        contrasts=[ShuffleContrast(base,shuffles=8,seed=s) for s in (2701,9901)]
        records=json.loads((PARENT/'design.json').read_text())['heldouts']
        report={'works':[],'model_sha256':base.identity,'inventory_sha256':inventory.identity,
                'scope':'Evaluation-only reference controls; public-only candidate scoring'}
        for r in records:
            if r['split']!='development':continue
            controls,coverage=fixture(r,inventory,base);scores=evaluate_controls(base,contrasts,controls)
            banks={}
            for seed in (2701,9901):
                s={name:row['contrast'][str(seed)] for name,row in scores.items()};ref=s['reference']
                checks={'positive':ref>0,'frequency':ref>s['frequency'],'null':ref>s['null'],
                        'random':ref>statistics.median(s[f'random-{i}'] for i in range(3))}
                for level in (.1,.25,.5):checks[f'corrupt-{level}']=ref>statistics.median(s[f'corrupt-{level}-{i}'] for i in range(3))
                banks[str(seed)]={'checks':checks,'pass':all(checks.values())}
            report['works'].append({'id':r['id'],**coverage,'scores':scores,'banks':banks})
            write(ROOT/'development.json',report)
            print(json.dumps({'stage':'screen','work':r['id'],'banks':banks,
                'reference':scores['reference'],'frequency':scores['frequency']}),flush=True)
        report['pass']=all(sum(w['banks'][str(seed)]['pass'] for w in report['works'])>=2 for seed in (2701,9901))
        report['seconds']=time.monotonic()-t
        write(ROOT/'development.json',report)
        write(ROOT/'decision.json',{'promote':report['pass'],'rule':protocol['gate'],
             'note':'Gate success is not evidence of recovered anchors; compare actual inference next.'})
        if report['pass']:
            output=ROOT/'resources';output.mkdir();os.link(SOURCE/'inventory.sqlite',output/'inventory.sqlite')
            contrasts[0].save(output/'model.sqlite')
        return report
    finally:inventory.close()


def measure(resources,output,fixture_root):
    from benchmarks.scalable_english_evaluate import evaluate
    from benchmarks.scalable_english_consensus import collect
    from voynich_smt.word_mapping.scalable.data import CipherStream
    from voynich_smt.word_mapping.scalable.trigram import load_model
    evaluation=evaluate(resources,output,fixture_root/'evaluation-only/truth.json')
    public=(json.loads((output/'consensus-public.json').read_text()) if (output/'consensus-public.json').exists()
            else collect(output,output/'consensus-public.json'))
    assert public['protocol']==json.loads((output/'inference.json').read_text())['protocol']
    assert public['input_inference_sha256']==digest(json.loads((output/'inference.json').read_text()))
    truth=json.loads((fixture_root/'evaluation-only/truth.json').read_text())
    stream=CipherStream.load(output/'public/cipher.json');counts=Counter(stream.documents[0])
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        base=getattr(model,'bigram',model)
        check=ShuffleContrast(base,shuffles=8,seed=9901)
        inference=json.loads((output/'inference.json').read_text())
        rows=[]
        for r in public['rows']:
            word=inventory.word(r['word_id'])
            rows.append({**r,'word':word,'count':counts[r['cipher']],
                         'original':truth['decoding'][r['cipher']],'correct':word==truth['decoding'][r['cipher']]})
        rows.sort(key=lambda r:(-r['votes'],-r['count'],r['cipher']))
        def metric(selected):
            good=[r for r in selected if r['correct']];n=sum(r['count'] for r in selected)
            return {'types':len(selected),'correct_types':len(good),
                    'type_precision':len(good)/len(selected) if selected else None,
                    'token_precision':sum(r['count'] for r in good)/n if n else None,
                    'token_coverage':n/len(stream.documents[0])}
        primary=[r for r in rows if len(inference['runs'])>=3 and r['votes']==len(inference['runs']) and r['count']>=100]
        report={'top':{str(n):metric(rows[:n]) for n in (10,20,50)},'primary':metric(primary),
                'primary_rows':primary,'rows':rows,
                'alternate_bank_scores':[{'seed':r['seed'],'score':check.score(r['joint_archive'][0]['assignments'][c]
                                              for c in stream.documents[0])} for r in inference['runs']],
                'alternate_bank_scope':'Pure ordering score at seed 9901 for every method; excludes any frequency regularizer.',
                'warning':'Raw agreement only; no old confidence calibrator applies.'}
        write(output/'anchors-evaluation.json',report)
        chosen=next(r for r in inference['runs'] if r['seed']==inference['selected_seed'])['joint_archive'][0]['assignments']
        original=truth['plaintext'][0];lines=['# Fixed 100-token excerpts','']
        for offset in (0,len(original)//2):
            lines.extend([f'## Offset {offset}','','Original:','',' '.join(original[offset:offset+100]),'',
              'Restored:','',' '.join(inventory.word(chosen[c]) for c in stream.documents[0][offset:offset+100]),''])
        (output/'inspection.md').write_text('\n'.join(lines)+'\n')
        return {'mean_token_accuracy':evaluation['mean_score_selected_token_accuracy'],
                'selected_token_accuracy':evaluation['selected_token_accuracy'],
                'runs':evaluation['runs'],'top':report['top'],'primary':report['primary']}
    finally:inventory.close()


def isolated_fixture(fixture_root,name):
    isolated=ROOT/'isolated-fixtures'/name
    if isolated.exists():return isolated
    shutil.copytree(fixture_root/'public',isolated/'public')
    private=fixture_root/'evaluation-only'
    if not private.exists():private=fixture_root/'evaluation-unavailable-during-search'
    shutil.copytree(private,isolated/'evaluation-only')
    return isolated


def trial(resources,fixture_root,output,*,seeds,proposals,initialization='frequency'):
    from benchmarks.scalable_english_run import run
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    fixture_root=isolated_fixture(fixture_root,output.name)
    private=fixture_root/'evaluation-only';hidden=fixture_root/'evaluation-unavailable-during-search'
    private.rename(hidden)
    try:
        run(resources,fixture_root/'public/cipher.json',output,seeds=seeds,
             config=SearchConfig(initialization=initialization,proposals=proposals,budget_seconds=600,reserve_seconds=10),trace=True)
    finally:hidden.rename(private)
    return measure(resources,output,fixture_root)


def smoke():
    assert json.loads((ROOT/'decision.json').read_text())['promote']
    write(ROOT/'smoke-design.json',{'work':'apuleius-1','seeds':[3],'proposals':500,
          'initialization':'frequency','purpose':'Numerical and public-only smoke; no parameter selection'})
    result={}
    for name,resources in [('surface',SOURCE),('contrast',ROOT/'resources')]:
        result[name]=trial(resources,ROOT/'fixtures/apuleius-1',ROOT/f'smoke-{name}',seeds=(3,),proposals=500)
        gc.collect()
        write(ROOT/'smoke.json',result)
    return result


def prepare_validation_fixture():
    if (ROOT/'validation-controls.json').exists():return
    record=next(r for r in json.loads((PARENT/'design.json').read_text())['heldouts'] if r['id']=='gellius-1')
    inventory=Inventory(SOURCE/'inventory.sqlite')
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        if not (ROOT/'validation-controls.json').exists():
            controls,coverage=fixture(record,inventory,base)
            report=evaluate_controls(base,[ShuffleContrast(base,seed=s) for s in (2701,9901)],controls)
            write(ROOT/'validation-controls.json',{'coverage':coverage,'scores':report})
            del controls
        del base;gc.collect()
    finally:inventory.close()


def validation():
    assert json.loads((ROOT/'decision.json').read_text())['promote']
    write(ROOT/'validation-design.json',{'work':'gellius-1','seeds':[3,5,7],'proposals':4000,
          'initialization':'frequency','budget_seconds_per_chain':600,
          'pairing':'Same full inventory, training and initial keys; objective-aware pair-lift ranking only for contrast',
          'decision':'No parameter selection; compare all seeds, top50 and frequent primary anchors',
          'limits':'One validation author; no sealed test or Caesar fitting; shared initial dictionary can create false agreement.'})
    prepare_validation_fixture()
    result={}
    for name,resources in [('surface',SOURCE),('contrast',ROOT/'resources')]:
        output=ROOT/f'validation-{name}'
        if (output/'inference.json').exists():
            isolated=isolated_fixture(ROOT/'fixtures/gellius-1',output.name+'-evaluation')
            result[name]=measure(resources,output,isolated)
        else:
            result[name]=trial(resources,ROOT/'fixtures/gellius-1',output,seeds=(3,5,7),proposals=4000)
        gc.collect();write(ROOT/'validation-comparison.json',result)
    return result


def regularize():
    if not (ROOT/'regularization-design.json').exists():
        write(ROOT/'regularization-design.json',{
          'motivation':'Retain lexical evidence after pure-contrast development smoke.',
          'weights':[0,.1,.25,.5],
          'selection':'Largest frequency weight passing reference discrimination on >=2/3 development works under BOTH banks; no validation recovery used.',
          'score':'Ordering contrast + gamma * sum token log source unigram probability; EOS excluded',
          'inference':'Selected gamma: 500-step development smoke, then three 4000-step frequency chains on Gellius.',
          'limits':'Exploratory follow-up to development smoke; not normalized likelihood.'})
    protocol=json.loads((ROOT/'regularization-design.json').read_text())
    protocol['positive_check']='Ordering component remains positive; a regularized absolute score need not be positive.'
    write(ROOT/'regularization-design.json',protocol)
    development=json.loads((ROOT/'development.json').read_text());grid=[]
    for gamma in protocol['weights']:
        banks={}
        for seed in ('2701','9901'):
            works=[]
            for w in development['works']:
                s={name:r['contrast'][seed]+gamma*r['unigram'] for name,r in w['scores'].items()}
                ref=s['reference'];checks={'positive_order':w['scores']['reference']['contrast'][seed]>0,
                    'frequency':ref>s['frequency'],'null':ref>s['null'],
                    'random':ref>statistics.median(s[f'random-{i}'] for i in range(3))}
                for level in (.1,.25,.5):checks[f'corrupt-{level}']=ref>statistics.median(s[f'corrupt-{level}-{i}'] for i in range(3))
                works.append({'id':w['id'],'scores':s,'checks':checks,'pass':all(checks.values())})
            banks[seed]={'works':works,'pass':sum(w['pass'] for w in works)>=2}
        grid.append({'weight':gamma,'banks':banks,'pass':all(r['pass'] for r in banks.values())})
    selected=max((r['weight'] for r in grid if r['pass']),default=None)
    write(ROOT/'regularization-selection.json',{'grid':grid,'selected_weight':selected,'selection':protocol['selection']})
    if selected is None or selected==0:return
    resources=ROOT/'resources-regularized';resources.mkdir(exist_ok=False)
    os.link(SOURCE/'inventory.sqlite',resources/'inventory.sqlite');inventory=Inventory(SOURCE/'inventory.sqlite')
    try:
        base=SparseBigram.load(SOURCE/'model.sqlite',inventory)
        model=ShuffleContrast(base,frequency_weight=selected);model.save(resources/'model.sqlite')
        del model,base;gc.collect()
    finally:inventory.close()
    print(json.dumps({'stage':'regularized-selection','weight':selected}),flush=True)
    result={}
    result['smoke']=trial(resources,ROOT/'fixtures/apuleius-1',ROOT/'smoke-regularized',seeds=(3,),proposals=500)
    write(ROOT/'regularized-comparison.json',result);gc.collect()
    prepare_validation_fixture()
    result['validation']=trial(resources,ROOT/'fixtures/gellius-1',ROOT/'validation-regularized',seeds=(3,5,7),proposals=4000)
    write(ROOT/'regularized-comparison.json',result)
    return result


def summarize():
    main=json.loads((ROOT/'validation-comparison.json').read_text())
    regularized=json.loads((ROOT/'regularized-comparison.json').read_text())
    result={'surface':main['surface'],'contrast':main['contrast'],'regularized':regularized['validation']}
    summary={'methods':{},'diagnosis':[],'defaults_changed':False,'sealed_test_recovery_evaluated':False,
         'selection':'Development controls chose gamma; validation recovery is reported for all methods, no best seed chosen with truth.',
         'scope':'One held-out validation work; whole-word Latin cipher, not Voynich evidence.'}
    protocols=[];initial_keys=[]
    import gzip
    for name,data in result.items():
        folder=ROOT/('validation-'+name)
        inference=json.loads((folder/'inference.json').read_text())
        normalized=dict(inference['protocol']);normalized.pop('model_sha256');normalized.pop('scope')
        protocols.append(normalized)
        assert all(r['step']==4000 and r['stop_reason']=='proposal_limit' for r in inference['runs'])
        keys=[]
        for r in inference['runs']:
            with gzip.open(folder/f"traces/seed-{r['seed']}.jsonl.gz",'rt') as f:
                first=json.loads(next(f));assert first['kind']=='initial';keys.append(first['assignments'])
        initial_keys.append(keys)
        anchors=json.loads((folder/'anchors-evaluation.json').read_text())
        majority=[r for r in anchors['rows'] if r['strict_majority']]
        summary['methods'][name]={
          'mean_token_accuracy':data['mean_token_accuracy'],'selected_token_accuracy':data['selected_token_accuracy'],
          'per_seed':[{'seed':r['seed'],'token_accuracy':r['score_selected_best']['token_accuracy']} for r in data['runs']],
          'top':data['top'],'primary':data['primary'],'primary_rows':anchors['primary_rows'],
          'majority_pool':{'types':len(majority),'correct_types':sum(r['correct'] for r in majority)},
          'search_seconds':sum(r['elapsed_seconds'] for r in inference['runs']),
          'peak_rss_bytes':max(r['peak_rss_bytes'] for r in inference['runs']),
          'alternate_ordering_bank_scores':anchors['alternate_bank_scores']}
    assert protocols[0]==protocols[1]==protocols[2]
    assert initial_keys[0]==initial_keys[1]==initial_keys[2]
    development=json.loads((ROOT/'development.json').read_text())
    for w in development['works']:
        ref=w['scores']['reference'];wrong=w['scores']['frequency']
        summary['diagnosis'].append({'work':w['id'],
             'wrong_key_unigram_advantage':wrong['unigram']-ref['unigram'],
             'reference_residual_advantage':ref['residual']-wrong['residual'],
             'reference_ordering_score':ref['contrast']['2701'],
             'frequency_ordering_score':wrong['contrast']['2701']})
    summary['paired_protocols_verified']=True
    summary['identical_initial_keys_verified']=True
    summary['decision']='Retain experimental options; no defaults change. No robust overall recovery improvement on this validation work.'
    baseline=summary['methods']['surface']
    for name,row in summary['methods'].items():
        row['mean_accuracy_change']=row['mean_token_accuracy']-baseline['mean_token_accuracy']
    write(ROOT/'summary.json',summary)
    print(json.dumps({name:{k:r[k] for k in ('mean_token_accuracy','top','primary')} for name,r in summary['methods'].items()}),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['screen','smoke','validation','regularize','summarize'])
    parser.add_argument('--output',type=Path,default=ROOT)
    args=parser.parse_args();ROOT=args.output;globals()[args.stage]()
