"""Expand training types using existing source-fit annotations only."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
OUT=ROOT/'iteration147';COLS=['corrected','role_similarity']

def eligibility():
    public,lookup,anchors,split,words,allowed=training_inputs();data=load(ROOT/'iteration44/annotations-truth.json');fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];counts={}
    for sid in fit:
        for t in data[sid]['tokens']:counts.setdefault(t['word'],Counter())[t['pos']]+=1
    old=split['training'];records={};labels={w:anchors[w] for w in old}
    for w,c in sorted(counts.items()):
        tag,n=sorted(c.items(),key=lambda x:(-x[1],x[0]))[0];total=sum(c.values());eligible=w not in words and total>=5 and tag in ['ADP','CCONJ'] and n/total>=.8
        if tag in ['ADP','CCONJ'] or w in old:records[w]=dict(count=total,modal=tag,modal_count=n,purity=n/total,eligible_new=eligible and w not in old,pos_counts=dict(c))
        if eligible and w not in old:labels[w]=tag
    folds=dict(split['oof_folds'])
    for tag in ['ADP','CCONJ']:
        added=sorted([w for w in labels if w not in old and labels[w]==tag],key=lambda w:hashlib.sha256(('expanded147|'+w).encode()).hexdigest())
        for j,w in enumerate(added):folds[w]=j%3
    lookup.update({w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in labels});return public,lookup,labels,folds,records,old,words

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_scalars_iteration142.py'),ROOT/'iteration142/models.json',ROOT/'iteration142/oof-probabilities.json',ROOT/'iteration144/predictions.json',ROOT/'iteration144/verification-manifest.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration143/streams.json',ROOT/'iteration143/selection.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration135/predictions.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Expand existing13 training types ONLY using cached44 annotations in49 partition0 fit. Retain original13 labels/folds; add all other types with>=5 total fit occurrences, modalPOS ADP/CCONJ, modal share>=.8 (ties lexicographic); exclude entire16targetcatalogue. Added types within each class sorted SHA(expanded147|word), roundrobin3folds. No wordlength/identity/target-outcome eligibility. Allmodal labels from fit ONLY, no new annotations/reserve/sealedworks. Original two scalar features, same142 classbalanced L2/optimizer/trainfoldstandardization/raw>.5. Fit3OOF+final, compare old13 OOF on exactly original folds (extra types may train), report expanded OOF separately never equate denominators. Freeze eligibility then features/models before seven inspected target fullstreams. Unchanged142baseline, allpresenttype metrics/labels same144, no calibration/model/authorselection. If no extra types eligible stop diagnostic. No new null batch: this tests training expansion; if promising null/stability replication is next, do not claim verified transfer from target improvement alone.'))
    public,lookup,labels,folds,records,old,words=eligibility();train=sorted(labels);assert not set(train)&set(words);save(OUT/'eligibility.json',dict(records=records,labels=labels,folds=folds,old=old,training=train,lookup={w:lookup[w] for w in train}));save(OUT/'eligibility-freeze.json',dict(inputs={str(OUT/'eligibility.json'):digest(OUT/'eligibility.json')}));print('TRAINING',labels,flush=True)
    if len(train)==len(old):save(OUT/'no-expansion.json',dict(reason='No additional eligible types'));return
    ids=[t['id'] for s in public for t in s['tokens']];f=features_for(ids,{lookup[w] for w in train});models={};oof={}
    for fold in range(3):
        held=[w for w in train if folds[w]==fold];tr=[w for w in train if w not in held];models[str(fold)]=fit_vector(f,tr,lookup,labels,COLS);oof.update({w:predict_vector(f[lookup[w]],models[str(fold)]) for w in held})
    models['final']=fit_vector(f,train,lookup,labels,COLS)
    for n,x in [('training-features',f),('models',models),('oof',oof)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['training-features','models','oof']}));streams,lookups=inputs();pred={};features={}
    for w,seq in streams.items():
        f=features_for(seq,set(lookups[w].values()));features[w]=f;pred[w]=[dict(type=word,opaque=i,n=f[i]['n'],sentences=1,supported=f[i]['n']>=5,probabilities=dict(raw=predict_vector(f[i],models['final']))) for word,i in sorted(lookups[w].items()) if i in f]
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];prior=load(ROOT/'iteration144/predictions.json');summary={w:{name:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for name,rows in [('baseline',prior[w+'/full']['joint']),('expanded',pred[w])]} for w in pred};old_oof=load(ROOT/'iteration142/oof-probabilities.json')['joint'];source={}
    for name,rr,ww in [('baseline_old13',old_oof,old),('expanded_old13',oof,old),('expanded_all',oof,train)]:
        source[name]=metrics([dict(type=w,n=frozenset() and 0 or 1,sentences=1,supported=True,probabilities=dict(raw=rr[w]),**{'class':labels[w]}) for w in ww],'raw')
    save(OUT/'source-summary.json',source);save(OUT/'summary.json',summary);print('SOURCE',source,flush=True)
    for w,r in summary.items():print(w,r,flush=True)
if __name__=='__main__':run()
