"""Post-primary fixed-grid sensitivity and threshold-free ranking audit."""
import numpy as np
from benchmarks.grammar_predicate_profiles_iteration42 import OUT,PREVIOUS,load,save,digest,metrics
from voynich_smt.predicate_profiles import vectorize,train,probability


def auc(rows,p):
    positives=[v for r,v in zip(rows,p) if r['case']=='Acc'];negatives=[v for r,v in zip(rows,p) if r['case']=='Abl']
    if not positives or not negatives:return None
    return sum(float(a>b)+.5*float(a==b) for a in positives for b in negatives)/(len(positives)*len(negatives))


def run():
    assert not (OUT/'sensitivity-freeze.json').exists()
    save(OUT/'sensitivity-config.json',dict(k=[1,3,5],strength=[.5,1.,4.],scope='Post-primary descriptive sensitivity. Primary target outcomes already inspected. Fixed grid, no winner selection or revised primary claim. Covers donor smoothing/neighbor averaging; only profile-covered, unseen-in target predicates scored.'))
    save(OUT/'sensitivity-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'sensitivity-config.json',OUT/'source-profiles.json',OUT/'models.json',OUT/'predictions.json',OUT/'evaluation.json')}))
    rec=load(PREVIOUS/'records-truth.json');profiles=load(OUT/'source-profiles.json')['profiles'];v=vectorize(profiles);counts=load(OUT/'models.json')['oracle']['counts'];result={};source=rec['source']['oracle'];predictions={}
    for k in (1,3,5):
        for strength in (.5,1.,4.):
            model=train(source,profiles,k,strength)
            for author in ('Jerome','Caesar'):
                rows=[r for r in rec[author]['oracle'] if r['predicate'] not in counts and r['predicate'] in v];p=[probability(model,r['predicate'],False,v) for r in rows];key=f'{author}/{k}/{strength}';predictions[key]=p;result[key]=dict(**metrics(rows,p),auc=auc(rows,p),p_range=[min(p),max(p)])
    ranking={};shuffles=load(OUT/'shuffled-predictions.json');pred=load(OUT/'predictions.json')
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];ix=[i for i,r in enumerate(rows) if r['predicate'] not in counts and r['predicate'] in v];selected=[rows[i] for i in ix];p=[pred[author]['hybrid'][i] for i in ix];random_auc=[auc(selected,[r['predictions'][author][i] for i in ix]) for r in shuffles]
        ranking[author]=dict(n=len(ix),primary_auc=auc(selected,p),shuffled_auc_mean=float(np.mean(random_auc)),shuffled_auc95=np.quantile(random_auc,[.025,.975]).tolist())
    save(OUT/'sensitivity-predictions.json',predictions);save(OUT/'sensitivity-evaluation.json',dict(grid=result,primary_ranking=ranking));print('Ranking',ranking)
    for key,value in result.items():print(key,value)
if __name__=='__main__':run()
