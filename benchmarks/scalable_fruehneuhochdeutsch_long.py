"""Frozen length/author replication with the original English algorithm."""
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import tarfile

from benchmarks.scalable_fruehneuhochdeutsch import RAW, ROOT as PARENT, evaluate_anchors
from voynich_smt.word_mapping.scalable.historical_german import parse_cora,TOKENIZATION
from voynich_smt.word_mapping.scalable.latin_corpus import sha,write
from voynich_smt.word_mapping.scalable.data import generate

ROOT=Path('experiments/results/scalable-fruehneuhochdeutsch/length-validation-v1')
REFERENCE=Path('experiments/results/scalable-english/independent-wells-frequency-8000-v2/protocol.json')


def prepare():
    ROOT.mkdir(parents=True,exist_ok=False)
    parent_report=json.loads((PARENT/'resources/report.json').read_text())
    write(ROOT/'design.json',{'source_resources':str(PARENT/'resources'),'parent_model_sha256':parent_report['model_sha256'],
        'parent_inventory_sha256':parent_report['inventory_sha256'],'english_reference_sha256':sha(REFERENCE),
        'reference_protocol':json.loads(REFERENCE.read_text()),'proposals':8000,'seeds':[3,5,7],
        'initializations':['random','frequency'],'ref_targets':['F137','F332','F064'],
        'ref_selection':'All three predeclared development works; use each longest retained continuous segment, no recovery-based selection',
        'heldout_validation_and_sealed':'F019,F283,F001,F161 remain unrun by this experiment',
        'long_source':'Arndt 1610 DTA volume 1, pending extraction/continuity and overlap audit; no topic matching or vocabulary filtering',
        'method':'Original sparse bigram, mixed scheduler and numerical English settings; no scoring/retrieval variants or target anchors',
        'success':'Report all works and seeds. A useful nucleus requires >=20 selected types at >=80% measured precision on each of two independent works; agreement is not calibrated confidence.',
        'comparability':'4k pilot to full-length 8k-cap comparison changes length and cap together; not a causal estimate of either alone.'})
    census=json.loads((PARENT/'census.json').read_text());needed={r['member']:r for r in census['documents'] if r['id'] in ('F137','F332','F064')}
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    inventory=Inventory(PARENT/'resources/inventory.sqlite');rows=[]
    try:
        with tarfile.open(RAW/'ReF-v1.0.2.tar.gz') as archive:
            for member in sorted(needed):
                raw=archive.extractfile(member).read();record=needed[member]
                import hashlib
                if hashlib.sha256(raw).hexdigest()!=record['source_sha256']:raise ValueError('Reserved source changed')
                doc=parse_cora(raw);index=max(range(len(doc.segments)),key=lambda i:len(doc.segments[i]));words=doc.segments[index]
                fixture=ROOT/'fixtures'/doc.identifier
                stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION);stream.save(fixture/'public/cipher.json');truth.save(fixture/'evaluation-only/truth.json')
                write(fixture/'evaluation-only/source.json',{'record':record,'segment':index,'tokens':len(words),'full_segment':True})
                write(fixture/'evaluation-only/annotations.json',[a for a in doc.annotations if a['segment']==index])
                missing={}
                for w,n in Counter(words).items():
                    try:inventory.id(w)
                    except KeyError:missing[w]=n
                row={'id':doc.identifier,'tokens':len(words),'types':stream.type_count,'missing_types':len(missing),'missing_tokens':sum(missing.values()),'token_ceiling':1-sum(missing.values())/len(words),'cipher_sha256':stream.identity}
                rows.append(row)
        write(ROOT/'ref-preparation.json',{'fixtures':rows,'resources_unchanged':True});print(json.dumps(rows),flush=True)
    finally:inventory.close()


def prepare_long(*, name='arndt-35000', source_slug='arndt_christentum01_1610', year='1610', token_count=35000, segment_policy='first', resource_name='long-resources', design_name='long', author_fragment='arndt'):
    """Freeze a full original-spelling DTA prefix and audit independent training."""
    import hashlib
    import os
    import unicodedata
    from voynich_smt.word_mapping.scalable.historical_german_tei import parse_dta
    from voynich_smt.word_mapping.scalable.latin_corpus import shingles
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
    from voynich_smt.word_mapping.scalable.config import ModelConfig
    source=RAW/'long-source-audit'/(source_slug+'.xml')
    doc=parse_dta(source.read_bytes())
    index=0 if segment_policy=='first' else max(range(len(doc.segments)),key=lambda i:len(doc.segments[i]))
    if doc.metadata['source_dates']!=[year] or len(doc.segments[index])<token_count:raise ValueError('Not the pinned in-period long source')
    if not any('creativecommons.org/licenses/by-sa/' in u for u in doc.metadata['licenses']):raise ValueError('Unverified source license')
    fixture=ROOT/'fixtures'/name;words=doc.segments[index][:token_count]
    stream,truth=generate((words,),seed=83,tokenization=TOKENIZATION)
    from voynich_smt.word_mapping.scalable.data import CipherStream
    if (fixture/'public/cipher.json').exists():
        if CipherStream.load(fixture/'public/cipher.json').identity!=stream.identity:raise ValueError('Prepared fixture changed')
    else:
        stream.save(fixture/'public/cipher.json');truth.save(fixture/'evaluation-only/truth.json')
    write(fixture/'evaluation-only/source.json',{'source_path':str(source),'sha256':sha(source),'metadata':doc.metadata,'statistics':doc.statistics,
        'selection':segment_policy+' retained main-body segment; positional prefix, no topic/vocabulary filtering','segment_index':index,'full_segment_tokens':len(doc.segments[index]),
        'parser_sha256':sha('src/voynich_smt/word_mapping/scalable/historical_german_tei.py')})
    resources=ROOT/resource_name;resources.mkdir(exist_ok=False)
    write(ROOT/(design_name+'-design.json'),{'source_sha256':sha(source),'tokens':token_count,'selection':segment_policy+' segment, positional prefix, frozen before recovery','segment_index':index,
        'source_metadata':doc.metadata,'continuity':doc.statistics,
        'source_tokens_total':sum(map(len,doc.segments)),
        'training':'Parent admitted segments, minus author '+author_fragment+' or any segment sharing an exact/folded 12-word shingle with full DTA main body',
        'folded_screen':'NFD remove combining marks; v->u,j->i, only for overlap auditing, never change inference surfaces',
        'inventory':'Identical frozen parent inventory, no target-word insertions; retain source-only dictionary forms even if count becomes zero',
        'search':'Same 8000-proposal seeds/settings as ReF trials; freeze cleaned resources before recovery',
        'limits':['Late-period printed prose; does not establish generalization across all historical regions/periods.',
            'TEI word segmentation versus annotated CorA segmentation is an unavoidable resource difference.',
            'Quoted biblical material is not treated as an independent topic; overlapping training segments are screened.']})
    def folded(segment):
        return tuple(''.join(c for c in unicodedata.normalize('NFD',w) if not unicodedata.category(c).startswith('M')).replace('v','u').replace('j','i') for w in segment)
    exact=set().union(*(set(shingles(s)) for s in doc.segments));normalized=set().union(*(set(shingles(folded(s))) for s in doc.segments))
    prior=json.loads((PARENT/'resources/training-manifest.json').read_text());by_member={}
    for r in prior['segments']:by_member.setdefault(r['member'],{})[r['segment']]=r
    training=[];admitted=[];removed=[];author_exclusions=[]
    with tarfile.open(RAW/'ReF-v1.0.2.tar.gz') as archive:
        for member,segments in sorted(by_member.items()):
            raw=archive.extractfile(member).read();ref=parse_cora(raw)
            if hashlib.sha256(raw).hexdigest()!=next(iter(segments.values()))['source_sha256']:raise ValueError('Training source changed')
            if author_fragment in ref.metadata.get('text-author','').lower():author_exclusions.append(ref.identifier);continue
            for index,record in segments.items():
                segment=ref.segments[index]
                if hashlib.sha256(' '.join(segment).encode()).hexdigest()!=record['surface_sha256']:raise ValueError('Training extraction changed')
                matches=len(set(shingles(segment))&exact);norm=len(set(shingles(folded(segment)))&normalized)
                if matches or norm:
                    removed.append({**record,'exact_12grams':matches,'folded_12grams':norm});continue
                training.append(segment);admitted.append(record)
    os.link(PARENT/'resources/inventory.sqlite',resources/'inventory.sqlite')
    inv=Inventory(resources/'inventory.sqlite')
    try:
        model=SparseBigram.train(inv,((inv.id(w) for w in segment) for segment in training),config=ModelConfig(language='de',tokenization=TOKENIZATION))
        model.save(resources/'model.sqlite')
        report=json.loads((PARENT/'resources/report.json').read_text());report.update(training_tokens=sum(map(len,training)),training_segments=len(training),
            training_works=len({r['id'] for r in admitted}),model_sha256=model.identity,observed_edges=len(model.edges),
            limitations=report['limitations']+[name+' is an independent DTA holdout; exact/folded overlap cleanup may change counts relative to ReF trials.'])
        write(resources/'report.json',report);write(resources/'training-manifest.json',{'segments':admitted,'removed_overlap':removed,'author_exclusions':author_exclusions,
            'parent_manifest_sha256':sha(PARENT/'resources/training-manifest.json'),'remaining_exact_or_folded_12gram_matches':0})
        missing={}
        for word,n in Counter(words).items():
            try:inv.id(word)
            except KeyError:missing[word]=n
        write(ROOT/(design_name+'-preparation.json'),{'id':name,'tokens':len(words),'types':stream.type_count,'missing_types':len(missing),
            'missing_tokens':sum(missing.values()),'token_ceiling':1-sum(missing.values())/len(words),'cipher_sha256':stream.identity,
            'metadata':doc.metadata,'statistics':doc.statistics,'resource_cleaning_pending':False,'model_sha256':model.identity,
            'removed_training_segments':len(removed),'removed_training_tokens':sum(r['tokens'] for r in removed),'training_tokens':report['training_tokens']})
        print(json.dumps({'stage':'long-prepared','tokens':len(words),'training_tokens':report['training_tokens'],'removed_segments':len(removed),'missing_tokens':sum(missing.values()),'model_sha256':model.identity}),flush=True)
    finally:inv.close()


def trial(name, method, *, budget_seconds=None):
    from benchmarks.scalable_english_run import run
    from benchmarks.scalable_english_evaluate import evaluate
    from voynich_smt.word_mapping.scalable.confidence import extract
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    design=json.loads((ROOT/'design.json').read_text());protocol=design['reference_protocol']
    cfg=SearchConfig(**protocol['search']);cfg=replace(cfg,proposals=8000,initialization=method)
    if budget_seconds is not None:cfg=replace(cfg,budget_seconds=budget_seconds)
    fixture=ROOT/'fixtures'/name;resources=PARENT/'resources'
    if name=='arndt-35000':resources=ROOT/'long-resources'
    if name=='abelin-31260':resources=ROOT/'confirmation-resources'
    # Each initializer gets its own isolated private directory, allowing independent runs.
    import shutil
    isolated=ROOT/'isolated-fixtures'/f'{name}-{method}'
    shutil.copytree(fixture/'public',isolated/'public');shutil.copytree(fixture/'evaluation-only',isolated/'evaluation-only')
    private=isolated/'evaluation-only';hidden=isolated/'evaluation-unavailable-during-search';private.rename(hidden)
    output=ROOT/'runs'/f'{name}-{method}'
    try:run(resources,isolated/'public/cipher.json',output,seeds=(3,5,7),config=cfg,retrieval=RetrievalConfig(**protocol['retrieval']),trace=True)
    finally:hidden.rename(private)
    write(output/'confidence-public.json',extract(resources,output))
    measured=evaluate(resources,output,private/'truth.json');anchors=evaluate_anchors(resources,output,isolated)
    write(output/'summary.json',{'id':name,'initialization':method,'literal':measured,'anchors':anchors})
    print(json.dumps({'stage':'complete','id':name,'initialization':method,'mean':measured['mean_score_selected_token_accuracy'],'selected':measured['selected_token_accuracy'],'primary_correct':anchors['primary_correct'],'primary_types':anchors['primary_types']}),flush=True)


def summarize():
    """Require every predeclared chain; preserve failed outcomes and protocol audits."""
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    rows=[];chains=0;proposals=0;seconds=0.;peak=0;protocols={}
    for name in ('F137','F332','F064','arndt-35000','abelin-31260'):
        for method in ('random','frequency'):
            output=ROOT/'runs'/f'{name}-{method}'
            result=json.loads((output/'summary.json').read_text());inference=json.loads((output/'inference.json').read_text())
            resources=ROOT/'long-resources' if name=='arndt-35000' else ROOT/'confirmation-resources' if name=='abelin-31260' else PARENT/'resources'
            resource_report=json.loads((resources/'report.json').read_text())
            protocol=inference['protocol']
            if protocol['model_sha256']!=resource_report['model_sha256']:raise ValueError('Model mismatch')
            if protocol['inventory_sha256']!=resource_report['inventory_sha256']:raise ValueError('Inventory mismatch')
            compare=json.loads(json.dumps(protocol));compare['search'].pop('initialization');protocols[name,method]=compare
            for run in inference['runs']:
                if run['step']!=8000 or run['stop_reason']!='proposal_limit':raise ValueError('Incomplete fixed-cap trial; report separately')
                chains+=1;proposals+=run['step'];seconds+=run['elapsed_seconds'];peak=max(peak,run['peak_rss_bytes'])
            private=ROOT/'isolated-fixtures'/f'{name}-{method}'/'evaluation-only'
            if not (private/'truth.json').exists():raise ValueError('Private fixture not restored')
            literal=result['literal'];a=result['anchors']
            rows.append({'id':name,'initialization':method,'tokens':literal['tokens'],
                'mean_token_accuracy':literal['mean_score_selected_token_accuracy'],'selected_token_accuracy':literal['selected_token_accuracy'],
                'per_seed_accuracy':{str(r['seed']):r['score_selected_best']['token_accuracy'] for r in literal['runs']},
                'initial_accuracy':{str(r['seed']):r['initial']['token_accuracy'] for r in literal['runs']},
                'primary_types':a['primary_types'],'primary_correct':a['primary_correct'],
                'primary_type_precision':a['primary_correct']/a['primary_types'] if a['primary_types'] else None,
                'primary_correct_token_coverage':a['primary_correct_token_coverage'],
                'primary_eligible_types':a.get('primary_eligible_types'),
                'top50_correct':a['agreement_first_top']['50'],
                'inventory_coverage':literal['inventory_coverage'],
                'nucleus_target_met':a['primary_types']>=20 and a['primary_correct']/a['primary_types']>=.8})
        if protocols[name,'random']!=protocols[name,'frequency']:raise ValueError('Initializer protocols otherwise differ')
    for resource_dir in ('long-resources','confirmation-resources'):
        manifest=json.loads((ROOT/resource_dir/'training-manifest.json').read_text())
        if manifest['remaining_exact_or_folded_12gram_matches']!=0:raise ValueError('Unresolved source overlap')
    frozen=json.loads((ROOT/'design.json').read_text())
    if sha(REFERENCE)!=frozen['english_reference_sha256']:raise ValueError('Reference changed')
    confirmed=[]
    for method in ('random','frequency'):
        confirmed.append({'initialization':method,'works_meeting_nucleus_target':[r['id'] for r in rows if r['initialization']==method and r['nucleus_target_met']]})
    report={'rows':rows,'chains':chains,'proposals':proposals,'search_seconds_sum':seconds,'peak_shared_process_rss_bytes':peak,
        'long_text_replication_completed':True,'long_confirmation_tokens':31260,'initial_design_extended_by':'confirmation-selection.json, frozen before Abelin decipherment','all_predeclared_trials_completed':True,'paired_protocols_verified':True,
        'nucleus_criterion':'>=20 unanimous types with count>=100, >=80% measured precision, on each of >=2 independent works; not confidence calibration',
        'nucleus_results':confirmed,'unrun_reserved_sources':['F019','F283','F001','F161'],
        'voynich_run':False,'algorithm_changed':False,
        'code_sha256':{p:sha(p) for p in ['benchmarks/scalable_fruehneuhochdeutsch_long.py','src/voynich_smt/word_mapping/scalable/historical_german_tei.py']}}
    write(ROOT/'summary.json',report);print(json.dumps(report),flush=True);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['prepare','prepare-long','prepare-confirmation','trial','summarize']);parser.add_argument('--work',choices=['F137','F332','F064','arndt-35000','abelin-31260']);parser.add_argument('--initialization',choices=['random','frequency']);parser.add_argument('--budget-seconds',type=float);args=parser.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='prepare-long':prepare_long()
    elif args.stage=='prepare-confirmation':prepare_long(name='abelin-31260',source_slug='abelinus_theatrum_1635',year='1635',token_count=31260,segment_policy='longest',resource_name='confirmation-resources',design_name='confirmation',author_fragment='abelin')
    elif args.stage=='summarize':summarize()
    else:
        if not args.work or not args.initialization:parser.error('trial needs --work and --initialization')
        trial(args.work,args.initialization,budget_seconds=args.budget_seconds)
