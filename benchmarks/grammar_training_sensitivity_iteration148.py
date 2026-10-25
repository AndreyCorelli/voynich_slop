"""Predeclared leave-one-training-type-out sensitivity of the joint model."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
OUT=ROOT/'iteration148';COLS=['corrected','role_similarity']

def evaluate(pred,anchors,training_labels):
    result={}
    for work,models in pred.items():
        baseline={r['type']:r for r in models['full']};result[work]={}
        for name,rows in models.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];changes=[]
            for r in rows:
                b=baseline[r['type']];p=r['probabilities']['raw'];q=b['probabilities']['raw'];correct=(p>.5)==(anchors[r['type']]=='CCONJ');old=(q>.5)==(anchors[r['type']]=='CCONJ')
                if (p>.5)!=(q>.5):changes.append(dict(type=r['type'],baseline_correct=old,omitted_correct=correct,baseline_probability=q,omitted_probability=p))
            result[work][name]=dict(metrics=metrics(refs,'raw'),omitted_class=None if name=='full' else training_labels[name],decision_flips=changes,correct_to_wrong=sum(x['baseline_correct'] for x in changes),wrong_to_correct=sum(x['omitted_correct'] for x in changes),mean_absolute_probability_change=float(np.mean([abs(r['probabilities']['raw']-baseline[r['type']]['probabilities']['raw']) for r in rows])),maximum_absolute_probability_change=max(abs(r['probabilities']['raw']-baseline[r['type']]['probabilities']['raw']) for r in rows))
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_scalars_iteration142.py'),ROOT/'iteration142/models.json',ROOT/'iteration142/training-features.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration144/verification-manifest.json',ROOT/'iteration116/type-split.json',ROOT/'iteration85/anchor-budgets.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Leave each of original13 training types out once; same original two scalar features, classbalanced L2 optimizer142 and retained-type standardization, no new features/labels/calibration/thresholdselection. Reuse frozen142 training feature cache and144 fulltarget features, all7alreadyinspectedtexts. Freeze all13 omission models before predictions and all predictions before target modal-reference evaluation. Full142 model unchanged baseline must exactly replay144. Allpresent types, no favorable omission/author selection; metrics accuracy,NLL,AUC plus paired decision flips correct->wrong/wrong->correct and mean/max absolute probability movement. Report all13 omissions grouped ADP10/CCONJ3, no pooling as independent evidence, no agreementconfidencegate/nuclei/generalPOS claims. No reserve/sealedworks/newannotations/rawtext. Purpose model-training sensitivity diagnostic.'))
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates']);f=load(ROOT/'iteration142/training-features.json');public,lookup,_,_,_,_=training_inputs();models={'full':load(ROOT/'iteration142/models.json')['joint']['final']}
    for omitted in train:models[omitted]=fit_vector(f,[w for w in train if w!=omitted],lookup,anchors,COLS)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/'models.json'):digest(OUT/'models.json')}));cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');pred={}
    for key,configs in old.items():
        if not key.endswith('/full'):continue
        work=key[:-5];pred[work]={}
        for name,m in models.items():pred[work][name]=[dict(r,probabilities=dict(raw=predict_vector(cached[key][r['opaque']],m))) for r in configs['joint']]
        assert pred[work]['full']==configs['joint']
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary=evaluate(pred,anchors,anchors);save(OUT/'summary.json',summary)
    for w,rr in summary.items():print(w,{name:dict(correct=r['metrics']['correct'],n=r['metrics']['n'],auc=r['metrics']['auc'],nll=r['metrics']['nll'],flips=len(r['decision_flips'])) for name,r in rr.items()},flush=True)
if __name__=='__main__':run()
