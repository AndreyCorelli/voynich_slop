"""Independent contrast enumeration, Newton optimization, scores and metric audit."""
from benchmarks.grammar_within_author_ranking_iteration196 import OUT,BASE,PREVIOUS,AUTHORS,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_consensus_core_iteration195_review import scalar_metrics
import numpy as np
from scipy.special import expit

def newton(objective,hessian,n):
    b=np.zeros(n)
    for _ in range(100):
        value,g=objective(b)
        if max(abs(g))<1e-11:break
        step=np.linalg.solve(hessian(b),g);rate=1.
        while objective(b-rate*step)[0]>value-1e-4*rate*(g@step):
            rate/=2;assert rate>1e-12
        b-=rate*step
    assert max(abs(objective(b)[1]))<1e-9
    return b

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for file in ['trial-freeze.json','prediction-freeze.json']:
        for p,h in load(OUT/file).items():assert digest(OUT/p)==h;hashes+=1
    for folder in [BASE,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    ff=load(BASE/'features.json');refs=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');trials=load(OUT/'trials.json');models=load(OUT/'models.json');scores=load(OUT/'scores.json');summary=load(OUT/'summary.json');selection=load(OUT/'selections.json');details=load(OUT/'shortlist-details.json');contrasts=load(OUT/'contrasts.json');oldmodels=load(BASE/'models.json');oldpred=load(BASE/'predictions.json');previousmodels=load(PREVIOUS/'models.json');previouspred=load(PREVIOUS/'predictions.json');fits=groups=totalpairs=0;uniques=set()
    for target in AUTHORS:
        evidence={a:dict(rows=len(ff[a]),positive=sum(r['case_occurrence_pairs']>0 for r in refs[a]),negative=sum(r['case_occurrence_pairs']==0 for r in refs[a])) for a in AUTHORS if a!=target};train=[a for a,e in evidence.items() if e['positive']>0 and e['negative']>0];uniques.add(tuple(train))
        assert trials[target]==dict(source_evidence=evidence,eligible_authors=train,excluded_authors=[a for a in evidence if a not in train],contrasts={a:evidence[a]['positive']*evidence[a]['negative'] for a in train})
        raw=np.array([r['values'] for a in train for r in ff[a]]);y=np.array([int(r['case_occurrence_pairs']>0) for a in train for r in refs[a]]);w=np.concatenate([np.full(len(ff[a]),1/(len(train)*len(ff[a]))) for a in train]);yy=[int(r['case_occurrence_pairs']>0) for r in refs[target]]
        for label,columns in [('rich',list(range(19))),('control',[0,9,18])]:
            point=models[target]['point_'+label]['model'];rank=models[target]['rank_'+label]['model'];xx=raw[:,columns];mean=np.average(xx,axis=0,weights=w);sd=np.sqrt(np.average((xx-mean)**2,axis=0,weights=w));sd[sd<1e-12]=1
            for model in [point,rank]:assert model['columns']==columns;assert model['strength']==.1;assert np.allclose(model['mean'],mean,atol=1e-12,rtol=1e-12);assert np.allclose(model['scale'],sd,atol=1e-12,rtol=1e-12)
            x=np.column_stack([np.ones(len(xx)),(xx-mean)/sd]);penalty=np.diag([0]+[.1]*len(columns))
            def pointobjective(b):
                z=x@b;return float(w@(np.logaddexp(0,z)-y*z)+.5*b@penalty@b), x.T@(w*(expit(z)-y))+penalty@b
            def pointhessian(b):
                p=expit(x@b);return x.T@((w*p*(1-p))[:,None]*x)+penalty
            b=newton(pointobjective,pointhessian,len(columns)+1);stored=np.array(point['beta']);assert max(abs(pointobjective(stored)[1]))<1e-6;assert abs(pointobjective(stored)[0]-pointobjective(b)[0])<1e-10;fits+=1
            # Exact matched pointwise source-policy replay, including singleton exclusion.
            oldname='baseline' if target=='Palladius' else 'without-Palladius';oldlabel='rich' if label=='rich' else 'frequency_support'
            assert point==previousmodels[target][oldname][oldlabel];assert scores[target]['point_'+label]==previouspred[target][oldname][oldlabel]
            assert models[target]['original_'+label]['model']==oldmodels[target][oldlabel];assert scores[target]['original_'+label]==oldpred[target][oldlabel]
            ds=[]
            for a in train:
                values=np.array([r['values'] for r in ff[a]])[:,columns];pos=[i for i,r in enumerate(refs[a]) if r['case_occurrence_pairs']];neg=[i for i,r in enumerate(refs[a]) if not r['case_occurrence_pairs']]
                aa=np.repeat(pos,len(neg));bb=np.tile(neg,len(pos));d=(values[aa]-values[bb])/sd;assert len(d)==trials[target]['contrasts'][a];ds.append(d);totalpairs+=len(d)
            n=len(ds)
            def rankobjective(beta):
                loss=.05*(beta@beta);gradient=.1*beta.copy()
                for d in ds:
                    z=d@beta;loss+=np.mean(np.logaddexp(0,-z))/n;gradient-=d.T@expit(-z)/(n*len(d))
                return float(loss),gradient
            def rankhessian(beta):
                h=.1*np.eye(len(columns))
                for d in ds:
                    p=expit(d@beta);h+=d.T@((p*(1-p))[:,None]*d)/(n*len(d))
                return h
            br=newton(rankobjective,rankhessian,len(columns));storedrank=np.array(rank['beta']);assert rank['intercept']==0.;assert rank['contrasts']==sum(map(len,ds));assert abs(rankobjective(storedrank)[0]-rank['objective'])<1e-12;assert abs(rankobjective(br)[0]-rank['objective'])<1e-10;assert max(abs(rankobjective(storedrank)[1]))<1e-6;fits+=1
            if ff[target]:
                xt=(np.array([r['values'] for r in ff[target]])[:,columns]-mean)/sd
                assert np.max(abs(expit(np.column_stack([np.ones(len(xt)),xt])@b)-scores[target]['point_'+label]))<1e-6
                assert np.max(abs(xt@br-scores[target]['rank_'+label]))<1e-6
        for name,values in scores[target].items():
            kind=models[target][name]['kind'];assert kind==('ranking_score' if name.startswith('rank_') else 'probability')
            pp=[v for y,v in zip(yy,values) if y];nn=[v for y,v in zip(yy,values) if not y];a=sum((p>n)+.5*(p==n) for p in pp for n in nn)/(len(pp)*len(nn)) if pp and nn else None
            sels={}
            for k in [10,20]:sels['top'+str(k)]=[i for i,v in enumerate(values) if sum(t>v for t in values)<k]
            assert sels==selection[target][name]
            computed=dict(auc=a,classification=independent_evaluate(yy,values) if values and kind=='probability' else None,lists={key:scalar_metrics([refs[target][i] for i in ix],sizes[target]['types']) for key,ix in sels.items()});close(computed,summary[target][name]);groups+=2
            assert details[target][name]==[dict(edge=i,score=values[i],applicable=bool(yy[i]),**refs[target][i]) for i in sels['top10']]
        for label in ['rich','control']:
            for kind in ['point','original']:
                rank=summary[target]['rank_'+label];base=summary[target][kind+'_'+label];ix=selection[target]['rank_'+label]['top10'];bx=selection[target][kind+'_'+label]['top10'];c=dict(auc_change=rank['auc']-base['auc'] if rank['auc'] is not None else None,top10_applicable_change=rank['lists']['top10']['case_edges']-base['lists']['top10']['case_edges'],top10_selected_change=rank['lists']['top10']['edges']-base['lists']['top10']['edges'],entered=sorted(set(ix)-set(bx)),left=sorted(set(bx)-set(ix)));close(c,contrasts[target][label][kind])
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,independent_newton_fits=fits,distinct_eligible_source_sets=len(uniques),positive_negative_contrasts_enumerated_across_all_fits=totalpairs,metric_groups=groups,exact_original_and_matched_pointwise_replays=24,all_scores_and_contrasts_replayed=True,ranking_scores_never_probability_evaluated=True,no_new_raw_or_reserved_data=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
