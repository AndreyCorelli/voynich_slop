"""Frozen candidate-quality flags: retained accuracy and coverage, no tag edits."""
import numpy as np
from benchmarks.grammar_candidate_abstention_iteration35 import OUT,PREVIOUS,DATA,EPSILONS,BUDGETS,SCORES,PRIMARY,load,save,digest
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread
from voynich_smt.candidate_abstention import flag,abstention_metrics


def pooled(rows):
    keys=('tokens','baseline_correct','flagged','retained','retained_correct','excluded','flagged_excluded','flagged_errors','correct_tags_discarded','protected_correct','false_flags_protected')
    r={k:sum(c['metrics'][k] for c in rows) for k in keys};n=r['tokens'];nf=r['flagged'];nk=r['retained'];ne=r['excluded'];prot=r['protected_correct']
    r.update(baseline_accuracy=r['baseline_correct']/n,coverage=nk/n,retained_accuracy=r['retained_correct']/nk if nk else None,retained_correct_fraction=r['retained_correct']/n,
        excluded_precision=r['flagged_excluded']/nf if nf else None,excluded_recall=r['flagged_excluded']/ne if ne else None,flagged_error_precision=r['flagged_errors']/nf if nf else None,false_flag_rate_protected=r['false_flags_protected']/prot if prot else None,
        random_expected_retained_accuracy=sum(c['metrics']['baseline_accuracy']*c['metrics']['retained'] for c in rows)/nk if nk else None)
    return r


def bootstrap(rows,repetitions=1000):
    rng=np.random.default_rng(3501);base=np.array([r['sentence_counts']['baseline_correct'] for r in rows]);kept=np.array([r['sentence_counts']['retained'] for r in rows]);hit=np.array([r['sentence_counts']['retained_correct'] for r in rows]);sizes=np.array(rows[0]['sentence_counts']['tokens']);delta=[]
    for _ in range(repetitions):
        ix=rng.integers(len(sizes),size=len(sizes));den=kept[:,ix].sum()
        if den:delta.append(float(hit[:,ix].sum()/den-base[:,ix].sum()/(len(rows)*sizes[ix].sum())))
    return dict(replicates=repetitions,retained_minus_full_accuracy_95=[float(v) for v in np.quantile(delta,[.025,.975])])


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve evaluation')
    for p,h in load(OUT/'evaluation-freeze.json')['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];records=load(OUT/'observations.json');truth=load(PREVIOUS/'feature-truth.json');policies=load(OUT/'policies.json');offset=sum(map(len,obs['sequences'][:obs['offset']]));sizes=list(map(len,obs['sequences'][obs['offset']:]));bounds=np.r_[0,np.cumsum(sizes)];cells=[]
    for r,y in zip(records,truth):
        pred=np.asarray(r['predicted'])[offset:];gold=np.asarray(y['gold'])[offset:];excluded=np.asarray(y['excluded'])[offset:];correct=pred==gold
        for score in SCORES:
            values=np.asarray(r['scores'][score])[offset:]
            for budget in BUDGETS:
                policy=policies[f"{r['arm']}/{r['epsilon']}/{score}/{budget}"];flagged=flag(values,policy);m=abstention_metrics(pred,gold,excluded,flagged);keep=~flagged
                row=dict(**{k:r[k] for k in ('mask_seed','rate','epsilon','arm')},score=score,budget=budget,policy=policy,metrics=m,flagged=flagged.tolist(),sentence_counts=dict(tokens=sizes,
                    baseline_correct=[int(correct[a:b].sum()) for a,b in zip(bounds[:-1],bounds[1:])],retained=[int(keep[a:b].sum()) for a,b in zip(bounds[:-1],bounds[1:])],retained_correct=[int((keep[a:b]&correct[a:b]).sum()) for a,b in zip(bounds[:-1],bounds[1:])]))
                cells.append(row)
    summary=[]
    for arm in ('word','ending'):
        for eps in EPSILONS:
            for rate in (.1,.5):
                for score in SCORES:
                    for budget in BUDGETS:
                        group=[c for c in cells if c['arm']==arm and c['epsilon']==eps and c['rate']==rate and c['score']==score and c['budget']==budget];assert len(group)==5
                        summary.append(dict(arm=arm,epsilon=eps,rate=rate,score=score,budget=budget,pooled=pooled(group),spread={k:spread([r['metrics'][k] for r in group]) for k in ('coverage','retained_accuracy','excluded_precision','excluded_recall','false_flag_rate_protected')},bootstrap=bootstrap(group)))
    save(OUT/'evaluation.json',dict(cells=cells,summary=summary))
    for row in summary:
        if row['score']=='outside_mass':
            p=row['pooled'];print(row['arm'],row['epsilon'],row['rate'],row['budget'],'P/R',p['excluded_precision'],p['excluded_recall'],'falseflag',p['false_flag_rate_protected'],'accuracy/coverage',p['retained_accuracy'],p['coverage'],'base',p['baseline_accuracy'])
    plot(summary)


def plot(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(9,4),layout='constrained')
    for ax,rate in zip(axes,(.1,.5)):
        for score in SCORES:
            rows=sorted([r for r in summary if r['arm']=='word' and r['epsilon']==.01 and r['rate']==rate and r['score']==score],key=lambda r:r['budget'])
            points=[(1.,rows[0]['pooled']['baseline_accuracy'])]+[(r['pooled']['coverage'],r['pooled']['retained_accuracy']) for r in rows]
            ax.plot([x*100 for x,y in points],[y*100 for x,y in points],'o-',label=score)
            for r in rows:ax.annotate(f"{r['budget']:.0%} budget",(100*r['pooled']['coverage'],100*r['pooled']['retained_accuracy']),fontsize=7,xytext=(3,3),textcoords='offset points')
        ax.set(title=f'{rate:.0%} types lose one true class',xlabel='Retained query tokens (%)',ylabel='Retained tag accuracy (%)',ylim=(0,100));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Candidate flags: existing development queries, word arm, epsilon .01');fig.savefig(OUT/'abstention-accuracy-coverage.svg');plt.close(fig)

if __name__=='__main__':run()
