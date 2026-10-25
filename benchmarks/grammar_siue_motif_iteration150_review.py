"""Independent focal-substitution, feature, model and prediction audit."""
from benchmarks.grammar_siue_motif_iteration150 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','selection-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);wanted={lookup[w] for w in train};ids=[t['id'] for s in public for t in s['tokens']];sel=load(OUT/'selection.json');offset=sum(len(s['tokens']) for s in public[:590]);positions=[offset+35,offset+37,offset+39];assert sel['positions']==positions and public[590]['sent_id']=='76252';assert sel['fresh']==[hashlib.sha256(f'motif150|{p}'.encode()).hexdigest() for p in positions];assert len(set(sel['fresh']))==3 and not set(sel['fresh'])&set(ids);assert set(sel['transforms'])==set(map(str,range(1,8)))
    features=load(OUT/'features.json');models=load(OUT/'models.json')
    for name in ['full']+list(map(str,range(1,8))):
        mask=0 if name=='full' else int(name);selected=[p for j,p in enumerate(positions) if mask&(2**j)]
        if mask:assert sel['transforms'][name]==selected
        seq=[sel['fresh'][positions.index(p)] if p in selected else i for p,i in enumerate(ids)];assert len(seq)==len(ids);assert sum(a!=b for a,b in zip(seq,ids))==len(selected);f=combined(seq,wanted);assert set(f)==set(features[name])
        for i in f:
            for c in f[i]:assert abs(f[i][c]-features[name][i][c])<1e-11
            fc+=1
        assert f[lookup['siue']]['n']==6-len(selected);m=models[name];assert m['training']==train;re=fit_vector(f,train,lookup,anchors,COLS);assert abs(re['loss']-m['loss'])<1e-8 and np.allclose(re['weights'],m['weights'],atol=1e-6)
    assert models['sentence_deleted']==load(ROOT/'iteration149/models.json')['delete590'];pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');deleted=load(ROOT/'iteration149/predictions.json')
    for w,views in pred.items():
        assert views['full']==old[w+'/full']['joint'] and views['sentence_deleted']==deleted[w]['delete590']
        for name,rows in views.items():
            m=models[name];coef=np.array(m['weights'])[:,1]-np.array(m['weights'])[:,0]
            for r in rows:
                f=cached[w+'/full'][r['opaque']];x=(np.array([f[c] for c in COLS])-np.array(m['mean']))/np.array(m['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
            q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);s=summary[w][name]['metrics'];assert s['correct']==int(((q>.5)==y).sum());assert abs(s['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert s['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
    assert summary==evaluate(pred,anchors,{name:'opaque_substitution' for name in models})
    save(OUT/'audit.json',dict(input_hashes_verified=hc,nonempty_subsets_verified=7,source_tokens_otherwise_unchanged=True,independent_training_feature_pairs=fc,models_retrained=8,probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,full_and_sentence_deleted_references_matched=14,strict_target_exclusion=True))
if __name__=='__main__':run()
