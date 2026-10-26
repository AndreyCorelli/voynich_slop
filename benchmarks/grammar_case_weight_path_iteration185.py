"""Fixed diagnostic weight path for influential negative source pair21."""
from benchmarks.grammar_case_fixed_scaling_iteration184 import *
OUT=ROOT/'iteration185'
WEIGHTS=[i/10 for i in range(11)]
PAIR=21

def fit_weight(raw,y,columns,reference,weight):
    xx=np.array(raw)[:,columns];mean=np.array(reference['mean']);scale=np.array(reference['scale']);x=np.column_stack([np.ones(len(xx)),(xx-mean)/scale]);y=np.array(y);mass=np.ones(len(y));mass[PAIR]=weight
    def loss(beta):
        z=x@beta;pen=beta.copy();pen[0]=0
        return float(mass@(np.logaddexp(0,z)-y*z)/sum(mass)+.05*(pen@pen)),x.T@(mass*(expit(z)-y))/sum(mass)+.1*pen
    r=minimize(loss,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=1000,ftol=1e-13,gtol=1e-9));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),strength=.1,weight=weight,objective=float(r.fun),gradient_max=float(max(abs(loss(r.x)[1]))))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),ROOT/'iteration184/verification-manifest.json',ROOT/'iteration184/models.json',ROOT/'iteration184/predictions.json',ROOT/'iteration184/summary.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},weights=WEIGHTS,pair=PAIR,design='Diagnostic ONLY: negative sourcepair21 already identified184. Weight grid0,.1,..1 frozen, no weight chosen by target results. Same180 rich19/control3 fixed full-source scaling/ridge.1/unpenalizedintercept/feature projection; weighted loss divided by sum of training weights (51+w), so0 equals fixed-scale omission184 and1 equals180, within1e-6 numerical tolerance. All other examples unit weight. Freeze all models then source+target predictions before target labels. Record all classification/calibration, fixed.5/top10/top20 tie-inclusive lists, sourcepair21 predicted probability, full standardized coefficient path and coordinate endpoint logit contributions for ALL126 targets. Adjacent-grid top10 entrants/leavers are grid crossings, not exact continuous breakpoints. Logit contribution decomposition is algebraic, not causal/unique importance with correlated features. No target tuning, confidence repair or selected model, no new annotations/reserves/sealeddata or namedcase/POS/nuclei claim. Independent weighted Newton fits/endpoint baselines/predictions/metrics/decompositions/crossings audit.'))
    ff=load(ROOT/'iteration180/features.json');y=load(ROOT/'iteration180/source-labels.json');assert y[PAIR]==0;reference=load(ROOT/'iteration180/models.json');raw=[r['values'] for r in ff['earlier']];models={str(w):{a:fit_weight(raw,y,cols,reference[a],w) for a,cols in ARMS.items()} for w in WEIGHTS};save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/'models.json'):digest(OUT/'models.json')}))
    predictions={w:{pool:{a:predict(rows,m) for a,m in arms.items()} for pool,rows in ff.items()} for w,arms in models.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}))
    rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in rr];summary={};selections={}
    for w,pools in predictions.items():
        summary[w]={};selections[w]={}
        for arm,pp in pools['replication'].items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            selections[w][arm]=lists;summary[w][arm]=dict(source_pair_probability=pools['earlier'][arm][PAIR],classification=evaluate(target,pp),lists={label:metrics([rr[i] for i in ix],857) for label,ix in lists.items()})
    save(OUT/'selections.json',selections);save(OUT/'summary.json',summary)
    changes={a:[] for a in ARMS};contributions={}
    for arm,cols in ARMS.items():
        for lo,hi in zip(WEIGHTS,WEIGHTS[1:]):
            before=set(selections[str(lo)][arm]['top10']);after=set(selections[str(hi)][arm]['top10']);changes[arm].append(dict(lower=lo,upper=hi,entered=sorted(after-before),left=sorted(before-after)))
        m=models['0.0'][arm];delta=np.array(models['1.0'][arm]['beta'])-m['beta'];x=np.column_stack([np.ones(len(rr)),(np.array([r['values'] for r in ff['replication']])[:,cols]-m['mean'])/m['scale']]);contributions[arm]=dict(columns=['intercept']+[COLS[i] for i in cols],delta_beta=delta.tolist(),targets=[dict(index=i,contributions=(row*delta).tolist(),logit_change=float(row@delta)) for i,row in enumerate(x)])
    save(OUT/'top10-grid-crossings.json',changes);save(OUT/'endpoint-logit-contributions.json',contributions)
    print(json.dumps({w:{a:dict(nll=s['classification']['nll'],auc=s['classification']['auc'],top10_cases=s['lists']['top10']['case_edges'],joint=s['lists']['top10']['edge_joint_yield'],source_pair_probability=s['source_pair_probability']) for a,s in arms.items()} for w,arms in summary.items()}),flush=True)
if __name__=='__main__':run()
