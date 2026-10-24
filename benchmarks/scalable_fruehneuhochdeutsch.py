"""ReF resource census and English-algorithm replication, staged and versioned."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile
import time

from voynich_smt.word_mapping.scalable.historical_german import parse_cora,TOKENIZATION
from voynich_smt.word_mapping.scalable.latin_corpus import sha,write

RAW=Path('data/raw/scalable-fruehneuhochdeutsch')
ROOT=Path('experiments/results/scalable-fruehneuhochdeutsch/v1')


def corpus():
    with tarfile.open(RAW/'ReF-v1.0.2.tar.gz') as archive:
        for member in sorted(archive.getmembers(),key=lambda m:m.name):
            if member.isfile() and member.name.endswith('.xml') and any('/'+p+'/' in member.name for p in ('ref-mlu','ref-rub')):
                data=archive.extractfile(member).read()
                yield member.name,hashlib.sha256(data).hexdigest(),parse_cora(data)


def census():
    ROOT.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    with tarfile.open(RAW/'ReF-v1.0.2.tar.gz') as archive:
        for name in ('LICENSE','README.md'):
            member=next(m for m in archive if m.name.endswith('/'+name))
            (ROOT/name).write_bytes(archive.extractfile(member).read())
    download=json.loads((RAW/'download.json').read_text())
    if sha(RAW/download['file'])!=download['sha256']:raise ValueError('Raw archive changed')
    write(ROOT/'design.json',{'release':download,'tokenization':TOKENIZATION,
        'license':'CC BY-SA 4.0 per archive LICENSE and README; repository metadata says CC BY 4.0 and is retained separately',
        'citation':'Wegera; Solms; Demske; Dipper (2021), Referenzkorpus Frühneuhochdeutsch, Version 1.0; archive v1.0.2, Zenodo 5793616',
        'primary_surface':'CorA tok_anno utf; NFC lowercase, long-s folding, remove ZWJ; retain combining marks, abbreviations, u/v and i/j; no lemma modernization',
        'excluded_component':'ReF.UP TIGER overlaps CorA sources and has different tokenization; not concatenated or independently counted',
        'continuity':'Split on numeric page jumps/backtracking and unsupported lexical tokens; no sentence resets. Unmarked excerpt gaps remain a limitation.',
        'titles_and_foreign_language':'Retained, like the English continuous text; annotations do not select topic or language spans',
        'training_scope':'All admitted CorA work segments after frozen held-out author/work exclusions and overlap screen',
        'split_status':'Census only: no source/model or decipherment selection using recovery',
        'english_reference':'experiments/results/scalable-english/independent-wells-frequency-8000-v2/protocol.json',
        'main_proposals':8000,'pilot_proposals':4000,'seeds':[3,5,7]})
    rows=[];totals=Counter()
    for member,checksum,doc in corpus():
        row={'id':doc.identifier,'member':member,'source_sha256':checksum,'metadata':doc.metadata,
            'statistics':doc.statistics,'segments':[len(s) for s in doc.segments]}
        rows.append(row);totals.update({k:v for k,v in doc.statistics.items() if k!='longest_segment'})
        # Census contains metadata/counts only; parsed text remains in the archive.
        if len(rows)%40==0:print(json.dumps({'stage':'census','documents':len(rows),'seconds':time.monotonic()-start}),flush=True)
    write(ROOT/'census.json',{'documents':rows,'totals':dict(totals),
        'longest_segment':max(r['statistics']['longest_segment'] for r in rows),'seconds':time.monotonic()-start})
    for r in sorted(rows,key=lambda r:-r['statistics']['longest_segment'])[:20]:
        print(r['id'],r['statistics']['surface_tokens'],r['statistics']['longest_segment'],r['metadata'].get('text'),r['metadata'].get('text-author'),r['metadata'].get('genre'),flush=True)


def build():
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
    from voynich_smt.word_mapping.scalable.config import ModelConfig
    from voynich_smt.word_mapping.scalable.data import generate
    from voynich_smt.word_mapping.scalable.latin_corpus import shingles
    output=ROOT/'resources';output.mkdir(exist_ok=False)
    splits={'development':['F137','F332','F064'],'validation':['F019','F283'],'sealed':['F001','F161']}
    aliases=['hartlieb','gelnhausen','merswin','durandus','wurm','megenberg','passau']
    write(ROOT/'splits.json',{'splits':splits,'author_exclusion_fragments':aliases,
        'selection':'Seven longest explicitly genre-P prose sources with identifiable named authors, excluding the nonspecific Stadtschreiber Heinrich; order frozen from census before recovery',
        'pilot':'F137 longest retained segment, first 4000 words, seed83',
        'overlap':'Reject each training segment sharing any exact 12-word window with any reserved work segment; report losses. This is an exact-surface screen, not proof against paraphrase or spelling-variant duplicates.',
        'inventory':'Observed admitted training forms only, no heldout-word insertion; dictionary expansion deferred',
        'continuity':'No 35000-word fixture under current conservative adapter; long-text milestone deferred'})
    heldout=set(x for xs in splits.values() for x in xs)
    docs=list(corpus());targets={d.identifier:d for _,_,d in docs if d.identifier in heldout}
    if set(targets)!=heldout:raise ValueError('Missing reserved source')
    excluded=set().union(*(set(shingles(segment)) for d in targets.values() for segment in d.segments))
    training=[];records=[];losses=[];forms=set();seen=set();total=0
    for member,checksum,d in docs:
        if d.identifier in heldout or any(a in d.metadata.get('text-author','').lower() for a in aliases):
            losses.append({'id':d.identifier,'reason':'heldout_work_or_author','tokens':sum(map(len,d.segments))});continue
        for index,segment in enumerate(d.segments):
            if len(segment)<2:continue
            overlap=len(set(shingles(segment))&excluded)
            fingerprint=hashlib.sha256(' '.join(segment).encode()).hexdigest()
            if overlap or fingerprint in seen:
                losses.append({'id':d.identifier,'segment':index,'tokens':len(segment),'reason':'exact_12gram_overlap' if overlap else 'exact_duplicate','overlapping_windows':overlap});continue
            seen.add(fingerprint);training.append(segment);forms.update(segment);total+=len(segment)
            records.append({'id':d.identifier,'member':member,'source_sha256':checksum,'segment':index,'tokens':len(segment),'surface_sha256':fingerprint})
    # Resources are built without accessing target types or labels.
    inventory=Inventory.build(output/'inventory.sqlite',forms,tokenization=TOKENIZATION)
    try:
        model=SparseBigram.train(inventory,((inventory.id(w) for w in segment) for segment in training),config=ModelConfig(language='de',tokenization=TOKENIZATION))
        model.save(output/'model.sqlite')
        report={'benchmark_role':'historical-german-independent-source-resources','training_tokens':total,'training_segments':len(training),
            'training_works':len({r['id'] for r in records}),'inventory_forms':inventory.size,'inventory_sha256':inventory.identity,
            'model_sha256':model.identity,'observed_edges':len(model.edges),'tokenization':TOKENIZATION,
            'limitations':['Historical surface spellings and abbreviations retained; source tok_anno segmentation is given.',
                'Observed-training vocabulary only; no independent historical dictionary yet.',
                'Short source excerpts and conservative gap splits differ from the continuous 35k English benchmark.',
                'Exact overlap screen cannot rule out spelling-variant, paraphrased or unidentified author overlap.',
                'Titles and foreign-language spans retained; grammatical annotation quality varies.']}
        write(output/'report.json',report);write(output/'training-manifest.json',{'segments':records,'excluded':losses})
        # Fixture/coverage preparation is separate from resource fitting.
        target=targets['F137'];index=max(range(len(target.segments)),key=lambda i:len(target.segments[i]));words=target.segments[index][:4000]
        fixture=ROOT/'pilot-fixture';stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION)
        stream.save(fixture/'public/cipher.json');truth.save(fixture/'evaluation-only/truth.json')
        labels=[a for a in target.annotations if a['segment']==index and a['offset']<len(words)]
        assert [a['surface'] for a in labels]==list(words)
        write(fixture/'evaluation-only/annotations.json',labels)
        write(fixture/'evaluation-only/source.json',{'id':target.identifier,'metadata':target.metadata,'segment':index,'prefix_tokens':len(words),
            'full_segment_tokens':len(target.segments[index]),'original_spelling_policy':TOKENIZATION})
        counts=Counter(words);covered=set(forms)&set(words)
        write(ROOT/'pilot-coverage.json',{'tokens':len(words),'types':len(counts),'covered_types':len(covered),
            'missing_types':len(counts)-len(covered),'token_ceiling':sum(counts[w] for w in covered)/len(words),
            'cipher_sha256':stream.identity})
        print(json.dumps({'stage':'built',**report}),flush=True)
    finally:inventory.close()


def pilot(*, budget_seconds=None):
    from dataclasses import replace
    from benchmarks.scalable_english_run import run
    from benchmarks.scalable_english_evaluate import evaluate
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.confidence import extract
    fixture=ROOT/'pilot-fixture';resources=ROOT/'resources'
    reference=Path(json.loads((ROOT/'design.json').read_text())['english_reference'])
    protocol=json.loads(reference.read_text());base=SearchConfig(**protocol['search']);retrieval=RetrievalConfig(**protocol['retrieval'])
    config=replace(base,proposals=4000)
    if budget_seconds is not None:config=replace(config,budget_seconds=budget_seconds)
    write(ROOT/'pilot-design.json',{'reference_sha256':sha(reference),'reference_protocol':protocol,
        'deviations':{'proposals':'4000 preliminary pilot versus 8000 main replication','budget_seconds_per_chain':config.budget_seconds,'reserve_seconds_per_chain':config.reserve_seconds},
        'main_replication_pending':True,'initializations':['random','frequency'],'seeds':[3,5,7],
        'primary':'Literal recovery and frequent anchor precision/coverage; no confidence probabilities'})
    results={}
    for method in ('random','frequency'):
        private=fixture/'evaluation-only';hidden=fixture/'evaluation-unavailable-during-search';private.rename(hidden)
        try:run(resources,fixture/'public/cipher.json',ROOT/f'pilot-{method}',seeds=(3,5,7),config=replace(config,initialization=method),retrieval=retrieval,trace=True)
        finally:hidden.rename(private)
        out=ROOT/f'pilot-{method}'
        public=extract(resources,out);write(out/'confidence-public.json',public)
        measured=evaluate(resources,out,private/'truth.json')
        anchors=evaluate_anchors(resources,out,fixture)
        results[method]={'literal':measured,'anchors':anchors}
        write(ROOT/'pilot-summary.json',results)
        print(json.dumps({'stage':'pilot','initialization':method,'mean':measured['mean_score_selected_token_accuracy'],'selected':measured['selected_token_accuracy'],'anchors':anchors}),flush=True)


def objective_diagnostics():
    """Evaluation-only controls; unsupported true types get explicit proxies."""
    import random
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
    from voynich_smt.word_mapping.scalable.data import CipherStream
    resources=ROOT/'resources';fixture=ROOT/'pilot-fixture';inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=SparseBigram.load(resources/'model.sqlite',inventory)
        stream=CipherStream.load(fixture/'public/cipher.json');truth=json.loads((fixture/'evaluation-only/truth.json').read_text())
        if stream.identity!=truth['public_sha256']:raise ValueError('Truth mismatch')
        known={};missing=[]
        for c,word in enumerate(truth['decoding']):
            try:known[c]=inventory.id(word)
            except KeyError:missing.append(c)
        used=set(known.values());rare=sorted((i for i in range(inventory.size) if i not in used),key=lambda i:(model.counts[i],i))
        reference=[known[c] if c in known else -1 for c in range(stream.type_count)]
        for c,w in zip(missing,rare):reference[c]=w
        def value(key):return model.score(tuple(key[c] for c in stream.documents[0]))
        controls={'covered_reference_with_rare_observed_proxies':value(reference)}
        alternate=reference.copy()
        for c,w in zip(missing,reversed(rare)):alternate[c]=w
        controls['covered_reference_with_common_observed_proxies']=value(alternate)
        for seed in range(3):
            controls[f'random-{seed}']=value(random.Random(seed).sample(range(inventory.size),stream.type_count))
        for fraction in (.1,.25,.5):
            for seed in range(3):
                rng=random.Random(1000+seed);indices=rng.sample(range(stream.type_count),max(2,int(fraction*stream.type_count)))
                values=[reference[c] for c in indices];rng.shuffle(values);key=reference.copy()
                for c,w in zip(indices,values):key[c]=w
                controls[f'corrupt-{fraction}-{seed}']=value(key)
        optimized={}
        for method in ('random','frequency'):
            inferred=json.loads((ROOT/f'pilot-{method}/inference.json').read_text())
            if inferred['protocol']['cipher_sha256']!=stream.identity or inferred['protocol']['model_sha256']!=model.identity:raise ValueError('Inference mismatch')
            optimized[method]=[{'seed':r['seed'],'score':value(r['joint_archive'][0]['assignments'])} for r in inferred['runs']]
        result={'controls':controls,'optimized':optimized,'missing_types_using_proxies':len(missing),
            'note':'No unobserved/null dictionary control exists in this all-attested inventory. Proxy choices are observed words and affect scores; these are not full correct references or inference outputs. No control enters search.',
            'rare_proxy_reference_beats_all_optimized':all(controls['covered_reference_with_rare_observed_proxies']>r['score'] for runs in optimized.values() for r in runs)}
        write(ROOT/'objective-diagnostics.json',result);return result
    finally:inventory.close()


def evaluate_anchors(resources,out,fixture):
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.data import CipherStream
    inference=json.loads((out/'inference.json').read_text());stream=CipherStream.load(fixture/'public/cipher.json')
    truth=json.loads((fixture/'evaluation-only/truth.json').read_text());counts=Counter(c for d in stream.documents for c in d)
    keys=[r['joint_archive'][0]['assignments'] for r in inference['runs']]
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        rows=[]
        for c in counts:
            votes=Counter(key[c] for key in keys);wid,n=min(votes.items(),key=lambda kv:(-kv[1],kv[0]));word=inventory.word(wid)
            rows.append({'cipher_type':c,'count':counts[c],'votes':n,'prediction':word,'actual':truth['decoding'][c],'correct':word==truth['decoding'][c]})
        ranked=sorted(rows,key=lambda r:(-r['votes'],-r['count'],r['cipher_type']))
        primary=[r for r in ranked if r['votes']==len(keys) and r['count']>=100]
        frequency=sorted(rows,key=lambda r:(-r['count'],r['cipher_type']))
        report={'primary_types':len(primary),'primary_correct':sum(r['correct'] for r in primary),
            'primary_correct_token_coverage':sum(r['count'] for r in primary if r['correct'])/sum(counts.values()),
            'primary_eligible_types':sum(n>=100 for n in counts.values()),
            'agreement_first_predictions':ranked[:50],'frequency_first_predictions':frequency[:50],
            'primary':primary,'agreement_first_top':{str(k):sum(r['correct'] for r in ranked[:k]) for k in (10,20,50)},
            'frequency_first_top':{str(k):sum(r['correct'] for r in frequency[:k]) for k in (10,20,50)},
            'warning':'One majority prediction per type; not the historical padded candidate ranking. Agreement is not confidence.'}
        write(out/'anchors-evaluation.json',report)
        selected=next(r for r in inference['runs'] if r['seed']==inference['selected_seed'])['joint_archive'][0]['assignments']
        for offset in (0,1000,2000):
            actual=truth['plaintext'][0][offset:offset+100];restored=[inventory.word(selected[c]) for c in stream.documents[0][offset:offset+100]]
            path=out/f'excerpt-{offset}.md';path.write_text('# Fixed-position pilot excerpt\n\nOriginal:\n\n'+' '.join(actual)+'\n\nRestored:\n\n'+' '.join(restored)+'\n')
        return report
    finally:inventory.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['census','build','pilot','diagnose']);parser.add_argument('--budget-seconds',type=float,help='Optional per-chain pilot search budget');args=parser.parse_args()
    {'census':census,'build':build,'pilot':pilot,'diagnose':objective_diagnostics}[args.stage](**({'budget_seconds':args.budget_seconds} if args.stage=='pilot' else {}))
