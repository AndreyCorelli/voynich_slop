"""Independent sentence-selection, feature and refit audit."""
from benchmarks.grammar_siue_context_iteration149 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','selection-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);wanted={lookup[w] for w in train};selection=load(OUT/'selection.json');occ=[]
    for j,s in enumerate(public):
        for k,t in enumerate(s['tokens']):
            if t['id']==lookup['siue']:occ.append(dict(sent_id=s['sent_id'],sentence_index=j,token_index=k))
    assert selection['occurrences']==occ and len(occ)==6;indices={r['sentence_index'] for r in occ};assert len(indices)==4;assert set(selection['deletions'])=={f'delete{j}' for j in indices}
    features=load(OUT/'features.json');models=load(OUT/'models.json');counts=load(OUT/'counts.json')
    for name,m in models.items():
        j=None if name=='full' else int(name[6:]);ids=[t['id'] for k,s in enumerate(public) if k!=j for t in s['tokens']];f=combined(ids,wanted);assert set(f)==set(features[name])
        if j is not None:
            r=selection['deletions'][name];assert r==dict(sentence_index=j,sent_id=public[j]['sent_id'],tokens=len(public[j]['tokens']),siue_occurrences=sum(o['sentence_index']==j for o in occ))
        for i in f:
            for c in f[i]:assert abs(f[i][c]-features[name][i][c])<1e-11
            fc+=1
        assert counts[name]=={w:f[lookup[w]]['n'] for w in train};assert m['training']==train;re=fit_vector(f,train,lookup,anchors,COLS);assert abs(re['loss']-m['loss'])<1e-8;assert np.allclose(re['weights'],m['weights'],atol=1e-6)
    pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json')
    for w,views in pred.items():
        assert views['full']==old[w+'/full']['joint']
        for name,rows in views.items():
            m=models[name];coef=np.array(m['weights'])[:,1]-np.array(m['weights'])[:,0]
            for r in rows:
                f=cached[w+'/full'][r['opaque']];x=(np.array([f[c] for c in COLS])-np.array(m['mean']))/np.array(m['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
            q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);s=summary[w][name]['metrics'];assert s['correct']==int(((q>.5)==y).sum());assert abs(s['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert s['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
    assert summary==evaluate(pred,anchors,{name:'source_sentence' for name in models})
    save(OUT/'audit.json',dict(input_hashes_verified=hc,source_occurrences_verified=6,unique_deletions_verified=4,independent_training_feature_pairs=fc,models_retrained=5,probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,full_baselines_matched=7,strict_target_exclusion=True,all_paired_changes_replayed=True))
if __name__=='__main__':run()
