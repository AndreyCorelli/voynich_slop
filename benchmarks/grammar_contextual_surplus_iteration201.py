"""Development-only contextual-surplus supervision with fixed anonymous features."""
from collections import Counter,defaultdict
import re
import numpy as np
from benchmarks.grammar_within_author_ranking_iteration196 import ROOT,Path,load,save,digest,topk,CONTROL
from benchmarks.grammar_case_subfamilies_iteration172 import score,CASES,TAGS
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration201';BASE=ROOT/'iteration193';PREVIOUS=ROOT/'iteration196'
AUTHORS=['Aquinas','Caesar','Cicero','Jerome'];EPS=1e-12
POLICY='Development-only four authors Aq/Ca/Ci/Je; fixed193 anonymousgraphs/features/admission, no Dante/Seneca/letters/quarantine references. Decode UPOS+Case only admitted development rows, verify old Case scores. For each wordxPOS profile use all lexical occurrences includingmissingCase. Edge label = average across its sharedframes of average across ALL Cartesian occurrence comparisons of [recognizedmatchingCase indicator - sum_c p(c|wordA,POS_i)*p(c|wordB,POS_j)]; missing contributeszero; distinct endpointwords imply independent buckets, analytic exact profile-shuffle expectation. POS/Case serve supervised labels/evaluation only, never prediction inputs. Source authors fixed other3, no residual-label-based eligibility. Authorbalanced ridge .5weightedmean squaredloss+.1/2slopeL2, intercept unpenalized; sourceweightedmean/std identical196matchedpoint scales; rich19/control3, no newfeatures/tuning. Copy196matched point/rank rich/control scores, all targets excluded from training/scaling; freeze labels/trials then allnewmodels/scores/selections before metric aggregation. Fixed tiedtop10/20, allcandidate baseline and clearly labeled gold-residual oracle top10/20 as evaluation-only headroom. Primary richsurplus top10 mean residual and count residual>1e-12; report negative/zero counts, observed/expected frame-macro jointmatching, Case applicability/equality/joint/type coverage as costs. No score probabilities, target-selected winner/source/model, freshvalidation or namedcase/identity claim. Gold heldout residuals cached procedurally but never used in fitting/scaling/selection except explicitly evaluation-only oracle computed AFTER prediction freeze.'

def project_references(admission,graphs):
    lookup={};wanted=defaultdict(set)
    for a in AUTHORS:
        for r in admission[a]:wanted[r['path']].add(r['sent_id'])
    for path,sids in wanted.items():
        sid=None
        with Path(path).open() as f:
            for line in f:
                if line.startswith('# sent_id ='):sid=line.split('=',1)[1].strip()
                elif line.startswith('#') or not line.strip() or sid not in sids:continue
                else:
                    tabs=[i for i,c in enumerate(line) if c=='\t'];assert len(tabs)==9;identifier=line[:tabs[0]]
                    if not identifier.isdigit():continue
                    tag=line[tabs[2]+1:tabs[3]];assert tag in TAGS;feats=line[tabs[4]+1:tabs[5]];m=re.search(r'(?:^|\|)Case=([^|]+)',feats);c=m[1] if m and m[1] in CASES else '';lookup[(path,sid,int(identifier))]=(tag,c)
    return {a:dict(pos=[lookup[tuple(p)][0] if p else 'X' for p in graphs[a]['positions']],case=[lookup[tuple(p)][1] if p else '' for p in graphs[a]['positions']]) for a in AUTHORS}

def labels_for(g,ref):
    profiles=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p:profiles[(g['ids'][i],ref['pos'][i])][ref['case'][i]]+=1
    probs={k:{c:n/sum(v.values()) for c,n in v.items() if c in CASES} for k,v in profiles.items()};result=[]
    for e in g['descriptors']:
        obs=[];expected=[];framecounts=[]
        for f in e['frames']:
            matches=exp=0.;n=0
            for i in f['a_positions']:
                for j in f['b_positions']:
                    n+=1;ci=ref['case'][i];cj=ref['case'][j];matches+=int(ci in CASES and cj in CASES and ci==cj);a=probs[(g['ids'][i],ref['pos'][i])];b=probs[(g['ids'][j],ref['pos'][j])];exp+=sum(p*b.get(c,0) for c,p in a.items())
            obs.append(matches/n);expected.append(exp/n);framecounts.append(n)
        o=sum(obs)/len(obs);x=sum(expected)/len(expected);result.append(dict(a=e['a'],b=e['b'],observed_frame_macro_joint_matching=o,expected_frame_macro_joint_matching=x,surplus=o-x,frames=e['shared_frames'],frame_comparison_counts=framecounts))
    return result

def fit_surplus(raw,y,weights,cols,reference):
    mean=np.array(reference['mean']);scale=np.array(reference['scale']);w=np.array(weights);w/=w.sum();x=np.column_stack([np.ones(len(raw)),(np.array(raw)[:,cols]-mean)/scale]);y=np.array(y);pen=np.diag([0]+[.1]*len(cols));beta=np.linalg.solve(x.T@(w[:,None]*x)+pen,x.T@(w*y));grad=x.T@(w*(x@beta-y))+pen@beta;assert max(abs(grad))<1e-10
    return dict(columns=cols,mean=mean.tolist(),scale=scale.tolist(),beta=beta.tolist(),strength=.1,gradient_max=float(max(abs(grad))),objective=float(.5*np.sum(w*(x@beta-y)**2)+.5*beta@pen@beta))

def predict_surplus(rows,m):
    x=np.column_stack([np.ones(len(rows)),(np.array([r['values'] for r in rows])[:,m['columns']]-m['mean'])/m['scale']]);return (x@np.array(m['beta'])).tolist()

def summarize(ix,labels,case_rows,eligible):
    values=[labels[i]['surplus'] for i in ix];n=len(ix)
    return dict(selected=n,mean_surplus=sum(values)/n if n else None,positive_surplus_pairs=sum(v>EPS for v in values),negative_surplus_pairs=sum(v<-EPS for v in values),zero_surplus_pairs=sum(abs(v)<=EPS for v in values),observed_frame_macro_joint_matching=sum(labels[i]['observed_frame_macro_joint_matching'] for i in ix)/n if n else None,expected_frame_macro_joint_matching=sum(labels[i]['expected_frame_macro_joint_matching'] for i in ix)/n if n else None,case_metrics=listmetrics([case_rows[i] for i in ix],eligible))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());admission=load(BASE/'admission.json');rawpaths=sorted({r['path'] for a in AUTHORS for r in admission[a]});paths=[Path(__file__),Path('benchmarks/grammar_multi_author_review192_193.py')]+[BASE/n for n in ['verification-manifest.json','admission.json','graphs.json','features.json','development-references.json','finalized-sizes.json']]+[PREVIOUS/n for n in ['verification-manifest.json','models.json','scores.json','trials.json']]+[Path(p) for p in rawpaths]
    save(OUT/'design-freeze.json',dict(policy=POLICY,authors=AUTHORS,positive_tolerance=EPS,inputs={str(p):digest(p) for p in paths}))
    for folder in [BASE,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    graphs=load(BASE/'graphs.json');ff=load(BASE/'features.json');oldcase=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');ref=project_references(admission,graphs);save(OUT/'development-references.json',ref);labels={a:labels_for(graphs[a],ref[a]) for a in AUTHORS}
    for a in AUTHORS:assert score(graphs[a]['descriptors'],ref[a]['case'],ref[a]['pos'])['all']==oldcase[a]
    save(OUT/'labels.json',labels);trials={a:[b for b in AUTHORS if b!=a] for a in AUTHORS};save(OUT/'trials.json',trials);save(OUT/'label-trial-freeze.json',{n:digest(OUT/n) for n in ['labels.json','trials.json','development-references.json']})
    oldmodels=load(PREVIOUS/'models.json');oldoutputs=load(PREVIOUS/'scores.json');oldtrials=load(PREVIOUS/'trials.json');models={};outputs={};selections={}
    for target,train in trials.items():
        assert train==oldtrials[target]['eligible_authors'];raw=[r['values'] for a in train for r in ff[a]];y=[r['surplus'] for a in train for r in labels[a]];weights=[1/len(ff[a]) for a in train for _ in ff[a]];models[target]={};outputs[target]={}
        for name,cols in [('rich',list(range(19))),('control',CONTROL)]:
            m=fit_surplus(raw,y,weights,cols,oldmodels[target]['point_'+name]['model']);models[target]['surplus_'+name]=m;outputs[target]['surplus_'+name]=predict_surplus(ff[target],m)
        for n in ['point_rich','point_control','rank_rich','rank_control']:outputs[target][n]=oldoutputs[target][n]
        selections[target]={name+'/top'+str(k):topk(scores,k) for name,scores in outputs[target].items() for k in [10,20]}
    for n,obj in [('models',models),('outputs',outputs),('selections',selections)]:save(OUT/(n+'.json'),obj)
    save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','outputs.json','selections.json']})
    summary={};details={};contrasts={}
    for a in AUTHORS:
        selections[a]['all_candidates']=list(range(len(labels[a])))
        for k in [10,20]:selections[a]['oracle/top'+str(k)]=topk([r['surplus'] for r in labels[a]],k)
        summary[a]={n:summarize(ix,labels[a],oldcase[a],sizes[a]['types']) for n,ix in selections[a].items()};details[a]={n:[dict(edge=i,**labels[a][i]) for i in ix] for n,ix in selections[a].items()};contrasts[a]={}
        for kind in ['rich','control']:
            for baseline in ['point_'+kind,'rank_'+kind]:
                new=summary[a]['surplus_'+kind+'/top10'];old=summary[a][baseline+'/top10'];contrasts[a][kind+'_vs_'+baseline]=dict(mean_surplus_change=new['mean_surplus']-old['mean_surplus'],positive_pair_change=new['positive_surplus_pairs']-old['positive_surplus_pairs'],applicable_pair_change=new['case_metrics']['case_edges']-old['case_metrics']['case_edges'])
    for n,obj in [('evaluation-selections',selections),('summary',summary),('selected-details',details),('contrasts',contrasts)]:save(OUT/(n+'.json'),obj)
    for a in AUTHORS:print(a,{n:(round(v['mean_surplus'],6),v['positive_surplus_pairs'],v['case_metrics']['case_edges'],v['selected']) for n,v in summary[a].items()},flush=True)
if __name__=='__main__':run()
