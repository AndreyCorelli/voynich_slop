"""Sentence-cluster bootstrap: reuse one draw jointly across perturbation seeds."""
import numpy as np
from benchmarks.grammar_fresh_repair_iteration39 import OUT,load,save

def run():
    observations=load(OUT/'observations.json');truth=load(OUT/'observation-truth.json');predictions=load(OUT/'predictions.json');results={}
    for author,o in observations.items():
        lengths=list(map(len,o['sequences']));boundaries=np.cumsum([0]+lengths);gold=np.concatenate(truth[author]);rng=np.random.default_rng(39001);draws=rng.integers(0,40,(10000,40));den=np.array(lengths[60:])
        for rate in (.1,.5):
            for arm in ('word','ending'):
                for strategy in ('context','random'):
                    rows=[r for r in predictions if (r['author'],r['rate'],r['arm'],r['strategy'])==(author,rate,arm,strategy)];net=[]
                    for row in rows:
                        a=np.array(row['baseline'])==gold;b=np.array(row['prediction'])==gold
                        net.append([int(b[boundaries[i]:boundaries[i+1]].sum()-a[boundaries[i]:boundaries[i+1]].sum()) for i in range(60,100)])
                    per_sentence=np.array(net).mean(axis=0);gains=per_sentence[draws].sum(axis=1)/den[draws].sum(axis=1);results[f'{author}/{rate}/{arm}/{strategy}']=np.quantile(gains,[.025,.975]).tolist()
    save(OUT/'intervals.json',dict(method='10000 within-author sentence-cluster draws, shared across five perturbations; conditional on these masks and frozen transductive fits, not model refits or population guarantees.',gain_95=results))
if __name__=='__main__':run()
