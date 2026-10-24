"""Seven-stage frozen manuscript prediction replication on previously unscored folios."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from benchmarks import character_prediction as pred
from benchmarks.manuscript_width_audit import clean
from benchmarks.multilingual_character import eight_lines
from benchmarks.weak_boundary_calibration import reorder, stream_seed
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json
OUT=Path('experiments/results/manuscript-character-replication')


def extract(records,excluded):
    byfolio={}; pending=[]; folio=None
    for i,r in enumerate(records):
        if r['folio']!=folio: pending=[]; folio=r['folio']
        if folio in excluded or not clean(r): pending=[]; continue
        pending.append((i,r))
        if len(pending)==32:
            byfolio.setdefault(folio,[]).append({'folio':folio,'start':pending[0][0],'end_exclusive':i+1,
                'words':[x['tokens'] for _,x in pending],'positions':[x['word_in_locus'] for _,x in pending],
                'line_ids':[f"{x['folio']}:{x['locus']}:{x['physical_line']}" for _,x in pending], 'page_variables':pending[0][1].get('page_variables',{})}); pending=[]
    return byfolio


def prepare():
    source=pred.prepare(); previous=[source,pred.prior.prepare(),pred.prior.prior.prepare(),pred.prior.prior.prior.prepare()]
    excluded={b['folio'] for v in previous for kind in ('development','heldout') for b in v[kind]}|{'f1r'}
    path=Path('data/processed/zl-eva.json'); raw=json.loads(path.read_text()); byfolio=extract(raw['records'],excluded)
    ordered=sorted(byfolio,key=lambda f:(hashlib.sha256(('replication-30001:'+f).encode()).hexdigest(),f)); assert len(ordered)==116
    cohorts={'A':[byfolio[f][0] for f in ordered[:58]],'B':[byfolio[f][0] for f in ordered[58:]]}; allfirst=cohorts['A']+cohorts['B']; extra=[b for f in ordered for b in byfolio[f][1:]]
    selection=json.loads((pred.OUT/'iteration-6.json').read_text()); spec=selection['specs'][selection['selected']]; cases={}
    for name,blocks in cohorts.items():
        cases[name]={'train':source['development'],'heldout':blocks,'spec':spec,'variant':'primary'}
        cases[name+'-eight-lines']={'train':eight_lines(source['development']),'heldout':eight_lines(blocks),'spec':spec,'variant':'layout'}
        for gate in ('within','cross'): cases[name+'-'+gate]={'train':source['development'],'heldout':blocks,'spec':{**spec,'gate':gate},'variant':'gate'}
    for seed in (30001,30002,30003):
        cases[f'shuffle-{seed}']={'spec':spec,'variant':'shuffle','seed':seed,
            'train':reorder(source['development'],0,stream_seed(seed,'train'))[0],'heldout':reorder(allfirst,0,stream_seed(seed,'heldout'))[0]}
    cases['additional-blocks']={'train':source['development'],'heldout':extra,'spec':spec,'variant':'additional'}
    stages={'1':[],'2':['A'],'3':['B'],'4':['A-eight-lines','B-eight-lines'],'5':['A-within','A-cross','B-within','B-cross'],'6':[f'shuffle-{s}' for s in (30001,30002,30003)],'7':['additional-blocks']}
    p={'prior_sha256':digest(source),'selection_sha256':digest(selection),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'excluded_folios':sorted(excluded), 'ordered_folios':ordered,'cases':cases,'stages':stages,
       'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(pred.__file__),Path('benchmarks/multilingual_character.py'),Path('benchmarks/weak_boundary_calibration.py'))},
       'scope':'All116 newly eligible folios exclude every prior statistical experiment development/evaluation folio and f1r cipher pilot. Earlier manuscript-wide descriptive audits inspected full text; not full data blindness or proof of absence from every older solver artifact. A/B hash split58folios each, first eligible32wordblock perfolio. Later blocks separately predeclared, same folios but disjoint words. Original1024trainingwords fixed; no new model selection. Layout sensitivity refits both train/eval under artificial8wordlines. Gate variants diagnostic, not reselected. Three independently seeded refitted nulls preserve exact folio/position/length word inventories. Primary folio-equal scores; all-source case eligibility fixed before likelihood scoring. No cipher/language/mechanism identification.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'cases':p['stages'][str(i)],'selection':False}; write_json(OUT/f'plan-{i}.json',plan)
    results={n:pred.aggregate(pred.evaluate(p['cases'][n]['train'],p['cases'][n]['heldout'],p['cases'][n]['spec'])) for n in plan['cases']}
    assessment={1:'Freeze116newfolios and two58folio cohorts; proceed to A.',2:'First cohort scored; next independent folio cohort B.',3:'Second cohort scored; test artificial line layout.',4:'Layout sensitivity scored; inspect preset within/cross gates.',5:'Gate diagnostics scored without model reselection; test three refitted nulls.',6:'Refitted nulls scored; evaluate predeclared disjoint additional words.',7:'Additional-block check complete; assess whether frozen effect replicates across folios/layout/cohorts.'}[i]
    r={'plan':plan,'results':results,'summary':{n:summarize(result) for n,result in results.items()},'assessment':assessment}; write_json(path,r); print(i,assessment,json.dumps(r['summary']),flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--iteration',type=int,choices=range(1,8)); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    elif args.iteration: iteration(args.iteration)
    else: prepare()
