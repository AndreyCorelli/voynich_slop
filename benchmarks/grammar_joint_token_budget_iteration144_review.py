"""Independent feature, window, probability and metric audit for iteration144."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def run():
    hashes=0
    for n in ['design-freeze','selection-freeze','predictions-freeze']:
        for p,h in load(OUT/(n+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    streams,lookups=inputs();selection=load(OUT/'selection.json');expected={}
    for w,seq in streams.items():
        expected[w+'/full']=dict(work=w,start=0,stop=len(seq))
        for seed in [14400,14401,14402]:
            start=int.from_bytes(hashlib.sha256(f'{seed}|{w}'.encode()).digest(),'big')%(len(seq)-3999)
            for size in [1000,3000,4000]:
                lo=start+(4000-size)//2;expected[f'{w}/{seed}/{size}']=dict(work=w,start=lo,stop=lo+size)
    assert selection==expected and len(selection)==70
    features=load(OUT/'features.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');models=load(ROOT/'iteration142/models.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];fc=pc=mc=0
    for key,r in selection.items():
        f=combined(streams[r['work']][r['start']:r['stop']],set(lookups[r['work']].values()));assert set(f)==set(features[key])
        for i in f:
            assert f[i]['n']==features[key][i]['n']
            for col in ['corrected','role_similarity']:assert abs(f[i][col]-features[key][i][col])<1e-11
            fc+=1
        for name,rows in pred[key].items():
            assert {x['opaque'] for x in rows}==set(f)
            model=models[name]['final'];weights=np.array(model['weights']);coef=weights[:,1]-weights[:,0]
            for row in rows:
                x=(np.array([f[row['opaque']][c] for c in model['columns']])-model['mean'])/model['scale'];logit=float(coef[0]+x@coef[1:]);p=1/(1+math.exp(-logit));assert abs(p-row['probabilities']['raw'])<1e-10;pc+=1
            for group in ['all','supported','common14']:
                core=set(load(ROOT/'iteration139/common-core.json'));rr=[x for x in rows if group=='all' or (group=='supported' and x['supported']) or (group=='common14' and x['type'] in core)];q=np.array([x['probabilities']['raw'] for x in rr]);y=np.array([anchors[x['type']]=='CCONJ' for x in rr]);m=summary[key][name]['metrics'][group];assert m['n']==len(rr) and m['correct']==int(((q>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert abs(m['auc']-float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:]))))<1e-12;mc+=1
        print('audited',key,flush=True)
    assert summary==summarize(pred,selection,lookups)
    for w in streams:
        reference=load(ROOT/('iteration142' if w in ['Caesar','Jerome','gellius-1','livy-1'] else 'iteration143')/'summary.json')
        old=reference[w]['original']['joint'];old=old['raw'] if 'raw' in old else old['all']['raw'];assert summary[w+'/full']['joint']['metrics']['all']==old
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,windows_verified=70,independent_feature_pairs=fc,probabilities_replayed=pc,independent_metric_groups=mc,full_references_matched=7,all_summary_fields_replayed=True))
if __name__=='__main__':run()
