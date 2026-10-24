"""Target labels/keys enter only oracle ceilings and separate evaluation."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from benchmarks.grammar_class_alignment_iteration25 import OUT,load,save
from voynich_smt.class_alignment import maps,score_maps,statistics,COARSE,FINE


def confusion(observed,labels,m,k):
    table=np.zeros((m,k),dtype=int)
    for seq,gold in zip(observed,labels):
        assert len(seq)==len(gold)
        for a,b in zip(seq,gold):table[a,b]+=1
    return table


def metrics(mapping,table):
    k=table.shape[1];total=table.sum();correct=sum(table[a,b] for a,b in enumerate(mapping) if b is not None)
    covered=sum(table[a].sum() for a,b in enumerate(mapping) if b is not None);counts=table.sum(axis=0)
    recalls=[sum(table[a,b] for a,label in enumerate(mapping) if label==b)/count for b,count in enumerate(counts) if count]
    return dict(tokens=int(total),accuracy=float(correct/total),balanced_accuracy=float(np.mean(recalls)),coverage=float(covered/total),
        covered_accuracy=float(correct/covered) if covered else None,class_counts=counts.tolist())


def oracle_maps(table,bijective):
    result={}
    for criterion,weight in [('accuracy',table),('balanced_accuracy',table/np.maximum(1,table.sum(axis=0))[None,:])]:
        if bijective:
            rows,cols=linear_sum_assignment(-weight);mapping=[None]*len(table)
            for a,b in zip(rows,cols):mapping[int(a)]=int(b)
        else:mapping=np.argmax(weight,axis=1).tolist()
        result[criterion]=dict(mapping=mapping,metrics=metrics(mapping,table))
    return result


def evaluate(predictions,observations,truth,models):
    obs_byid={r['id']:r for r in observations};gold_byid={r['id']:r for r in truth};rows=[]
    for prediction in predictions:
        obs=obs_byid[prediction['id']];gold=gold_byid[prediction['id']];table=confusion(obs['query_sequences'],gold['labels'],obs['observed'],obs['k'])
        model=models[prediction['template']]['coarse' if obs['family']=='frequency_proxy' else obs['family']]
        possible,scores,components=score_maps(model,obs['sequences'],obs['observed'],obs['bijective'])
        oracle=oracle_maps(table,obs['bijective']);methods={}
        used=statistics(obs['sequences'],obs['observed'])['unigram']>0
        for method,result in prediction['methods'].items():
            report=dict(**metrics(result['mapping'],table),mapping=result['mapping'],score=result['score'],optimal_maps=result['optimal_maps'],score_gap_to_next=result['score_gap_to_next'])
            if obs['bijective']:
                inverse=gold['inverse_key'];index=int(np.flatnonzero(np.all(possible==np.asarray(inverse),axis=1))[0]);best=int(np.argmax(scores[method]))
                report.update(key_accuracy_observed=float(np.mean([result['mapping'][j]==inverse[j] for j in range(obs['observed']) if used[j]])),
                    known_key_score=float(scores[method][index]),known_key_strictly_outscored=bool(scores[method][index]<result['score']-1e-10),
                    known_key_metrics=metrics(inverse,table),
                    score_components_known={name:float(v[index]) for name,v in components.items()},
                    score_components_best={name:float(v[best]) for name,v in components.items()},
                    representative_best_map=possible[best].tolist(),
                    changed_class_mappings=[dict(anonymous=j,correct=inverse[j],predicted=result['mapping'][j]) for j in range(obs['observed']) if used[j] and result['mapping'][j]!=inverse[j]])
            methods[method]=report
        rng=np.random.default_rng(25071);random=[]
        for _ in range(100):
            mapping=rng.permutation(obs['k']).tolist() if obs['bijective'] else rng.integers(obs['k'],size=obs['observed']).tolist()
            random.append(metrics(mapping,table))
        random_summary={name:float(np.mean([r[name] for r in random])) for name in ('accuracy','balanced_accuracy')}
        rows.append(dict(id=prediction['id'],split=obs['split'],family=obs['family'],noise=obs['noise'],condition=obs['condition'],template=prediction['template'],
            oracle=oracle,random_alignment=random_summary,methods=methods))
    return rows

if __name__=='__main__':
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve target evaluation')
    rows=evaluate(load(OUT/'predictions.json'),load(OUT/'observations.json'),load(OUT/'observation-truth.json'),load(OUT/'models.json'))
    save(OUT/'evaluation.json',rows)
    for r in rows:
        if r['template']=='pooled' and r['condition']=='ordered':
            print(r['split'],r['family'],r['noise'],{m:round(v['balanced_accuracy'],3) for m,v in r['methods'].items()},'oracle',round(r['oracle']['balanced_accuracy']['metrics']['balanced_accuracy'],3))
