"""Finalize empty-safe metrics and independently replay frozen development runs."""
from benchmarks.grammar_case_applicability_iteration180_review import independent_features,independent_evaluate,close
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_multi_author_iteration192 import AUTHORS,ROOT,load,save,digest,np,expit,Counter,Path,math

def listmetrics(rows,n):
    r=independent_metrics(rows,max(1,n));r['eligible_types']=n;r['case_type_coverage']=r['case_types_involved']/n if n else None;return r

def run(folder):
    out=ROOT/folder;assert not (out/'finalized-summary.json').exists()
    save(out/'finalization-design.json',dict(code=digest(Path(__file__)),policy='Preserve frozen runner/predictions. Empty-list summary failure only: finalize all author metrics from saved predictions without refit or reselection; absent types have null coverage. Independent features, graph incidence, source-only weighted scaling, Newton refits, predictions, scalar metrics and reserve exclusion audit.',inputs={n:digest(out/n) for n in ['design-freeze.json','feature-freeze.json','prediction-freeze.json','predictions.json','models.json']}))
    for p,h in load(out/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h
    for name in ['feature-freeze','prediction-freeze']:
        for p,h in load(out/(name+'.json')).items():assert digest(out/p)==h
    graphs=load(out/'graphs.json');features=load(out/'features.json');refs=load(out/'development-references.json');models=load(out/'models.json');pred=load(out/'predictions.json');admission=load(out/'admission.json');sizes={};summary={};selection={};fits=0
    reserve={r['sent_id'] for rows in load(Path('experiments/holdouts/grammar-construction-next.json'))['authors'].values() for r in rows}
    allowed={(r['path'],r['sent_id']) for r in load(Path('experiments/datasets/latin-grammar-expansion/v1/development-sentences.json'))}
    allkeys={}
    for a,g in graphs.items():
        assert all('/proiel-' in r['path'] or (r['path'],r['sent_id']) in allowed for r in admission[a]);assert all(r['sent_id'] not in reserve or '/proiel-' not in r['path'] for r in admission[a])
        for r in admission[a]:
            assert r['key'] not in allkeys or allkeys[r['key']]==a;allkeys[r['key']]=a
        ids=g['ids'];dd=g['descriptors'];counts=Counter(ids);expected={}
        for i in range(1,len(ids)-1):
            if g['positions'][i] and g['positions'][i-1] and g['positions'][i+1] and counts[ids[i]]>=5:
                frame=(ids[i-1],ids[i+1]);expected.setdefault(frame,{}).setdefault(ids[i],[]).append(i)
        ep={}
        for frame,centers in expected.items():
            words=sorted(centers)
            for ix,x in enumerate(words):
                for y in words[ix+1:]:ep.setdefault((x,y),{})[frame]=(centers[x],centers[y])
        assert {(e['a'],e['b']) for e in dd}=={k for k,v in ep.items() if len(v)>=2}
        for e in dd:
            assert counts[e['a']]>=5 and counts[e['b']]>=5
            assert {tuple(f['frame']):(f['a_positions'],f['b_positions']) for f in e['frames']}==ep[(e['a'],e['b'])]
        close(independent_features(ids,dd),features[a])
        sizes[a]=dict(sentences=len(admission[a]),lexical_tokens=sum(r['n'] for r in admission[a]),pairs=len(dd),types=len({e[k] for e in dd for k in ['a','b']}),applicable_pairs=sum(r['case_occurrence_pairs']>0 for r in refs[a]))
    for target in AUTHORS:
        train=[a for a in AUTHORS if a!=target and features[a]];raw=np.array([r['values'] for a in train for r in features[a]]);y=np.array([int(r['case_occurrence_pairs']>0) for a in train for r in refs[a]]);w=np.array([1/len(features[a]) for a in train for _ in features[a]]);w/=w.sum()
        for name,m in models[target].items():
            if name=='prior':assert abs(w@y-m['probability'])<1e-12;continue
            xx=raw[:,m['columns']];mean=np.average(xx,axis=0,weights=w);sd=np.sqrt(np.average((xx-mean)**2,axis=0,weights=w));sd[sd<1e-12]=1
            assert np.allclose(mean,m['mean'],atol=1e-12);assert np.allclose(sd,m['scale'],atol=1e-12)
            x=np.column_stack([np.ones(len(xx)),(xx-mean)/sd]);b=np.zeros(x.shape[1]);reg=np.diag([0]+[.1]*(x.shape[1]-1))
            def loss(v):return w@(np.logaddexp(0,x@v)-y*(x@v))+.5*v@reg@v
            for _ in range(100):
                p=expit(x@b);grad=x.T@(w*(p-y))+reg@b
                if max(abs(grad))<1e-11:break
                h=x.T@((w*p*(1-p))[:,None]*x)+reg;step=np.linalg.solve(h,grad);rate=1.
                while loss(b-rate*step)>loss(b)-1e-4*rate*(grad@step):rate*=.5;assert rate>1e-12
                b-=rate*step
            assert max(abs(grad))<1e-9;stored=np.array(m['beta']);assert max(abs(x.T@(w*(expit(x@stored)-y))+reg@stored))<1e-6;assert abs(loss(stored)-loss(b))<1e-10
            if features[target]:
                xt=np.array([r['values'] for r in features[target]])[:,m['columns']];px=expit(np.column_stack([np.ones(len(xt)),(xt-mean)/sd])@b);assert np.max(np.abs(px-pred[target][name]))<1e-6
            fits+=1
        rr=refs[target];yy=[int(r['case_occurrence_pairs']>0) for r in rr];summary[target]={};selection[target]={}
        for name,pp in pred[target].items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                order=sorted(range(len(pp)),key=lambda i:pp[i],reverse=True);lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=pp[order[min(k,len(order))-1]]] if order else []
            selection[target][name]=lists;summary[target][name]=dict(classification=independent_evaluate(yy,pp) if pp else None,lists={n:listmetrics([rr[i] for i in ix],sizes[target]['types']) for n,ix in lists.items()})
    save(out/'finalized-summary.json',summary);save(out/'finalized-selections.json',selection);save(out/'finalized-sizes.json',sizes)
    save(out/'audit.json',dict(passed=True,independent_newton_fits=fits,features_replayed=sum(len(f) for f in features.values()),all_graph_incidence_replayed=True,raw_case_reference_replay='pending separate scalar verification',admission_role_and_reserve_checks=True,reserved_author_labels_not_projected=True,empty_metrics_explicit=True))
    print(folder,sizes,flush=True)
    for a in AUTHORS:
        print(a,{n:dict(auc=v['classification']['auc'] if v['classification'] else None,nll=v['classification']['nll'] if v['classification'] else None,top10=(v['lists']['top10']['case_edges'],v['lists']['top10']['edges']),agreement=v['lists']['top10']['edge_macro_frame_case_agreement']) for n,v in summary[a].items()},flush=True)
if __name__=='__main__':
    for folder in ['iteration192-retry','iteration193']:run(folder)
