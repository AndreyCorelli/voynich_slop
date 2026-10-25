"""Independent dictionary-based graph role and frozen-model audit."""
from benchmarks.grammar_context_roles_iteration141 import *
from collections import defaultdict

def dictionary_stats(ids,wanted):
    left=defaultdict(Counter);right=defaultdict(Counter);counts=Counter(ids)
    for a,b in zip(ids,ids[1:]):right[a][b]+=1;left[b][a]+=1
    def aggregate(neighbors):
        result=defaultdict(float);total=sum(neighbors.values())
        for word,count in neighbors.items():
            mass=count/total
            for side,distribution in [('L',left[word]),('R',right[word])]:
                denom=sum(distribution.values())
                for context,n in distribution.items():result[side,context]+=mass*n/denom
        return result
    result={}
    for word in set(wanted)&set(counts):
        a=aggregate(left[word]);b=aggregate(right[word]);na=math.sqrt(sum(x*x for x in a.values()));nb=math.sqrt(sum(x*x for x in b.values()));dot=sum(x*b.get(k,0.) for k,x in a.items());valid=bool(na and nb);result[word]=dict(n=counts[word],supported=valid,role_similarity=max(0.,min(1.,dot/(na*nb))) if valid else 0.)
    return result

def equal(a,b):
    assert set(a)==set(b)
    for w in a:assert a[w]['n']==b[w]['n'] and a[w]['supported']==b[w]['supported'] and abs(a[w][FEATURE]-b[w][FEATURE])<1e-11

def run():
    hashes=0
    for name in ['design-freeze','model-freeze','transform-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&reserved;stats=dictionary_stats(ids,{lookup[w] for w in train});equal(stats,load(OUT/'training-statistics.json'));models=load(OUT/'models.json');oof=load(OUT/'oof-probabilities.json');cal=load(OUT/'calibrator.json')
    for key in ['0','1','2','final']:
        held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];m=fit_scalar(stats,tr,lookup,anchors,FEATURE);assert m['types']==models[key]['types'];assert abs(m['loss']-models[key]['loss'])<1e-8;assert np.allclose(m['weights'],models[key]['weights'],rtol=1e-6,atol=1e-6)
        for w in held:assert abs(predict_scalar(stats[lookup[w]][FEATURE],models[key])-oof[w])<1e-10
    assert fit_offset([oof[w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True)==cal
    streams,lookups=streams_and_lookups();transforms=load(OUT/'transforms.json');saved=load(OUT/'statistics.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');baseline=load(ROOT/'iteration138/four-text-summary.json');types=metricschecks=0
    for work,seq in streams.items():
        assert len(transforms[work])==17 and transforms[work]['original'] is None
        for name,ix in transforms[work].items():
            if ix is None:stream=seq
            else:
                seed=int(name[4:]);assert seed in NULL_SEEDS;assert ix==np.random.default_rng(seed).permutation(len(seq)).tolist();assert sorted(ix)==list(range(len(seq)));stream=[seq[i] for i in ix]
            assert Counter(stream)==Counter(seq);st=dictionary_stats(stream,set(lookups[work].values()));equal(st,saved[work][name]);rr=pred[work][name];assert {r['opaque'] for r in rr}==set(st)
            for r in rr:
                raw=predict_scalar(st[r['opaque']][FEATURE],models['final']);assert r['n']==st[r['opaque']]['n'];assert abs(raw-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal)[0])-r['probabilities']['new'])<1e-10;types+=1
            for arm,m in summary[work][name].items():
                p=np.array([r['probabilities'][arm] for r in rr]);y=np.array([anchors[r['type']]=='CCONJ' for r in rr]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12;assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])));metricschecks+=1
        c=contrasts[work];assert c['actual']==summary[work]['original']['new'] and c['old_overlap']==baseline[work];null=[summary[work]['word'+str(seed)]['new'] for seed in NULL_SEEDS]
        for name in ['accuracy','nll','auc']:assert abs(c['null_mean'][name]-np.mean([r[name] for r in null]))<1e-12
        assert c['null_auc_range']==[min(r['auc'] for r in null),max(r['auc'] for r in null)];assert c['null_auc_at_least_actual']==sum(r['auc']>=c['actual']['auc'] for r in null);print('audited',work,flush=True)
    m=models['final'];w=np.array(m['weights']);slope=float((w[1,1]-w[1,0])/m['scale']);intercept=float(w[0,1]-w[0,0]-slope*m['mean']+cal['offset']);endpoints=[float(1/(1+math.exp(-(intercept+slope*x)))) for x in [0.,1.]];assert min(endpoints)>.5;save(OUT/'decision-boundary.json',dict(feature_domain=[0.,1.],calibrated_logit_slope=slope,calibrated_logit_intercept=intercept,unclipped_feature_at_probability_half=-intercept/slope,endpoint_probabilities=endpoints,calibrated_classifier_always_CCONJ=True))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,models_retrained=4,dictionary_graph_statistic_types=13+types,probabilities_replayed=types,metric_groups=metricschecks,all68_transformations_and_counts_verified=True,calibrated_domain_collapse_verified=True,strict_type_and_reserve_exclusion_checked=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
