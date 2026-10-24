"""Seven frozen natural Caesar H2 calibration passages, with coverage gates."""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter
from benchmarks import latin_h2_identifiability as baseline
from benchmarks import latin_pattern_natural_long as passages
from voynich_smt.cipher.pattern_shuffle import pattern_preserving_shuffle
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/latin-h2-natural')


def prepare():
    path = OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        for name,sha in p['code_sha256'].items(): assert digest(Path(name).read_text())==sha
        assert digest(json.loads(Path(p['source_path']).read_text()))==p['source_sha256']
        return p
    compact=baseline.compact.prepare()
    report=json.loads((baseline.compact.OUT/'report.json').read_text())
    source_path=Path('data/processed/caesar-latin-v2.json'); raw=json.loads(source_path.read_text())
    previous=json.loads((passages.OUT/'prepared.json').read_text())
    start=max(x['record_end_exclusive'] for x in previous['passages'])
    selected=passages.select_passages(raw['records'],start,set(report['modes']['through-medieval-rare']['alphabet']['symbols']),count=7)
    automata={mode:baseline.compact.load_automaton(row['automaton']) for mode,row in report['modes'].items()}
    fixtures=[]; audits=[]
    for i,block in enumerate(selected):
        train,held=block['train'],block['held']; coverage={}
        for mode,a in automata.items():
            coverage[mode]={'missing_training':[w for w in train if not a.accepts(w)],'missing_held':[w for w in held if not a.accepts(w)]}
        mode='through-medieval-rare'; row=report['modes'][mode]
        codes=[''.join(x) for x in product('qrstuvwx',repeat=2)]; random.Random(10201+i).shuffle(codes)
        key={letter:codes[2*j:2*j+2] for j,letter in enumerate(row['alphabet']['symbols'])}
        positive,held_cipher=baseline.encrypt(train,held,key)
        seen={c for w in positive for c in w}; unseen=sorted({c for w in held_cipher for c in w}-seen)
        audit={'id':f'passage-{i+1}','record_start':block['record_start'],'record_end_exclusive':block['record_end_exclusive'],
               'coverage':coverage,'unseen_held_codes':unseen,'admitted':not coverage[mode]['missing_training'] and not unseen}
        audits.append(audit)
        if not audit['admitted']: continue
        fixtures.append({'id':audit['id'],'case':{**row,'mode':mode,'kind':'natural-h2'},'inventory':compact['inventories'][mode]['inventory'],
            'solver_ms':30000,'worker_wall_seconds':60,'max_homophones':2,
            'arms':{'positive':positive,'shuffle':pattern_preserving_shuffle(positive,10301+i)},'held_cipher':held_cipher,
            'truth':{'train':train,'held':held,'key':key},'key_seed':10201+i,'shuffle_seed':10301+i})
    dependencies=[Path(__file__),Path(passages.__file__),Path(baseline.__file__),Path(baseline.engine.__file__),Path(baseline.encoding.__file__)]
    dependencies+=list(Path('src/voynich_smt/solver').glob('*.py'))+[Path('src/voynich_smt/language/homophone_patterns.py'),Path('src/voynich_smt/cipher/pattern_shuffle.py')]
    p={'source_path':str(source_path),'source_sha256':digest(raw),'prior_sha256':digest(previous),'passages':selected,'audits':audits,'fixtures':fixtures,
       'code_sha256':{str(x):digest(x.read_text()) for x in dependencies},
       'scope':'Seven fresh nonoverlapping structurally selected Caesar 48+6 passages. Both policy inventories audited after selection; broader fixed for fits. Full finite broader inventory, no target additions. Cyclic generating choice, free H<=2 fitted model, public two-glyph codes and boundaries. Unseen held codes or missing training forms gate case without replacement. First-key scoring; 30s solve/60s worker, exclusion checks separate.'}
    write_json(path,p); return p


def worker(case,task):
    folder=OUT/case
    if task=='ambiguity': baseline.ambiguity(folder)
    else: baseline.encoding.configure(folder,'dag'); baseline.engine.fit(task)


def run():
    p=prepare()
    print('Frozen seven passages;',len(p['fixtures']),'admitted',flush=True)
    for f in p['fixtures']:
        folder=OUT/f['id']; write_json(folder/'prepared.json',f)
        for task in ('positive','shuffle','ambiguity'):
            path=folder/f'{task}-result.json'; print(f['id'],task,flush=True)
            if not path.exists():
                start=perf_counter()
                try:
                    result=subprocess.run([sys.executable,'-m','benchmarks.latin_h2_natural','--worker',f['id'],'--task',task],capture_output=True,text=True,timeout=f['worker_wall_seconds'])
                    if result.returncode: raise RuntimeError(result.stderr[-3000:])
                except subprocess.TimeoutExpired:
                    write_json(path,{'status':'WALL_TIMEOUT','verified':False,'wall_seconds':perf_counter()-start,'fixture_sha256':digest(f)})
            r=json.loads(path.read_text()); print(r['status'],r.get('training_exact'),r.get('held_exact'),flush=True)
    validate()


def validate():
    p=prepare(); summary=[]
    for audit,block in zip(p['audits'],p['passages']):
        assert audit['record_start']==block['record_start']
        row={**audit,'status':'NOT_ADMITTED'}
        if audit['admitted']:
            f=next(x for x in p['fixtures'] if x['id']==audit['id']); folder=OUT/f['id']
            assert json.loads((folder/'prepared.json').read_text())==f
            meta=f['inventory']; assert hashlib.sha256(Path(meta['path']).read_bytes()).hexdigest()==meta['sha256']
            a=baseline.compact.load_automaton(f['case']['automaton'])
            assert all(a.accepts(w) for w in f['truth']['train'])
            assert baseline.encrypt(f['truth']['train'],f['truth']['held'],f['truth']['key'])==(f['arms']['positive'],f['held_cipher'])
            assert pattern_preserving_shuffle(f['arms']['positive'],f['shuffle_seed'])==f['arms']['shuffle']
            results={}
            for task in ('positive','shuffle','ambiguity'):
                r=json.loads((folder/f'{task}-result.json').read_text()); results[task]=r
                if r['status']=='SAT':
                    key=r['alternative_key'] if task=='ambiguity' else r['recovered_key']
                    cipher=f['arms']['positive' if task=='ambiguity' else task]
                    assert set(key)=={c for w in cipher for c in w} and max(Counter(key.values()).values())<=2
                    words=[''.join(key[c] for c in w) for w in cipher]
                    assert words==r['training_words'] and all(a.accepts(w) for w in words) and r['verified']
                    if task=='positive':
                        held=[''.join(key[c] for c in w) for w in f['held_cipher']]
                        assert held==r['held_words'] and r['held_exact']==sum(w==t for w,t in zip(held,f['truth']['held']))
                        assert r['training_exact']==sum(w==t for w,t in zip(words,f['truth']['train']))
                    if task=='ambiguity': assert key!=results['positive']['recovered_key']
                if r['status'] in ('SAT','UNSAT','UNKNOWN'):
                    phases=json.loads((folder/f'{task}-phases.json').read_text()); assert phases['phase']=='complete'
                    assert phases.get('prepared_sha256',phases.get('fixture_sha256'))==digest(f)
                if task=='ambiguity' and 'first_result_sha256' in r: assert r['first_result_sha256']==digest(results['positive'])
            row.update(status=results['positive']['status'],training_exact=results['positive'].get('training_exact'),held_exact=results['positive'].get('held_exact'),shuffle_status=results['shuffle']['status'],alternative_status=results['ambiguity']['status'],phases={t:json.loads((folder/f'{t}-phases.json').read_text()) if (folder/f'{t}-phases.json').exists() else None for t in results})
        summary.append(row)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'complete':True,'cases':summary})
    write_json(OUT/'validation.json',{'verified':True,'selected':7,'admitted':len(p['fixtures']),'fit_records':3*len(p['fixtures'])})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--run',action='store_true'); parser.add_argument('--validate',action='store_true'); parser.add_argument('--worker'); parser.add_argument('--task',choices=['positive','shuffle','ambiguity']); args=parser.parse_args()
    if args.worker: worker(args.worker,args.task)
    elif args.validate: validate()
    elif args.run: run()
    else: prepare()
