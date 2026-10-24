"""Apply frozen background-selected repair budgets to old query scenarios."""
import numpy as np
from benchmarks.grammar_calibrated_repair_iteration38 import OUT,MODELS,DATA,BASELINE,EXACT,HARD,RISKS,PRIMARY,load,save,digest
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import bootstrap
from voynich_smt.repair_budget_selection import edit_counts
from voynich_smt.missing_class_support import missing_support
from voynich_smt.candidate_abstention import abstention_metrics


def pool(rows):
    keys=('tokens','baseline_correct','corrected','spoiled','net','recovered_excluded')
    c={key:sum(r['counts'][key] for r in rows) for key in keys};c.update(baseline_accuracy=c['baseline_correct']/c['tokens'],accuracy=(c['baseline_correct']+c['net'])/c['tokens'],accuracy_delta=c['net']/c['tokens'],spoil_rate=c['spoiled']/c['baseline_correct'] if c['baseline_correct'] else None)
    retained=sum(r['abstention']['retained'] for r in rows);c['retained_accuracy']=sum(r['abstention']['retained_correct'] for r in rows)/retained if retained else None;c['retained_coverage']=retained/c['tokens'];return c


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'evaluation-freeze.json')['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];truth=load(DATA/'observation-truth.json')['calibration'];gold=np.concatenate(truth);offset=sum(map(len,obs['sequences'][:obs['offset']]));gq=gold[offset:];ids=np.concatenate(obs['sequences'])[offset:];sizes=list(map(len,obs['sequences'][obs['offset']:]));bounds=np.r_[0,np.cumsum(sizes)];reference=np.array(load(EXACT/'support-truth.json')['support']);additions=load(BASELINE/'schedules.json');deletions=load(HARD/'deletions.json');policies=load(OUT/'policies.json');cases=load(OUT/'predictions.json');cells=[]
    for case in cases:
        baseline=np.array(case['baseline'])[offset:];support,_=missing_support(reference,additions[str(case['mask_seed'])],deletions[str(case['mask_seed'])],case['rate']);excluded=~support[gq,ids];flagged=np.array(case['flagged'])[offset:]
        for risk in RISKS:
            p=policies[f"{case['arm']}/{case['strategy']}/{risk}"];budget=p['budget'];pred=np.array(case['predictions'][str(budget)])[offset:];delta=(pred==gq).astype(int)-(baseline==gq).astype(int);c=edit_counts(baseline,pred,gq);c['recovered_excluded']=int(((pred==gq)&excluded).sum())
            cells.append(dict(**{k:case[k] for k in ('mask_seed','rate','arm','strategy')},risk=risk,budget=budget,counts=c,query_prediction=pred.tolist(),spoil_rate=c['spoiled']/c['baseline_correct'] if c['baseline_correct'] else None,abstention=abstention_metrics(pred,gq,excluded,flagged),sentence_tokens=sizes,sentence_delta=[int(delta[a:b].sum()) for a,b in zip(bounds[:-1],bounds[1:])]))
    summary=[]
    for arm in ('word','ending'):
        for strategy in ('context','random'):
            for risk in RISKS:
                for rate in (.1,.5,'pooled'):
                    rows=[r for r in cells if r['arm']==arm and r['strategy']==strategy and r['risk']==risk and (rate=='pooled' or r['rate']==rate)];assert len(rows)==(10 if rate=='pooled' else 5)
                    summary.append(dict(arm=arm,strategy=strategy,risk=risk,rate=rate,budget=policies[f'{arm}/{strategy}/{risk}']['budget'],pooled=pool(rows),bootstrap=bootstrap(rows)))
    comparisons=[]
    for arm in ('word','ending'):
        for rate in (.1,.5):
            a=sorted([r for r in cells if r['arm']==arm and r['strategy']=='context' and r['risk']==PRIMARY and r['rate']==rate],key=lambda r:r['mask_seed']);b=sorted([r for r in cells if r['arm']==arm and r['strategy']=='random' and r['risk']==PRIMARY and r['rate']==rate],key=lambda r:r['mask_seed']);diff=[dict(sentence_tokens=x['sentence_tokens'],sentence_delta=(np.array(x['sentence_delta'])-np.array(y['sentence_delta'])).tolist()) for x,y in zip(a,b)];net=sum(sum(r['sentence_delta']) for r in diff);comparisons.append(dict(arm=arm,rate=rate,net_context_minus_random=net,accuracy_delta=net/(5*473),bootstrap=bootstrap(diff)))
    save(OUT/'evaluation.json',dict(cells=cells,summary=summary,comparisons=comparisons))
    for r in summary:
        if r['strategy']=='context':print(r['arm'],r['risk'],r['rate'],'budget',r['budget'],r['pooled'])

if __name__=='__main__':run()
