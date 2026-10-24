"""Exploratory early-budget prediction audit using already frozen weights."""
import hashlib,json,math
import numpy as np
from benchmarks.latin_compact_cipher import OUT,ARMS,resource,evidence,evaluate
from voynich_smt.letter_discovery import ALPHABET,encode_text,prepare,gram_positions,initialization,search,full_score
from voynich_smt.data.corpus import write_json,digest


def run():
    manifest=json.loads((OUT/'manifest.json').read_text())
    for p,h in manifest['files_sha256'].items():assert hashlib.sha256(__import__('pathlib').Path(p).read_bytes()).hexdigest()==h,p
    r=resource();rows,words,posmodel,logs,frequency,nodes,terminal=r;fixtures=[f for f in json.loads((OUT/'fixtures.json').read_text()) if f['split']=='test'];weights=json.loads((OUT/'selection.json').read_text())['weights'];results=[]
    # Added after seeing calibration ceiling, before reading final test results.
    protocol={'weights':'Existing calibration-selected 10,000-step weights, unchanged; no early-budget tuning','budgets':[100,1000],'restarts':[17,43],'scope':'Exploratory faster-discovery audit motivated by calibration ceiling; no new model or key selection using test outcomes.'}
    write_json(OUT/'budget-protocol.json',protocol)
    for f in fixtures:
        cipher=encode_text(' '.join(w for s in f['discovery'] for w in s));prepared=prepare([w for s in f['discovery'] for w in s],words);positions,counts=gram_positions(cipher,4);truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text())
        for arm in ARMS:
            scores,unknown,info=evidence(f,arm,prepared,rows,posmodel,None if not arm.startswith('oracle') else truth['discovery'])
            for budget in (100,1000):
                runs=[];best=None
                for seed in (17,43):
                    key,value,accepted,trace=search(cipher,initialization(cipher,frequency,seed),logs,4,positions,counts,prepared['words'],prepared['lengths'],prepared['frequency'],nodes,terminal,prepared['ptr'],prepared['candidate_ids'],scores,unknown,prepared['affected_words'],prepared['affected_word_counts'],weights[arm],budget,seed)
                    assert np.isclose(value,full_score(cipher,key,logs,4,prepared,nodes,terminal,scores,unknown,weights[arm]),atol=1e-7)
                    runs.append({'seed':seed,'key':key.tolist(),'objective':float(value)})
                    if best is None or value>best[0]:best=(value,key.copy())
                solved={'fixture':f['id'],'arm':arm,'budget':budget,'width':f['width'],'runs':runs,'hypothesis':{'alphabet':ALPHABET,'decryption_permutation':best[1].tolist(),'exceptions':[],'selection':'best discovery objective at this budget'}}
                path=OUT/'frozen-budget-hypotheses'/f"{digest((f['id'],arm,budget))}.json";write_json(path,solved);frozen=json.loads(path.read_text());solved.update(evaluate(f,frozen,truth));assert frozen==json.loads(path.read_text());results.append(solved)
        print('EARLY BUDGETS',f['id'],flush=True)
    summary={}
    for budget in (100,1000):
        summary[str(budget)]={}
        for arm in ARMS:
            rr=[x for x in results if x['budget']==budget and x['arm']==arm];summary[str(budget)][arm]={'mean_heldout_letter_accuracy':float(np.mean([x['heldout']['letter_accuracy'] for x in rr])),'mean_heldout_word_accuracy':float(np.mean([x['heldout']['word_accuracy'] for x in rr])),'widths':{str(w):float(np.mean([x['heldout']['letter_accuracy'] for x in rr if x['width']==w])) for w in (100,1000)}}
    write_json(OUT/'budget-report.json',{'protocol':protocol,'runs':results,'summary':summary});write_json(OUT/'budget-manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [__import__('pathlib').Path(__file__),OUT/'selection.json',OUT/'budget-protocol.json']}});print('EARLY RESULTS',summary,flush=True)
if __name__=='__main__':run()
