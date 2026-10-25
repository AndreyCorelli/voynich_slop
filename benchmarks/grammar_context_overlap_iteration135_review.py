"""Independent combinatorial null and frozen scalar-classifier replay."""
from benchmarks.grammar_context_overlap_iteration135 import *

def independent_stats(public,wanted):
    n=Counter();left={w:Counter() for w in wanted};right={w:Counter() for w in wanted}
    for s in public:
        for i,t in enumerate(s['tokens']):
            w=t['id']
            if w not in wanted:continue
            n[w]+=1
            if i:left[w][s['tokens'][i-1]['id']]+=1
            if i+1<len(s['tokens']):right[w][s['tokens'][i+1]['id']]+=1
    result={}
    for w in wanted:
        if not n[w]:continue
        a=left[w];b=right[w];nl=sum(a.values());nr=sum(b.values());actual=null=0.
        if nl and nr:
            denominator=math.comb(nl+nr,nl)
            for neighbor in set(a)|set(b):
                count=a[neighbor]+b[neighbor];actual+=min(a[neighbor]/nl,b[neighbor]/nr)
                for k in range(max(0,count-nr),min(count,nl)+1):null+=(math.comb(count,k)*math.comb(nl+nr-count,nl-k)/denominator)*min(k/nl,(count-k)/nr)
        result[w]=dict(n=n[w],left_n=nl,right_n=nr,supported=bool(nl and nr),overlap=actual,null_mean=null,corrected=actual-null,frequency=math.log1p(n[w]))
    return result

def equal_stats(a,b):
    assert set(a)==set(b)
    for w in a:
        for k in a[w]:assert abs(a[w][k]-b[w][k])<1e-11,(w,k,a[w][k],b[w][k])

def run():
    hashes=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);st=independent_stats(public,{lookup[w] for w in train});equal_stats(st,load(OUT/'training-statistics.json'));models=load(OUT/'models.json');oof=load(OUT/'oof-probabilities.json');cal=load(OUT/'calibrators.json')
    for arm in ARMS:
        for key in ['0','1','2','final']:
            held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];assert models[arm][key]['types']==tr;m=fit_scalar(st,tr,lookup,anchors,arm);assert abs(m['loss']-models[arm][key]['loss'])<1e-8;assert np.allclose(m['weights'],models[arm][key]['weights'],atol=1e-6,rtol=1e-6)
            for w in held:assert abs(predict_scalar(st[lookup[w]][arm],models[arm][key])-oof[arm][w])<1e-10
        offset=fit_offset([oof[arm][w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);assert offset==cal[arm]
    contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration132/predictions.json');pred=load(OUT/'predictions.json');saved=load(OUT/'statistics.json');summary=load(OUT/'class-summary.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&reserved;typechecks=metricschecks=0
    for key,context in contexts.items():
        assert not {s['sent_id'] for s in context}&reserved;lookup={r['type']:r['opaque'] for r in old[key]};stats=independent_stats(context,set(lookup.values()));equal_stats(stats,saved[key]);identities=sorted({t['id'] for s in context for t in s['tokens']});rename={w:str(len(identities)-i) for i,w in enumerate(identities)};poison=[dict(s,tokens=[dict(id=rename[t['id']],anchor='POISON',tag='POISON') for t in s['tokens']]) for s in context];renamed=statistics(poison,{rename[w] for w in lookup.values()});equal_stats(stats,{w:renamed[rename[w]] for w in lookup.values()})
        for arm,rows in pred[key].items():
            assert {r['type'] for r in rows}==set(lookup)
            for r in rows:
                value=stats[r['opaque']][arm];assert abs(value-r['statistic'])<1e-11;p=predict_scalar(value,models[arm]['final']);assert abs(p-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([p],cal[arm])[0])-r['probabilities']['new'])<1e-10;typechecks+=1
            for name,m in summary[key][arm].items():
                p=np.array([r['probabilities'][name] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);a=p>.5;assert m['correct']==int((a==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12;assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])));counts=np.array([r['n'] for r in rows]);assert abs(m['token_weighted_accuracy']-float(np.dot(counts,a==y)/counts.sum()))<1e-12;metricschecks+=1
    diagnostic={}
    for key,arms in pred.items():
        rows=arms['corrected'];diagnostic[key]=dict(wrong_types=[r['type'] for r in rows if (r['probabilities']['new']>.5)!=(anchors[r['type']]=='CCONJ')],ADP=[dict(type=r['type'],statistic=r['statistic'],probability=r['probabilities']['new']) for r in rows if anchors[r['type']]=='ADP'],CCONJ=[dict(type=r['type'],statistic=r['statistic'],probability=r['probabilities']['new']) for r in rows if anchors[r['type']]=='CCONJ'])
    save(OUT/'diagnostic.json',diagnostic);save(OUT/'audit.json',dict(input_hashes_verified=hashes,scalar_models_retrained=12,independent_combinatorial_statistic_types=13+sum(len(v) for v in saved.values()),target_probabilities_replayed=typechecks,metric_groups=metricschecks,anchor_tag_poison_and_id_renaming_views=5,no_anchor_inputs_or_pp_inference=True,strict_training_type_and_reserve_exclusion_checked=True));print(load(OUT/'audit.json'));print({k:v['wrong_types'] for k,v in diagnostic.items()})
if __name__=='__main__':run()
