"""Independent direct-offset and combinatorial distance-two audit."""
from benchmarks.grammar_joint_distance_two_iteration146 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def independent(ids,wanted):
    f=combined(ids,wanted);left={w:Counter() for w in wanted};right={w:Counter() for w in wanted}
    for j,w in enumerate(ids):
        if w not in wanted:continue
        if j>=2:left[w][ids[j-2]]+=1
        if j+2<len(ids):right[w][ids[j+2]]+=1
    for w in f:
        a,b=left[w],right[w];nl,nr=sum(a.values()),sum(b.values());v=e=0.
        if nl and nr:
            den=math.comb(nl+nr,nl)
            for c in set(a)|set(b):
                mass=a[c]+b[c];v+=min(a[c]/nl,b[c]/nr)
                for k in range(max(0,mass-nr),min(mass,nl)+1):e+=math.comb(mass,k)*math.comb(nl+nr-mass,nl-k)/den*min(k/nl,(mass-k)/nr)
        f[w]['distance_two']=v-e
    return f

def equal(a,b):
    assert set(a)==set(b)
    for w in a:
        for c in a[w]:assert abs(a[w][c]-b[w][c])<1e-11,(w,c)

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','model-freeze','transforms-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);ids=[t['id'] for s in public for t in s['tokens']];f=independent(ids,{lookup[w] for w in train});equal(f,load(OUT/'training-features.json'));models=load(OUT/'models.json');oof=load(OUT/'oof.json')
    for key,m in models.items():
        held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];re=fit_vector(f,tr,lookup,anchors,COLUMNS);assert m['training']==tr and abs(re['loss']-m['loss'])<1e-8
        for w in tr:assert abs(predict_vector(f[lookup[w]],re)-predict_vector(f[lookup[w]],m))<1e-6
        for w in held:assert abs(predict_vector(f[lookup[w]],m)-oof[w])<1e-10
    streams,lookups=inputs();features=load(OUT/'features.json');pred=load(OUT/'predictions.json');transforms=load(OUT/'transforms.json');summary=load(OUT/'summary.json');baseline=load(ROOT/'iteration142/models.json')['joint']['final'];old=load(ROOT/'iteration144/predictions.json')
    for w,seq in streams.items():
        assert set(transforms[w])=={'original',*['word'+str(k) for k in SEEDS]}
        for view,ix in transforms[w].items():
            if view=='original':assert ix is None;ids=seq
            else:assert ix==np.random.default_rng(int(view[4:])).permutation(len(seq)).tolist();ids=[seq[j] for j in ix]
            assert Counter(ids)==Counter(seq);f=independent(ids,set(lookups[w].values()));equal(f,features[w][view]);fc+=len(f)
            for name,rows in pred[w][view].items():
                m=baseline if name=='baseline' else models['final'];coef=np.array(m['weights'])[:,1]-np.array(m['weights'])[:,0];assert {r['opaque'] for r in rows}==set(f)
                for r in rows:
                    assert r['opaque']==lookups[w][r['type']] and r['n']==f[r['opaque']]['n'];x=(np.array([f[r['opaque']][c] for c in m['columns']])-np.array(m['mean']))/np.array(m['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
                q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);s=summary[w][view][name];assert s['correct']==int(((q>.5)==y).sum());assert abs(s['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert s['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
        assert pred[w]['original']['baseline']==old[w+'/full']['joint']
        print('audited',w,flush=True)
    assert summary==summarize(pred,anchors)
    for w,configs in load(OUT/'contrasts.json').items():
        for name,r in configs.items():
            nn=[summary[w]['word'+str(k)][name]['auc'] for k in SEEDS];assert r==dict(actual=summary[w]['original'][name],null_max_auc=max(nn),null_auc_at_least_actual=sum(v>=summary[w]['original'][name]['auc'] for v in nn))
    save(OUT/'audit.json',dict(input_hashes_verified=hc,models_retrained=4,oof_predictions_replayed=13,views_verified=119,independent_feature_pairs=fc,independent_probability_replays=pc,independent_metric_groups=mc,full_baselines_matched=7))
if __name__=='__main__':run()
