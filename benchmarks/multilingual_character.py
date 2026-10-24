"""Seven-stage cached historical-text comparison using the frozen spelling statistic."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from benchmarks import character_prediction as pred
from benchmarks import historical_word_lengths as historical
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/multilingual-character')
GERMAN=('german-113','german-133','german-233','german-243')


def blocks32(segments):
    blocks=[]; pending=[]; slots=0; rejected=0
    for segment in segments:
        pending=[]
        for word in segment:
            index=slots; slots+=1
            if word is None or not word or not word.isascii() or not word.isalpha(): pending=[]; rejected+=1; continue
            pending.append((index,word))
            if len(pending)==32: blocks.append({'source_slots':[i for i,_ in pending],'words':[list(w) for _,w in pending]}); pending=[]
    return blocks,{'source_slots':slots,'barrier_or_nonascii_slots':rejected,'eligible_blocks32':len(blocks)}


def assign(template,source):
    assert len(template)==len(source)
    return [{**copy.deepcopy(b),'words':s['words'],'source_slots':s['source_slots']} for b,s in zip(template,source)]


def eight_lines(blocks):
    out=copy.deepcopy(blocks)
    for b in out:
        b['positions']=[i%8 for i in range(32)]; b['line_ids']=[f"artificial:{b['start']}:{i//8}" for i in range(32)]
    return out


def prepare():
    prior=pred.prepare(); selection=json.loads((pred.OUT/'iteration-6.json').read_text()); sources=[]
    for n,file,incipit in (('aquinas','latin-aquinas-ente.html','Quia parvus error'),('caroli','latin-caroli.html','Secundis sedentibus')):
        seg,meta=historical.latin_segments(file,incipit); sources.append((n,seg,meta,'Latin: historical spelling and ligature expansions from cached parser; additionally j→i/v→u.'))
    sources+= [(n,s,m,'German: cached expanded letters/known abbreviations, umlaut base vowel, ß→ss; unresolved abbreviations and editorial additions are barriers.') for n,s,m in historical.german_sources()]
    seg,meta=historical.italian_segments(); sources.append(('italian',seg,meta,'Italian: cached historical forms, accents stripped; internal apostrophe retained as one written word; no missing letters supplied.'))
    seg,meta=historical.czech_segments(); sources.append(('czech-verse',seg,meta,'Czech Dalimil transcription: verse, cached historical normalization, not a prose comparator.'))
    for i,(title,seg,meta) in enumerate(historical.czech_bible_segments()): sources.append((f'czech-prose-{i}',seg,{**meta,'title':title},'Czech Bible: cached historical spelling; excerpt too short for full design.'))
    tables={}; coverage={}; metadata={}
    for n,segs,meta,normal in sources:
        if n in ('aquinas','caroli'): segs=[[w.replace('j','i').replace('v','u') if w else None for w in s] for s in segs]
        tables[n],coverage[n]=blocks32(segs); metadata[n]={'source':meta,'normalization':normal}
    included=('aquinas','caroli',*GERMAN,'italian'); cases={}
    for n in included:
        source=tables[n]; assert len(source)>=121
        train=assign(prior['development'],source[:32]); held=assign(prior['heldout'],source[32:121]); cases[n]={'train':train,'heldout':held,'source':n,'variant':'primary'}
        cases[n+'-shuffle']={'source':n,'variant':'shuffle'}
        for split in ('train','heldout'): cases[n+'-shuffle'][split]=reorder(cases[n][split],0,stream_seed(29001,split))[0]
        cases[n+'-eight-lines']={'source':n,'variant':'eight-lines',**{split:eight_lines(cases[n][split]) for split in ('train','heldout')}}
    replications=('caroli','german-113','german-133','italian')
    for n in replications:
        assert len(tables[n])>=242
        tail=tables[n][-121:]; cases[n+'-replication']={'source':n,'variant':'replication','train':assign(prior['development'],tail[:32]),'heldout':assign(prior['heldout'],tail[32:])}
    stages={'1':[],'2':['aquinas','caroli'],'3':list(GERMAN),'4':['italian'],'5':[n+'-shuffle' for n in included],'6':[n+'-eight-lines' for n in included],'7':[n+'-replication' for n in replications]}
    p={'prior_sha256':digest(prior),'selection_sha256':digest(selection),'spec':selection['specs'][selection['selected']],'cases':cases,'coverage':coverage,'metadata':metadata,'stages':stages,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(pred.__file__),Path(historical.__file__),Path('benchmarks/weak_boundary_calibration.py'))},
       'scope':'Cached independently sourced works, not representative languages. Freeze source IDs and first121 complete32-word blocks before scoring. Barriers/nonASCII words break runs, never silently bridge. Seven primary cases matched1024train2848held words, not lengths/alphabet distributions. Copied EVA layout slots are artificial for prose; eight-word-line sensitivity replaces them. No crossing source segment/barrier within32-word blocks; gaps between blocks allowed. Four disjoint tail replications, no claim of never used in prior project experiments. Refitted nulls preserve folio/position-bin/length word inventories but source slot metadata identifies original selected blocks only, not permuted word provenance. Fixed26-letter alphabet/EOS; nonASCII exclusions counted. No model selection, no cipher fit or language likelihood ranking. Czech short samples excluded; Dalimil is verse.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['spec'])) for n in plan['cases']}
    assessment={1:'Coverage frozen: seven full-size comparators; Czech short/verse exclusions explicit. Proceed to two medieval Latin sources.',2:'Latin sources scored; proceed to four preset German sources.',3:'German sources scored; proceed to Italian stories.',4:'Italian scored; check refitted inventory-preserving nulls.',5:'Refitted nulls scored; check dependence on copied manuscript layout.',6:'Eight-word-line sensitivity scored; finish disjoint-tail replication.',7:'Disjoint within-work replications scored. Compare corpus heterogeneity and layout sensitivity without language ranking.'}[i]
    r={'plan':plan,'results':results,'summary':{n:summarize(m) for n,m in results.items()},'assessment':assessment}; write_json(path,r); print(i,assessment,json.dumps(r['summary']),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
