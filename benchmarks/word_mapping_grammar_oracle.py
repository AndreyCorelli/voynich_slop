"""Oracle target-analysis filtering; exact recovery avoids circular compatibility."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from benchmarks import word_mapping_cloze_finetune as parent
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.grammar_retrieval import admits
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/word-mapping/grammar-oracle-calibration')
STAGES={'none':'none','pos':frozenset(),'pos_case_number':frozenset({'Case','Number'}),'full_analysis':None,'exact_profile':'equality'}

def run(validate=False):
    public,anchors,targets,entries,forms,frequencies=parent.base.prepare()
    truth=json.loads((parent.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    oracle=StructuralOracle(entries,truth['decoding'])
    source_manifest=json.loads((parent.OUT/'manifest.json').read_text())
    source_report=json.loads((parent.OUT/'report.json').read_text())
    assert digest(source_manifest['protocol'])==source_manifest['sha256']==source_report['manifest_sha256']
    paths=[Path(__file__),Path('src/voynich_smt/grammar_retrieval.py'),Path('src/voynich_smt/structural_oracle.py')]
    scores_files=[parent.OUT/'scores'/f'base-{target}.npz' for target in targets]
    protocol={'targets':targets,'source_report_sha256':digest(source_report),'truth_sha256':digest(truth),
        'profiles_sha256':digest({w:sorted(p,key=repr) for w,p in oracle.profiles.items()}),
        'stages':{k:(sorted(v) if isinstance(v,frozenset) else v) for k,v in STAGES.items()},'primary':'exact identity among known lexical content; compatibility supplementary and oracle-filtered compatibility circular',
        'scope':'oracle target dictionary analysis sets; no token disambiguation or syntactic links; reused development; no final test',
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scores_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in scores_files}}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'manifest.json').exists():
        if not validate or json.loads((OUT/'manifest.json').read_text())!=manifest:raise ValueError('Existing output or changed protocol')
    elif validate:raise ValueError('No saved experiment')
    else:write_json(OUT/'manifest.json',manifest)
    reserved=set(anchors.values());base_eligible=[i for i,w in enumerate(forms) if w not in reserved and oracle.kind(w)=='content']
    rows=[]
    for target in targets:
        gold=truth['decoding'][target];profile=oracle.profiles.get(gold,frozenset());compatible={w for w in forms if oracle.status(target,w)=='compatible'}
        lexical=oracle.kind(gold)=='content' and gold not in parent.GLUE
        with np.load(parent.OUT/'scores'/f'base-{target}.npz') as saved:neural=saved['0.0'].copy()
        frequency=np.asarray([np.log(frequencies[w]+.1) for w in forms])
        for stage,fields in STAGES.items():
            if stage=='none' or not profile:eligible=base_eligible
            elif stage=='exact_profile':eligible=[i for i in base_eligible if oracle.profiles.get(forms[i])==profile]
            else:eligible=[i for i in base_eligible if admits(oracle.profiles.get(forms[i],frozenset()),profile,fields)]
            row={'cipher':target,'gold':gold,'gold_kind':oracle.kind(gold),'lexical':lexical,'stage':stage,
                'candidates':len(eligible),'gold_retained':gold in {forms[i] for i in eligible},
                'chance_exact_top1':(1/len(eligible) if eligible and gold in {forms[i] for i in eligible} else 0),
                'chance_exact_top10':(min(10,len(eligible))/len(eligible) if eligible and gold in {forms[i] for i in eligible} else 0),
                'rankings':{label:parent.base.ranking(values,forms,eligible,gold,compatible) for label,values in [('neural',neural),('frequency',frequency)]}}
            rows.append(row)
    summary=[]
    for population in ('known_content','lexical_content'):
        for stage in STAGES:
            selected=[r for r in rows if r['stage']==stage and r['gold_kind']=='content' and (population=='known_content' or r['lexical'])]
            for metric in ('neural','frequency'):
                summary.append({'population':population,'stage':stage,'metric':metric,'types':len(selected),
                    'median_candidates':float(np.median([r['candidates'] for r in selected])),
                    'minimum_candidates':min(r['candidates'] for r in selected),'maximum_candidates':max(r['candidates'] for r in selected),
                    'chance_expected_exact_top10':sum(r['chance_exact_top10'] for r in selected),
                    **{key:sum(r['rankings'][metric][key] for r in selected) for key in ('exact_top1','exact_top10','compatible_top1','compatible_top10')}})
    report={'manifest_sha256':manifest['sha256'],'summary':summary,'cases_sha256':digest(rows)}
    if validate:
        assert json.loads((OUT/'cases.json').read_text())==rows;assert json.loads((OUT/'report.json').read_text())==report
        write_json(OUT/'validation.json',{'all_rankings_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'cases.json',rows);write_json(OUT/'report.json',report)
    for row in summary:
        if row['population']=='lexical_content':print(row,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
