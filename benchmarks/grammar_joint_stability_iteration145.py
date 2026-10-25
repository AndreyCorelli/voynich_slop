"""Predeclared contiguous-block deletion stability diagnostic."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
OUT=ROOT/'iteration145'

def views_for(streams):
    return {w:{'full':None,**{f'delete{k}':[len(seq)*k//5,len(seq)*(k+1)//5] for k in range(5)}} for w,seq in streams.items()}

def summarize(pred):
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];out={}
    for w,views in pred.items():
        rows=[]
        for word,r in views['full'].items():
            p=r['p'];decision=p>.5;available=[v[word]['p'] for key,v in views.items() if key!='full' and word in v];agree=sum((q>.5)==decision for q in available)
            rows.append(dict(type=word,n=r['n'],probability=p,correct=decision==(anchors[word]=='CCONJ'),available=len(available),agreement_count=agree,unanimous=len(available)==5 and agree==5,minimum_probability=min(available) if available else None,maximum_probability=max(available) if available else None))
        bins={str(k):dict(n=sum(r['available']==5 and r['agreement_count']==k for r in rows),correct=sum(r['available']==5 and r['agreement_count']==k and r['correct'] for r in rows)) for k in range(6)}
        out[w]=dict(rows=rows,all=dict(n=len(rows),correct=sum(r['correct'] for r in rows)),unanimous=dict(n=sum(r['unanimous'] for r in rows),correct=sum(r['unanimous'] and r['correct'] for r in rows)),incomplete=[r['type'] for r in rows if r['available']<5],agreement_bins=bins)
    return out

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_token_budget_iteration144.py'),ROOT/'iteration144/verification-manifest.json',ROOT/'iteration142/models.json',ROOT/'iteration143/streams.json',ROOT/'iteration143/selection.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration135/predictions.json',ROOT/'iteration85/anchor-budgets.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen142 joint RAW only, no refit/offset/label threshold tuning. Same seven already inspected streams. Five fixed consecutive blocks boundaries floor(k*N/5), delete each separately and concatenate remainder (new seam explicitly part of perturbation); full reference. 42 views. Freeze geometry before features and predictions before references. Per full-present candidate: agreement count with full hard prediction (>0.5 CCONJ) across all five deletions; absent candidate is unavailable, never agreement. Predeclared unanimous subset requires available=5 and agreement=5, retain ALL bins0..5 and incomplete cases. Report per-text correct/count, coverage, stable wrong identities. Diagnostic association only, no pooled independence, no cutoff optimization, no nuclei/generalPOS/untouched validation claim. No reserve/new annotations/sealed works.'))
    streams,lookups=inputs();views=views_for(streams);save(OUT/'views.json',views);save(OUT/'views-freeze.json',dict(inputs={str(OUT/'views.json'):digest(OUT/'views.json')}));model=load(ROOT/'iteration142/models.json')['joint']['final'];features={};pred={}
    for w,seq in streams.items():
        features[w]={};pred[w]={}
        for view,bounds in views[w].items():
            ids=seq if bounds is None else seq[:bounds[0]]+seq[bounds[1]:];f=features_for(ids,set(lookups[w].values()));features[w][view]=f;pred[w][view]={word:dict(opaque=i,n=f[i]['n'],p=predict_vector(f[i],model)) for word,i in sorted(lookups[w].items()) if i in f}
        print('predicted',w,flush=True)
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));summary=summarize(pred);save(OUT/'summary.json',summary)
    for w,r in summary.items():print(w,r['all'],r['unanimous'],r['agreement_bins'],r['incomplete'],flush=True)
if __name__=='__main__':run()
