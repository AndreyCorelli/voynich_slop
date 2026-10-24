"""Post-hoc agreement consequence audit with oracle context Number only.

Query-word features are masked before relation prediction. Gold head/relation
never enters prediction. Context Number is privileged evaluation evidence.
"""
from collections import Counter
import numpy as np
from benchmarks.grammar_cipher_relations_iteration23 import OUT,load,save,KEYS
from voynich_smt.cipher_relations import ARMS,RADIUS,views,pair_features,matrix,probabilities,decode


def calculate(data,lattice,models):
    predictions=[];metrics={}
    majority=int(np.argmax(np.bincount([y for s in data['train'] for p,y in s['numbers']],minlength=2)))
    for split in ('test_jerome','test_caesar'):
        ss=data[split];vv=views(ss,KEYS[split],lattice)
        for arm in ARMS:
            queries=[];features=[];start=0
            for sentence,view in zip(ss,vv):
                numbers=dict(sentence['numbers'])
                for child,target in sentence['numbers']:
                    pairs=[(child,p) for p in range(max(0,child-RADIUS),min(len(view['tokens']),child+RADIUS+1)) if p!=child]
                    features.extend(pair_features(view,c,p,arm,masked_type=view['tokens'][child]) for c,p in pairs)
                    queries.append((sentence,view,child,target,numbers,pairs,start,start+len(pairs)));start+=len(pairs)
            prob=probabilities(matrix(features),models[arm]['relation']);records=[]
            for sentence,view,child,target,numbers,pairs,a,b in queries:
                selected=decode(pairs,prob[a:b],models[arm]['threshold'])
                edge=selected[0] if selected else None
                # Only subject and nominal-modifier links predict Number.
                parent=edge[1] if edge and edge[2] in (1,3) else None
                covered=parent in numbers and view['tokens'][parent]!=view['tokens'][child] if parent is not None else False
                guess=numbers[parent] if covered else majority
                gold_edge=next((e for e in sentence['edges'] if e[0]==child),None)
                oracle_parent=gold_edge[1] if gold_edge and gold_edge[2] in (1,3) else None
                oracle_covered=oracle_parent in numbers and view['tokens'][oracle_parent]!=view['tokens'][child] if oracle_parent is not None else False
                oracle_guess=numbers[oracle_parent] if oracle_covered else majority
                records.append(dict(sent_id=sentence['sent_id'],position=child,target=target,edge=edge,covered=covered,guess=int(guess),
                    correct_relation=bool(edge and [child,edge[1],edge[2]] in sentence['edges']),
                    oracle_edge_covered=oracle_covered,oracle_edge_guess=int(oracle_guess)))
            guesses=np.array([r['guess'] for r in records]);targets=np.array([r['target'] for r in records]);covered=np.array([r['covered'] for r in records],dtype=bool)
            oracle=np.array([r['oracle_edge_guess'] for r in records]);ocovered=np.array([r['oracle_edge_covered'] for r in records],dtype=bool)
            balanced=lambda values:float(np.mean([np.mean(values[targets==c]==c) for c in (0,1)]))
            metrics[split+'/'+arm]=dict(queries=len(records),coverage=float(covered.mean()),
                covered_number_accuracy=float(np.mean(guesses[covered]==targets[covered])) if covered.any() else None,
                covered_majority_accuracy=float(np.mean(targets[covered]==majority)) if covered.any() else None,
                covered_relation_precision=float(np.mean([r['correct_relation'] for r in records if r['covered']])) if covered.any() else None,
                full_accuracy_with_majority_fallback=float(np.mean(guesses==targets)),full_balanced_accuracy_with_majority_fallback=balanced(guesses),
                oracle_edge_coverage=float(ocovered.mean()),oracle_edge_number_accuracy=float(np.mean(oracle[ocovered]==targets[ocovered])) if ocovered.any() else None,
                oracle_edge_full_balanced_accuracy=balanced(oracle))
            predictions.append(dict(split=split,arm=arm,records=records))
    return metrics,predictions

if __name__=='__main__':
    if (OUT/'agreement-transfer.json').exists():raise ValueError('Preserve previous transfer audit')
    metrics,predictions=calculate(load(OUT/'datasets.json'),load(OUT/'morphology-lattice.json'),load(OUT/'models.json'))
    save(OUT/'agreement-transfer.json',metrics);save(OUT/'agreement-transfer-predictions.json',predictions)
    for key,value in metrics.items():print(key,{k:round(value[k],3) if value[k] is not None else None for k in ('coverage','covered_number_accuracy','covered_relation_precision','full_balanced_accuracy_with_majority_fallback','oracle_edge_full_balanced_accuracy')})
