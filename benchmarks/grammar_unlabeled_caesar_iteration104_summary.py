"""Freeze all outcomes and summarize matched author-context additions."""
from benchmarks.grammar_unlabeled_caesar_iteration104 import *


def run():
    cases=load(OUT/'evaluation-cases.json');actions=load(OUT/'actions.json');summary={}
    for view in ['base','civil','expanded']:
        rows=[c for c in cases if c['block']==view];errors=[c for c in rows if c['reference']['error']];control=[c for c in rows if not c['reference']['error']];correct=next(c for c in rows if c['case']=='correct')
        summary[view]=dict(counts=correct['counts'],supported_true_pairs=sum(c['reference']['supported'] for c in errors),raw_top1_correct=sum(c['features']['pair']==c['reference']['pair'] for c in errors),descriptive_top1_correct_stability90=sum(c['features']['pair']==c['reference']['pair'] and c['features']['stability']>=.9 for c in errors),minimum_error_top1_stability=min(c['features']['stability'] for c in errors),error_details=[])
        for c in errors:
            summary[view]['error_details'].append(dict(case=c['case'],reference_supported=c['reference']['supported'],raw_top1_correct=c['features']['pair']==c['reference']['pair'],stability=c['features']['stability'],lower_gap=c['features']['lower_gap'],gain=c['features']['gain'],gap=c['features']['gap'],winner_words=[c['identities'][i] for i in c['features']['pair']] if c['features']['pair'] is not None else None,arms={a:dict(selected=actions[a][view+'/'+c['case']],hit=actions[a][view+'/'+c['case']] is not None and actions[a][view+'/'+c['case']]==c['reference']['pair']) for a in ['frozen95','gain_gap']}))
    summary['paired_transitions']={}
    for arm in ['frozen95','gain_gap']:
        for view in ['civil','expanded']:
            base={c['case']:c for c in cases if c['block']=='base'};after={c['case']:c for c in cases if c['block']==view};changes=[]
            for case,c in base.items():
                def outcome(row,key):
                    p=actions[arm][key+'/'+case]
                    return 'abstain' if p is None else 'correct' if p==row['reference']['pair'] else 'wrong'
                b=outcome(c,'base');a=outcome(after[case],view)
                if b!=a:changes.append(dict(case=case,before=b,after=a))
            summary['paired_transitions'][arm+'/'+view]=changes
    save(OUT/'diagnostic-summary.json',summary)
    print(json.dumps({k:{n:v for n,v in s.items() if n!='error_details'} for k,s in summary.items() if k in ['base','civil','expanded']},indent=2));print(json.dumps(summary['paired_transitions'],indent=2))
if __name__=='__main__':run()
