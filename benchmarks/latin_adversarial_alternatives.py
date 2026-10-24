"""Freeze nonflat calibration alternatives before fresh attacks."""
import json,hashlib
from pathlib import Path
import numpy as np
from benchmarks.latin_adversarial_objective import OUT,Engine,STARTS,BUDGETS,expanded,quality
from voynich_smt.data.corpus import digest,write_json


def run():
    engine=Engine();selection=json.loads((OUT/'selection.json').read_text());nonflat=[m for m in selection['models'] if np.linalg.norm(m['weights'])>1e-8]
    choices={'nonflat_best_repair':max(nonflat,key=lambda m:(m['calibration']['valid_stability'],m['calibration']['median_minimum_edge_role_repair'],-m['calibration']['worst_valid_degradation'],m['calibration']['calibration_pair_accuracy'])),
             'nonflat_best_pair_accuracy':max(nonflat,key=lambda m:m['calibration']['calibration_pair_accuracy'])}
    frozen={'selection_sha256':digest(selection),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'choices':choices,'scope':'Supplemental nonflat alternatives selected exclusively from calibration results before fresh test attacks; no original selection change.'}
    if (OUT/'alternative-selection.json').exists():assert json.loads((OUT/'alternative-selection.json').read_text())==frozen
    else:write_json(OUT/'alternative-selection.json',frozen)
    runs=[];summaries={}
    for label,m in choices.items():
        weights=np.asarray(m['weights']);transform=lambda v:expanded(v,np.asarray(selection['center']),np.asarray(selection['scale']),m['quadratic'])
        for f in engine.fixtures:
            if f['split']!='test':continue
            for start in STARTS:
                for seed in (907,919):
                    r=engine.attack(f,start,seed,weights,5000,False,transform);r['model']=label;runs.append(r)
            print('ATTACKED',label,f['id'],flush=True)
        local=[r for r in runs if r['model']==label];bybudget=[]
        for budget in BUDGETS:
            partial=[{**r,'snapshots':[r['snapshots'][0],next(s for s in r['snapshots'] if s['budget']==budget)]} for r in local];bybudget.append({'budget':budget,**quality(partial)})
        nonworse=[]
        for r in local:
            a=next(s for s in r['snapshots'] if s['budget']==100)['grammar'];b=r['snapshots'][-1]['grammar'];nonworse.append(b['satisfied_gold_edges']>=a['satisfied_gold_edges'] and b['role_inflection_compatible_tokens']>=a['role_inflection_compatible_tokens'])
        summaries[label]={'budgets':bybudget,'budget_nonregression':float(np.mean(nonworse)),'fresh_palladius':quality([r for r in local if r['document']=='palladius.opus_agriculturae']),'gate_passed':False}
    report={'alternative_selection_sha256':digest(frozen),'runs':runs,'summaries':summaries}
    if (OUT/'alternative-report.json').exists():assert json.loads((OUT/'alternative-report.json').read_text())==report;write_json(OUT/'alternative-validation.json',{'fresh_nonflat_attacks_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'alternative-report.json',report)
    print('RESULT',summaries,flush=True)
if __name__=='__main__':run()
