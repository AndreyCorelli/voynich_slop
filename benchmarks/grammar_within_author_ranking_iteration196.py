"""Matched-source pointwise versus within-author pairwise applicability ranking."""
from benchmarks.grammar_multi_author_iteration193 import AUTHORS,ROOT,Path,load,save,digest,weighted_fit,predict,CONTROL,np,expit,minimize,evaluate
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration196';BASE=ROOT/'iteration193';PREVIOUS=ROOT/'iteration194'
POLICY='Fixed193 graphs/features/case references, no new raw data or reserved evaluation. For each target exclude that author; source eligibility requires >=1 positive and >=1 negative edge, source labels only. Pairwise and matched pointwise use identical eligible authors, columns and equal-author row-weighted mean/std; preserve193 baselines. Rank loss: equally weight eligible authors, within author average log(1+exp(-(x_positive-x_negative) beta)) over ALL positive-negative pairs, +.1/2 slopeL2; no intercept (unidentifiable in contrasts), zero initialization L-BFGS-B, gradient<1e-6. Pointwise same193 .1ridge/intercept and equal-author meanNLL on same sources. Rich19 and control3, fixed settings, no tuning/consensus/filtering. Freeze trials before fitting, all models/scores before metric computation. Rank outputs raw linear scores, never probabilities or .5 decisions; compare all6 target authors at tied top10/20, AUC, applicability/conditional equality/joint yield/type coverage. Classification NLL/Brier/calibration only original/matched pointwise. No gold-selected source subset/objective or winner. Reused development diagnostic; correlated edge/contrast samples, not new independent grammatical cases or exact words.'

def ranking_fit(ff,refs,authors,columns,reference):
    mean=np.array(reference['mean']);scale=np.array(reference['scale']);parts=[];weights=[]
    for a in authors:
        x=(np.array([r['values'] for r in ff[a]])[:,columns]-mean)/scale;y=np.array([r['case_occurrence_pairs']>0 for r in refs[a]])
        d=(x[y][:,None,:]-x[~y][None,:,:]).reshape(-1,len(columns));parts.append(d);weights.append(np.full(len(d),1/(len(authors)*len(d))))
    d=np.concatenate(parts);w=np.concatenate(weights)
    def loss(b):
        z=d@b;return float(w@np.logaddexp(0,-z)+.05*(b@b)), -(d.T@(w*expit(-z)))+.1*b
    r=minimize(loss,np.zeros(len(columns)),jac=True,method='L-BFGS-B',options=dict(maxiter=2000,ftol=1e-14,gtol=1e-9));grad=float(max(abs(loss(r.x)[1])));assert grad<1e-6,(r.message,grad)
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),intercept=0.,strength=.1,objective=float(r.fun),gradient_max=grad,contrasts=len(d))

def ranking_predict(rows,m):
    if not rows:return []
    x=np.array([r['values'] for r in rows])[:,m['columns']];return (((x-m['mean'])/m['scale'])@np.array(m['beta'])).tolist()

def auc(y,values):
    pos=np.array([v for t,v in zip(y,values) if t]);neg=np.array([v for t,v in zip(y,values) if not t])
    return float(np.mean(pos[:,None]>neg[None,:])+.5*np.mean(pos[:,None]==neg[None,:])) if len(pos) and len(neg) else None

def topk(values,k):
    threshold=sorted(values,reverse=True)[min(k,len(values))-1] if values else None
    return [i for i,v in enumerate(values) if v>=threshold]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),Path('benchmarks/grammar_multi_author_review192_193.py')]+[BASE/n for n in ['verification-manifest.json','features.json','development-references.json','finalized-sizes.json','models.json','predictions.json']]+[PREVIOUS/n for n in ['verification-manifest.json','models.json','predictions.json']]
    save(OUT/'design-freeze.json',dict(policy=POLICY,inputs={str(p):digest(p) for p in paths}))
    for folder in [BASE,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    ff=load(BASE/'features.json');refs=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');trials={}
    for target in AUTHORS:
        evidence={a:dict(rows=len(ff[a]),positive=sum(r['case_occurrence_pairs']>0 for r in refs[a]),negative=sum(r['case_occurrence_pairs']==0 for r in refs[a])) for a in AUTHORS if a!=target}
        eligible=[a for a,e in evidence.items() if e['positive'] and e['negative']]
        trials[target]=dict(source_evidence=evidence,eligible_authors=eligible,excluded_authors=[a for a in evidence if a not in eligible],contrasts={a:evidence[a]['positive']*evidence[a]['negative'] for a in eligible})
    save(OUT/'trials.json',trials);save(OUT/'trial-freeze.json',{'trials.json':digest(OUT/'trials.json')})
    models={};scores={};oldmodels=load(BASE/'models.json');oldpred=load(BASE/'predictions.json')
    for target,t in trials.items():
        train=t['eligible_authors'];raw=[r['values'] for a in train for r in ff[a]];y=[int(r['case_occurrence_pairs']>0) for a in train for r in refs[a]];weights=[1/len(ff[a]) for a in train for _ in ff[a]];models[target]={};scores[target]={}
        for label,cols in [('rich',list(range(19))),('control',CONTROL)]:
            point=weighted_fit(raw,y,weights,cols);rank=ranking_fit(ff,refs,train,cols,point);original=oldmodels[target]['rich' if label=='rich' else 'frequency_support']
            for name,m,kind in [('original_'+label,original,'probability'),('point_'+label,point,'probability'),('rank_'+label,rank,'ranking_score')]:
                models[target][name]=dict(kind=kind,model=m);scores[target][name]=ranking_predict(ff[target],m) if kind=='ranking_score' else (predict(ff[target],m) if ff[target] else [])
            assert scores[target]['original_'+label]==oldpred[target]['rich' if label=='rich' else 'frequency_support']
    save(OUT/'models.json',models);save(OUT/'scores.json',scores);save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','scores.json']})
    summary={};selection={};details={};contrasts={}
    for a,mm in scores.items():
        rr=refs[a];y=[int(r['case_occurrence_pairs']>0) for r in rr];summary[a]={};selection[a]={};details[a]={};contrasts[a]={}
        for name,values in mm.items():
            ix={'top'+str(k):topk(values,k) for k in [10,20]};selection[a][name]=ix;summary[a][name]=dict(auc=auc(y,values),classification=evaluate(y,values) if values and models[a][name]['kind']=='probability' else None,lists={k:listmetrics([rr[i] for i in sel],sizes[a]['types']) for k,sel in ix.items()});details[a][name]=[dict(edge=i,score=values[i],applicable=bool(y[i]),**rr[i]) for i in ix['top10']]
        for label in ['rich','control']:
            contrasts[a][label]={}
            for kind in ['point','original']:
                rank=summary[a]['rank_'+label];base=summary[a][kind+'_'+label]
                contrasts[a][label][kind]=dict(auc_change=rank['auc']-base['auc'] if rank['auc'] is not None else None,top10_applicable_change=rank['lists']['top10']['case_edges']-base['lists']['top10']['case_edges'],top10_selected_change=rank['lists']['top10']['edges']-base['lists']['top10']['edges'],entered=sorted(set(selection[a]['rank_'+label]['top10'])-set(selection[a][kind+'_'+label]['top10'])),left=sorted(set(selection[a][kind+'_'+label]['top10'])-set(selection[a]['rank_'+label]['top10'])))
    for n,obj in [('summary',summary),('selections',selection),('shortlist-details',details),('contrasts',contrasts)]:save(OUT/(n+'.json'),obj)
    for a,vv in summary.items():print(a,{n:dict(top10=(v['lists']['top10']['case_edges'],v['lists']['top10']['edges']),auc=v['auc'],joint=v['lists']['top10']['edge_joint_yield']) for n,v in vv.items()},flush=True)
if __name__=='__main__':run()
