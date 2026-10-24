"""Fresh-test scoring after model/threshold freeze; no test-time selection."""
from collections import Counter
import hashlib
import numpy as np
from benchmarks.grammar_cipher_relations_iteration23 import OUT,load,save,KEYS,relation_matrix,number_matrix
from voynich_smt.cipher_relations import ARMS,LABELS,RADIUS,views,probabilities,decode,encrypt


def prf(tp,predicted,gold):
    return dict(tp=int(tp),predicted=int(predicted),gold=int(gold),precision=float(tp/max(1,predicted)),recall=float(tp/max(1,gold)),f1=float(2*tp/max(1,predicted+gold)))


def per_sentence(rows,gold):
    result=[]
    for prediction,sentence in zip(rows,gold):
        guessed={(c,p,l) for c,p,l,confidence in prediction['edges']};target=set(map(tuple,sentence['edges']))
        result.append([len(guessed&target),len(guessed),len(target)])
    return np.asarray(result,dtype=int)


def relation_metrics(rows,gold):
    counts=per_sentence(rows,gold).sum(axis=0);result={'micro':prf(*counts),'per_relation':{}}
    for label in range(1,len(LABELS)):
        totals=Counter()
        for prediction,sentence in zip(rows,gold):
            guessed={(c,p,l) for c,p,l,confidence in prediction['edges'] if l==label};target={tuple(e) for e in sentence['edges'] if e[2]==label}
            totals['tp']+=len(guessed&target);totals['predicted']+=len(guessed);totals['gold']+=len(target)
        result['per_relation'][LABELS[label]]=prf(totals['tp'],totals['predicted'],totals['gold'])
    result['macro_f1']=float(np.mean([v['f1'] for v in result['per_relation'].values()]))
    result['radius_reachable_gold']=sum(abs(c-p)<=RADIUS for s in gold for c,p,l in s['edges'])
    result['radius_coverage']=result['radius_reachable_gold']/max(1,result['micro']['gold'])
    result['sentences_with_predicted_cycle']=0
    for row in rows:
        heads={c:p for c,p,l,confidence in row['edges']};has_cycle=False
        for c in heads:
            seen=set();current=c
            while current in heads:
                if current in seen:has_cycle=True;break
                seen.add(current);current=heads[current]
        result['sentences_with_predicted_cycle']+=has_cycle
    return result


def number_metrics(predictions,targets,majority):
    guessed=np.asarray(predictions);y=np.asarray(targets)
    recalls=[float(np.mean(guessed[y==c]==c)) for c in (0,1)]
    return dict(queries=len(y),accuracy=float(np.mean(guessed==y)),balanced_accuracy=float(np.mean(recalls)),
        singular_recall=recalls[0],plural_recall=recalls[1],majority_accuracy=float(np.mean(y==majority)),majority_balanced_accuracy=.5,
        class_counts=np.bincount(y,minlength=2).tolist())


def paired_interval(a,b,gold):
    first=per_sentence(a,gold);second=per_sentence(b,gold);rng=np.random.default_rng(2301);differences=[]
    for _ in range(1000):
        indices=rng.integers(len(gold),size=len(gold));x=first[indices].sum(axis=0);y=second[indices].sum(axis=0)
        differences.append(2*x[0]/max(1,x[1]+x[2])-2*y[0]/max(1,y[1]+y[2]))
    return dict(delta_f1=relation_metrics(a,gold)['micro']['f1']-relation_metrics(b,gold)['micro']['f1'],
        sentence_bootstrap_95=[float(x) for x in np.quantile(differences,[.025,.975])],replicates=1000)


def fingerprint(x):
    h=hashlib.sha256()
    for arr in (x.indptr,x.indices):h.update(np.asarray(arr,dtype='<i8').tobytes())
    return h.hexdigest()


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve test evaluation')
    frozen=load(OUT/'fit-freeze.json')
    for p,h in frozen['inputs'].items():assert hashlib.sha256(open(p,'rb').read()).hexdigest()==h,p
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');models=load(OUT/'models.json');predictions=[];summaries={};rekeys=[]
    majority=int(np.argmax(np.bincount([y for s in data['train'] for p,y in s['numbers']],minlength=2)))
    for split in ('test_jerome','test_caesar'):
        sentences=data[split];v=views(sentences,KEYS[split],lattice);scores={};arm_rows={};matrices={}
        for arm in ARMS:
            x,_,slices,pairs=relation_matrix(sentences,v,arm);matrices[arm]=fingerprint(x);p=probabilities(x,models[arm]['relation'])
            rows=[dict(split=split,arm=arm,sent_id=s['sent_id'],edges=decode(pair,p[a:b],models[arm]['threshold'])) for s,(a,b),pair in zip(sentences,slices,pairs)]
            arm_rows[arm]=rows;predictions.extend(rows)
            nx,ny,queries=number_matrix(sentences,v,arm);npred=np.argmax(probabilities(nx,models[arm]['number']),axis=1).tolist()
            save(OUT/f'number-{split}-{arm}.json',dict(queries=queries,predicted=npred))
            scores[arm]=dict(relations=relation_metrics(rows,sentences),masked_number=number_metrics(npred,ny,majority))
        scores['paired_comparisons']={f'{a}-minus-{b}':paired_interval(arm_rows[a],arm_rows[b],sentences) for a,b in [('repetition','geometry'),('ending_blind','repetition'),('ending_exposed','ending_blind'),('dictionary','ending_blind')]}
        summaries[split]=scores
        # Fresh key checks are invariance checks, not extra statistical samples.
        base_cipher={w for s in v for w in s['tokens']}
        for seed in (710,711):
            other=views(sentences,seed,lattice);changed={w for s in other for w in s['tokens']};assert not base_cipher&changed
            for arm in ARMS:
                xx,_,_,_=relation_matrix(sentences,other,arm);same=fingerprint(xx)==matrices[arm];assert same
                rekeys.append(dict(split=split,key=seed,arm=arm,feature_matrix_identical=same,sha256=matrices[arm]))
        print(split,{arm:round(scores[arm]['relations']['micro']['f1'],4) for arm in ARMS},flush=True)
    save(OUT/'predictions.json',predictions);save(OUT/'evaluation.json',summaries);save(OUT/'rekey-checks.json',rekeys)

if __name__=='__main__':run()
