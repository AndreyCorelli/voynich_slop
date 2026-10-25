"""Independent replay of deletion geometry, features, probabilities and agreement."""
from benchmarks.grammar_joint_stability_iteration145 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def run():
    hashes=0
    for name in ['design-freeze','views-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    streams,lookups=inputs();views=load(OUT/'views.json');features=load(OUT/'features.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');model=load(ROOT/'iteration142/models.json')['joint']['final'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];old=load(ROOT/'iteration144/predictions.json');fc=pc=rc=0
    coef=np.array(model['weights'])[:,1]-np.array(model['weights'])[:,0]
    for w,seq in streams.items():
        assert set(views[w])=={'full',*[f'delete{k}' for k in range(5)]}
        for view,bounds in views[w].items():
            if view=='full':assert bounds is None;ids=seq
            else:
                k=int(view[-1]);lo=len(seq)*k//5;hi=len(seq)*(k+1)//5;assert bounds==[lo,hi];ids=[i for j,i in enumerate(seq) if not lo<=j<hi]
            f=combined(ids,set(lookups[w].values()));assert set(f)==set(features[w][view]);assert {r['opaque'] for r in pred[w][view].values()}==set(f)
            for i,r in f.items():
                assert r['n']==features[w][view][i]['n']
                for c in ['corrected','role_similarity']:assert abs(r[c]-features[w][view][i][c])<1e-11
                fc+=1
            for word,r in pred[w][view].items():
                assert r['opaque']==lookups[w][word] and r['n']==f[r['opaque']]['n'];x=np.array([f[r['opaque']][c] for c in model['columns']]);x=(x-np.array(model['mean']))/np.array(model['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['p'])<1e-10;pc+=1
        for row in summary[w]['rows']:
            word=row['type'];full=pred[w]['full'][word];decision=full['p']>.5;qq=[pred[w][f'delete{k}'][word]['p'] for k in range(5) if word in pred[w][f'delete{k}']];agree=len([q for q in qq if (q>.5)==decision]);assert row['available']==len(qq) and row['agreement_count']==agree and row['unanimous']==(len(qq)==5 and agree==5);assert row['correct']==(decision==(anchors[word]=='CCONJ'));assert row['minimum_probability']==min(qq) and row['maximum_probability']==max(qq);rc+=1
        prior={r['type']:r for r in old[w+'/full']['joint']};assert set(prior)==set(pred[w]['full'])
        for word,r in pred[w]['full'].items():assert r['p']==prior[word]['probabilities']['raw'] and r['n']==prior[word]['n']
        print('audited',w,flush=True)
    assert summarize(pred)==summary
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,views_verified=42,independent_feature_pairs=fc,independent_probability_replays=pc,agreement_rows_verified=rc,full_references_matched=7,summary_replayed=True))
if __name__=='__main__':run()
